import hashlib
import json
import random
from datetime import timedelta
from html import escape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


class EmailSendError(Exception):
    pass


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


def send_email(*, subject, text, recipients, html=None):
    if settings.EMAIL_PROVIDER == "resend":
        return send_resend_email(
            subject=subject,
            text=text,
            recipients=recipients,
            html=html,
        )

    return send_mail(
        subject=subject,
        message=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=False,
        html_message=html,
    )


def send_resend_email(*, subject, text, recipients, html=None):
    if not settings.RESEND_API_KEY:
        raise EmailSendError("RESEND_API_KEY is not configured.")

    payload = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": recipients,
        "subject": subject,
        "text": text,
    }
    if html:
        payload["html"] = html

    request = Request(
        settings.RESEND_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "kwetu-care-foundation/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise EmailSendError(f"Resend rejected the email request: {exc.code} {body}") from exc
    except URLError as exc:
        raise EmailSendError(f"Could not reach Resend email API: {exc.reason}") from exc


def send_user_verification_email(user, code):
    expires = settings.EMAIL_VERIFICATION_EXPIRY_MINUTES
    message = (
        f"Hello {user.get_full_name() or user.username},\n\n"
        f"Your Kwetu Care verification code is {code}.\n"
        f"It expires in {expires} minutes. You have up to "
        f"{settings.EMAIL_VERIFICATION_MAX_ATTEMPTS} attempts.\n\n"
        "After verification, an administrator will review your account."
    )
    send_email(
        subject="Verify your Kwetu Care account",
        text=message,
        recipients=[user.email],
    )


def send_admin_signup_notification(user):
    display_name = user.get_full_name() or user.username
    role_label = user.get_role_display()
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
    message = (
        "A new verified signup is awaiting admin review.\n\n"
        f"Name: {display_name}\n"
        f"Role: {role_label}\n"
        f"Email: {user.email}\n"
        f"Timestamp: {timestamp}\n\n"
        f"Open dashboard: {dashboard_url}\n"
        f"Approve: {approve_url}\n"
        f"Reject: {reject_url}\n\n"
        "Rejecting an account requires a reason in the admin dashboard."
    )
    html_message = f"""
    <p>A new verified signup is awaiting admin review.</p>
    <table>
      <tr><td><strong>Name</strong></td><td>{escape(display_name)}</td></tr>
      <tr><td><strong>Role</strong></td><td>{escape(role_label)}</td></tr>
      <tr><td><strong>Email</strong></td><td>{escape(user.email)}</td></tr>
      <tr><td><strong>Timestamp</strong></td><td>{timestamp}</td></tr>
    </table>
    <p>
      <a href="{approve_url}">Approve &#x2705;</a>
      &nbsp;|&nbsp;
      <a href="{reject_url}">Reject &#x274C;</a>
      &nbsp;|&nbsp;
      <a href="{dashboard_url}">Open dashboard</a>
    </p>
    <p>Rejecting an account requires a reason in the admin dashboard.</p>
    """

    send_email(
        subject="New Kwetu Care signup awaiting approval",
        text=message,
        recipients=[settings.ADMIN_NOTIFICATION_EMAIL],
        html=html_message,
    )


def send_user_approved_email(user):
    login_url = frontend_url("/")
    display_name = user.get_full_name() or user.username
    message = (
        f"Hello {display_name},\n\n"
        "Welcome to Kwetu Care. Your account has been approved and you can now log in.\n\n"
        f"Login: {login_url}"
    )
    send_email(
        subject="Your Kwetu Care account has been approved",
        text=message,
        recipients=[user.email],
        html=(
            f"<p>Hello {escape(display_name)},</p>"
            "<p>Welcome to Kwetu Care. Your account has been approved and you can now log in.</p>"
            f'<p><a href="{login_url}">Login to Kwetu Care</a></p>'
        ),
    )


def send_user_rejected_email(user, reason):
    send_email(
        subject="Kwetu Care account request update",
        text=(
            f"Hello {user.get_full_name() or user.username},\n\n"
            "Your Kwetu Care account request was not approved.\n\n"
            f"Reason: {reason}"
        ),
        recipients=[user.email],
    )
