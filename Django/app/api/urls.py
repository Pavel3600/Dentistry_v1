from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AppointmentViewSet,
    FastAPIStatusAPIView,
    MaterialViewSet,
    MeAPIView,
    MedicalRecordViewSet,
    MKBSCodeViewSet,
    PatientViewSet,
    ReferralViewSet,
    ServiceViewSet,
    StatisticsViewSet,
    StudyViewSet,
    UserProfileViewSet,
    VisitViewSet,
    WorkOrderViewSet,
    mkbs_validate,
)

router = DefaultRouter()
router.register('patients', PatientViewSet, basename='patient')
router.register('appointments', AppointmentViewSet, basename='appointment')
router.register('medical-records', MedicalRecordViewSet, basename='medical-record')
router.register('visits', VisitViewSet, basename='visit')
router.register('services', ServiceViewSet, basename='service')
router.register('materials', MaterialViewSet, basename='material')
router.register('mkbs', MKBSCodeViewSet, basename='mkbs')
router.register('users', UserProfileViewSet, basename='user')
router.register('statistics', StatisticsViewSet, basename='statistics')
router.register('studies', StudyViewSet, basename='study')
router.register('referrals', ReferralViewSet, basename='referral')
router.register('work-orders', WorkOrderViewSet, basename='work-order')

urlpatterns = [
    path('', include(router.urls)),
    path('fastapi-status/', FastAPIStatusAPIView.as_view(), name='fastapi-status'),
    path('me/', MeAPIView.as_view(), name='me'),
    path('mkbs/validate/<str:code>/', mkbs_validate, name='mkbs-validate'),
]
