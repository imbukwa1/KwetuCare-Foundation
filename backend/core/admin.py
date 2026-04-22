from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    AuditLog,
    BloodSugarCheck,
    Consultation,
    DentalConsultation,
    DrugBatch,
    DrugInventory,
    GynecologyConsultation,
    NutritionConsultation,
    ObstetricConsultation,
    OpticianConsultation,
    Patient,
    PediatricConsultation,
    Prescription,
    Triage,
    User,
)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_approved", "is_staff")
    list_filter = ("role", "is_approved", "is_staff", "is_superuser")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Kwetu Care", {"fields": ("role", "is_approved")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Kwetu Care", {"fields": ("role", "is_approved")}),
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("reg_no", "name", "phone", "camp", "priority", "status", "created_at")
    search_fields = ("reg_no", "name", "phone", "camp", "location")
    list_filter = ("status", "priority", "gender", "camp", "created_at")


@admin.register(Triage)
class TriageAdmin(admin.ModelAdmin):
    list_display = (
        "patient",
        "temperature",
        "weight",
        "height",
        "bmi",
        "heart_rate",
        "respiratory_rate",
        "spo2",
        "created_at",
    )
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(BloodSugarCheck)
class BloodSugarCheckAdmin(admin.ModelAdmin):
    list_display = ("patient", "blood_sugar_level", "test_type", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(PediatricConsultation)
class PediatricConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(GynecologyConsultation)
class GynecologyConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(ObstetricConsultation)
class ObstetricConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(NutritionConsultation)
class NutritionConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "nutrition_diagnosis", "risk_level", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(OpticianConsultation)
class OpticianConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(DentalConsultation)
class DentalConsultationAdmin(admin.ModelAdmin):
    list_display = ("patient", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ("drug_name", "consultation", "quantity", "frequency", "status")
    search_fields = ("drug_name", "consultation__patient__reg_no", "consultation__patient__name")
    list_filter = ("status",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "user", "patient", "created_at")
    search_fields = ("action", "user__username", "patient__reg_no", "patient__name")
    list_filter = ("action", "created_at")


@admin.register(DrugInventory)
class DrugInventoryAdmin(admin.ModelAdmin):
    list_display = ("category", "drug_name", "amount", "stock_quantity", "reorder_level", "updated_at")
    search_fields = ("category", "drug_name", "amount")


@admin.register(DrugBatch)
class DrugBatchAdmin(admin.ModelAdmin):
    list_display = ("inventory", "quantity_received", "quantity_remaining", "expiry_date", "status", "created_at")
    search_fields = ("inventory__camp", "inventory__drug_name", "inventory__amount")
    list_filter = ("status", "expiry_date", "inventory__camp")
