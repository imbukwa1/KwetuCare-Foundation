import hashlib
import random
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


def build_email_verification_code():
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def hash_email_verification_code(code):
    payload = f"{settings.SECRET_KEY}:{code}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def set_email_verification_code(user):
    code = build_email_verification_code()
    user.email_verification_code_hash = hash_email_verification_code(code)
    user.email_verification_expires_at = timezone.now() + timedelta(minutes=settings.EMAIL_VERIFICATION_EXPIRY_MINUTES)
    user.email_verification_attempts = 0
    user.email_verification_locked_at = None
    user.save(
        update_fields=[
            "email_verification_code_hash",
            "email_verification_expires_at",
            "email_verification_attempts",
            "email_verification_locked_at",
        ]
    )
    return code


def frontend_url(path="", **query):
    url = f"{settings.FRONTEND_URL}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"
    return url


def send_user_verification_email(user, code):
    expires = settings.EMAIL_VERIFICATION_EXPIRY_MINUTES
    send_mail(
        subject="Verify your Kwetu Care account",
        message=(
            f"Hello {user.get_full_name() or user.username},\n\n"
            f"Your Kwetu Care verification code is {code}.\n"
            f"It expires in {expires} minutes. You have up to "
            f"{settings.EMAIL_VERIFICATION_MAX_ATTEMPTS} attempts.\n\n"
            "After verification, an administrator will review your account."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_admin_signup_notification(user):
    dashboard_url = frontend_url(
        "/admin",
        pendingUser=user.id,
        action="review",
    )
    approve_url = frontend_url(
        "/admin",
        pendingUser=user.id,
        action="approve",
    )
    reject_url = frontend_url(
        "/admin",
        pendingUser=user.id,
        action="reject",
    )
    timestamp = timezone.localtime(user.date_joined).strftime("%Y-%m-%d %H:%M:%S %Z")

    send_mail(
        subject="New Kwetu Care signup awaiting approval",
        message=(
            "A new verified signup is awaiting admin review.\n\n"
            f"Name: {user.get_full_name() or user.username}\n"
            f"Role: {user.get_role_display()}\n"
            f"Email: {user.email}\n"
            f"Timestamp: {timestamp}\n\n"
            f"Open dashboard: {dashboard_url}\n"
            f"Approve: {approve_url}\n"
            f"Reject: {reject_url}\n\n"
            "Rejecting an account requires a reason in the admin dashboard."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
        fail_silently=False,
    )


def send_user_approved_email(user):
    send_mail(
        subject="Your Kwetu Care account has been approved",
        message=(
            f"Hello {user.get_full_name() or user.username},\n\n"
            "Welcome to Kwetu Care. Your account has been approved and you can now log in.\n\n"
            f"Login: {frontend_url('/')}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_user_rejected_email(user, reason):
    send_mail(
        subject="Kwetu Care account request update",
        message=(
            f"Hello {user.get_full_name() or user.username},\n\n"
            "Your Kwetu Care account request was not approved.\n\n"
            f"Reason: {reason}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
