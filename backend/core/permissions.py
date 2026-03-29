from django.conf import settings
from rest_framework.permissions import BasePermission


CONSULTATION_ROLES = {
    "general_doctor",
    "pediatrician",
    "gynecologist",
    "obstetrician",
    "nutritionist",
    "dental",
    "optician",
}


class IsApprovedUser(BasePermission):
    message = "Your account is pending admin approval."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(request.user and request.user.is_authenticated)
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
        )


class IsAdminUserRole(BasePermission):
    message = "Only admin users can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "admin"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "admin"
        )


class IsRegistrationOfficer(BasePermission):
    message = "Only approved registration officers can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "registration"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "registration"
        )


class IsNurseUser(BasePermission):
    message = "Only approved nurses can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "nurse"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "nurse"
        )


class IsBloodSugarUser(BasePermission):
    message = "Only approved blood sugar department users can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "blood_sugar"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "blood_sugar"
        )


class IsDoctorUser(BasePermission):
    message = "Only approved doctors and specialists can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role in CONSULTATION_ROLES
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role in CONSULTATION_ROLES
        )


class IsPediatricianUser(BasePermission):
    message = "Only approved pediatricians can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "pediatrician"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "pediatrician"
        )


class IsGynecologistUser(BasePermission):
    message = "Only approved gynecologists can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "gynecologist"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "gynecologist"
        )


class IsObstetricianUser(BasePermission):
    message = "Only approved obstetricians can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "obstetrician"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "obstetrician"
        )


class IsNutritionistUser(BasePermission):
    message = "Only approved nutritionists can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "nutritionist"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "nutritionist"
        )


class IsOpticianUser(BasePermission):
    message = "Only approved opticians can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "optician"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "optician"
        )


class IsDentalUser(BasePermission):
    message = "Only approved dentists can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "dental"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "dental"
        )


class IsPharmacistUser(BasePermission):
    message = "Only approved pharmacists can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "pharmacist"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "pharmacist"
        )


class IsAdminOrPharmacistUser(BasePermission):
    message = "Only approved admins or pharmacists can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role in {"admin", "pharmacist"}
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role in {"admin", "pharmacist"}
        )


class IsInventoryViewer(BasePermission):
    message = "Only approved admins, consultation roles, or pharmacists can view inventory."

    def has_permission(self, request, view):
        allowed_roles = {"admin", "pharmacist", *CONSULTATION_ROLES}
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role in allowed_roles
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role in allowed_roles
        )
