"""Tests for authentication flow — register, login, logout."""
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from app.models import UserProfile


@pytest.mark.django_db
class TestAuthFlow:
    def test_register_new_user(self, client):
        """Регистрация нового пользователя создаёт учётную запись и делает редирект."""
        # Arrange
        payload = {
            'username': 'newuser123',
            'email': 'new@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'role': 'patient',
        }

        # Act
        r = client.post(reverse('register'), payload)

        # Assert
        assert r.status_code == 302
        assert User.objects.filter(username='newuser123').exists()

    def test_register_duplicate_username(self, client, user_dentist):
        """Регистрация с уже существующим именем пользователя возвращает форму с ошибкой."""
        # Arrange
        payload = {
            'username': 'dentist_test',  # already exists via fixture
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'Pass123!',
            'password2': 'Pass123!',
            'role': 'patient',
        }

        # Act
        r = client.post(reverse('register'), payload)

        # Assert
        assert r.status_code == 200
        assert 'form' in r.context

    def test_login_success(self, client, user_dentist, mocker):
        """Успешный вход редиректит пользователя при доступном FastAPI."""
        # Arrange
        # Вход разрешён только при доступном FastAPI (CustomLoginView).
        mocker.patch('app.views.is_fastapi_available', return_value=True)
        payload = {'username': 'dentist_test', 'password': 'pass123'}

        # Act
        r = client.post(reverse('login'), payload)

        # Assert
        assert r.status_code == 302

    def test_login_wrong_password(self, client, user_dentist):
        """Неверный пароль возвращает форму входа с ошибкой без редиректа."""
        # Arrange
        payload = {'username': 'dentist_test', 'password': 'wrongpassword'}

        # Act
        r = client.post(reverse('login'), payload)

        # Assert
        assert r.status_code == 200
        assert 'form' in r.context

    def test_register_creates_user_profile(self, client):
        """Публичная регистрация всегда создаёт профиль с ролью patient независимо от переданной роли."""
        # Arrange
        # Публичная регистрация всегда создаёт пациента, даже если прислать role=manager
        # (защита от эскалации прав — привилегии назначает только админ).
        payload = {
            'username': 'profileuser',
            'email': 'profile@x.com',
            'first_name': 'P',
            'last_name': 'U',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'role': 'manager',
        }

        # Act
        client.post(reverse('register'), payload)
        user = User.objects.get(username='profileuser')
        profile = UserProfile.objects.get(user=user)

        # Assert
        assert profile.role == 'patient'
