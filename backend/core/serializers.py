from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.db import transaction

from .models import AuditLog, Consultation, DrugInventory, Patient, Prescription, Triage

User = get_user_model()


def create_audit_log(*, user, action, patient=None, details=None):
    AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        patient=patient,
        details=details or {},
    )


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "role")

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.is_approved = False
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "is_approved")


class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["is_approved"] = user.is_approved
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class PatientRegistrationSerializer(serializers.ModelSerializer):
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
            "reg_no",
            "priority",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "status", "created_at")

    def validate_age(self, value):
        if value < 0 or value > 120:
            raise serializers.ValidationError("Age must be between 0 and 120.")
        return value

    def validate_reg_no(self, value):
        normalized_value = value.strip()
        if not normalized_value:
            raise serializers.ValidationError("Registration number is required.")

        if Patient.objects.filter(reg_no__iexact=normalized_value).exists():
            raise serializers.ValidationError("A patient with this registration number already exists.")

        return normalized_value

    def create(self, validated_data):
        validated_data["status"] = Patient.Status.TRIAGE
        patient = super().create(validated_data)
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

        seen_drugs = set()
        for item in value:
            drug_name = item["drug_name"].strip().lower()
            if drug_name in seen_drugs:
                raise serializers.ValidationError("Duplicate drug names are not allowed in one consultation.")
            seen_drugs.add(drug_name)

        return value

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
            item.drug_name.lower(): item
            for item in DrugInventory.objects.select_for_update().filter(
                drug_name__in=[prescription.drug_name for prescription in prescription_map.values()]
            )
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
        return normalized_value


class InventoryAdjustSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)


class PatientListSerializer(serializers.ModelSerializer):
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
            "priority",
            "status",
            "created_at",
        )


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ("id", "drug_name", "dosage", "quantity", "frequency", "status")


class PatientWorkflowDetailSerializer(serializers.ModelSerializer):
    prescriptions = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "reg_no",
            "name",
            "camp",
            "priority",
            "status",
            "prescriptions",
        )

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


class AdminReportSerializer(serializers.Serializer):
    patients_per_camp = CampPatientSummarySerializer(many=True)
    drugs_issued_per_camp = CampDrugIssuedSummarySerializer(many=True)
    completed_patients = serializers.IntegerField()


class StageTimingAnalyticsSerializer(serializers.Serializer):
    average_triage_to_doctor_minutes = serializers.FloatField()
    average_doctor_to_pharmacy_minutes = serializers.FloatField()
    average_pharmacy_to_complete_minutes = serializers.FloatField()
    average_total_completion_minutes = serializers.FloatField()
    completed_patient_count = serializers.IntegerField()
