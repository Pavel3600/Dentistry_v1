"""Tests for model __str__, save hooks and signals."""
import pytest
from django.contrib.auth.models import User


pytestmark = pytest.mark.django_db


class TestServiceModel:
    def test_str(self, service):
        """__str__ модели Service содержит код услуги."""
        # Assert
        assert 'S001' in str(service)

    def test_str_contains_name(self, service):
        """__str__ модели Service содержит название услуги."""
        # Assert
        assert 'Удаление' in str(service)


class TestMaterialModel:
    def test_str(self, material):
        """__str__ модели Material содержит название материала."""
        # Assert
        assert 'Анестетик' in str(material)


class TestUserProfileModel:
    def test_str_dentist(self, user_dentist):
        """__str__ профиля стоматолога содержит слово 'Стоматолог'."""
        # Act
        s = str(user_dentist.profile)

        # Assert
        assert 'Стоматолог' in s

    def test_role_choices_all_roles_present(self):
        """ROLE_CHOICES содержит все четыре роли: dentist, manager, admin, patient."""
        # Arrange
        from app.models import UserProfile
        roles = dict(UserProfile.ROLE_CHOICES)

        # Assert
        for role in ('dentist', 'manager', 'admin', 'patient'):
            assert role in roles

    def test_signal_creates_profile_on_user_create(self):
        """Сигнал post_save создаёт UserProfile с ролью dentist при создании User."""
        # Act
        user = User.objects.create_user(username='signal_test_user99', password='test')

        # Assert
        assert hasattr(user, 'profile')
        assert user.profile is not None
        assert user.profile.role == 'dentist'


class TestPatientModel:
    def test_str(self, patient):
        """__str__ модели Patient содержит фамилию пациента."""
        # Assert
        assert 'Иванов' in str(patient)


class TestAppointmentModel:
    def test_str(self, appointment):
        """__str__ модели Appointment содержит слово 'Appointment'."""
        # Assert
        assert 'Appointment' in str(appointment)

    def test_status_choices_include_all(self):
        """STATUS_CHOICES содержит статусы scheduled, completed и cancelled."""
        # Arrange
        from app.models import Appointment
        statuses = dict(Appointment.STATUS_CHOICES)

        # Assert
        assert 'scheduled' in statuses
        assert 'completed' in statuses
        assert 'cancelled' in statuses


class TestVisitModel:
    def test_str_contains_date(self, visit):
        """__str__ модели Visit содержит слово 'Visit'."""
        # Assert
        assert 'Visit' in str(visit)


class TestProcedureModel:
    def test_auto_calculates_total_cost(self, visit, service):
        """Поле total_cost рассчитывается автоматически как cost * quantity при создании Procedure."""
        # Arrange
        from app.models import Procedure

        # Act
        proc = Procedure.objects.create(visit=visit, service=service, quantity=3)

        # Assert
        assert proc.total_cost == service.cost * 3

    def test_total_cost_updates_on_save(self, procedure, service):
        """Поле total_cost пересчитывается при изменении quantity и повторном сохранении."""
        # Arrange
        procedure.quantity = 2

        # Act
        procedure.save()

        # Assert
        assert procedure.total_cost == service.cost * 2


class TestMKBSCodeModel:
    def test_str(self, mkb):
        """__str__ модели MKBSCode содержит код и название диагноза."""
        # Assert
        assert 'K02.0' in str(mkb)
        assert 'Кариес' in str(mkb)


class TestMkbCodeProxy:
    def test_is_proxy_of_mkbs(self):
        """MkbCode является прокси-моделью MKBSCode."""
        # Arrange
        from app.models import MkbCode, MKBSCode

        # Assert
        assert issubclass(MkbCode, MKBSCode)

    def test_create_via_proxy(self):
        """Через прокси-модель MkbCode можно создать запись в БД."""
        # Arrange
        from app.models import MkbCode

        # Act
        code = MkbCode.objects.create(
            code='T11.1',
            name='Тест прокси',
            category='diagnosis',
            is_active=True,
        )

        # Assert
        assert code.pk is not None


class TestInvestigationModel:
    def test_str(self, visit):
        """__str__ модели Investigation содержит тип исследования."""
        # Arrange
        from app.models import Investigation

        # Act
        inv = Investigation.objects.create(
            visit=visit, type='Рентген', description='Снимок зуба',
        )

        # Assert
        assert 'Рентген' in str(inv)


class TestAppointmentLogModel:
    def test_str(self, appointment, user_admin):
        """__str__ модели AppointmentLog содержит старый и новый статус."""
        # Arrange
        from app.models import AppointmentLog

        # Act
        log = AppointmentLog.objects.create(
            appointment=appointment,
            changed_by=user_admin,
            old_status='scheduled',
            new_status='cancelled',
        )

        # Assert
        assert 'scheduled' in str(log)
        assert 'cancelled' in str(log)


class TestMaterialUsageModel:
    def test_auto_calculates_cost(self, procedure, material):
        """Поле cost в MaterialUsage рассчитывается как price_per_unit * quantity."""
        # Arrange
        from app.models import MaterialUsage

        # Act
        usage = MaterialUsage.objects.create(
            procedure=procedure,
            material=material,
            quantity=2,
        )

        # Assert
        assert usage.cost == material.price_per_unit * 2


class TestSyncSignals:
    def test_sync_user_creates_clients_entry(self):
        """Создание User автоматически создаёт соответствующую запись в таблице Clients."""
        # Arrange
        from app.models import Clients

        # Act
        user = User.objects.create_user(username='sync_cli_test', password='x')

        # Assert
        assert Clients.objects.filter(login='sync_cli_test').exists()

    def test_update_user_still_has_clients(self):
        """После обновления User запись в Clients остаётся."""
        # Arrange
        from app.models import Clients
        user = User.objects.create_user(username='sync_update99', password='x')

        # Act
        user.first_name = 'Updated'
        user.save()

        # Assert
        assert Clients.objects.filter(login='sync_update99').exists()
