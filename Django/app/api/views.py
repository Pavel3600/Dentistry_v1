import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers as drf_serializers, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from ..models import (
    UserProfile, MKBSCode, Patient, PatientMedicalInfo,
    Appointment, Visit, Procedure, Investigation,
    Service, Material, Study, Referral, WorkOrder, AppointmentLog,
)
from ..serializers import UserProfileSerializer
from ..services.fastapi_health import get_fastapi_status
from .permissions import (
    IsDentistOrAdmin, IsManagerDentistOrAdmin, IsManagerOrAdmin,
    IsAdminRole, ReadOnlyOrAdmin,
)


class _Pagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'

    def get_paginated_dict(self, data):
        return {'count': self.page.paginator.count, 'results': data}


def _paginate(request, qs, serializer_fn):
    pager = _Pagination()
    page = pager.paginate_queryset(qs, request)
    data = [serializer_fn(obj) for obj in (page if page is not None else qs)]
    if page is not None:
        return Response(pager.get_paginated_dict(data))
    return Response(data)


def _dt_str(v):
    if v is None:
        return None
    return v.isoformat() if hasattr(v, 'isoformat') else str(v)


def _patient_dict(p):
    return {
        'id': p.id, 'full_name': p.full_name,
        'birth_date': _dt_str(p.birth_date),
        'gender': p.gender, 'phone': p.phone,
        'address': p.address, 'card_number': p.card_number,
        'user_id': p.user_id,
    }


def _appointment_dict(a):
    return {
        'id': a.id, 'patient_id': a.patient_id, 'doctor_id': a.doctor_id,
        'datetime': _dt_str(a.datetime),
        'status': a.status,
    }


def _visit_dict(v):
    return {
        'id': v.id, 'appointment_id': v.appointment_id,
        'patient_id': v.patient_id, 'doctor_id': v.doctor_id,
        'visit_date': v.visit_date.isoformat() if v.visit_date else None,
        'anamnesis': v.anamnesis, 'diagnosis_id': v.diagnosis_id,
    }


def _service_dict(s):
    return {
        'id': s.id, 'code': s.code, 'name': s.name,
        'cost': f'{s.cost:.2f}',
        'duration_minutes': s.duration_minutes, 'material_cost': f'{s.material_cost:.2f}',
    }


def _material_dict(m):
    return {'id': m.id, 'name': m.name, 'unit': m.unit, 'price_per_unit': m.price_per_unit}


def _procedure_dict(p):
    return {'id': p.id, 'service_id': p.service_id, 'quantity': p.quantity, 'total_cost': p.total_cost}


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

    def _check_admin(self, request):
        profile = getattr(request.user, 'profile', None)
        return profile and profile.role in ('admin',)

    def list(self, request):
        qs = Patient.objects.all().order_by('id')
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(full_name__icontains=search)
        return _paginate(request, qs, _patient_dict)

    def retrieve(self, request, pk=None):
        p = get_object_or_404(Patient, pk=pk)
        return Response(_patient_dict(p))

    def create(self, request):
        d = request.data
        p = Patient.objects.create(
            full_name=d.get('full_name', ''),
            birth_date=d.get('birth_date'),
            gender=d.get('gender', 'M'),
            phone=d.get('phone', ''),
            address=d.get('address', ''),
            user_id=d.get('user_id'),
        )
        return Response(_patient_dict(p), status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        p = get_object_or_404(Patient, pk=pk)
        for field in ('full_name', 'birth_date', 'gender', 'phone', 'address', 'user_id'):
            if field in request.data:
                setattr(p, field, request.data[field])
        p.save()
        return Response(_patient_dict(p))

    def update(self, request, pk=None):
        return self.partial_update(request, pk=pk)

    def destroy(self, request, pk=None):
        if not self._check_admin(request):
            return Response({'error': 'Только для администраторов'}, status=status.HTTP_403_FORBIDDEN)
        Patient.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        qs = Appointment.objects.filter(patient_id=pk)
        return Response([_appointment_dict(a) for a in qs])

    @action(detail=True, methods=['get'])
    def visits(self, request, pk=None):
        qs = Visit.objects.filter(patient_id=pk)
        return Response([_visit_dict(v) for v in qs])

    @action(detail=True, methods=['get'])
    def medical_records(self, request, pk=None):
        info = PatientMedicalInfo.objects.filter(patient_id=pk).first()
        if info:
            return Response([{
                'id': info.id, 'patient_id': info.patient_id,
                'allergies': info.allergies, 'chronic_conditions': info.chronic_conditions,
                'contraindications': info.contraindications,
            }])
        return Response([])

    @action(detail=False, methods=['get'], url_path='fastapi-health')
    def fastapi_health(self, request):
        return Response(get_fastapi_status())


# ──────────────────────────────────────────────────────────────────────────────
# Appointment
# ──────────────────────────────────────────────────────────────────────────────

class AppointmentViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsManagerDentistOrAdmin]

    def list(self, request):
        qs = Appointment.objects.select_related('patient', 'doctor').order_by('-datetime')
        status_filter = request.query_params.get('status')
        doctor_id = request.query_params.get('doctor_id')
        if status_filter:
            qs = qs.filter(status=status_filter)
        if doctor_id:
            try:
                profile = UserProfile.objects.get(pk=doctor_id)
                qs = qs.filter(doctor=profile.user)
            except UserProfile.DoesNotExist:
                qs = qs.none()
        return _paginate(request, qs, _appointment_dict)

    def retrieve(self, request, pk=None):
        a = get_object_or_404(Appointment, pk=pk)
        return Response(_appointment_dict(a))

    def create(self, request):
        d = request.data
        patient = get_object_or_404(Patient, pk=d.get('patient_id'))
        try:
            profile = UserProfile.objects.get(pk=d.get('doctor_id'))
            doctor = profile.user
        except UserProfile.DoesNotExist:
            from django.contrib.auth.models import User
            doctor = get_object_or_404(User, pk=d.get('doctor_id'))
        a = Appointment.objects.create(
            patient=patient, doctor=doctor,
            datetime=d.get('datetime'), status=d.get('status', 'scheduled'),
        )
        return Response(_appointment_dict(a), status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        Appointment.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appt = get_object_or_404(Appointment, pk=pk)
        if appt.status != 'scheduled':
            return Response({'error': 'Можно отменить только запланированные записи.'}, status=400)
        old_status = appt.status
        appt.status = 'cancelled'
        appt.save()
        AppointmentLog.objects.create(
            appointment=appt, changed_by=request.user,
            old_status=old_status, new_status='cancelled',
        )
        return Response({'status': 'cancelled'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        appt = get_object_or_404(Appointment, pk=pk)
        if appt.status != 'scheduled':
            return Response({'error': 'Можно завершить только запланированные записи.'}, status=400)
        old_status = appt.status
        appt.status = 'completed'
        appt.save()
        AppointmentLog.objects.create(
            appointment=appt, changed_by=request.user,
            old_status=old_status, new_status='completed',
        )
        return Response({'status': 'completed'})

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        qs = AppointmentLog.objects.filter(appointment_id=pk)
        return Response([{
            'id': l.id, 'old_status': l.old_status, 'new_status': l.new_status,
            'changed_at': l.changed_at.isoformat(),
        } for l in qs])


# ──────────────────────────────────────────────────────────────────────────────
# Medical record (PatientMedicalInfo)
# ──────────────────────────────────────────────────────────────────────────────

class MedicalRecordViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        qs = PatientMedicalInfo.objects.all()
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return Response([{'id': m.id, 'patient_id': m.patient_id,
                          'allergies': m.allergies, 'notes': m.notes} for m in qs])

    def retrieve(self, request, pk=None):
        m = get_object_or_404(PatientMedicalInfo, pk=pk)
        return Response({'id': m.id, 'patient_id': m.patient_id, 'allergies': m.allergies})

    def create(self, request):
        d = request.data
        patient = get_object_or_404(Patient, pk=d.get('patient_id'))
        m, _ = PatientMedicalInfo.objects.get_or_create(patient=patient)
        m.allergies = d.get('allergies', m.allergies)
        m.notes = d.get('notes', m.notes)
        m.save()
        return Response({'id': m.id, 'patient_id': m.patient_id}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        PatientMedicalInfo.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# Visit
# ──────────────────────────────────────────────────────────────────────────────

class VisitViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        qs = Visit.objects.select_related('patient', 'doctor').order_by('-visit_date')
        patient_id = request.query_params.get('patient_id')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return Response([_visit_dict(v) for v in qs])

    def retrieve(self, request, pk=None):
        v = get_object_or_404(Visit, pk=pk)
        return Response(_visit_dict(v))

    def create(self, request):
        d = request.data
        patient = get_object_or_404(Patient, pk=d.get('patient_id'))
        appt = get_object_or_404(Appointment, pk=d.get('appointment_id'))
        v = Visit.objects.create(appointment=appt, patient=patient, doctor=request.user)
        return Response(_visit_dict(v), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def procedures(self, request, pk=None):
        qs = Procedure.objects.filter(visit_id=pk)
        return Response([_procedure_dict(p) for p in qs])

    @action(detail=True, methods=['post'])
    def add_procedure(self, request, pk=None):
        v = get_object_or_404(Visit, pk=pk)
        d = request.data
        svc = get_object_or_404(Service, pk=d.get('service'))
        proc = Procedure.objects.create(visit=v, service=svc, quantity=d.get('quantity', 1))
        return Response(_procedure_dict(proc), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def investigations(self, request, pk=None):
        qs = Investigation.objects.filter(visit_id=pk)
        return Response([{'id': i.id, 'type': i.type, 'description': i.description} for i in qs])


# ──────────────────────────────────────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────────────────────────────────────

class ServiceViewSet(ViewSet):
    permission_classes = [IsAuthenticated, ReadOnlyOrAdmin]

    def list(self, request):
        qs = Service.objects.all()
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        return Response([_service_dict(s) for s in qs])

    def retrieve(self, request, pk=None):
        s = get_object_or_404(Service, pk=pk)
        return Response(_service_dict(s))

    def create(self, request):
        d = request.data
        s = Service.objects.create(
            code=d.get('code', ''), name=d.get('name', ''),
            cost=d.get('cost', 0), duration_minutes=d.get('duration_minutes', 30),
            material_cost=d.get('material_cost', 0),
        )
        return Response(_service_dict(s), status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        s = get_object_or_404(Service, pk=pk)
        for field in ('code', 'name', 'cost', 'duration_minutes', 'material_cost'):
            if field in request.data:
                setattr(s, field, request.data[field])
        s.save()
        return Response(_service_dict(s))

    def update(self, request, pk=None):
        return self.partial_update(request, pk=pk)

    def destroy(self, request, pk=None):
        Service.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# Material
# ──────────────────────────────────────────────────────────────────────────────

class MaterialViewSet(ViewSet):
    permission_classes = [IsAuthenticated, ReadOnlyOrAdmin]

    def list(self, request):
        qs = Material.objects.all()
        return Response([_material_dict(m) for m in qs])

    def retrieve(self, request, pk=None):
        m = get_object_or_404(Material, pk=pk)
        return Response(_material_dict(m))

    def create(self, request):
        d = request.data
        m = Material.objects.create(
            name=d.get('name', ''), unit=d.get('unit', ''), price_per_unit=d.get('price_per_unit', 0),
        )
        return Response(_material_dict(m), status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        Material.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────────────────────
# MKB codes
# ──────────────────────────────────────────────────────────────────────────────

class MKBSCodeViewSet(ViewSet):
    permission_classes = [IsAuthenticated, ReadOnlyOrAdmin]

    def list(self, request):
        qs = MKBSCode.objects.all()
        search = request.query_params.get('search')
        category = request.query_params.get('category')
        active_only = request.query_params.get('active_only')
        if search:
            qs = qs.filter(name__icontains=search) | MKBSCode.objects.filter(code__icontains=search)
        if category:
            qs = qs.filter(category=category)
        if active_only:
            qs = qs.filter(is_active=True)
        data = [{'id': c.id, 'code': c.code, 'name': c.name, 'category': c.category,
                 'is_active': c.is_active} for c in qs]
        return Response(data)

    def retrieve(self, request, pk=None):
        c = get_object_or_404(MKBSCode, pk=pk)
        return Response({'id': c.id, 'code': c.code, 'name': c.name,
                         'category': c.category, 'is_active': c.is_active})

    def create(self, request):
        data = request.data
        c = MKBSCode.objects.create(
            code=data['code'], name=data['name'],
            category=data.get('category', 'diagnosis'),
            is_active=data.get('is_active', True),
        )
        return Response({'id': c.id, 'code': c.code}, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        c = get_object_or_404(MKBSCode, pk=pk)
        for k, v in request.data.items():
            setattr(c, k, v)
        c.save()
        return Response({'id': c.id, 'code': c.code})

    def destroy(self, request, pk=None):
        MKBSCode.objects.filter(pk=pk).delete()
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
        since = timezone.now() - datetime.timedelta(days=days)
        total_patients = Patient.objects.count()
        appts = Appointment.objects.filter(created_at__gte=since)
        total_revenue = sum(p.total_cost for p in Procedure.objects.all())
        return Response({
            'total_patients': total_patients,
            'total_appointments': appts.count(),
            'completed_appointments': appts.filter(status='completed').count(),
            'cancelled_appointments': appts.filter(status='cancelled').count(),
            'scheduled_appointments': appts.filter(status='scheduled').count(),
            'total_visits': Visit.objects.filter(visit_date__gte=since).count(),
            'total_revenue': total_revenue,
            'period_days': days,
        })

    @action(detail=False, methods=['get'])
    def by_doctor(self, request):
        from django.db.models import Count
        data = (Appointment.objects.values('doctor__username')
                .annotate(count=Count('id'))
                .order_by('-count'))
        return Response(list(data))

    @action(detail=False, methods=['get'])
    def by_service(self, request):
        from django.db.models import Count, Sum
        data = (Procedure.objects.values('service__name')
                .annotate(count=Count('id'), revenue=Sum('total_cost'))
                .order_by('-count'))
        return Response(list(data))

    @action(detail=False, methods=['get'])
    def fastapi_status(self, request):
        return Response(get_fastapi_status())


# ──────────────────────────────────────────────────────────────────────────────
# Study / Referral / WorkOrder
# ──────────────────────────────────────────────────────────────────────────────

class StudyViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        patient_id = request.query_params.get('patient_id')
        qs = Study.objects.all()
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        data = [{'id': s.id, 'patient_id': s.patient_id, 'study_type': s.study_type,
                 'result': s.result, 'date': s.date} for s in qs]
        return Response(data)

    def retrieve(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        s = get_object_or_404(Study, pk=pk)
        return Response({'id': s.id, 'patient_id': s.patient_id, 'study_type': s.study_type})

    def create(self, request):
        data = request.data
        patient = Patient.objects.get(pk=data['patient_id'])
        s = Study.objects.create(
            patient=patient,
            study_type=data['study_type'],
            result=data.get('result', ''),
        )
        return Response({'id': s.id, 'study_type': s.study_type}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        Study.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ReferralViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        qs = Referral.objects.all()
        data = [{'id': r.id, 'patient_id': r.patient_id, 'to_specialist': r.to_specialist} for r in qs]
        return Response(data)

    def retrieve(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        r = get_object_or_404(Referral, pk=pk)
        return Response({'id': r.id, 'patient_id': r.patient_id, 'to_specialist': r.to_specialist})

    def create(self, request):
        data = request.data
        patient = Patient.objects.get(pk=data['patient_id'])
        ref = Referral.objects.create(
            patient=patient,
            doctor=request.user,
            to_specialist=data['to_specialist'],
            reason=data.get('reason', ''),
        )
        return Response({'id': ref.id}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        Referral.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkOrderViewSet(ViewSet):
    permission_classes = [IsAuthenticated, IsDentistOrAdmin]

    def list(self, request):
        qs = WorkOrder.objects.all()
        data = [{'id': w.id, 'patient_id': w.patient_id, 'manipulations': w.manipulations} for w in qs]
        return Response(data)

    def retrieve(self, request, pk=None):
        from django.shortcuts import get_object_or_404
        w = get_object_or_404(WorkOrder, pk=pk)
        return Response({'id': w.id, 'manipulations': w.manipulations})

    def create(self, request):
        data = request.data
        patient = Patient.objects.get(pk=data['patient_id'])
        wo = WorkOrder.objects.create(
            patient=patient,
            doctor=request.user,
            manipulations=data.get('manipulations', ''),
            materials=data.get('materials', ''),
            labor_cost=data.get('labor_cost', 0),
        )
        return Response({'id': wo.id}, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        WorkOrder.objects.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


from rest_framework.decorators import api_view, permission_classes as drf_permission_classes

@api_view(['GET'])
@drf_permission_classes([IsAuthenticated])
def mkbs_validate(request, code):
    exists = MKBSCode.objects.filter(code=code, is_active=True).exists()
    return Response({'valid': exists, 'code': code})
