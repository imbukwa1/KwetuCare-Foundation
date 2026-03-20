from django.conf import settings
from rest_framework.permissions import BasePermission


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


class IsDoctorUser(BasePermission):
    message = "Only approved doctors can perform this action."

    def has_permission(self, request, view):
        if settings.BYPASS_USER_APPROVAL:
            return bool(
                request.user
                and request.user.is_authenticated
                and request.user.role == "doctor"
            )
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_approved
            and request.user.role == "doctor"
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
