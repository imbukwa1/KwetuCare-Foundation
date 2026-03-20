from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AuditLog, Consultation, DrugInventory, Patient, Prescription, Triage, User


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
    search_fields = ("reg_no", "name", "phone", "camp", "village")
    list_filter = ("status", "priority", "gender", "camp", "created_at")


@admin.register(Triage)
class TriageAdmin(admin.ModelAdmin):
    list_display = ("patient", "temperature", "weight", "heart_rate", "created_at")
    search_fields = ("patient__reg_no", "patient__name")


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
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
    list_display = ("drug_name", "stock_quantity", "reorder_level", "updated_at")
    search_fields = ("drug_name",)
