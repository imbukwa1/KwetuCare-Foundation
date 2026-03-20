from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AdminPatientListView,
    AdminReportExportView,
    AdminReportView,
    AdminStageTimingView,
    DrugInventoryListCreateView,
    DrugInventoryRestockView,
    DrugInventoryUpdateView,
    ApproveUserView,
    ConsultationCreateView,
    LoginView,
    MeView,
    PharmacyDispenseView,
    PatientRegistrationView,
    PatientWorkflowDetailView,
    PendingUsersView,
    RejectUserView,
    SignupView,
    StageQueueView,
    TriageCreateView,
)


urlpatterns = [
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/pending-users/", PendingUsersView.as_view(), name="pending_users"),
    path("auth/users/<int:user_id>/approve/", ApproveUserView.as_view(), name="approve_user"),
    path("auth/users/<int:user_id>/reject/", RejectUserView.as_view(), name="reject_user"),
    path("admin/patients/", AdminPatientListView.as_view(), name="admin_patient_list"),
    path("admin/reports/summary/", AdminReportView.as_view(), name="admin_report_summary"),
    path("admin/reports/export/", AdminReportExportView.as_view(), name="admin_report_export"),
    path("admin/reports/stage-timing/", AdminStageTimingView.as_view(), name="admin_stage_timing"),
    path("inventory/", DrugInventoryListCreateView.as_view(), name="inventory_list_create"),
    path("inventory/<int:pk>/", DrugInventoryUpdateView.as_view(), name="inventory_update"),
    path("inventory/<int:pk>/restock/", DrugInventoryRestockView.as_view(), name="inventory_restock"),
    path("queue/", StageQueueView.as_view(), name="stage_queue"),
    path("patients/<int:pk>/", PatientWorkflowDetailView.as_view(), name="patient_workflow_detail"),
    path("patients/", PatientRegistrationView.as_view(), name="patient_registration"),
    path("triage/", TriageCreateView.as_view(), name="triage_create"),
    path("consultations/", ConsultationCreateView.as_view(), name="consultation_create"),
    path("pharmacy/dispense/", PharmacyDispenseView.as_view(), name="pharmacy_dispense"),
]
