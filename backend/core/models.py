from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        REGISTRATION = "registration", "Registration"
        NURSE = "nurse", "Nurse"
        BLOOD_SUGAR = "blood_sugar", "Blood Sugar Department"
        GENERAL_DOCTOR = "general_doctor", "General Doctor"
        PEDIATRICIAN = "pediatrician", "Pediatrician"
        GYNECOLOGIST = "gynecologist", "Gynecologist"
        OBSTETRICIAN = "obstetrician", "Obstetrician"
        NUTRITIONIST = "nutritionist", "Nutritionist"
        DENTAL = "dental", "Dentist"
        OPTICIAN = "optician", "Optician"
        PHARMACIST = "pharmacist", "Pharmacist"
        ADMIN = "admin", "Admin"

    role = models.CharField(max_length=20, choices=Role.choices)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Patient(models.Model):
    class Priority(models.TextChoices):
        URGENT = "urgent", "Urgent"
        NORMAL = "normal", "Normal"

    class Status(models.TextChoices):
        TRIAGE = "triage", "Triage"
        BLOOD_SUGAR = "blood_sugar", "Blood Sugar"
        DOCTOR = "doctor", "Doctor"
        PHARMACY = "pharmacy", "Pharmacy"
        COMPLETE = "complete", "Complete"

    class DoctorType(models.TextChoices):
        GENERAL_DOCTOR = User.Role.GENERAL_DOCTOR, "General Doctor"
        PEDIATRICIAN = User.Role.PEDIATRICIAN, "Pediatrician"
        GYNECOLOGIST = User.Role.GYNECOLOGIST, "Gynecologist"
        OBSTETRICIAN = User.Role.OBSTETRICIAN, "Obstetrician"
        NUTRITIONIST = User.Role.NUTRITIONIST, "Nutritionist"
        DENTAL = User.Role.DENTAL, "Dentist"
        OPTICIAN = User.Role.OPTICIAN, "Optician"

    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    camp = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    next_of_kin = models.CharField(max_length=255)
    has_child = models.BooleanField(default=False)
    child_name = models.CharField(max_length=255, blank=True)
    child_age = models.PositiveIntegerField(null=True, blank=True)
    child_date_of_birth = models.DateField(null=True, blank=True)
    guardian_name = models.CharField(max_length=255, blank=True)
    reg_no = models.CharField(max_length=100, unique=True)
    assigned_doctor_type = models.CharField(
        max_length=20,
        choices=DoctorType.choices,
        default=DoctorType.GENERAL_DOCTOR,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TRIAGE,
    )
    triage_started_at = models.DateTimeField(default=timezone.now)
    doctor_started_at = models.DateTimeField(null=True, blank=True)
    pharmacy_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reg_no} - {self.name}"


class Triage(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="triage",
    )
    blood_pressure = models.CharField(max_length=20)
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    height = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    heart_rate = models.PositiveIntegerField()
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    spo2 = models.PositiveIntegerField(null=True, blank=True)
    nurse_notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.height and self.height > 0:
            self.bmi = self.weight / (self.height * self.height)
        else:
            self.bmi = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Triage for {self.patient.reg_no}"


class BloodSugarCheck(models.Model):
    class TestType(models.TextChoices):
        FASTING = "fasting", "Fasting"
        RANDOM = "random", "Random"

    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="blood_sugar_check",
    )
    blood_sugar_level = models.DecimalField(max_digits=6, decimal_places=2)
    test_type = models.CharField(max_length=20, choices=TestType.choices)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blood Sugar Check for {self.patient.reg_no}"


class Consultation(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="consultation",
    )
    # Health Information
    health_conditions = models.JSONField(default=list, blank=True)  # List of conditions
    on_medication = models.CharField(max_length=10, blank=True)  # "yes" or "no"
    medication_details = models.TextField(blank=True)
    
    # History of Presenting Illness
    illness_onset = models.TextField(blank=True)
    illness_severity = models.CharField(max_length=50, blank=True)
    illness_location = models.TextField(blank=True)
    associated_symptoms = models.TextField(blank=True)
    
    # Past Medical History
    chronic_illnesses = models.TextField(blank=True)
    surgeries = models.JSONField(default=list, blank=True)  # List of surgical history
    hospitalizations = models.JSONField(default=list, blank=True)  # List of hospitalizations
    significant_infections = models.TextField(blank=True)
    
    # Family History
    family_history = models.TextField(blank=True)
    
    # Medications and Allergies
    current_medications = models.TextField(blank=True)
    drug_allergies = models.TextField(blank=True)
    food_allergies = models.TextField(blank=True)
    
    # Review of Systems
    systems_heent = models.TextField(blank=True)
    systems_cardiovascular = models.TextField(blank=True)
    systems_respiratory = models.TextField(blank=True)
    systems_gastrointestinal = models.TextField(blank=True)
    systems_musculoskeletal = models.TextField(blank=True)
    systems_neurological = models.TextField(blank=True)
    
    # Diagnosis and Management
    diagnosis = models.TextField(blank=True)  # Required for new consultations but blank for existing
    is_referral_case = models.BooleanField(default=False)
    doctor_notes = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    follow_up_instructions = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation for {self.patient.reg_no}"


class PediatricConsultation(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="pediatric_consultation",
    )
    presenting_complaint = models.TextField()
    history_presenting_illness = models.TextField()
    past_medical_history = models.TextField()
    prenatal_antenatal_history = models.TextField()
    birth_history = models.TextField()
    nutritional_history = models.TextField()
    growth_development_history = models.TextField()
    family_social_history = models.TextField()
    diagnosis = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pediatric Consultation for {self.patient.reg_no}"


class GynecologyConsultation(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="gynecology_consultation",
    )
    presenting_complaints = models.TextField()
    history_presenting_complaints = models.TextField()
    antenatal_history = models.TextField()
    obstetric_history = models.TextField()
    gynecological_history = models.TextField()
    sexual_reproductive_history = models.TextField()
    past_medical_surgical_family_history = models.TextField()
    examination_review_systems = models.TextField()
    diagnosis = models.TextField()
    treatment_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gynecology Consultation for {self.patient.reg_no}"


class ObstetricConsultation(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="obstetric_consultation",
    )
    presenting_complaints = models.TextField()
    history_presenting_complaints = models.TextField()
    antenatal_history = models.TextField()
    obstetric_history = models.TextField()
    gynecological_history = models.TextField()
    sexual_reproductive_history = models.TextField()
    past_medical_surgical_family_history = models.TextField()
    examination_review_systems = models.TextField()
    diagnosis = models.TextField()
    treatment_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Obstetric Consultation for {self.patient.reg_no}"


class NutritionConsultation(models.Model):
    class NutritionDiagnosis(models.TextChoices):
        UNDERNUTRITION = "undernutrition", "Undernutrition"
        OVERNUTRITION = "overnutrition", "Overnutrition"
        BALANCED = "balanced", "Balanced"

    class RiskLevel(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"

    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="nutrition_consultation",
    )
    presenting_complaint = models.TextField()
    dietary_history = models.TextField()
    nutritional_assessment = models.TextField()
    medical_health_conditions = models.TextField()
    child_feeding_history = models.TextField(blank=True)
    lifestyle_assessment = models.TextField()
    nutrition_diagnosis = models.CharField(max_length=20, choices=NutritionDiagnosis.choices)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices)
    nutrition_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Nutrition Consultation for {self.patient.reg_no}"


class OpticianConsultation(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="optician_consultation",
    )
    presenting_complaint = models.TextField()
    ocular_history = models.TextField()
    visual_symptoms_functional_impact = models.TextField()
    past_ocular_medical_history = models.TextField()
    medication_allergy_eye_drop_history = models.TextField()
    examination_vision_assessment = models.TextField()
    diagnosis = models.TextField()
    treatment_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Optician Consultation for {self.patient.reg_no}"


class DentalConsultation(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="dental_consultation",
    )
    presenting_complaint = models.TextField()
    history_presenting_illness = models.TextField()
    oral_examination = models.TextField()
    oral_hygiene_practices = models.TextField()
    past_dental_history = models.TextField()
    medical_history = models.TextField()
    diagnosis = models.TextField()
    treatment_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Dental Consultation for {self.patient.reg_no}"


class Prescription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        GIVEN = "given", "Given"
        NOT_AVAILABLE = "not_available", "Not Available"

    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name="prescriptions",
    )
    drug_name = models.CharField(max_length=255)
    dosage = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    frequency = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    def __str__(self):
        return f"{self.drug_name} for {self.consultation.patient.reg_no}"


class DrugInventory(models.Model):
    camp = models.CharField(max_length=255, default="General")
    drug_name = models.CharField(max_length=255)
    amount = models.CharField(max_length=50)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["camp", "drug_name", "amount"]
        constraints = [
            models.UniqueConstraint(
                fields=["camp", "drug_name", "amount"],
                name="unique_inventory_per_camp_drug_amount",
            )
        ]

    def __str__(self):
        return f"{self.camp} - {self.drug_name} {self.amount} ({self.stock_quantity})"


class DrugBatch(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        DEPLETED = "depleted", "Depleted"

    inventory = models.ForeignKey(
        DrugInventory,
        on_delete=models.CASCADE,
        related_name="batches",
    )
    quantity_received = models.PositiveIntegerField()
    quantity_remaining = models.PositiveIntegerField()
    expiry_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expiry_date", "created_at", "id"]

    def __str__(self):
        return (
            f"{self.inventory.camp} - {self.inventory.drug_name} "
            f"{self.inventory.amount} batch ({self.quantity_remaining})"
        )


class AuditLog(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100)
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} at {self.created_at:%Y-%m-%d %H:%M:%S}"
