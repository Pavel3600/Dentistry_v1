"""Tests for legacy API endpoints (JWT token, public services API)."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from app.models import Service


pytestmark = pytest.mark.django_db


class TestJWTToken:
    def test_obtain_token_valid_credentials(self, user_dentist):
        """JWT-токен успешно выдаётся при корректных учётных данных."""
        # Arrange
        client = APIClient()
        payload = {'username': 'dentist_test', 'password': 'pass123'}

        # Act
        r = client.post(reverse('token_obtain_pair'), payload)

        # Assert
        assert r.status_code == 200
        assert 'access' in r.data
        assert 'refresh' in r.data

    def test_obtain_token_invalid_credentials(self):
        """JWT-токен не выдаётся при неверных учётных данных."""
        # Arrange
        client = APIClient()
        payload = {'username': 'nobody', 'password': 'wrongpass'}

        # Act
        r = client.post(reverse('token_obtain_pair'), payload)

        # Assert
        assert r.status_code == 401

    def test_refresh_token(self, user_dentist):
        """Refresh-токен позволяет получить новый access-токен."""
        # Arrange
        client = APIClient()
        r = client.post(reverse('token_obtain_pair'), {
            'username': 'dentist_test', 'password': 'pass123',
        })
        refresh = r.data['refresh']

        # Act
        r2 = client.post(reverse('token_refresh'), {'refresh': refresh})

        # Assert
        assert r2.status_code == 200
        assert 'access' in r2.data


class TestPublicServicesAPI:
    def test_api_services_no_auth_required(self, service):
        """Публичный эндпоинт услуг доступен без аутентификации."""
        # Arrange
        client = APIClient()

        # Act
        r = client.get(reverse('api_services'))

        # Assert
        assert r.status_code == 200

    def test_api_services_returns_service_data(self, service):
        """Эндпоинт услуг возвращает данные созданной услуги."""
        # Arrange
        client = APIClient()

        # Act
        r = client.get(reverse('api_services'))
        data = r.data

        # Assert
        assert any(s.get('code') == 'S001' for s in data)
