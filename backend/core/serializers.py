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

from .models import (
    AuditLog,
    BloodSugarCheck,
    Consultation,
    DentalConsultation,
    DrugInventory,
    GynecologyConsultation,
    NutritionConsultation,
    ObstetricConsultation,
    OpticianConsultation,
    Patient,
    PediatricConsultation,
    Prescription,
    Triage,
)
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
            "location",
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
    assigned_doctor_type = serializers.ChoiceField(
        choices=Patient.DoctorType.choices,
        required=False,
        allow_null=True,
        write_only=True,
    )
    requires_blood_sugar_check = serializers.BooleanField(write_only=True, default=False)
    height = serializers.DecimalField(max_digits=4, decimal_places=2, required=True)
    respiratory_rate = serializers.IntegerField(required=True)
    spo2 = serializers.IntegerField(required=True)

    class Meta:
        model = Triage
        fields = (
            "id",
            "patient_id",
            "patient",
            "requires_blood_sugar_check",
            "assigned_doctor_type",
            "blood_pressure",
            "temperature",
            "weight",
            "height",
            "bmi",
            "heart_rate",
            "respiratory_rate",
            "spo2",
            "nurse_notes",
            "created_at",
        )
        read_only_fields = ("id", "patient", "bmi", "created_at")

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

    def validate_height(self, value):
        if value <= 0:
            raise serializers.ValidationError("Height must be greater than 0.")
        if value < 0.5 or value > 2.5:
            raise serializers.ValidationError("Height must be between 0.50m and 2.50m.")
        return value

    def validate_heart_rate(self, value):
        if value < 30 or value > 220:
            raise serializers.ValidationError("Heart rate must be between 30 and 220 bpm.")
        return value

    def validate_respiratory_rate(self, value):
        if value < 12 or value > 25:
            raise serializers.ValidationError("Respiratory rate must be between 12 and 25 breaths per minute.")
        return value

    def validate_spo2(self, value):
        if value < 70 or value > 100:
            raise serializers.ValidationError("SpO2 must be between 70 and 100.")
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

    def validate(self, attrs):
        requires_blood_sugar_check = attrs.get("requires_blood_sugar_check", False)
        assigned_doctor_type = attrs.get("assigned_doctor_type")

        if not requires_blood_sugar_check and not assigned_doctor_type:
            raise serializers.ValidationError(
                {"assigned_doctor_type": "Select the doctor type when blood sugar check is not required."}
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("patient_id")
        assigned_doctor_type = validated_data.pop("assigned_doctor_type", None)
        requires_blood_sugar_check = validated_data.pop("requires_blood_sugar_check", False)

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
            if requires_blood_sugar_check:
                patient.status = Patient.Status.BLOOD_SUGAR
                patient.save(update_fields=["status"])
            else:
                patient.status = Patient.Status.DOCTOR
                patient.doctor_started_at = timezone.now()
                patient.assigned_doctor_type = assigned_doctor_type
                patient.save(update_fields=["status", "doctor_started_at", "assigned_doctor_type"])
            create_audit_log(
                user=self.context["request"].user,
                action="triage_completed",
                patient=patient,
                details={
                    "requires_blood_sugar_check": requires_blood_sugar_check,
                    "assigned_doctor_type": patient.assigned_doctor_type,
                    "blood_pressure": triage.blood_pressure,
                    "temperature": str(triage.temperature),
                    "weight": str(triage.weight),
                    "height": str(triage.height),
                    "bmi": str(triage.bmi) if triage.bmi is not None else None,
                    "heart_rate": triage.heart_rate,
                    "respiratory_rate": triage.respiratory_rate,
                    "spo2": triage.spo2,
                    "status": patient.status,
                },
            )
            return triage

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["assigned_doctor_type"] = instance.patient.assigned_doctor_type
        data["requires_blood_sugar_check"] = instance.patient.status == Patient.Status.BLOOD_SUGAR
        return data


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
    
    # Health Information
    healthInformation = serializers.JSONField(write_only=True, required=False)
    
    # History of Presenting Illness
    historyOfPresentingIllness = serializers.JSONField(write_only=True, required=False)
    
    # Past Medical History
    pastMedicalHistory = serializers.JSONField(write_only=True, required=False)
    
    # Family History
    familyHistory = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Medications and Allergies
    medicationsAndAllergies = serializers.JSONField(write_only=True, required=False)
    
    # Review of Systems
    reviewOfSystems = serializers.JSONField(write_only=True, required=False)
    
    # Diagnosis and Management
    diagnosis = serializers.CharField(required=True)
    doctorNotes = serializers.CharField(write_only=True, required=False, allow_blank=True)
    recommendations = serializers.CharField(write_only=True, required=False, allow_blank=True)
    followUpInstructions = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Consultation
        fields = (
            "id",
            "patient_id",
            "patient",
            "health_conditions",
            "on_medication",
            "medication_details",
            "illness_onset",
            "illness_severity",
            "illness_location",
            "associated_symptoms",
            "chronic_illnesses",
            "surgeries",
            "hospitalizations",
            "significant_infections",
            "family_history",
            "current_medications",
            "drug_allergies",
            "food_allergies",
            "systems_heent",
            "systems_cardiovascular",
            "systems_respiratory",
            "systems_gastrointestinal",
            "systems_musculoskeletal",
            "systems_neurological",
            "diagnosis",
            "doctor_notes",
            "recommendations",
            "follow_up_instructions",
            "prescriptions",
            "created_at",
            "healthInformation",
            "historyOfPresentingIllness",
            "pastMedicalHistory",
            "familyHistory",
            "medicationsAndAllergies",
            "reviewOfSystems",
            "doctorNotes",
            "followUpInstructions",
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
        
        # Extract camelCase fields and map to snake_case
        health_info = validated_data.pop("healthInformation", {})
        illness_history = validated_data.pop("historyOfPresentingIllness", {})
        past_history = validated_data.pop("pastMedicalHistory", {})
        family = validated_data.pop("familyHistory", "")
        meds_allergies = validated_data.pop("medicationsAndAllergies", {})
        systems = validated_data.pop("reviewOfSystems", {})
        doctor_notes = validated_data.pop("doctorNotes", "")
        recommendations = validated_data.pop("recommendations", "")
        follow_up = validated_data.pop("followUpInstructions", "")
        
        # Map extracted data to model fields
        validated_data["health_conditions"] = health_info.get("conditions", [])
        validated_data["on_medication"] = health_info.get("onMedication", "no")
        validated_data["medication_details"] = health_info.get("medicationDetails", "")
        
        validated_data["illness_onset"] = illness_history.get("onset", "")
        validated_data["illness_severity"] = illness_history.get("severity", "")
        validated_data["illness_location"] = illness_history.get("location", "")
        validated_data["associated_symptoms"] = illness_history.get("associatedSymptoms", "")
        
        validated_data["chronic_illnesses"] = past_history.get("chronicIllnesses", "")
        validated_data["surgeries"] = past_history.get("surgeries", [])
        validated_data["hospitalizations"] = past_history.get("hospitalizations", [])
        validated_data["significant_infections"] = past_history.get("significantInfections", "")
        
        validated_data["family_history"] = family
        
        validated_data["current_medications"] = meds_allergies.get("currentMedications", "")
        validated_data["drug_allergies"] = meds_allergies.get("drugAllergies", "")
        validated_data["food_allergies"] = meds_allergies.get("foodAllergies", "")
        
        validated_data["systems_heent"] = systems.get("heent", "")
        validated_data["systems_cardiovascular"] = systems.get("cardiovascular", "")
        validated_data["systems_respiratory"] = systems.get("respiratory", "")
        validated_data["systems_gastrointestinal"] = systems.get("gastrointestinal", "")
        validated_data["systems_musculoskeletal"] = systems.get("musculoskeletal", "")
        validated_data["systems_neurological"] = systems.get("neurological", "")
        
        validated_data["doctor_notes"] = doctor_notes
        validated_data["recommendations"] = recommendations
        validated_data["follow_up_instructions"] = follow_up

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
                "diagnosis": consultation.diagnosis,
            },
        )
        return consultation


class PediatricConsultationCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)
    prescriptions = PrescriptionCreateSerializer(many=True, write_only=True)

    class Meta:
        model = PediatricConsultation
        fields = (
            "id",
            "patient_id",
            "presenting_complaint",
            "history_presenting_illness",
            "past_medical_history",
            "prenatal_antenatal_history",
            "birth_history",
            "nutritional_history",
            "growth_development_history",
            "family_social_history",
            "diagnosis",
            "prescriptions",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError(
                "Only patients in the doctor stage can be processed by a pediatrician."
            )

        if patient.assigned_doctor_type != Patient.DoctorType.PEDIATRICIAN:
            raise serializers.ValidationError("This patient is not assigned to pediatric care.")

        if hasattr(patient, "pediatric_consultation"):
            raise serializers.ValidationError("Pediatric consultation has already been recorded for this patient.")

        if hasattr(patient, "consultation"):
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        self.context["patient"] = patient
        return value

    def validate_prescriptions(self, value):
        if not value:
            raise serializers.ValidationError("At least one prescription is required.")
        inventory_by_name = {
            item.drug_name.strip().lower(): item.drug_name
            for item in DrugInventory.objects.all()
        }
        normalized_items = []
        seen_drugs = set()
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
            normalized_items.append({**item, "drug_name": canonical_name})
        return normalized_items

    @transaction.atomic
    def create(self, validated_data):
        prescriptions_data = validated_data.pop("prescriptions")
        validated_data.pop("patient_id")

        patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError("This patient is no longer in the doctor stage.")

        if patient.assigned_doctor_type != Patient.DoctorType.PEDIATRICIAN:
            raise serializers.ValidationError("This patient is not assigned to pediatric care.")

        pediatric_consultation = PediatricConsultation.objects.create(patient=patient, **validated_data)

        note_sections = [
            ("Presenting Complaint", pediatric_consultation.presenting_complaint),
            ("History of Presenting Illness", pediatric_consultation.history_presenting_illness),
            ("Past Medical History", pediatric_consultation.past_medical_history),
            ("Pre-natal / Ante-natal History", pediatric_consultation.prenatal_antenatal_history),
            ("Birth History", pediatric_consultation.birth_history),
            ("Nutritional History", pediatric_consultation.nutritional_history),
            ("Growth and Development History", pediatric_consultation.growth_development_history),
            ("Family and Social History", pediatric_consultation.family_social_history),
            ("Diagnosis", pediatric_consultation.diagnosis),
        ]
        consultation_notes = "\n\n".join(
            f"{title}:\n{content}" for title, content in note_sections if content.strip()
        )

        consultation = Consultation.objects.create(
            patient=patient,
            doctor_notes=consultation_notes,
        )

        for prescription_data in prescriptions_data:
            Prescription.objects.create(consultation=consultation, **prescription_data)

        patient.status = Patient.Status.PHARMACY
        patient.pharmacy_started_at = timezone.now()
        patient.save(update_fields=["status", "pharmacy_started_at"])

        create_audit_log(
            user=self.context["request"].user,
            action="pediatric_consultation_completed",
            patient=patient,
            details={
                "status": patient.status,
                "prescription_count": len(prescriptions_data),
            },
        )
        return pediatric_consultation

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["patient_id"] = instance.patient_id
        data["status"] = instance.patient.status
        data["prescription_count"] = instance.patient.consultation.prescriptions.count()
        return data


class WomensHealthConsultationBaseSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)
    prescriptions = PrescriptionCreateSerializer(many=True, write_only=True)

    assigned_doctor_type = None
    consultation_model = None
    audit_action = ""

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError(
                "Only patients in the doctor stage can be processed in this module."
            )

        if patient.assigned_doctor_type != self.assigned_doctor_type:
            raise serializers.ValidationError("This patient is not assigned to this specialist.")

        if Consultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        if self.consultation_model.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Specialist consultation has already been recorded for this patient.")

        self.context["patient"] = patient
        return value

    def validate_prescriptions(self, value):
        if not value:
            raise serializers.ValidationError("At least one prescription is required.")

        inventory_by_name = {
            item.drug_name.strip().lower(): item.drug_name
            for item in DrugInventory.objects.all()
        }
        normalized_items = []
        seen_drugs = set()
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
            normalized_items.append({**item, "drug_name": canonical_name})
        return normalized_items

    def build_consultation_notes(self, specialist_consultation):
        sections = [
            ("Presenting Complaints", specialist_consultation.presenting_complaints),
            ("History of Presenting Complaints", specialist_consultation.history_presenting_complaints),
            ("Antenatal History", specialist_consultation.antenatal_history),
            ("Obstetric History", specialist_consultation.obstetric_history),
            ("Gynecological History", specialist_consultation.gynecological_history),
            ("Sexual and Reproductive History", specialist_consultation.sexual_reproductive_history),
            ("Past Medical, Surgical, and Family History", specialist_consultation.past_medical_surgical_family_history),
            ("Examination and Review of Systems", specialist_consultation.examination_review_systems),
            ("Impression / Diagnosis", specialist_consultation.diagnosis),
            ("Treatment Plan / Action Plan", specialist_consultation.treatment_plan),
        ]
        return "\n\n".join(
            f"{title}:\n{content}" for title, content in sections if content.strip()
        )

    @transaction.atomic
    def create(self, validated_data):
        prescriptions_data = validated_data.pop("prescriptions")
        validated_data.pop("patient_id")

        patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError("This patient is no longer in the doctor stage.")

        if patient.assigned_doctor_type != self.assigned_doctor_type:
            raise serializers.ValidationError("This patient is not assigned to this specialist.")

        if Consultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        if self.consultation_model.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Specialist consultation has already been recorded for this patient.")

        specialist_consultation = self.consultation_model.objects.create(patient=patient, **validated_data)
        consultation = Consultation.objects.create(
            patient=patient,
            doctor_notes=self.build_consultation_notes(specialist_consultation),
        )

        for prescription_data in prescriptions_data:
            Prescription.objects.create(consultation=consultation, **prescription_data)

        patient.status = Patient.Status.PHARMACY
        patient.pharmacy_started_at = timezone.now()
        patient.save(update_fields=["status", "pharmacy_started_at"])

        create_audit_log(
            user=self.context["request"].user,
            action=self.audit_action,
            patient=patient,
            details={
                "status": patient.status,
                "prescription_count": len(prescriptions_data),
            },
        )
        return specialist_consultation

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["patient_id"] = instance.patient_id
        data["status"] = instance.patient.status
        data["prescription_count"] = instance.patient.consultation.prescriptions.count()
        return data


class GynecologyConsultationCreateSerializer(WomensHealthConsultationBaseSerializer):
    assigned_doctor_type = Patient.DoctorType.GYNECOLOGIST
    consultation_model = GynecologyConsultation
    audit_action = "gynecology_consultation_completed"

    class Meta:
        model = GynecologyConsultation
        fields = (
            "id",
            "patient_id",
            "presenting_complaints",
            "history_presenting_complaints",
            "antenatal_history",
            "obstetric_history",
            "gynecological_history",
            "sexual_reproductive_history",
            "past_medical_surgical_family_history",
            "examination_review_systems",
            "diagnosis",
            "treatment_plan",
            "prescriptions",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class ObstetricConsultationCreateSerializer(WomensHealthConsultationBaseSerializer):
    assigned_doctor_type = Patient.DoctorType.OBSTETRICIAN
    consultation_model = ObstetricConsultation
    audit_action = "obstetric_consultation_completed"

    class Meta:
        model = ObstetricConsultation
        fields = (
            "id",
            "patient_id",
            "presenting_complaints",
            "history_presenting_complaints",
            "antenatal_history",
            "obstetric_history",
            "gynecological_history",
            "sexual_reproductive_history",
            "past_medical_surgical_family_history",
            "examination_review_systems",
            "diagnosis",
            "treatment_plan",
            "prescriptions",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class NutritionConsultationCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)
    prescriptions = PrescriptionCreateSerializer(many=True, write_only=True)

    class Meta:
        model = NutritionConsultation
        fields = (
            "id",
            "patient_id",
            "presenting_complaint",
            "dietary_history",
            "nutritional_assessment",
            "medical_health_conditions",
            "child_feeding_history",
            "lifestyle_assessment",
            "nutrition_diagnosis",
            "risk_level",
            "nutrition_plan",
            "prescriptions",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError(
                "Only patients in the doctor stage can be processed by a nutritionist."
            )

        if patient.assigned_doctor_type != Patient.DoctorType.NUTRITIONIST:
            raise serializers.ValidationError("This patient is not assigned to nutrition care.")

        if hasattr(patient, "nutrition_consultation"):
            raise serializers.ValidationError("Nutrition consultation has already been recorded for this patient.")

        if hasattr(patient, "consultation"):
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        self.context["patient"] = patient
        return value

    def validate_prescriptions(self, value):
        if not value:
            raise serializers.ValidationError("At least one prescription is required.")
        inventory_by_name = {
            item.drug_name.strip().lower(): item.drug_name
            for item in DrugInventory.objects.all()
        }
        normalized_items = []
        seen_drugs = set()
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
            normalized_items.append({**item, "drug_name": canonical_name})
        return normalized_items

    @transaction.atomic
    def create(self, validated_data):
        prescriptions_data = validated_data.pop("prescriptions")
        validated_data.pop("patient_id")

        patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError("This patient is no longer in the doctor stage.")

        if patient.assigned_doctor_type != Patient.DoctorType.NUTRITIONIST:
            raise serializers.ValidationError("This patient is not assigned to nutrition care.")

        if NutritionConsultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Nutrition consultation has already been recorded for this patient.")

        if Consultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        nutrition_consultation = NutritionConsultation.objects.create(patient=patient, **validated_data)
        note_sections = [
            ("Presenting Complaint", nutrition_consultation.presenting_complaint),
            ("Dietary History", nutrition_consultation.dietary_history),
            ("Nutritional Assessment", nutrition_consultation.nutritional_assessment),
            ("Medical and Health Conditions", nutrition_consultation.medical_health_conditions),
            ("Infant/Child Feeding History", nutrition_consultation.child_feeding_history),
            ("Lifestyle Assessment", nutrition_consultation.lifestyle_assessment),
            (
                "Nutrition Diagnosis",
                f"{nutrition_consultation.get_nutrition_diagnosis_display()} | Risk level: {nutrition_consultation.get_risk_level_display()}",
            ),
            ("Nutrition Plan", nutrition_consultation.nutrition_plan),
        ]
        consultation_notes = "\n\n".join(
            f"{title}:\n{content}" for title, content in note_sections if content.strip()
        )

        consultation = Consultation.objects.create(
            patient=patient,
            doctor_notes=consultation_notes,
        )

        for prescription_data in prescriptions_data:
            Prescription.objects.create(consultation=consultation, **prescription_data)

        patient.status = Patient.Status.PHARMACY
        patient.pharmacy_started_at = timezone.now()
        patient.save(update_fields=["status", "pharmacy_started_at"])

        create_audit_log(
            user=self.context["request"].user,
            action="nutrition_consultation_completed",
            patient=patient,
            details={
                "status": patient.status,
                "prescription_count": len(prescriptions_data),
                "nutrition_diagnosis": nutrition_consultation.nutrition_diagnosis,
                "risk_level": nutrition_consultation.risk_level,
            },
        )
        return nutrition_consultation

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["patient_id"] = instance.patient_id
        data["status"] = instance.patient.status
        data["prescription_count"] = instance.patient.consultation.prescriptions.count()
        return data


class OpticianConsultationCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)
    prescriptions = PrescriptionCreateSerializer(many=True, write_only=True)

    class Meta:
        model = OpticianConsultation
        fields = (
            "id",
            "patient_id",
            "presenting_complaint",
            "ocular_history",
            "visual_symptoms_functional_impact",
            "past_ocular_medical_history",
            "medication_allergy_eye_drop_history",
            "examination_vision_assessment",
            "diagnosis",
            "treatment_plan",
            "prescriptions",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError(
                "Only patients in the doctor stage can be processed by an optician."
            )

        if patient.assigned_doctor_type != Patient.DoctorType.OPTICIAN:
            raise serializers.ValidationError("This patient is not assigned to optician care.")

        if hasattr(patient, "optician_consultation"):
            raise serializers.ValidationError("Optician consultation has already been recorded for this patient.")

        if hasattr(patient, "consultation"):
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        self.context["patient"] = patient
        return value

    def validate_prescriptions(self, value):
        if not value:
            raise serializers.ValidationError("At least one prescription is required.")
        inventory_by_name = {
            item.drug_name.strip().lower(): item.drug_name
            for item in DrugInventory.objects.all()
        }
        normalized_items = []
        seen_drugs = set()
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
            normalized_items.append({**item, "drug_name": canonical_name})
        return normalized_items

    @transaction.atomic
    def create(self, validated_data):
        prescriptions_data = validated_data.pop("prescriptions")
        validated_data.pop("patient_id")

        patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError("This patient is no longer in the doctor stage.")

        if patient.assigned_doctor_type != Patient.DoctorType.OPTICIAN:
            raise serializers.ValidationError("This patient is not assigned to optician care.")

        if OpticianConsultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Optician consultation has already been recorded for this patient.")

        if Consultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        optician_consultation = OpticianConsultation.objects.create(patient=patient, **validated_data)
        note_sections = [
            ("Presenting Complaint", optician_consultation.presenting_complaint),
            ("Ocular History", optician_consultation.ocular_history),
            ("Visual Symptoms and Functional Impact", optician_consultation.visual_symptoms_functional_impact),
            ("Past Ocular and Medical History", optician_consultation.past_ocular_medical_history),
            ("Medication, Allergy, and Eye Drop History", optician_consultation.medication_allergy_eye_drop_history),
            ("Examination and Vision Assessment", optician_consultation.examination_vision_assessment),
            ("Impression / Diagnosis", optician_consultation.diagnosis),
            ("Treatment Plan / Optical Advice", optician_consultation.treatment_plan),
        ]
        consultation_notes = "\n\n".join(
            f"{title}:\n{content}" for title, content in note_sections if content.strip()
        )

        consultation = Consultation.objects.create(
            patient=patient,
            doctor_notes=consultation_notes,
        )

        for prescription_data in prescriptions_data:
            Prescription.objects.create(consultation=consultation, **prescription_data)

        patient.status = Patient.Status.PHARMACY
        patient.pharmacy_started_at = timezone.now()
        patient.save(update_fields=["status", "pharmacy_started_at"])

        create_audit_log(
            user=self.context["request"].user,
            action="optician_consultation_completed",
            patient=patient,
            details={
                "status": patient.status,
                "prescription_count": len(prescriptions_data),
            },
        )
        return optician_consultation

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["patient_id"] = instance.patient_id
        data["status"] = instance.patient.status
        data["prescription_count"] = instance.patient.consultation.prescriptions.count()
        return data


class DentalConsultationCreateSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)
    prescriptions = PrescriptionCreateSerializer(many=True, write_only=True)

    class Meta:
        model = DentalConsultation
        fields = (
            "id",
            "patient_id",
            "presenting_complaint",
            "history_presenting_illness",
            "oral_examination",
            "oral_hygiene_practices",
            "past_dental_history",
            "medical_history",
            "diagnosis",
            "treatment_plan",
            "prescriptions",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError(
                "Only patients in the doctor stage can be processed by a dentist."
            )

        if patient.assigned_doctor_type != Patient.DoctorType.DENTAL:
            raise serializers.ValidationError("This patient is not assigned to dental care.")

        if hasattr(patient, "dental_consultation"):
            raise serializers.ValidationError("Dental consultation has already been recorded for this patient.")

        if hasattr(patient, "consultation"):
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        self.context["patient"] = patient
        return value

    def validate_prescriptions(self, value):
        if not value:
            raise serializers.ValidationError("At least one prescription is required.")
        inventory_by_name = {
            item.drug_name.strip().lower(): item.drug_name
            for item in DrugInventory.objects.all()
        }
        normalized_items = []
        seen_drugs = set()
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
            normalized_items.append({**item, "drug_name": canonical_name})
        return normalized_items

    @transaction.atomic
    def create(self, validated_data):
        prescriptions_data = validated_data.pop("prescriptions")
        validated_data.pop("patient_id")

        patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

        if patient.status != Patient.Status.DOCTOR:
            raise serializers.ValidationError("This patient is no longer in the doctor stage.")

        if patient.assigned_doctor_type != Patient.DoctorType.DENTAL:
            raise serializers.ValidationError("This patient is not assigned to dental care.")

        if DentalConsultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Dental consultation has already been recorded for this patient.")

        if Consultation.objects.filter(patient=patient).exists():
            raise serializers.ValidationError("Consultation has already been recorded for this patient.")

        dental_consultation = DentalConsultation.objects.create(patient=patient, **validated_data)
        note_sections = [
            ("Presenting Complaint", dental_consultation.presenting_complaint),
            ("History of Presenting Illness", dental_consultation.history_presenting_illness),
            ("Oral Examination", dental_consultation.oral_examination),
            ("Oral Hygiene Practices", dental_consultation.oral_hygiene_practices),
            ("Past Dental History", dental_consultation.past_dental_history),
            ("Medical History", dental_consultation.medical_history),
            ("Diagnosis", dental_consultation.diagnosis),
            ("Treatment Plan", dental_consultation.treatment_plan),
        ]
        consultation_notes = "\n\n".join(
            f"{title}:\n{content}" for title, content in note_sections if content.strip()
        )

        consultation = Consultation.objects.create(
            patient=patient,
            doctor_notes=consultation_notes,
        )

        for prescription_data in prescriptions_data:
            Prescription.objects.create(consultation=consultation, **prescription_data)

        patient.status = Patient.Status.PHARMACY
        patient.pharmacy_started_at = timezone.now()
        patient.save(update_fields=["status", "pharmacy_started_at"])

        create_audit_log(
            user=self.context["request"].user,
            action="dental_consultation_completed",
            patient=patient,
            details={
                "status": patient.status,
                "prescription_count": len(prescriptions_data),
            },
        )
        return dental_consultation

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["patient_id"] = instance.patient_id
        data["status"] = instance.patient.status
        data["prescription_count"] = instance.patient.consultation.prescriptions.count()
        return data


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
            "location",
            "assigned_doctor_type",
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
            "height",
            "bmi",
            "heart_rate",
            "respiratory_rate",
            "spo2",
            "nurse_notes",
            "created_at",
        )


class BloodSugarCheckSerializer(serializers.ModelSerializer):
    patient_id = serializers.IntegerField(write_only=True)
    assigned_doctor_type = serializers.ChoiceField(
        choices=Patient.DoctorType.choices,
        write_only=True,
    )

    class Meta:
        model = BloodSugarCheck
        fields = (
            "id",
            "patient_id",
            "patient",
            "blood_sugar_level",
            "test_type",
            "notes",
            "assigned_doctor_type",
            "created_at",
        )
        read_only_fields = ("id", "patient", "created_at")

    def validate_blood_sugar_level(self, value):
        if value <= 0:
            raise serializers.ValidationError("Blood sugar level must be greater than 0.")
        if value > 1000:
            raise serializers.ValidationError("Blood sugar level is unrealistically high.")
        return value

    def validate_patient_id(self, value):
        try:
            patient = Patient.objects.get(id=value)
        except Patient.DoesNotExist as exc:
            raise serializers.ValidationError("Patient not found.") from exc

        if patient.status != Patient.Status.BLOOD_SUGAR:
            raise serializers.ValidationError(
                "Only patients in the blood sugar stage can be processed here."
            )

        if hasattr(patient, "blood_sugar_check"):
            raise serializers.ValidationError("Blood sugar has already been recorded for this patient.")

        self.context["patient"] = patient
        return value

    def create(self, validated_data):
        validated_data.pop("patient_id")
        assigned_doctor_type = validated_data.pop("assigned_doctor_type")

        with transaction.atomic():
            patient = Patient.objects.select_for_update().get(id=self.context["patient"].id)

            if patient.status != Patient.Status.BLOOD_SUGAR:
                raise serializers.ValidationError(
                    "This patient is no longer in the blood sugar stage."
                )

            if BloodSugarCheck.objects.filter(patient=patient).exists():
                raise serializers.ValidationError(
                    "Blood sugar has already been recorded for this patient."
                )

            blood_sugar = BloodSugarCheck.objects.create(patient=patient, **validated_data)
            patient.status = Patient.Status.DOCTOR
            patient.doctor_started_at = timezone.now()
            patient.assigned_doctor_type = assigned_doctor_type
            patient.save(update_fields=["status", "doctor_started_at", "assigned_doctor_type"])

            create_audit_log(
                user=self.context["request"].user,
                action="blood_sugar_checked",
                patient=patient,
                details={
                    "blood_sugar_level": str(blood_sugar.blood_sugar_level),
                    "test_type": blood_sugar.test_type,
                    "assigned_doctor_type": assigned_doctor_type,
                    "status": patient.status,
                },
            )
            return blood_sugar

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["assigned_doctor_type"] = instance.patient.assigned_doctor_type
        data["status"] = instance.patient.status
        return data


class PatientWorkflowDetailSerializer(serializers.ModelSerializer):
    consultation = serializers.SerializerMethodField()
    prescriptions = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    guardian_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    triage = serializers.SerializerMethodField()
    blood_sugar_check = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = (
            "id",
            "reg_no",
            "name",
            "age",
            "camp",
            "location",
            "assigned_doctor_type",
            "has_child",
            "guardian_name",
            "priority",
            "status",
            "triage",
            "blood_sugar_check",
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

    def get_blood_sugar_check(self, obj):
        if not hasattr(obj, "blood_sugar_check"):
            return None
        return {
            "blood_sugar_level": str(obj.blood_sugar_check.blood_sugar_level),
            "test_type": obj.blood_sugar_check.test_type,
            "notes": obj.blood_sugar_check.notes,
            "created_at": obj.blood_sugar_check.created_at,
        }

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
    blood_sugar = serializers.IntegerField()
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
