"""Shared fixtures."""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient


def _make_user(username, role='dentist', password='pass123',
               first_name='Test', last_name='User'):
    user = User.objects.create_user(
        username=username, password=password,
        first_name=first_name, last_name=last_name,
    )
    user.profile.role = role
    user.profile.save()
    return user


@pytest.fixture
def user_admin(db):
    return _make_user('admin_test', role='admin')


@pytest.fixture
def user_manager(db):
    return _make_user('manager_test', role='manager')


@pytest.fixture
def user_dentist(db):
    return _make_user('dentist_test', role='dentist')


@pytest.fixture
def user_patient(db):
    return _make_user('patient_test', role='patient')


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_client(api_client, user_admin):
    api_client.force_authenticate(user=user_admin)
    return api_client


@pytest.fixture
def manager_client(api_client, user_manager):
    api_client.force_authenticate(user=user_manager)
    return api_client


@pytest.fixture
def dentist_client(api_client, user_dentist):
    api_client.force_authenticate(user=user_dentist)
    return api_client


@pytest.fixture
def patient_client(api_client, user_patient):
    api_client.force_authenticate(user=user_patient)
    return api_client


# ---- Domain model fixtures ----

@pytest.fixture
def service(db):
    from app.models import Service
    return Service.objects.create(
        code='S001', name='Удаление зуба', cost=1500.0,
        duration_minutes=30, material_cost=200.0,
    )


@pytest.fixture
def material(db):
    from app.models import Material
    return Material.objects.create(name='Анестетик', unit='мл', price_per_unit=100.0)


@pytest.fixture
def mkb(db):
    from app.models import MKBSCode
    return MKBSCode.objects.create(
        code='K02.0', name='Кариес эмали', category='diagnosis', is_active=True,
    )


@pytest.fixture
def patient(db):
    from app.models import Patient
    return Patient.objects.create(
        full_name='Иванов Иван', birth_date=timezone.make_aware(timezone.datetime(1990, 1, 1)),
        gender='M', phone='+79991234567',
    )


@pytest.fixture
def appointment(db, patient, user_dentist):
    from app.models import Appointment
    return Appointment.objects.create(
        patient=patient, doctor=user_dentist,
        datetime=timezone.now() + timezone.timedelta(days=1),
        status='scheduled',
    )


@pytest.fixture
def visit(db, appointment, patient, user_dentist):
    from app.models import Visit
    return Visit.objects.create(
        appointment=appointment, patient=patient, doctor=user_dentist,
    )


@pytest.fixture
def procedure(db, visit, service):
    from app.models import Procedure
    return Procedure.objects.create(visit=visit, service=service, quantity=1)
