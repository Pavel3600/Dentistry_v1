"""Tests for serializers.py."""
import pytest
from django.utils import timezone

from app.serializers import (
    AppointmentSerializer, PatientSerializer, ServiceSerializer,
    MaterialSerializer, MKBSCodeSerializer, VisitSerializer,
    UserProfileSerializer, StatisticsSerializer, MedicalRecordSerializer,
)


pytestmark = pytest.mark.django_db


class TestPatientSerializer:
    def test_valid_data_serializes(self, patient):
        """Сериализатор корректно возвращает данные существующего пациента."""
        # Arrange
        # (объект patient создан фикстурой)

        # Act
        s = PatientSerializer(patient)

        # Assert
        assert s.data['full_name'] == patient.full_name
        assert s.data['phone'] == patient.phone

    def test_invalid_phone_raises(self, user_admin):
        """Сериализатор отклоняет данные с некорректным форматом телефона."""
        # Arrange
        data = {
            'user_id': user_admin.id,
            'full_name': 'Тест',
            'birth_date': '1990-01-01T00:00:00Z',
            'gender': 'M',
            'phone': 'bad_phone',
        }

        # Act
        s = PatientSerializer(data=data)

        # Assert
        assert not s.is_valid()
        assert 'phone' in s.errors

    def test_valid_phone_normalised(self, user_admin):
        """Сериализатор нормализует телефон, начинающийся с 8, к формату 7."""
        # Arrange
        data = {
            'user_id': user_admin.id,
            'full_name': 'Тест',
            'birth_date': '1990-01-01T00:00:00Z',
            'gender': 'M',
            'phone': '89991234567',
        }

        # Act
        s = PatientSerializer(data=data)

        # Assert
        assert s.is_valid(), s.errors
        assert s.validated_data['phone'].startswith('7')


class TestAppointmentSerializer:
    def test_past_datetime_invalid(self, patient, user_dentist):
        """Сериализатор отклоняет запись с датой приёма в прошлом."""
        # Arrange
        data = {
            'patient_id': patient.id,
            'doctor_id': user_dentist.profile.id,
            'datetime': (timezone.now() - timezone.timedelta(days=1)).isoformat(),
            'status': 'scheduled',
        }

        # Act
        s = AppointmentSerializer(data=data)

        # Assert
        assert not s.is_valid()
        assert 'datetime' in s.errors

    def test_future_datetime_valid(self, patient, user_dentist):
        """Сериализатор принимает запись с датой приёма в будущем."""
        # Arrange
        data = {
            'patient_id': patient.id,
            'doctor_id': user_dentist.profile.id,
            'datetime': (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            'status': 'scheduled',
        }

        # Act
        s = AppointmentSerializer(data=data)

        # Assert
        assert s.is_valid(), s.errors

    def test_serializes_appointment(self, appointment):
        """Сериализатор корректно возвращает статус и id пациента для записи на приём."""
        # Arrange
        # (объект appointment создан фикстурой)

        # Act
        s = AppointmentSerializer(appointment)

        # Assert
        assert s.data['status'] == 'scheduled'
        assert s.data['patient_id'] == appointment.patient_id


class TestServiceSerializer:
    def test_fields_present(self, service):
        """Сериализатор услуги содержит все обязательные поля."""
        # Arrange
        # (объект service создан фикстурой)

        # Act
        s = ServiceSerializer(service)

        # Assert
        for field in ('id', 'code', 'name', 'cost', 'duration_minutes', 'material_cost'):
            assert field in s.data

    def test_valid_service_data(self):
        """Сериализатор принимает корректные данные новой услуги."""
        # Arrange
        data = {'code': 'T01', 'name': 'Тест услуга', 'cost': '500.00',
                'duration_minutes': 15, 'material_cost': '0.00'}

        # Act
        s = ServiceSerializer(data=data)

        # Assert
        assert s.is_valid(), s.errors


class TestMKBSCodeSerializer:
    def test_serializes(self, mkb):
        """Сериализатор МКБ-кода возвращает правильные code и is_active."""
        # Arrange
        # (объект mkb создан фикстурой)

        # Act
        s = MKBSCodeSerializer(mkb)

        # Assert
        assert s.data['code'] == 'K02.0'
        assert s.data['is_active'] is True

    def test_invalid_missing_required(self):
        """Сериализатор МКБ-кода отклоняет пустые данные — поле code обязательно."""
        # Arrange
        data = {}

        # Act
        s = MKBSCodeSerializer(data=data)

        # Assert
        assert not s.is_valid()
        assert 'code' in s.errors


class TestUserProfileSerializer:
    def test_contains_role(self, user_admin):
        """Сериализатор профиля возвращает корректную роль пользователя."""
        # Arrange
        # (объект user_admin создан фикстурой)

        # Act
        s = UserProfileSerializer(user_admin.profile)

        # Assert
        assert s.data['role'] == 'admin'

    def test_contains_username(self, user_manager):
        """Сериализатор профиля возвращает корректное имя пользователя."""
        # Arrange
        # (объект user_manager создан фикстурой)

        # Act
        s = UserProfileSerializer(user_manager.profile)

        # Assert
        assert s.data['username'] == 'manager_test'


class TestStatisticsSerializer:
    def test_validates_data(self):
        """Сериализатор статистики принимает корректный набор числовых полей."""
        # Arrange
        data = {
            'total_patients': 10,
            'total_appointments': 20,
            'completed_appointments': 5,
            'cancelled_appointments': 3,
            'scheduled_appointments': 12,
            'total_visits': 5,
            'total_revenue': '15000.00',
            'period_days': 30,
        }

        # Act
        s = StatisticsSerializer(data=data)

        # Assert
        assert s.is_valid(), s.errors
