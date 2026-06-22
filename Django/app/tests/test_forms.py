"""Tests for forms.py."""
import pytest
from django.contrib.auth.models import User

from app.forms import (
    PatientForm, ServiceForm, MaterialForm, RegistrationForm,
    VisitForm, ProcedureForm, ReferralForm, MkbCodeForm,
    VisitSearchForm, AppointmentForm,
)


pytestmark = pytest.mark.django_db


class TestPatientForm:
    def test_valid_data(self):
        """PatientForm принимает корректные данные пациента."""
        # Arrange
        data = {
            'full_name': 'Петров Пётр',
            'birth_date': '1985-05-05',
            'gender': 'M',
            'phone': '+79991112233',
        }

        # Act
        form = PatientForm(data=data)

        # Assert
        assert form.is_valid(), form.errors

    def test_missing_required_full_name(self):
        """PatientForm невалидна без поля full_name."""
        # Act
        form = PatientForm(data={'gender': 'M', 'phone': '+79991112233', 'birth_date': '1990-01-01'})

        # Assert
        assert not form.is_valid()
        assert 'full_name' in form.errors

    def test_invalid_gender_rejected(self):
        """PatientForm отклоняет недопустимое значение пола."""
        # Act
        form = PatientForm(data={
            'full_name': 'Тест', 'birth_date': '1990-01-01',
            'gender': 'X', 'phone': '+79991234567',
        })

        # Assert
        assert not form.is_valid()


class TestRegistrationForm:
    def test_valid_creates_user_with_role(self):
        """RegistrationForm сохраняет пользователя и создаёт профиль с указанной ролью."""
        # Arrange
        data = {
            'username': 'newreguser',
            'email': 'reg@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'role': 'patient',
        }

        # Act
        form = RegistrationForm(data=data)
        assert form.is_valid(), form.errors
        user = form.save()

        # Assert
        assert User.objects.filter(username='newreguser').exists()
        from app.models import UserProfile
        profile = UserProfile.objects.get(user=user)
        assert profile.role == 'patient'

    def test_password_mismatch_invalid(self):
        """RegistrationForm невалидна при несовпадающих паролях."""
        # Arrange
        data = {
            'username': 'mismatch',
            'email': 'x@x.com',
            'password1': 'pass1',
            'password2': 'pass2',
            'role': 'patient',
        }

        # Act
        form = RegistrationForm(data=data)

        # Assert
        assert not form.is_valid()
        assert 'password2' in form.errors

    def test_role_not_user_selectable(self):
        """Роль нельзя выбрать при публичной регистрации (защита от эскалации прав)."""
        # Act
        form = RegistrationForm()

        # Assert
        assert 'role' not in form.fields


class TestServiceForm:
    def test_valid_service(self):
        """ServiceForm принимает корректные данные услуги."""
        # Arrange
        data = {'code': 'T99', 'name': 'Тест', 'cost': '500.00', 'duration_minutes': 20, 'material_cost': '0.00'}

        # Act
        form = ServiceForm(data=data)

        # Assert
        assert form.is_valid(), form.errors

    def test_missing_code(self):
        """ServiceForm невалидна без поля code."""
        # Arrange
        data = {'name': 'Тест', 'cost': '500.00', 'duration_minutes': 20, 'material_cost': '0.00'}

        # Act
        form = ServiceForm(data=data)

        # Assert
        assert not form.is_valid()
        assert 'code' in form.errors


class TestMaterialForm:
    def test_valid_material(self):
        """MaterialForm принимает корректные данные материала."""
        # Arrange
        data = {'name': 'Гель', 'unit': 'мл', 'price_per_unit': '30.00'}

        # Act
        form = MaterialForm(data=data)

        # Assert
        assert form.is_valid(), form.errors


class TestVisitForm:
    def test_partial_visit_is_valid(self):
        """VisitForm валидна при заполнении только части полей."""
        # Act
        form = VisitForm(data={'anamnesis': 'Боль', 'examination_results': 'OK'})

        # Assert
        assert form.is_valid(), form.errors


class TestProcedureForm:
    def test_valid_procedure(self, service):
        """ProcedureForm принимает корректные данные процедуры."""
        # Act
        form = ProcedureForm(data={'service': service.id, 'quantity': 2})

        # Assert
        assert form.is_valid(), form.errors

    def test_missing_service_invalid(self):
        """ProcedureForm невалидна без указания услуги."""
        # Act
        form = ProcedureForm(data={'service': '', 'quantity': 1})

        # Assert
        assert not form.is_valid()


class TestVisitSearchForm:
    def test_empty_form_valid(self):
        """VisitSearchForm валидна при пустых данных (все поля необязательны)."""
        # Act
        form = VisitSearchForm(data={})

        # Assert
        assert form.is_valid()

    def test_date_range_valid(self):
        """VisitSearchForm принимает корректный диапазон дат."""
        # Act
        form = VisitSearchForm(data={'date_from': '2026-01-01', 'date_to': '2026-12-31'})

        # Assert
        assert form.is_valid()


class TestAppointmentForm:
    def test_form_has_required_fields(self, patient, user_dentist):
        """AppointmentForm валидна при заполнении всех обязательных полей."""
        # Arrange
        from django.utils import timezone
        data = {
            'patient_id': patient.id,
            'doctor_id': user_dentist.id,
            'datetime': (timezone.now() + timezone.timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
        }

        # Act
        form = AppointmentForm(data=data)

        # Assert
        assert form.is_valid(), form.errors

    def test_save_creates_appointment(self, patient, user_dentist):
        """AppointmentForm.save() создаёт запись Appointment со статусом scheduled."""
        # Arrange
        from app.models import Appointment
        from django.utils import timezone
        data = {
            'patient_id': patient.id,
            'doctor_id': user_dentist.id,
            'datetime': (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
        }
        form = AppointmentForm(data=data)
        assert form.is_valid(), form.errors

        # Act
        appt = form.save()

        # Assert
        assert Appointment.objects.filter(id=appt.id).exists()
        assert appt.status == 'scheduled'
