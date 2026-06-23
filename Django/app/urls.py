from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    # Общие
    path('', views.index, name='index'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),

    # Администратор
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/appointment/create/', views.AdminAppointmentCreateView.as_view(), name='admin_appointment_create'),

    # CRUD Service
    path('admin/services/', views.ServiceListView.as_view(), name='service_list'),
    path('admin/services/create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('admin/services/<int:pk>/edit/', views.ServiceUpdateView.as_view(), name='service_edit'),
    path('admin/services/<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),

    # CRUD Material
    path('admin/materials/', views.MaterialListView.as_view(), name='material_list'),
    path('admin/materials/create/', views.MaterialCreateView.as_view(), name='material_create'),
    path('admin/materials/<int:pk>/edit/', views.MaterialUpdateView.as_view(), name='material_edit'),
    path('admin/materials/<int:pk>/delete/', views.MaterialDeleteView.as_view(), name='material_delete'),

    # CRUD MkbCode
    path('admin/mkb/', views.MkbCodeListView.as_view(), name='mkb_list'),
    path('admin/mkb/create/', views.MkbCodeCreateView.as_view(), name='mkb_create'),
    path('admin/mkb/<int:pk>/edit/', views.MkbCodeUpdateView.as_view(), name='mkb_edit'),
    path('admin/mkb/<int:pk>/delete/', views.MkbCodeDeleteView.as_view(), name='mkb_delete'),

    # Менеджер
    path('manager/dashboard/', views.ManagerDashboardView.as_view(), name='manager_dashboard'),
    path('manager/patients/', views.PatientListView.as_view(), name='patient_list'),
    path('manager/patients/create/', views.PatientCreateView.as_view(), name='patient_create'),
    path('manager/patients/<int:pk>/edit/', views.PatientUpdateView.as_view(), name='patient_edit'),
    path('manager/doctors/', views.DoctorListView.as_view(), name='doctor_list'),
    path('manager/doctors/create/', views.DoctorCreateView.as_view(), name='doctor_create'),
    path('admin/managers/', views.ManagerListView.as_view(), name='manager_list'),
    path('admin/managers/create/', views.ManagerCreateView.as_view(), name='manager_create'),
    path('manager/appointments/', views.AppointmentListView.as_view(), name='appointment_list'),
    path('manager/appointments/create/', views.AppointmentCreateView.as_view(), name='appointment_create'),
    path('manager/appointments/<int:pk>/cancel/', views.AppointmentCancelView.as_view(), name='appointment_cancel'),
    path('manager/appointments/<int:pk>/status/', views.AppointmentChangeStatusView.as_view(), name='appointment_change_status'),
    path('manager/appointments/<int:pk>/delete/', views.AppointmentDeleteView.as_view(), name='appointment_delete'),

    # Стоматолог
    path('doctor/dashboard/', views.DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('doctor/appointments/<int:pk>/', views.AppointmentDetailView.as_view(), name='appointment_detail'),
    path('doctor/appointments/<int:pk>/start/', views.StartVisitView.as_view(), name='start_visit'),
    path('doctor/visits/<int:visit_pk>/procedure/', views.ProcedureCreateView.as_view(), name='add_procedure'),
    path('doctor/visits/<int:visit_pk>/referral/', views.ReferralCreateView.as_view(), name='create_referral'),
    path('doctor/visits/<int:visit_pk>/extract/', views.CreateExtractWordView.as_view(), name='create_extract'),
    path('doctor/patients/<int:patient_pk>/history/', views.PatientHistoryView.as_view(), name='patient_history'),
    path('doctor/patients/<int:patient_pk>/medical-info/', views.PatientMedicalInfoView.as_view(), name='patient_medical_info'),
    path('doctor/visits/<int:visit_pk>/report/', views.VisitReportCreateView.as_view(), name='visit_report'),
    path('doctor/reports/<int:pk>/edit/', views.VisitReportUpdateView.as_view(), name='report_edit'),
    path('doctor/reports/<int:pk>/delete/', views.VisitReportDeleteView.as_view(), name='report_delete'),
    path('doctor/search/', views.SearchByDateView.as_view(), name='search_by_date'),

    # Пациент
    path('patient/dashboard/', views.PatientDashboardView.as_view(), name='patient_dashboard'),
    path('patient/appointments/<int:pk>/cancel/', views.PatientCancelAppointmentView.as_view(), name='patient_cancel_appointment'),

    # Отчёты
    path('reports/revenue/', views.RevenueReportView.as_view(), name='revenue_report'),

    # Управление ролями
    path('admin/roles/', views.RoleManagerView.as_view(), name='role_manager'),
    path('admin/roles/<int:user_id>/change/', views.ChangeRoleView.as_view(), name='change_role'),
    path('admin/roles/create/', views.CreateUserWithRoleView.as_view(), name='create_user_with_role'),
    path('admin/impersonate/<int:user_id>/', views.ImpersonateUserView.as_view(), name='impersonate_user'),

    # API
    path('api/services/', views.api_services, name='api_services'),
    path('api/patients/', views.api_patients, name='api_patients'),
    path('api/appointments/', views.api_appointments, name='api_appointments'),

    # FastAPI интеграция
    path('fastapi/ping/', views.fastapi_ping, name='fastapi_ping'),
    path('fastapi/demo/', views.FastAPIDemoView.as_view(), name='fastapi_demo'),
    path('fastapi/services/', views.FastAPIServicesView.as_view(), name='fastapi_services'),
    path('fastapi/status/', views.FastAPIServiceStatusView.as_view(), name='fastapi_status'),
    path('fastapi/full-status/', views.FastAPIFullStatusView.as_view(), name='fastapi_full_status'),
    path('fastapi/status-page/', views.FastAPIStatusPageView.as_view(), name='fastapi_status_page'),
    path('fastapi/patients/', views.FastAPIPatientsView.as_view(), name='fastapi_patients'),
    path('fastapi/services-data/', views.FastAPIServicesDataView.as_view(), name='fastapi_services_data'),
    path('fastapi/mkbs/', views.FastAPIMkbsView.as_view(), name='fastapi_mkbs'),
    path('fastapi/sync-patient/', views.FastAPISyncPatientView.as_view(), name='fastapi_sync_patient'),
    path('fastapi/patients-legacy/', views.fastapi_patients, name='fastapi_patients_legacy'),
]