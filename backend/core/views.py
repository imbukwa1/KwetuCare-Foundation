from django.contrib.auth import get_user_model
from django.conf import settings
from datetime import timedelta
import logging
import smtplib
import threading
import time
from django.db import models
from django.db import OperationalError
from django.db import close_old_connections
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.db.utils import ProgrammingError
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import APIException
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
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
)
from .permissions import (
    CONSULTATION_ROLES,
    IsAdminUserRole,
    IsAdminOrPharmacistUser,
    IsApprovedUser,
    IsBloodSugarUser,
    IsDentalUser,
    IsDoctorUser,
    IsGynecologistUser,
    IsInventoryViewer,
    IsNurseUser,
    IsNutritionistUser,
    IsObstetricianUser,
    IsOpticianUser,
    IsPediatricianUser,
    IsPharmacistUser,
    IsRegistrationOfficer,
)
from .serializers import (
    AvailableDrugSerializer,
    BloodSugarCheckSerializer,
    ConsultationCreateSerializer,
    DentalConsultationCreateSerializer,
    DrugInventoryCreateSerializer,
    DrugInventorySerializer,
    GynecologyConsultationCreateSerializer,
    InventoryRestockSerializer,
    ObstetricConsultationCreateSerializer,
    NutritionConsultationCreateSerializer,
    OpticianConsultationCreateSerializer,
    LoginSerializer,
    PediatricConsultationCreateSerializer,
    PharmacyDispenseSerializer,
    PatientRegistrationSerializer,
    PatientListSerializer,
    PatientWorkflowDetailSerializer,
    RejectUserSerializer,
    ResendVerificationCodeSerializer,
    SignupSerializer,
    StageTimingAnalyticsSerializer,
    TriageSerializer,
    UserSerializer,
    VerifyEmailSerializer,
    AdminReportSerializer,
    create_audit_log,
    ensure_consultation_referral_column,
    get_available_inventory_queryset,
    refresh_inventory_totals,
    safe_refresh_inventory_totals,
    sync_batch_statuses,
)
from .auth_emails import (
    EmailSendError,
    send_admin_signup_notification,
    send_user_approved_email,
    send_user_rejected_email,
    send_user_verification_email,
    set_email_verification_code,
)

User = get_user_model()
EMAIL_DELIVERY_EXCEPTIONS = (EmailSendError, OSError, smtplib.SMTPException)
logger = logging.getLogger(__name__)


REPORT_PERIODS = {
    "1m": ("Last 1 Month", timedelta(days=30)),
    "3m": ("Last 3 Months", timedelta(days=90)),
    "1y": ("Last 1 Year", timedelta(days=365)),
}


class EmailDeliveryUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "email_delivery_unavailable"
    default_detail = "Email delivery is temporarily unavailable. Please try again."


def raise_email_delivery_error(exc):
    logger.exception("Email delivery failed during auth flow.")
    raise EmailDeliveryUnavailable(
        "We could not send the email right now. Please try again in a moment."
    ) from exc


def deliver_auth_email(send_func, *args):
    try:
        send_func(*args)
    except Exception as exc:
        raise_email_delivery_error(exc)


def resolve_report_period(period_key):
    key = period_key if period_key in REPORT_PERIODS else "1m"
    label, delta = REPORT_PERIODS[key]
    return key, label, timezone.now() - delta


def collect_condition_rows(since):
    rows = []

    def append_rows(queryset, camp_field, diagnosis_field):
        for camp, diagnosis in queryset.values_list(camp_field, diagnosis_field):
            diagnosis_text = (diagnosis or "").strip()
            if diagnosis_text:
                rows.append((camp, diagnosis_text))

    append_rows(
        Consultation.objects.filter(created_at__gte=since),
        "patient__camp",
        "diagnosis",
    )
    append_rows(
        PediatricConsultation.objects.filter(created_at__gte=since),
        "patient__camp",
        "diagnosis",
    )
    append_rows(
        GynecologyConsultation.objects.filter(created_at__gte=since),
        "patient__camp",
        "diagnosis",
    )
    append_rows(
        ObstetricConsultation.objects.filter(created_at__gte=since),
        "patient__camp",
        "diagnosis",
    )
    append_rows(
        NutritionConsultation.objects.filter(created_at__gte=since),
        "patient__camp",
        "nutrition_diagnosis",
    )
    append_rows(
        OpticianConsultation.objects.filter(created_at__gte=since),
        "patient__camp",
        "diagnosis",
    )
    append_rows(
        DentalConsultation.objects.filter(created_at__gte=since),
        "patient__camp",
        "diagnosis",
    )
    return rows


def safe_referral_case_count(since):
    try:
        return Consultation.objects.filter(created_at__gte=since, is_referral_case=True).count()
    except (OperationalError, ProgrammingError):
        return 0


def build_admin_report_data(period_key="1m"):
    safe_refresh_inventory_totals()
    period_key, period_label, since = resolve_report_period(period_key)
    patient_queryset = Patient.objects.filter(created_at__gte=since)
    dispensed_prescriptions = Prescription.objects.filter(
        status=Prescription.Status.GIVEN,
        consultation__created_at__gte=since,
    )

    patients_per_camp = list(
        patient_queryset.values("camp")
        .annotate(total_patients=Count("id"))
        .order_by("camp")
    )
    drugs_issued_per_camp = list(
        dispensed_prescriptions
        .values("consultation__patient__camp")
        .annotate(total_drugs_issued=Count("id"))
        .order_by("consultation__patient__camp")
    )
    drug_details_per_camp = []
    for item in (
        dispensed_prescriptions
        .values("consultation__patient__camp", "drug_name", "dosage")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("consultation__patient__camp", "drug_name", "dosage")
    ):
        drug_details_per_camp.append(
            {
                "camp": item["consultation__patient__camp"],
                "drug_name": item["drug_name"],
                "amount": item["dosage"],
                "total_quantity": item["total_quantity"] or 0,
            }
        )

    drug_usage_by_name = [
        {
            "drug_name": item["drug_name"],
            "amount": item["dosage"] or "N/A",
            "total_quantity": item["total_quantity"] or 0,
            "display": f"{item['drug_name']} - {(item['total_quantity'] or 0)} units of {item['dosage'] or 'N/A'}",
        }
        for item in (
            dispensed_prescriptions.values("drug_name", "dosage")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("drug_name", "dosage")
        )
    ]

    condition_rows = collect_condition_rows(since)
    diagnosis_distribution_map = {}
    common_condition_map = {}
    for camp, condition in condition_rows:
        diagnosis_distribution_map[(camp, condition)] = diagnosis_distribution_map.get((camp, condition), 0) + 1
        common_condition_map[condition] = common_condition_map.get(condition, 0) + 1

    diagnosis_distribution_per_camp = [
        {"camp": camp, "condition": condition, "total_cases": total}
        for (camp, condition), total in sorted(
            diagnosis_distribution_map.items(),
            key=lambda item: (item[0][0], -item[1], item[0][1]),
        )
    ]
    most_common_conditions = [
        {"condition": condition, "total_cases": total}
        for condition, total in sorted(
            common_condition_map.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ][:10]

    trends_map = {}
    for prescription in dispensed_prescriptions:
        label = prescription.consultation.created_at.strftime("%Y-%m")
        trends_map[label] = trends_map.get(label, 0) + prescription.quantity
    drug_usage_trends = [
        {"period": period, "total_quantity": total}
        for period, total in sorted(trends_map.items())
    ]

    stage_waiting_counts = {
        "triage": patient_queryset.filter(status=Patient.Status.TRIAGE).count(),
        "blood_sugar": patient_queryset.filter(status=Patient.Status.BLOOD_SUGAR).count(),
        "doctor": patient_queryset.filter(status=Patient.Status.DOCTOR).count(),
        "pharmacy": patient_queryset.filter(status=Patient.Status.PHARMACY).count(),
        "complete": patient_queryset.filter(status=Patient.Status.COMPLETE).count(),
    }
    specialist_waiting_counts = {
        "pediatrician": patient_queryset.filter(status=Patient.Status.DOCTOR, assigned_doctor_type=Patient.DoctorType.PEDIATRICIAN).count(),
        "gynecologist": patient_queryset.filter(status=Patient.Status.DOCTOR, assigned_doctor_type=Patient.DoctorType.GYNECOLOGIST).count(),
        "obstetrician": patient_queryset.filter(status=Patient.Status.DOCTOR, assigned_doctor_type=Patient.DoctorType.OBSTETRICIAN).count(),
        "nutritionist": patient_queryset.filter(status=Patient.Status.DOCTOR, assigned_doctor_type=Patient.DoctorType.NUTRITIONIST).count(),
        "dental": patient_queryset.filter(status=Patient.Status.DOCTOR, assigned_doctor_type=Patient.DoctorType.DENTAL).count(),
        "optician": patient_queryset.filter(status=Patient.Status.DOCTOR, assigned_doctor_type=Patient.DoctorType.OPTICIAN).count(),
    }
    completed_patients = stage_waiting_counts["complete"]
    referral_cases = safe_referral_case_count(since)
    pending_patients = patient_queryset.exclude(status=Patient.Status.COMPLETE).count()
    outcome_summary = {
        "treated": completed_patients,
        "referred": referral_cases,
        "pending": pending_patients,
    }
    referral_case_details = []
    for consultation in Consultation.objects.filter(created_at__gte=since, is_referral_case=True).select_related("patient").prefetch_related("prescriptions"):
        referral_case_details.append(
            {
                "patient_name": consultation.patient.name,
                "reg_no": consultation.patient.reg_no,
                "camp": consultation.patient.camp,
                "diagnosis": (consultation.diagnosis or "").strip() or "N/A",
                "referral_details": (consultation.doctor_notes or consultation.recommendations or consultation.follow_up_instructions or "").strip() or "Referral case flagged for follow-up.",
                "prescriptions": [
                    f"{item.drug_name} - {item.quantity} of {item.dosage} ({item.frequency})"
                    for item in consultation.prescriptions.all().order_by("id")
                ],
            }
        )
    return {
        "period_key": period_key,
        "period_label": period_label,
        "patients_per_camp": patients_per_camp,
        "drugs_issued_per_camp": drugs_issued_per_camp,
        "drug_details_per_camp": drug_details_per_camp,
        "drug_usage_by_name": drug_usage_by_name,
        "diagnosis_distribution_per_camp": diagnosis_distribution_per_camp,
        "most_common_conditions": most_common_conditions,
        "drug_usage_trends": drug_usage_trends,
        "stage_waiting_counts": stage_waiting_counts,
        "specialist_waiting_counts": specialist_waiting_counts,
        "completed_patients": completed_patients,
        "referral_cases": referral_cases,
        "outcome_summary": outcome_summary,
        "referral_case_details": referral_case_details,
    }


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        last_error = None
        for attempt in range(12):
            try:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                user = serializer.save()
                return Response(
                    {
                        "detail": "Signup successful. You can now log in.",
                        "email": user.email,
                        "requires_email_verification": False,
                    },
                    status=status.HTTP_201_CREATED,
                )
            except OperationalError as exc:
                last_error = exc
                if "locked" not in str(exc).lower():
                    raise
                close_old_connections()
                time.sleep(min(0.1 * (attempt + 1), 0.75))
                continue
        if last_error is not None:
            raise last_error


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]


class EmailConfigHealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "email_backend": settings.EMAIL_BACKEND,
                "email_provider": settings.EMAIL_PROVIDER,
                "resend_api_key_configured": bool(settings.RESEND_API_KEY),
                "resend_from_email": settings.RESEND_FROM_EMAIL,
                "email_host": settings.EMAIL_HOST,
                "email_port": settings.EMAIL_PORT,
                "email_use_tls": settings.EMAIL_USE_TLS,
                "email_host_user_configured": bool(settings.EMAIL_HOST_USER),
                "email_host_password_configured": bool(settings.EMAIL_HOST_PASSWORD),
                "default_from_email": settings.DEFAULT_FROM_EMAIL,
                "admin_notification_email": settings.ADMIN_NOTIFICATION_EMAIL,
                "frontend_url": settings.FRONTEND_URL,
                "bypass_user_approval": settings.BYPASS_USER_APPROVAL,
                "debug": settings.DEBUG,
            },
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if not user.is_email_verified:
            deliver_auth_email(send_admin_signup_notification, user)
            user.is_email_verified = True
            user.email_verification_code_hash = ""
            user.email_verification_expires_at = None
            user.email_verification_attempts = 0
            user.email_verification_locked_at = None
            user.save(
                update_fields=[
                    "is_email_verified",
                    "email_verification_code_hash",
                    "email_verification_expires_at",
                    "email_verification_attempts",
                    "email_verification_locked_at",
                ]
            )
            create_audit_log(
                user=user,
                action="user_email_verified",
                details={"verified_user_id": user.id, "verified_username": user.username},
            )
        return Response(
            {"detail": "Email verified. Your account is now awaiting admin approval."},
            status=status.HTTP_200_OK,
        )


class ResendVerificationCodeView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.context["user"]
        if user.is_email_verified:
            return Response({"detail": "Email is already verified."}, status=status.HTTP_200_OK)
        code = set_email_verification_code(user)
        deliver_auth_email(send_user_verification_email, user, code)
        return Response({"detail": "A new verification code has been sent."}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class PendingUsersView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get_queryset(self):
        return User.objects.filter(is_email_verified=True, is_approved=False, rejected_at__isnull=True).order_by("date_joined")


class StaffUsersView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get_queryset(self):
        return User.objects.all().order_by("-is_active", "role", "username")


class LockStaffUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def post(self, request, user_id):
        user = generics.get_object_or_404(User, id=user_id)
        if user.id == request.user.id:
            return Response(
                {"detail": "You cannot remove your own admin account."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = False
        user.save(update_fields=["is_active"])
        create_audit_log(
            user=request.user,
            action="staff_locked",
            details={"locked_user_id": user.id, "locked_username": user.username},
        )
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class ApproveUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def post(self, request, user_id):
        user = generics.get_object_or_404(User, id=user_id, is_email_verified=True, rejected_at__isnull=True)
        user.is_approved = True
        user.approved_at = timezone.now()
        user.approval_rejection_reason = ""
        user.save(update_fields=["is_approved", "approved_at", "approval_rejection_reason"])
        deliver_auth_email(send_user_approved_email, user)
        create_audit_log(
            user=request.user,
            action="user_approved",
            details={"approved_user_id": user.id, "approved_username": user.username},
        )
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class RejectUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def delete(self, request, user_id):
        serializer = RejectUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"]
        user = generics.get_object_or_404(User, id=user_id, is_email_verified=True, rejected_at__isnull=True)
        user_data = UserSerializer(user).data
        user.approval_rejection_reason = reason
        user.rejected_at = timezone.now()
        user.save(update_fields=["approval_rejection_reason", "rejected_at"])
        deliver_auth_email(send_user_rejected_email, user, reason)
        create_audit_log(
            user=request.user,
            action="user_rejected",
            details={"rejected_user_id": user.id, "rejected_username": user.username, "reason": reason},
        )
        user.delete()
        return Response(user_data, status=status.HTTP_200_OK)


class PatientRegistrationView(generics.CreateAPIView):
    serializer_class = PatientRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, IsRegistrationOfficer]

    def create(self, request, *args, **kwargs):
        last_error = None
        for attempt in range(12):
            try:
                return super().create(request, *args, **kwargs)
            except OperationalError as exc:
                last_error = exc
                if "locked" not in str(exc).lower():
                    raise
                close_old_connections()
                time.sleep(min(0.1 * (attempt + 1), 0.75))
                continue
        if last_error is not None:
            raise last_error


class TriageCreateView(generics.CreateAPIView):
    serializer_class = TriageSerializer
    permission_classes = [permissions.IsAuthenticated, IsNurseUser]


class BloodSugarCheckCreateView(generics.CreateAPIView):
    serializer_class = BloodSugarCheckSerializer
    permission_classes = [permissions.IsAuthenticated, IsBloodSugarUser]


class ConsultationCreateView(generics.CreateAPIView):
    serializer_class = ConsultationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctorUser]

    def create(self, request, *args, **kwargs):
        ensure_consultation_referral_column()
        return super().create(request, *args, **kwargs)


class DentalConsultationCreateView(generics.CreateAPIView):
    serializer_class = DentalConsultationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDentalUser]


class PediatricConsultationCreateView(generics.CreateAPIView):
    serializer_class = PediatricConsultationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsPediatricianUser]


class GynecologyConsultationCreateView(generics.CreateAPIView):
    serializer_class = GynecologyConsultationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsGynecologistUser]


class ObstetricConsultationCreateView(generics.CreateAPIView):
    serializer_class = ObstetricConsultationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsObstetricianUser]


class NutritionConsultationCreateView(generics.CreateAPIView):
    serializer_class = NutritionConsultationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsNutritionistUser]


class OpticianConsultationCreateView(generics.CreateAPIView):
    serializer_class = OpticianConsultationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsOpticianUser]


class PharmacyDispenseView(generics.GenericAPIView):
    serializer_class = PharmacyDispenseSerializer
    permission_classes = [permissions.IsAuthenticated, IsPharmacistUser]

    def post(self, request, *args, **kwargs):
        ensure_consultation_referral_column()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()
        return Response(serializer.to_representation(patient), status=status.HTTP_200_OK)


class AdminPatientListView(generics.ListAPIView):
    serializer_class = PatientListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get_queryset(self):
        queryset = Patient.objects.order_by("-created_at", "-id")

        search = self.request.query_params.get("search", "").strip()
        camp = self.request.query_params.get("camp", "").strip()
        status_value = self.request.query_params.get("status", "").strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(reg_no__icontains=search)
                | Q(phone__icontains=search)
                | Q(location__icontains=search)
            )

        if camp:
            queryset = queryset.filter(camp__iexact=camp)

        if status_value:
            queryset = queryset.filter(status=status_value)

        return queryset


class StageQueueView(generics.ListAPIView):
    serializer_class = PatientListSerializer

    role_stage_map = {
        "nurse": Patient.Status.TRIAGE,
        "blood_sugar": Patient.Status.BLOOD_SUGAR,
        "pharmacist": Patient.Status.PHARMACY,
        **{role: Patient.Status.DOCTOR for role in CONSULTATION_ROLES},
    }

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsApprovedUser()]

    def get_queryset(self):
        user_role = self.request.user.role
        stage = self.role_stage_map.get(user_role)
        if stage is None:
            return Patient.objects.none()

        queryset = Patient.objects.filter(status=stage)
        if stage == Patient.Status.DOCTOR:
            queryset = queryset.filter(assigned_doctor_type=user_role)

        return queryset.annotate(
            priority_rank=Case(
                When(priority=Patient.Priority.URGENT, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("priority_rank", "created_at", "id")


class PatientWorkflowDetailView(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientWorkflowDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def get(self, request, *args, **kwargs):
        ensure_consultation_referral_column()
        return super().get(request, *args, **kwargs)


class AdminReportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        period_key = request.query_params.get("period", "1m").strip()
        serializer = AdminReportSerializer(build_admin_report_data(period_key))
        return Response(serializer.data)


class AdminReportExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        period_key = request.query_params.get("period", "1m").strip()
        report_data = build_admin_report_data(period_key)
        response = HttpResponse(content_type="application/msword")
        response["Content-Disposition"] = 'attachment; filename="kwetu-care-report.doc"'

        patients_rows = "".join(
            f"<tr><td>{item['camp']}</td><td>{item['total_patients']}</td></tr>"
            for item in report_data["patients_per_camp"]
        )
        drugs_rows = "".join(
            f"<tr><td>{item['consultation__patient__camp']}</td><td>{item['total_drugs_issued']}</td></tr>"
            for item in report_data["drugs_issued_per_camp"]
        )
        detail_rows = "".join(
            (
                f"<tr><td>{item['camp']}</td><td>{item['drug_name']}</td>"
                f"<td>{item['total_quantity']}</td><td>{item['amount'] or 'N/A'}</td></tr>"
            )
            for item in report_data["drug_details_per_camp"]
        )
        drug_usage_rows = "".join(
            f"<tr><td>{item['drug_name']}</td><td>{item['amount']}</td><td>{item['total_quantity']}</td></tr>"
            for item in report_data["drug_usage_by_name"]
        )
        diagnosis_rows = "".join(
            f"<tr><td>{item['camp']}</td><td>{item['condition']}</td><td>{item['total_cases']}</td></tr>"
            for item in report_data["diagnosis_distribution_per_camp"]
        )
        common_condition_rows = "".join(
            f"<tr><td>{item['condition']}</td><td>{item['total_cases']}</td></tr>"
            for item in report_data["most_common_conditions"]
        )
        trend_rows = "".join(
            f"<tr><td>{item['period']}</td><td>{item['total_quantity']}</td></tr>"
            for item in report_data["drug_usage_trends"]
        )
        referral_rows = "".join(
            "<tr>"
            f"<td>{item['patient_name']}</td>"
            f"<td>{item['reg_no']}</td>"
            f"<td>{item['camp']}</td>"
            f"<td>{item['diagnosis']}</td>"
            f"<td>{item['referral_details']}</td>"
            f"<td>{'<br/>'.join(item['prescriptions']) if item['prescriptions'] else 'No prescriptions'}</td>"
            "</tr>"
            for item in report_data["referral_case_details"]
        )

        html = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <title>Kwetu Care Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h1, h2 {{ color: #1f3b57; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #999; padding: 8px; text-align: left; }}
                th {{ background: #f0f4f8; }}
            </style>
        </head>
        <body>
            <h1>Kwetu Care Report</h1>
            <p>Reporting period: <strong>{report_data['period_label']}</strong></p>
            <p>Completed patients: <strong>{report_data['completed_patients']}</strong></p>
            <p>Referral cases: <strong>{report_data['referral_cases']}</strong></p>
            <p>Outcome summary: treated <strong>{report_data['outcome_summary']['treated']}</strong>, referred <strong>{report_data['outcome_summary']['referred']}</strong>, pending <strong>{report_data['outcome_summary']['pending']}</strong></p>

            <h2>Patients Per Camp</h2>
            <table>
                <tr><th>Camp</th><th>Total Patients</th></tr>
                {patients_rows}
            </table>

            <h2>Drugs Issued Per Camp</h2>
            <table>
                <tr><th>Camp</th><th>Total Drugs Issued</th></tr>
                {drugs_rows}
            </table>

            <h2>Specific Drugs Given Per Camp</h2>
            <table>
                <tr><th>Camp</th><th>Drug</th><th>Total Quantity</th><th>Amount</th></tr>
                {detail_rows}
            </table>

            <h2>Drug Usage By Name</h2>
            <table>
                <tr><th>Drug</th><th>Amount</th><th>Total Quantity</th></tr>
                {drug_usage_rows}
            </table>

            <h2>Disease Distribution Per Camp</h2>
            <table>
                <tr><th>Camp</th><th>Condition</th><th>Patients</th></tr>
                {diagnosis_rows}
            </table>

            <h2>Most Common Conditions Across Camps</h2>
            <table>
                <tr><th>Condition</th><th>Total Cases</th></tr>
                {common_condition_rows}
            </table>

            <h2>Drug Usage Trends Over Time</h2>
            <table>
                <tr><th>Period</th><th>Total Quantity Dispensed</th></tr>
                {trend_rows}
            </table>

            <h2>Referral Case Details</h2>
            <table>
                <tr><th>Patient Name</th><th>Reg No</th><th>Camp</th><th>Diagnosis</th><th>Referral Details</th><th>Prescriptions</th></tr>
                {referral_rows}
            </table>
        </body>
        </html>
        """

        response.write(html)
        return response


class AdminStageTimingView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        completed_patients = Patient.objects.filter(
            completed_at__isnull=False,
            doctor_started_at__isnull=False,
            pharmacy_started_at__isnull=False,
        )

        completed_patient_count = completed_patients.count()

        def avg_minutes(values):
            return round(sum(values) / len(values), 2) if values else 0.0

        triage_to_doctor = []
        doctor_to_pharmacy = []
        pharmacy_to_complete = []
        total_completion = []

        for patient in completed_patients:
            triage_to_doctor.append(
                (patient.doctor_started_at - patient.triage_started_at).total_seconds() / 60
            )
            doctor_to_pharmacy.append(
                (patient.pharmacy_started_at - patient.doctor_started_at).total_seconds() / 60
            )
            pharmacy_to_complete.append(
                (patient.completed_at - patient.pharmacy_started_at).total_seconds() / 60
            )
            total_completion.append(
                (patient.completed_at - patient.created_at).total_seconds() / 60
            )

        serializer = StageTimingAnalyticsSerializer(
            {
                "average_triage_to_doctor_minutes": avg_minutes(triage_to_doctor),
                "average_doctor_to_pharmacy_minutes": avg_minutes(doctor_to_pharmacy),
                "average_pharmacy_to_complete_minutes": avg_minutes(pharmacy_to_complete),
                "average_total_completion_minutes": avg_minutes(total_completion),
                "completed_patient_count": completed_patient_count,
            }
        )
        return Response(serializer.data)


class DrugInventoryListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        refresh_inventory_totals()
        queryset = DrugInventory.objects.all().order_by("category", "drug_name", "amount")
        search = self.request.query_params.get("search", "").strip()
        low_stock = self.request.query_params.get("low_stock", "").strip().lower()

        if search:
            queryset = queryset.filter(Q(drug_name__icontains=search) | Q(amount__icontains=search))
        if low_stock == "true":
            queryset = queryset.filter(stock_quantity__lte=models.F("reorder_level"))

        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DrugInventoryCreateSerializer
        return DrugInventorySerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.IsAuthenticated(), IsInventoryViewer()]
        return [permissions.IsAuthenticated(), IsAdminOrPharmacistUser()]

    def perform_create(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can create inventory records.")
        inventory = serializer.save()
        create_audit_log(
            user=self.request.user,
            action="inventory_created",
            details={
                "camp": inventory.camp,
                "drug_name": inventory.drug_name,
                "amount": inventory.amount,
                "stock_quantity": inventory.stock_quantity,
            },
        )
        self.created_inventory = inventory

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        output = DrugInventorySerializer(self.created_inventory).data
        headers = self.get_success_headers(output)
        return Response(output, status=status.HTTP_201_CREATED, headers=headers)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class DrugInventoryUpdateView(generics.RetrieveUpdateAPIView):
    queryset = DrugInventory.objects.all()
    serializer_class = DrugInventorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def perform_update(self, serializer):
        inventory = serializer.save()
        create_audit_log(
            user=self.request.user,
            action="inventory_updated",
            details={"drug_name": inventory.drug_name, "stock_quantity": inventory.stock_quantity},
        )


class DrugInventoryRestockView(generics.GenericAPIView):
    queryset = DrugInventory.objects.all()
    serializer_class = InventoryRestockSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def post(self, request, *args, **kwargs):
        inventory = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        DrugBatch.objects.create(
            inventory=inventory,
            quantity_received=serializer.validated_data["quantity"],
            quantity_remaining=serializer.validated_data["quantity"],
            expiry_date=serializer.validated_data["expiry_date"],
        )
        refresh_inventory_totals([inventory.id])
        inventory.refresh_from_db()
        create_audit_log(
            user=request.user,
            action="inventory_restocked",
            details={
                "camp": inventory.camp,
                "drug_name": inventory.drug_name,
                "amount": inventory.amount,
                "quantity": serializer.validated_data["quantity"],
                "expiry_date": str(serializer.validated_data["expiry_date"]),
            },
        )
        return Response(DrugInventorySerializer(inventory).data, status=status.HTTP_200_OK)


class AvailableDrugsView(generics.ListAPIView):
    serializer_class = AvailableDrugSerializer
    permission_classes = [permissions.IsAuthenticated, IsInventoryViewer]

    def get_queryset(self):
        return get_available_inventory_queryset()
