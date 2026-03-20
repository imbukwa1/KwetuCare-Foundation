from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        REGISTRATION = "registration", "Registration"
        NURSE = "nurse", "Nurse"
        DOCTOR = "doctor", "Doctor"
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
        DOCTOR = "doctor", "Doctor"
        PHARMACY = "pharmacy", "Pharmacy"
        COMPLETE = "complete", "Complete"

    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    camp = models.CharField(max_length=255)
    village = models.CharField(max_length=255)
    next_of_kin = models.CharField(max_length=255)
    reg_no = models.CharField(max_length=100, unique=True)
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
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    heart_rate = models.PositiveIntegerField()
    nurse_notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Triage for {self.patient.reg_no}"


class Consultation(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="consultation",
    )
    doctor_notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation for {self.patient.reg_no}"


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
    drug_name = models.CharField(max_length=255, unique=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["drug_name"]

    def __str__(self):
        return f"{self.drug_name} ({self.stock_quantity})"


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
