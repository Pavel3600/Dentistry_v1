"""Shared fixtures — only models that actually exist in app/models.py."""
import pytest
from django.contrib.auth.models import User
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
