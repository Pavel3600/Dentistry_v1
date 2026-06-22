import datetime

from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from ..models import UserProfile
from ..serializers import UserProfileSerializer
from ..controllers import (
    PatientController, AppointmentController, MedicalRecordController,
    MKBSController, ReferralController, StudyController, WorkOrderController,
    VisitController, ServiceController, MaterialController,
    AppointmentLogController,
)
from ..services.fastapi_health import get_fastapi_status
from .permissions import (
    IsDentistOrAdmin, IsManagerDentistOrAdmin, IsManagerOrAdmin,
    IsAdminRole, ReadOnlyOrAdmin,
)


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI status
# ──────────────────────────────────────────────────────────────────────────────

class FastAPIStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_fastapi_status())


# ──────────────────────────────────────────────────────────────────────────────
# Current user
# ──────────────────────────────────────────────────────────────────────────────

class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = getattr(request.user, 'profile', None)
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'role': getattr(profile, 'role', 'patient'),
        })


# ──────────────────────────────────────────────────────────────────────────────
# Patient
# ──────────────────────────────────────────────────────────────────────────────

class PatientViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsManagerDentistOrAdmin]

    def list(self, request):
        params = {k: v for k, v in request.query_params.items()}
        return Response(PatientController.get_all(**params))

    def retrieve(self, request, pk=None):
        return Response(PatientController.get_by_id(pk))

    def create(self, request):
        result = PatientController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(PatientController.update(pk, request.data))

    def destroy(self, request, pk=None):
        PatientController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        return Response(AppointmentController.get_all(patient_id=pk))

    @action(detail=True, methods=['get'])
    def visits(self, request, pk=None):
        return Response(VisitController.get_all(patient_id=pk))

    @action(detail=True, methods=['get'])
    def medical_records(self, request, pk=None):
        return Response(MedicalRecordController.get_all(patient_id=pk))


# ──────────────────────────────────────────────────────────────────────────────
# Appointment
# ──────────────────────────────────────────────────────────────────────────────

class AppointmentViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsManagerDentistOrAdmin]

    def list(self, request):
        params = {k: v for k, v in request.query_params.items()}
        return Response(AppointmentController.get_all(**params))

    def retrieve(self, request, pk=None):
        return Response(AppointmentController.get_by_id(pk))

    def create(self, request):
        result = AppointmentController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(AppointmentController.update(pk, request.data))

    def destroy(self, request, pk=None):
        AppointmentController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appt = AppointmentController.get_by_id(pk)
        if appt.get('status') != 'scheduled':
            return Response({'error': 'Можно отменить только запланированные записи.'}, status=400)
        AppointmentController.update_status(pk, 'cancelled')
        try:
            AppointmentLogController.create({
                'appointment_id': pk,
                'changed_by_login': request.user.username,
                'old_status': appt.get('status'),
                'new_status': 'cancelled',
                'comment': f"API: отменено пользователем {request.user.username}",
            })
        except Exception:
            pass
        return Response({'status': 'cancelled'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        appt = AppointmentController.get_by_id(pk)
        if appt.get('status') != 'scheduled':
            return Response({'error': 'Можно завершить только запланированные записи.'}, status=400)
        AppointmentController.update_status(pk, 'completed')
        try:
            AppointmentLogController.create({
                'appointment_id': pk,
                'changed_by_login': request.user.username,
                'old_status': appt.get('status'),
                'new_status': 'completed',
                'comment': f"API: завершено пользователем {request.user.username}",
            })
        except Exception:
            pass
        return Response({'status': 'completed'})

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        return Response(AppointmentLogController.get_all(appointment_id=pk))


# ──────────────────────────────────────────────────────────────────────────────
# Medical record
# ──────────────────────────────────────────────────────────────────────────────

class MedicalRecordViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        params = {k: v for k, v in request.query_params.items()}
        return Response(MedicalRecordController.get_all(**params))

    def retrieve(self, request, pk=None):
        return Response(MedicalRecordController.get_by_id(pk))

    def create(self, request):
        result = MedicalRecordController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(MedicalRecordController.update(pk, request.data))

    def destroy(self, request, pk=None):
        MedicalRecordController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# Visit
# ──────────────────────────────────────────────────────────────────────────────

class VisitViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        params = {k: v for k, v in request.query_params.items()}
        return Response(VisitController.get_all(**params))

    def retrieve(self, request, pk=None):
        return Response(VisitController.get_by_id(pk))

    def create(self, request):
        result = VisitController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(VisitController.update(pk, request.data))

    @action(detail=True, methods=['get'])
    def procedures(self, request, pk=None):
        return Response(VisitController.get_procedures(pk))

    @action(detail=True, methods=['post'])
    def add_procedure(self, request, pk=None):
        result = VisitController.add_procedure(pk, request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def investigations(self, request, pk=None):
        return Response(VisitController.get_investigations(pk))


# ──────────────────────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────────────────────

class ServiceViewSet(ViewSet):
    permission_classes = [IsAuthenticated, ReadOnlyOrAdmin]

    def list(self, request):
        return Response(ServiceController.get_all())

    def retrieve(self, request, pk=None):
        return Response(ServiceController.get_by_id(pk))

    def create(self, request):
        result = ServiceController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(ServiceController.update(pk, request.data))

    def destroy(self, request, pk=None):
        ServiceController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# Material
# ──────────────────────────────────────────────────────────────────────────────

class MaterialViewSet(ViewSet):
    permission_classes = [IsAuthenticated, ReadOnlyOrAdmin]

    def list(self, request):
        return Response(MaterialController.get_all())

    def retrieve(self, request, pk=None):
        return Response(MaterialController.get_by_id(pk))

    def create(self, request):
        result = MaterialController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(MaterialController.update(pk, request.data))

    def destroy(self, request, pk=None):
        MaterialController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# MKB codes
# ──────────────────────────────────────────────────────────────────────────────

class MKBSCodeViewSet(ViewSet):
    permission_classes = [IsAuthenticated, ReadOnlyOrAdmin]

    def list(self, request):
        params = {k: v for k, v in request.query_params.items()}
        return Response(MKBSController.get_all(**params))

    def retrieve(self, request, pk=None):
        return Response(MKBSController.get_by_id(pk))

    def create(self, request):
        result = MKBSController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(MKBSController.update(pk, request.data))

    def destroy(self, request, pk=None):
        MKBSController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# User profile (Django-managed)
# ──────────────────────────────────────────────────────────────────────────────

class UserProfileViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsAdminRole]

    def list(self, request):
        qs = UserProfile.objects.select_related('user').order_by('user__username')
        return Response(UserProfileSerializer(qs, many=True).data)

    def retrieve(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        profile = get_object_or_404(UserProfile, pk=pk)
        return Response(UserProfileSerializer(profile).data)

    @action(detail=True, methods=['patch'])
    def set_role(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        profile = get_object_or_404(UserProfile, pk=pk)
        new_role = request.data.get('role')
        valid_roles = dict(UserProfile.ROLE_CHOICES)
        if new_role not in valid_roles:
            return Response({'error': f'Допустимые роли: {list(valid_roles)}'}, status=400)
        profile.role = new_role
        profile.save()
        return Response(UserProfileSerializer(profile).data)

    @action(detail=False, methods=['get'])
    def doctors(self, request):
        qs = UserProfile.objects.select_related('user').filter(role='dentist')
        return Response(UserProfileSerializer(qs, many=True).data)


# ──────────────────────────────────────────────────────────────────────────────
# Statistics (proxied from FastAPI)
# ──────────────────────────────────────────────────────────────────────────────

class StatisticsViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]

    def list(self, request):
        days = int(request.query_params.get('days', 30))
        start = (timezone.now().date() - datetime.timedelta(days=days)).isoformat()
        try:
            visits = VisitController.get_all(size=500, date_from=start)
            patients = PatientController.get_all(size=1)
            appointments = AppointmentController.get_all(size=500)
        except Exception:
            visits, patients, appointments = [], [], []

        completed = [a for a in appointments if a.get('status') == 'completed']
        cancelled = [a for a in appointments if a.get('status') == 'cancelled']
        scheduled = [a for a in appointments if a.get('status') == 'scheduled']

        return Response({
            'total_patients': patients[0].get('total', 0) if patients else 0,
            'total_appointments': len(appointments),
            'completed_appointments': len(completed),
            'cancelled_appointments': len(cancelled),
            'scheduled_appointments': len(scheduled),
            'total_visits': len(visits),
            'total_revenue': 0,
            'period_days': days,
        })

    @action(detail=False, methods=['get'])
    def fastapi_status(self, request):
        return Response(get_fastapi_status())


# ──────────────────────────────────────────────────────────────────────────────
# Study / Referral / WorkOrder
# ──────────────────────────────────────────────────────────────────────────────

class StudyViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        params = {k: v for k, v in request.query_params.items()}
        return Response(StudyController.get_all(**params))

    def retrieve(self, request, pk=None):
        return Response(StudyController.get_by_id(pk))

    def create(self, request):
        result = StudyController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(StudyController.update(pk, request.data))

    def destroy(self, request, pk=None):
        StudyController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReferralViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        params = {k: v for k, v in request.query_params.items()}
        return Response(ReferralController.get_all(**params))

    def retrieve(self, request, pk=None):
        return Response(ReferralController.get_by_id(pk))

    def create(self, request):
        result = ReferralController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(ReferralController.update(pk, request.data))

    def destroy(self, request, pk=None):
        ReferralController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkOrderViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        params = {k: v for k, v in request.query_params.items()}
        return Response(WorkOrderController.get_all(**params))

    def retrieve(self, request, pk=None):
        return Response(WorkOrderController.get_by_id(pk))

    def create(self, request):
        result = WorkOrderController.create(request.data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        return Response(WorkOrderController.update(pk, request.data))

    def destroy(self, request, pk=None):
        WorkOrderController.delete(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
