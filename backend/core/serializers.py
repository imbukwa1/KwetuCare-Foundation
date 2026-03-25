from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Count
from django.utils import timezone
from django.utils.text import slugify
import re
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.db import transaction

from .models import AuditLog, Consultation, DrugInventory, Patient, Prescription, Triage
from .realtime import publish_audit_event

User = get_user_model()


def build_unique_username(full_name):
    base_username = slugify(full_name).replace("-", "_") or "user"
    username = base_username
    suffix = 1

    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base_username}_{suffix}"

    return username


def create_audit_log(*, user, action, patient=None, details=None):
    payload = details or {}
    AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        patient=patient,
        details=payload,
    )
    publish_audit_event(action=action, patient=patient, details=payload)


def generate_patient_reg_no():
    current_year = timezone.now().year
    prefix = f"KCF-{current_year}-"
    latest_patient = (
        Patient.objects.filter(reg_no__startswith=prefix)
        .order_by("-reg_no")
        .first()
    )

    next_number = 1
    if latest_patient:
        try:
            next_number = int(latest_patient.reg_no.rsplit("-", 1)[-1]) + 1
        except (TypeError, ValueError):
            next_number = 1

    return f"{prefix}{next_number:04d}"


class SignupSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(write_only=True, max_length=150)
    role = serializers.ChoiceField(choices=User.Role.choices)
    email = serializers.EmailField()

    def validate_full_name(self, value):
        normalized_value = " ".join(value.split()).strip()
        if not normalized_value:
            raise serializers.ValidationError("Full name is required.")
        return normalized_value

    def validate_email(self, value):
        normalized_value = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return normalized_value

    def create(self, validated_data):
        full_name = validated_data.pop("full_name")
        password = validated_data.pop("password")
        name_parts = full_name.split(" ", 1)
        user = User(
            username=build_unique_username(full_name),
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
            **validated_data,
        )
        user.is_approved = settings.BYPASS_USER_APPROVAL
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "username", "full_name", "email", "role", "is_approved")

    def get_full_name(self, obj):
        full_name = obj.get_full_name().strip()
        return full_name or obj.username

    def get_is_approved(self, obj):
        return True if settings.BYPASS_USER_APPROVAL else obj.is_approved


class LoginSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Invalid email/username or password.",
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["is_approved"] = user.is_approved
        return token

    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "").strip()
        password = attrs.get("password")

        lookup_value = identifier
        if "@" in identifier:
            try:
                lookup_value = User.objects.get(email__iexact=identifier).username
            except User.DoesNotExist:
                self.fail("no_active_account")

        authenticate_kwargs = {
            self.username_field: lookup_value,
            "password": password,
        }
        request = self.context.get("request")
        if request is not None:
            authenticate_kwargs["request"] = request

        self.user = authenticate(**authenticate_kwargs)
        if not self.user:
            self.fail("no_active_account")

        refresh = self.get_token(self.user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        data["user"] = UserSerializer(self.user).data
        return data


class PatientRegistrationSerializer(serializers.ModelSerializer):
    reg_no = serializers.CharField(read_only=True)

    class Meta:
        model = Patient
        fields = (
            "id",
            "name",
            "age",
            "gender",
            "phone",
            "camp",
            "village",
            "next_of_kin",
            "has_child",
            "child_name",
            "child_age",
            "child_date_of_birth",
            "guardian_name",
            "reg_no",
            "priority",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "reg_no", "status", "created_at")

    def validate_age(self, value):
        if value < 0 or value > 120:
            raise serializers.ValidationError("Age must be between 0 and 120.")
        return value

    def validate_child_age(self, value):
        if value is not None and (value < 0 or value > 120):
            raise serializers.ValidationError("Child age must be between 0 and 120.")
        return value

    def validate(self, attrs):
        has_child = attrs.get("has_child", False)

        if has_child:
            child_name = (attrs.get("child_name") or "").strip()
            guardian_name = (attrs.get("guardian_name") or "").strip()
            child_age = attrs.get("child_age")
            child_date_of_birth = attrs.get("child_date_of_birth")

            errors = {}
            if not child_name:
                errors["child_name"] = "Child name is required when a child is present."
            if child_age in (None, ""):
                errors["child_age"] = "Child age is required when a child is present."
            if not child_date_of_birth:
                errors["child_date_of_birth"] = "Child date of birth is required when a child is present."
            if not guardian_name:
                errors["guardian_name"] = "Guardian name is required when a child is present."

            if errors:
                raise serializers.ValidationError(errors)

            attrs["child_name"] = child_name
            attrs["guardian_name"] = guardian_name
        else:
            attrs["child_name"] = ""
            attrs["child_age"] = None
            attrs["child_date_of_birth"] = None
            attrs["guardian_name"] = ""

        return attrs

    def create(self, validated_data):
        validated_data["status"] = Patient.Status.TRIAGE

        for _ in range(5):
            validated_data["reg_no"] = generate_patient_reg_no()
            try:
                patient = super().create(validated_data)
                break
            except IntegrityError:
                continue
        else:
            raise serializers.ValidationError(
                "Could not generate a unique registration number. Please try again."
            )

        create_audit_log(
            user=self.context["request"].user,
            action="patient_registered",
            patient=patient,
            details={"status": patient.status, "reg_no": patient.reg_no},
        )
        return patient


class TriageSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Triage
        fields = (
            "id",
            "patient_id",
            "patient",
            "blood_pressure",
            "temperature",
            "weight",
            "heart_rate",
            "nurse_notes",
            "created_at",
        )
        read_only_fields = ("id", "patient", "created_at")

    def validate_temperature(self, value):
        if value < 30 or value > 45:
            raise serializers.ValidationError("Temperature must be between 30.0 and 45.0 Celsius.")
        return value

    def validate_blood_pressure(self, value):
        normalized_value = value.strip()
        if not re.fullmatch(r"\d{2,3}/\d{2,3}", normalized_value):
            raise serializers.ValidationError("Blood pressure must be in the format systolic/diastolic, e.g. 120/80.")
        return normalized_value

    def validate_weight(self, value):
        if value <= 0 or value > 500:
            raise serializers.ValidationError("Weight must be greater than 0 and not exceed 500 kg.")
        return value

    def validate_heart_rate(self, value):
        if value < 30 or value > 220:
            raise serializers.ValidationError("Heart rate must be between 30 and 220 bpm.")
        return value

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.TRIAGE:
            raise serializers.ValidationError(
                "Only patients in the triage stage can be processed by a nurse."
            )

        if hasattr(patient, "triage"):
            raise serializers.ValidationError("Triage has already been recorded for this patient.")

        self.context["patient"] = patient
        return value

    def create(self, validated_data):
        validated_data.pop("patient_id")

        with transaction.atomic():
            patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

            if patient.status != Patient.Status.TRIAGE:
                raise serializers.ValidationError(
                    "This patient is no longer in the triage stage."
                )

            if Triage.objects.filter(patient=patient).exists():
                raise serializers.ValidationError(
                    "Triage has already been recorded for this patient."
                )

            triage = Triage.objects.create(patient=patient, **validated_data)
            patient.status = Patient.Status.DOCTOR
            patient.doctor_started_at = timezone.now()
            patient.save(update_fields=["status", "doctor_started_at"])
            create_audit_log(
                user=self.context["request"].user,
                action="triage_completed",
                patient=patient,
                details={
                    "blood_pressure": triage.blood_pressure,
                    "temperature": str(triage.temperature),
                    "weight": str(triage.weight),
                    "heart_rate": triage.heart_rate,
                    "status": patient.status,
                },
            )
            return triage


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ("drug_name", "dosage", "quantity", "frequency", "status")

    def validate_drug_name(self, value):
        normalized_value = value.strip()
        if not normalized_value:
            raise serializers.ValidationError("Drug name is required.")
        return normalized_value

    def validate_dosage(self, value):
        normalized_value = value.strip()
        if not normalized_value:
            raise serializers.ValidationError("Dosage is required.")
        return normalized_value

    def validate_frequency(self, value):
        normalized_value = value.strip()
        if not normalized_value:
            raise serializers.ValidationError("Frequency is required.")
        return normalized_value


class ConsultationCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)
    prescriptions = PrescriptionCreateSerializer(many=True)

    class Meta:
        model = Consultation
        fields = (
            "id",
            "patient_id",
            "patient",
            "doctor_notes",
            "prescriptions",
            "created_at",
        )
        read_only_fields = ("id", "patient", "created_at")

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError(
                "Only patients in the doctor stage can be processed by a doctor."
            )

        if hasattr(patient, "consultation"):
            raise serializers.ValidationError(
                "Consultation has already been recorded for this patient."
            )

        self.context["patient"] = patient
        return value

    def validate_prescriptions(self, value):
        if not value:
            raise serializers.ValidationError("At least one prescription is required.")

        inventory_by_name = {
            item.drug_name.strip().lower(): item.drug_name
            for item in DrugInventory.objects.all()
        }
        seen_drugs = set()
        normalized_items = []
        for item in value:
            drug_name = item["drug_name"].strip().lower()
            if drug_name in seen_drugs:
                raise serializers.ValidationError("Duplicate drug names are not allowed in one consultation.")
            canonical_name = inventory_by_name.get(drug_name)
            if canonical_name is None:
                raise serializers.ValidationError(
                    f"{item['drug_name'].strip()} is not available in inventory."
                )
            seen_drugs.add(drug_name)
            normalized_items.append(
                {
                    **item,
                    "drug_name": canonical_name,
                }
            )

        return normalized_items

    @transaction.atomic
    def create(self, validated_data):
        prescriptions_data = validated_data.pop("prescriptions")
        validated_data.pop("patient_id")

        patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError(
                "This patient is no longer in the doctor stage."
            )

        if Consultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError(
                "Consultation has already been recorded for this patient."
            )

        consultation = Consultation.objects.create(patient=patient, **validated_data)

        for prescription_data in prescriptions_data:
            Prescription.objects.create(
                consultation=consultation,
                **prescription_data,
            )

        patient.status = Patient.Status.PHARMACY
        patient.pharmacy_started_at = timezone.now()
        patient.save(update_fields=["status", "pharmacy_started_at"])
        create_audit_log(
            user=self.context["request"].user,
            action="consultation_completed",
            patient=patient,
            details={
                "status": patient.status,
                "prescription_count": len(prescriptions_data),
            },
        )
        return consultation


class PrescriptionDispenseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Prescription.Status.choices)


class PharmacyDispenseSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    prescriptions = PrescriptionDispenseSerializer(many=True)

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.PHARMACY:
            raise serializers.ValidationError(
                "Only patients in the pharmacy stage can be processed by a pharmacist."
            )

        if not hasattr(patient, "consultation"):
            raise serializers.ValidationError("This patient has no consultation record.")

        self.context["patient"] = patient
        return value

    def validate_prescriptions(self, value):
        if not value:
            raise serializers.ValidationError("At least one prescription update is required.")

        prescription_ids = [item["id"] for item in value]
        if len(prescription_ids) != len(set(prescription_ids)):
            raise serializers.ValidationError("Duplicate prescription updates are not allowed.")

        return value

    @transaction.atomic
    def save(self, **kwargs):
        patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

        if patient.status != Patient.Status.PHARMACY:
            raise serializers.ValidationError(
                "This patient is no longer in the pharmacy stage."
            )

        if not hasattr(patient, "consultation"):
            raise serializers.ValidationError("This patient has no consultation record.")

        consultation = patient.consultation
        prescription_map = {
            prescription.id: prescription
            for prescription in consultation.prescriptions.select_for_update()
        }
        inventory_map = {
            item.drug_name.strip().lower(): item
            for item in DrugInventory.objects.select_for_update()
        }

        submitted_ids = set()
        for item in self.validated_data["prescriptions"]:
            prescription_id = item["id"]
            prescription = prescription_map.get(prescription_id)
            if prescription is None:
                raise serializers.ValidationError(
                    {"prescriptions": f"Prescription {prescription_id} does not belong to this patient."}
                )

            requested_status = item["status"]
            if requested_status == Prescription.Status.GIVEN:
                inventory = inventory_map.get(prescription.drug_name.lower())
                if inventory is None:
                    raise serializers.ValidationError(
                        {"prescriptions": f"No inventory record found for {prescription.drug_name}."}
                    )
                if inventory.stock_quantity < prescription.quantity:
                    raise serializers.ValidationError(
                        {
                            "prescriptions": (
                                f"Insufficient stock for {prescription.drug_name}. "
                                f"Available: {inventory.stock_quantity}, required: {prescription.quantity}."
                            )
                        }
                    )
                inventory.stock_quantity -= prescription.quantity
                inventory.save(update_fields=["stock_quantity", "updated_at"])

            prescription.status = item["status"]
            prescription.save(update_fields=["status"])
            submitted_ids.add(prescription_id)

        if submitted_ids != set(prescription_map.keys()):
            raise serializers.ValidationError(
                {"prescriptions": "All consultation prescriptions must be updated before completion."}
            )

        patient.status = Patient.Status.COMPLETE
        patient.completed_at = timezone.now()
        patient.save(update_fields=["status", "completed_at"])
        create_audit_log(
            user=self.context["request"].user,
            action="pharmacy_dispensed",
            patient=patient,
            details={
                "status": patient.status,
                "prescription_ids": sorted(submitted_ids),
            },
        )
        return patient

    def to_representation(self, instance):
        consultation = instance.consultation
        return {
            "patient_id": instance.id,
            "reg_no": instance.reg_no,
            "status": instance.status,
            "prescriptions": [
                {
                    "id": prescription.id,
                    "drug_name": prescription.drug_name,
                    "status": prescription.status,
                }
                for prescription in consultation.prescriptions.all().order_by("id")
            ],
        }


class DrugInventorySerializer(serializers.ModelSerializer):
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = DrugInventory
        fields = (
            "id",
            "drug_name",
            "amount",
            "stock_quantity",
            "reorder_level",
            "is_low_stock",
            "updated_at",
        )
        read_only_fields = ("id", "is_low_stock", "updated_at")

    def get_is_low_stock(self, obj):
        return obj.stock_quantity <= obj.reorder_level

    def validate_drug_name(self, value):
        normalized_value = value.strip()
        if not normalized_value:
            raise serializers.ValidationError("Drug name is required.")
        queryset = DrugInventory.objects.filter(drug_name__iexact=normalized_value)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("A drug with this name already exists.")
        return normalized_value

    def validate_amount(self, value):
        normalized_value = value.strip()
        if not normalized_value:
            raise serializers.ValidationError("Amount is required.")
        return normalized_value


class InventoryAdjustSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1, required=False)
    quantity = serializers.IntegerField(min_value=1, required=False)

    def validate(self, attrs):
        amount = attrs.get("amount")
        quantity = attrs.get("quantity")

        if amount is None and quantity is None:
            raise serializers.ValidationError("Provide restock amount or quantity.")

        if amount is not None and quantity is not None and amount != quantity:
            raise serializers.ValidationError(
                "Amount and quantity must match when both are provided."
            )

        attrs["amount"] = amount if amount is not None else quantity
        return attrs


class PatientListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    guardian_name = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "reg_no",
            "name",
            "age",
            "gender",
            "phone",
            "camp",
            "village",
            "has_child",
            "guardian_name",
            "priority",
            "status",
            "created_at",
        )

    def get_name(self, obj):
        if obj.has_child and obj.child_name:
            return obj.child_name
        return obj.name

    def get_age(self, obj):
        if obj.has_child and obj.child_age is not None:
            return obj.child_age
        return obj.age

    def get_guardian_name(self, obj):
        if obj.has_child:
            return obj.guardian_name or obj.name
        return ""


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ("id", "drug_name", "dosage", "quantity", "frequency", "status")


class TriageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Triage
        fields = (
            "blood_pressure",
            "temperature",
            "weight",
            "heart_rate",
            "nurse_notes",
            "created_at",
        )


class PatientWorkflowDetailSerializer(serializers.ModelSerializer):
    consultation = serializers.SerializerMethodField()
    prescriptions = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    guardian_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    triage = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "reg_no",
            "name",
            "age",
            "camp",
            "has_child",
            "guardian_name",
            "priority",
            "status",
            "triage",
            "consultation",
            "prescriptions",
        )

    def get_name(self, obj):
        if obj.has_child and obj.child_name:
            return obj.child_name
        return obj.name

    def get_age(self, obj):
        if obj.has_child and obj.child_age is not None:
            return obj.child_age
        return obj.age

    def get_guardian_name(self, obj):
        if obj.has_child:
            return obj.guardian_name or obj.name
        return ""

    def get_triage(self, obj):
        if not hasattr(obj, "triage"):
            return None
        return TriageDetailSerializer(obj.triage).data

    def get_consultation(self, obj):
        if not hasattr(obj, "consultation"):
            return None
        prescriptions = obj.consultation.prescriptions.all().order_by("id")
        return {
            "id": obj.consultation.id,
            "doctor_notes": obj.consultation.doctor_notes,
            "created_at": obj.consultation.created_at,
            "prescriptions": PrescriptionDetailSerializer(prescriptions, many=True).data,
        }

    def get_prescriptions(self, obj):
        if not hasattr(obj, "consultation"):
            return []
        prescriptions = obj.consultation.prescriptions.all().order_by("id")
        return PrescriptionDetailSerializer(prescriptions, many=True).data


class CampPatientSummarySerializer(serializers.Serializer):
    camp = serializers.CharField()
    total_patients = serializers.IntegerField()


class CampDrugIssuedSummarySerializer(serializers.Serializer):
    consultation__patient__camp = serializers.CharField()
    total_drugs_issued = serializers.IntegerField()

    def to_representation(self, instance):
        return {
            "camp": instance["consultation__patient__camp"],
            "total_drugs_issued": instance["total_drugs_issued"],
        }


class CampDrugDetailSerializer(serializers.Serializer):
    camp = serializers.CharField()
    drug_name = serializers.CharField()
    amount = serializers.CharField()
    total_quantity = serializers.IntegerField()


class StageWaitingCountsSerializer(serializers.Serializer):
    triage = serializers.IntegerField()
    doctor = serializers.IntegerField()
    pharmacy = serializers.IntegerField()
    complete = serializers.IntegerField()


class AdminReportSerializer(serializers.Serializer):
    patients_per_camp = CampPatientSummarySerializer(many=True)
    drugs_issued_per_camp = CampDrugIssuedSummarySerializer(many=True)
    drug_details_per_camp = CampDrugDetailSerializer(many=True)
    stage_waiting_counts = StageWaitingCountsSerializer()
    completed_patients = serializers.IntegerField()


class StageTimingAnalyticsSerializer(serializers.Serializer):
    average_triage_to_doctor_minutes = serializers.FloatField()
    average_doctor_to_pharmacy_minutes = serializers.FloatField()
    average_pharmacy_to_complete_minutes = serializers.FloatField()
    average_total_completion_minutes = serializers.FloatField()
    completed_patient_count = serializers.IntegerField()
