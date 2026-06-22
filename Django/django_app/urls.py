from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from app import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("api/v2/", include("app.api.urls")),
    path("admin_panel/", include("app.urls")),
    path("admin/", admin.site.urls),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register, name="register"),
    path("", views.index, name="index"),

    # Восстановление пароля
    path("password-reset/",
         auth_views.PasswordResetView.as_view(template_name="registration/password_reset_form.html"),
         name="password_reset"),
    path("password-reset/done/",
         auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
         name="password_reset_done"),
    path("reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"),
         name="password_reset_confirm"),
    path("reset/done/",
         auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
         name="password_reset_complete"),

    # JWT endpoints
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # API для интеграции с FastAPI
    path("api/services/", views.api_services, name="api_services"),
    # FastAPI интеграция
    path('fastapi/status/', views.FastAPIServiceStatusView.as_view(), name='fastapi_status'),
    path('fastapi/ping/', views.fastapi_ping, name='fastapi_ping'),
    path('fastapi/patients/', views.FastAPIPatientsView.as_view(), name='fastapi_patients'),
    path('fastapi/services/', views.FastAPIServicesDataView.as_view(), name='fastapi_services'),
    path('fastapi/mkbs/', views.FastAPIMkbsView.as_view(), name='fastapi_mkbs'),
    path('fastapi/sync-patient/', views.FastAPISyncPatientView.as_view(), name='fastapi_sync_patient'),
    path('fastapi/full-status/', views.FastAPIFullStatusView.as_view(), name='fastapi_full_status'),
]