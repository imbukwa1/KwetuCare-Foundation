from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.http import HttpResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import DrugInventory, Patient, Prescription
from .permissions import (
    IsAdminUserRole,
    IsAdminOrPharmacistUser,
    IsApprovedUser,
    IsDoctorUser,
    IsInventoryViewer,
    IsNurseUser,
    IsPharmacistUser,
    IsRegistrationOfficer,
)
from .serializers import (
    ConsultationCreateSerializer,
    DrugInventorySerializer,
    InventoryAdjustSerializer,
    LoginSerializer,
    PharmacyDispenseSerializer,
    PatientRegistrationSerializer,
    PatientListSerializer,
    PatientWorkflowDetailSerializer,
    SignupSerializer,
    StageTimingAnalyticsSerializer,
    TriageSerializer,
    UserSerializer,
    AdminReportSerializer,
    create_audit_log,
)

User = get_user_model()


def build_admin_report_data():
    patients_per_camp = list(
        Patient.objects.values("camp")
        .annotate(total_patients=Count("id"))
        .order_by("camp")
    )
    drugs_issued_per_camp = list(
        Prescription.objects.filter(status=Prescription.Status.GIVEN)
        .values("consultation__patient__camp")
        .annotate(total_drugs_issued=Count("id"))
        .order_by("consultation__patient__camp")
    )
    inventory_amounts = {
        item.drug_name.strip().lower(): item.amount
        for item in DrugInventory.objects.all()
    }
    drug_details_per_camp = []
    for item in (
        Prescription.objects.filter(status=Prescription.Status.GIVEN)
        .values("consultation__patient__camp", "drug_name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("consultation__patient__camp", "drug_name")
    ):
        drug_details_per_camp.append(
            {
                "camp": item["consultation__patient__camp"],
                "drug_name": item["drug_name"],
                "amount": inventory_amounts.get(item["drug_name"].strip().lower(), ""),
                "total_quantity": item["total_quantity"] or 0,
            }
        )
    stage_waiting_counts = {
        "triage": Patient.objects.filter(status=Patient.Status.TRIAGE).count(),
        "doctor": Patient.objects.filter(status=Patient.Status.DOCTOR).count(),
        "pharmacy": Patient.objects.filter(status=Patient.Status.PHARMACY).count(),
        "complete": Patient.objects.filter(status=Patient.Status.COMPLETE).count(),
    }
    completed_patients = stage_waiting_counts["complete"]
    return {
        "patients_per_camp": patients_per_camp,
        "drugs_issued_per_camp": drugs_issued_per_camp,
        "drug_details_per_camp": drug_details_per_camp,
        "stage_waiting_counts": stage_waiting_counts,
        "completed_patients": completed_patients,
    }


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsApprovedUser]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class PendingUsersView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get_queryset(self):
        return User.objects.filter(is_approved=False).order_by("date_joined")


class ApproveUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def post(self, request, user_id):
        user = generics.get_object_or_404(User, id=user_id)
        user.is_approved = True
        user.save(update_fields=["is_approved"])
        create_audit_log(
            user=request.user,
            action="user_approved",
            details={"approved_user_id": user.id, "approved_username": user.username},
        )
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class RejectUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def delete(self, request, user_id):
        user = generics.get_object_or_404(User, id=user_id)
        user_data = UserSerializer(user).data
        create_audit_log(
            user=request.user,
            action="user_rejected",
            details={"rejected_user_id": user.id, "rejected_username": user.username},
        )
        user.delete()
        return Response(user_data, status=status.HTTP_200_OK)


class PatientRegistrationView(generics.CreateAPIView):
    serializer_class = PatientRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated, IsRegistrationOfficer]


class TriageCreateView(generics.CreateAPIView):
    serializer_class = TriageSerializer
    permission_classes = [permissions.IsAuthenticated, IsNurseUser]


class ConsultationCreateView(generics.CreateAPIView):
    serializer_class = ConsultationCreateSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctorUser]


class PharmacyDispenseView(generics.GenericAPIView):
    serializer_class = PharmacyDispenseSerializer
    permission_classes = [permissions.IsAuthenticated, IsPharmacistUser]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = serializer.save()
        return Response(serializer.to_representation(patient), status=status.HTTP_200_OK)


class AdminPatientListView(generics.ListAPIView):
    serializer_class = PatientListSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get_queryset(self):
        queryset = Patient.objects.annotate(
            priority_rank=Case(
                When(priority=Patient.Priority.URGENT, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("priority_rank", "created_at", "id")

        search = self.request.query_params.get("search", "").strip()
        camp = self.request.query_params.get("camp", "").strip()
        status_value = self.request.query_params.get("status", "").strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(reg_no__icontains=search)
                | Q(phone__icontains=search)
                | Q(village__icontains=search)
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
        "doctor": Patient.Status.DOCTOR,
        "pharmacist": Patient.Status.PHARMACY,
    }

    def get_permissions(self):
        return [permissions.IsAuthenticated(), IsApprovedUser()]

    def get_queryset(self):
        user_role = self.request.user.role
        stage = self.role_stage_map.get(user_role)
        if stage is None:
            return Patient.objects.none()

        return Patient.objects.filter(status=stage).annotate(
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


class AdminReportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        serializer = AdminReportSerializer(build_admin_report_data())
        return Response(serializer.data)


class AdminReportExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        report_data = build_admin_report_data()
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
            <p>Completed patients: <strong>{report_data['completed_patients']}</strong></p>

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
    serializer_class = DrugInventorySerializer

    def get_queryset(self):
        queryset = DrugInventory.objects.all()
        search = self.request.query_params.get("search", "").strip()
        low_stock = self.request.query_params.get("low_stock", "").strip().lower()

        if search:
            queryset = queryset.filter(drug_name__icontains=search)
        if low_stock == "true":
            queryset = queryset.filter(stock_quantity__lte=models.F("reorder_level"))

        return queryset

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
            details={"drug_name": inventory.drug_name, "stock_quantity": inventory.stock_quantity},
        )


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
    serializer_class = InventoryAdjustSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUserRole]

    def post(self, request, *args, **kwargs):
        inventory = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        inventory.stock_quantity += serializer.validated_data["amount"]
        inventory.save(update_fields=["stock_quantity", "updated_at"])
        create_audit_log(
            user=request.user,
            action="inventory_restocked",
            details={"drug_name": inventory.drug_name, "amount": serializer.validated_data["amount"]},
        )
        return Response(DrugInventorySerializer(inventory).data, status=status.HTTP_200_OK)
