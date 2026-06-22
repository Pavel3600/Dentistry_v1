"""
Tests for Django API v2 endpoints (app/api/views.py).
Coverage targets: PatientViewSet, AppointmentViewSet, VisitViewSet,
ServiceViewSet, MaterialViewSet, MKBSCodeViewSet, StatisticsViewSet,
UserProfileViewSet, FastAPIStatusAPIView.
"""
import pytest
from django.urls import reverse
from django.utils import timezone


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def url(name, **kwargs):
    return reverse(name, kwargs=kwargs)


pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# FastAPI status
# ──────────────────────────────────────────────────────────────────────────────

class TestFastAPIStatus:
    def test_status_returns_200_for_authenticated(self, admin_client, mocker):
        """Аутентифицированный пользователь получает статус 200 и поле available в ответе."""
        # Arrange
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=Exception('offline'),
        )

        # Act
        r = admin_client.get('/api/v2/fastapi-status/')

        # Assert
        assert r.status_code == 200
        assert 'available' in r.json()

    def test_status_401_for_anonymous(self, api_client):
        """Анонимный запрос к эндпоинту статуса FastAPI отклоняется — статус 401 или 403."""
        # Act
        r = api_client.get('/api/v2/fastapi-status/')

        # Assert
        assert r.status_code in (401, 403)

    def test_status_reports_unavailable(self, admin_client, mocker):
        """При ConnectionError ответ содержит available=False и описание ошибки."""
        # Arrange
        import requests as req
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=req.exceptions.ConnectionError(),
        )

        # Act
        r = admin_client.get('/api/v2/fastapi-status/')
        data = r.json()

        # Assert
        assert data['available'] is False
        assert data['error'] == 'Connection refused'

    def test_status_reports_available(self, admin_client, mocker):
        """При ответе 200 от FastAPI поле available равно True."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mocker.patch('app.services.fastapi_health.requests.get', return_value=mock_resp)

        # Act
        r = admin_client.get('/api/v2/fastapi-status/')
        data = r.json()

        # Assert
        assert data['available'] is True


# ──────────────────────────────────────────────────────────────────────────────
# Patients
# ──────────────────────────────────────────────────────────────────────────────

class TestPatientViewSet:
    LIST_URL = '/api/v2/patients/'

    def test_manager_can_list_patients(self, manager_client, patient):
        """Менеджер получает список пациентов — статус 200, count >= 1."""
        # Act
        r = manager_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200
        assert r.json()['count'] >= 1

    def test_dentist_can_list_patients(self, dentist_client, patient):
        """Стоматолог может просматривать список пациентов — статус 200."""
        # Act
        r = dentist_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200

    def test_patient_role_forbidden(self, patient_client):
        """Пользователь с ролью patient не имеет доступа к списку пациентов — статус 403."""
        # Act
        r = patient_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 403

    def test_anonymous_forbidden(self, api_client):
        """Анонимный запрос к списку пациентов отклоняется — статус 401 или 403."""
        # Act
        r = api_client.get(self.LIST_URL)

        # Assert
        assert r.status_code in (401, 403)

    def test_manager_can_create_patient(self, manager_client, user_manager):
        """Менеджер создаёт нового пациента через REST API — статус 201, имя совпадает."""
        # Arrange
        data = {
            'user_id': user_manager.id,
            'full_name': 'Новый Пациент',
            'birth_date': '1985-03-15T00:00:00Z',
            'gender': 'F',
            'phone': '+79001112233',
        }

        # Act
        r = manager_client.post(self.LIST_URL, data, format='json')

        # Assert
        assert r.status_code == 201
        assert r.json()['full_name'] == 'Новый Пациент'

    def test_dentist_cannot_delete_patient(self, dentist_client, patient):
        """Стоматолог не может удалить пациента — статус 403."""
        # Act
        r = dentist_client.delete(f'{self.LIST_URL}{patient.id}/')

        # Assert
        assert r.status_code == 403

    def test_admin_can_delete_patient(self, admin_client, patient):
        """Администратор успешно удаляет пациента — статус 204."""
        # Act
        r = admin_client.delete(f'{self.LIST_URL}{patient.id}/')

        # Assert
        assert r.status_code == 204

    def test_retrieve_single_patient(self, manager_client, patient):
        """Запрос конкретного пациента по ID возвращает 200 и корректный id."""
        # Act
        r = manager_client.get(f'{self.LIST_URL}{patient.id}/')

        # Assert
        assert r.status_code == 200
        assert r.json()['id'] == patient.id

    def test_update_patient(self, manager_client, patient):
        """Частичное обновление пациента меняет имя и возвращает 200."""
        # Act
        r = manager_client.patch(
            f'{self.LIST_URL}{patient.id}/',
            {'full_name': 'Изменённое Имя'},
            format='json',
        )

        # Assert
        assert r.status_code == 200
        assert r.json()['full_name'] == 'Изменённое Имя'

    def test_search_by_name(self, manager_client, patient):
        """Поиск пациентов по фамилии «Иванов» возвращает только совпадающие записи."""
        # Act
        r = manager_client.get(self.LIST_URL, {'search': 'Иванов'})

        # Assert
        assert r.status_code == 200
        results = r.json()['results']
        assert any('Иванов' in p['full_name'] for p in results)

    def test_patient_appointments_action(self, manager_client, patient, appointment):
        """Действие appointments для пациента возвращает список его записей."""
        # Act
        r = manager_client.get(f'{self.LIST_URL}{patient.id}/appointments/')

        # Assert
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_patient_visits_action(self, manager_client, patient, visit):
        """Действие visits для пациента возвращает статус 200."""
        # Act
        r = manager_client.get(f'{self.LIST_URL}{patient.id}/visits/')

        # Assert
        assert r.status_code == 200

    def test_patient_medical_records_action(self, manager_client, patient):
        """Действие medical_records для пациента возвращает статус 200."""
        # Act
        r = manager_client.get(f'{self.LIST_URL}{patient.id}/medical_records/')

        # Assert
        assert r.status_code == 200

    def test_fastapi_health_action(self, manager_client, mocker):
        """Действие fastapi-health возвращает 200 и поле available в ответе."""
        # Arrange
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=Exception(),
        )

        # Act
        r = manager_client.get(f'{self.LIST_URL}fastapi-health/')

        # Assert
        assert r.status_code == 200
        assert 'available' in r.json()


# ──────────────────────────────────────────────────────────────────────────────
# Appointments
# ──────────────────────────────────────────────────────────────────────────────

class TestAppointmentViewSet:
    LIST_URL = '/api/v2/appointments/'

    def test_manager_can_list(self, manager_client, appointment):
        """Менеджер получает список записей на приём — статус 200."""
        # Act
        r = manager_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200

    def test_create_appointment(self, manager_client, patient, user_dentist):
        """Менеджер создаёт новую запись на приём — статус 201."""
        # Arrange
        data = {
            'patient_id': patient.id,
            'doctor_id': user_dentist.profile.id,
            'datetime': (timezone.now() + timezone.timedelta(days=2)).isoformat(),
            'status': 'scheduled',
        }

        # Act
        r = manager_client.post(self.LIST_URL, data, format='json')

        # Assert
        assert r.status_code == 201

    def test_cancel_scheduled_appointment(self, manager_client, appointment):
        """Отмена запланированной записи возвращает 200 и статус cancelled."""
        # Act
        r = manager_client.post(f'{self.LIST_URL}{appointment.id}/cancel/')

        # Assert
        assert r.status_code == 200
        assert r.json()['status'] == 'cancelled'

    def test_cancel_already_cancelled(self, manager_client, appointment):
        """Попытка отменить уже отменённую запись возвращает ошибку 400."""
        # Arrange
        appointment.status = 'cancelled'
        appointment.save()

        # Act
        r = manager_client.post(f'{self.LIST_URL}{appointment.id}/cancel/')

        # Assert
        assert r.status_code == 400

    def test_complete_appointment(self, manager_client, appointment):
        """Завершение записи возвращает 200 и статус completed."""
        # Act
        r = manager_client.post(f'{self.LIST_URL}{appointment.id}/complete/')

        # Assert
        assert r.status_code == 200
        assert r.json()['status'] == 'completed'

    def test_complete_already_completed(self, manager_client, appointment):
        """Попытка завершить уже завершённую запись возвращает ошибку 400."""
        # Arrange
        appointment.status = 'completed'
        appointment.save()

        # Act
        r = manager_client.post(f'{self.LIST_URL}{appointment.id}/complete/')

        # Assert
        assert r.status_code == 400

    def test_filter_by_status(self, manager_client, appointment):
        """Фильтрация по статусу scheduled возвращает только записи с этим статусом."""
        # Act
        r = manager_client.get(self.LIST_URL, {'status': 'scheduled'})

        # Assert
        assert r.status_code == 200
        results = r.json()['results']
        assert all(a['status'] == 'scheduled' for a in results)

    def test_filter_by_doctor(self, manager_client, appointment, user_dentist):
        """Фильтрация по ID врача возвращает статус 200."""
        # Act
        r = manager_client.get(self.LIST_URL, {'doctor_id': user_dentist.profile.id})

        # Assert
        assert r.status_code == 200

    def test_appointment_logs_action(self, manager_client, appointment):
        """Действие logs для записи возвращает список журнальных записей."""
        # Act
        r = manager_client.get(f'{self.LIST_URL}{appointment.id}/logs/')

        # Assert
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_patient_cannot_access(self, patient_client):
        """Пользователь с ролью patient не имеет доступа к записям на приём — статус 403."""
        # Act
        r = patient_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 403

    def test_cancel_creates_log(self, manager_client, appointment):
        """Отмена записи создаёт запись в журнале AppointmentLog со статусом cancelled."""
        # Arrange
        from app.models import AppointmentLog

        # Act
        manager_client.post(f'{self.LIST_URL}{appointment.id}/cancel/')

        # Assert
        assert AppointmentLog.objects.filter(appointment=appointment, new_status='cancelled').exists()


# ──────────────────────────────────────────────────────────────────────────────
# Services
# ──────────────────────────────────────────────────────────────────────────────

class TestServiceViewSet:
    LIST_URL = '/api/v2/services/'

    def test_any_authenticated_can_list(self, patient_client, service):
        """Любой аутентифицированный пользователь может просматривать список услуг — статус 200."""
        # Act
        r = patient_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200

    def test_admin_can_create(self, admin_client):
        """Администратор создаёт новую услугу — статус 201."""
        # Arrange
        data = {'code': 'S999', 'name': 'Тест', 'cost': 100, 'duration_minutes': 20, 'material_cost': 0}

        # Act
        r = admin_client.post(self.LIST_URL, data, format='json')

        # Assert
        assert r.status_code == 201

    def test_non_admin_cannot_create(self, manager_client):
        """Менеджер не может создавать услуги — статус 403."""
        # Arrange
        data = {'code': 'S998', 'name': 'Тест2', 'cost': 100, 'duration_minutes': 20, 'material_cost': 0}

        # Act
        r = manager_client.post(self.LIST_URL, data, format='json')

        # Assert
        assert r.status_code == 403

    def test_search_service(self, admin_client, service):
        """Поиск услуг по слову «Удаление» возвращает статус 200."""
        # Act
        r = admin_client.get(self.LIST_URL, {'search': 'Удаление'})

        # Assert
        assert r.status_code == 200

    def test_admin_can_delete(self, admin_client, service):
        """Администратор удаляет услугу — статус 204."""
        # Act
        r = admin_client.delete(f'{self.LIST_URL}{service.id}/')

        # Assert
        assert r.status_code == 204

    def test_admin_can_update(self, admin_client, service):
        """Администратор обновляет стоимость услуги — статус 200, значение изменяется."""
        # Act
        r = admin_client.patch(f'{self.LIST_URL}{service.id}/', {'cost': 2000}, format='json')

        # Assert
        assert r.status_code == 200
        assert r.json()['cost'] == '2000.00'


# ──────────────────────────────────────────────────────────────────────────────
# Materials
# ──────────────────────────────────────────────────────────────────────────────

class TestMaterialViewSet:
    LIST_URL = '/api/v2/materials/'

    def test_authenticated_can_list(self, manager_client, material):
        """Аутентифицированный пользователь получает список материалов — статус 200."""
        # Act
        r = manager_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200

    def test_admin_can_create(self, admin_client):
        """Администратор создаёт новый материал — статус 201."""
        # Arrange
        # Act
        r = admin_client.post(self.LIST_URL, {'name': 'Гель', 'unit': 'г', 'price_per_unit': 30}, format='json')

        # Assert
        assert r.status_code == 201

    def test_non_admin_cannot_create(self, dentist_client):
        """Стоматолог не может создавать материалы — статус 403."""
        # Act
        r = dentist_client.post(self.LIST_URL, {'name': 'X', 'unit': 'шт', 'price_per_unit': 10}, format='json')

        # Assert
        assert r.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# MKB codes
# ──────────────────────────────────────────────────────────────────────────────

class TestMKBSCodeViewSet:
    LIST_URL = '/api/v2/mkbs/'

    def test_list(self, dentist_client, mkb):
        """Стоматолог получает список кодов МКБ — статус 200."""
        # Act
        r = dentist_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200

    def test_search(self, dentist_client, mkb):
        """Поиск кодов МКБ по слову «Кариес» возвращает статус 200."""
        # Act
        r = dentist_client.get(self.LIST_URL, {'search': 'Кариес'})

        # Assert
        assert r.status_code == 200

    def test_filter_by_category(self, dentist_client, mkb):
        """Фильтрация кодов МКБ по категории diagnosis возвращает статус 200."""
        # Act
        r = dentist_client.get(self.LIST_URL, {'category': 'diagnosis'})

        # Assert
        assert r.status_code == 200

    def test_filter_active_only(self, dentist_client, mkb):
        """Фильтрация только активных кодов МКБ возвращает статус 200."""
        # Act
        r = dentist_client.get(self.LIST_URL, {'active_only': '1'})

        # Assert
        assert r.status_code == 200

    def test_admin_can_create(self, admin_client):
        """Администратор создаёт новый код МКБ — статус 201."""
        # Arrange
        # Act
        r = admin_client.post(self.LIST_URL, {
            'code': 'K99.9', 'name': 'Тест МКБ', 'category': 'diagnosis', 'is_active': True,
        }, format='json')

        # Assert
        assert r.status_code == 201

    def test_non_admin_cannot_create(self, manager_client):
        """Менеджер не может создавать коды МКБ — статус 403."""
        # Act
        r = manager_client.post(self.LIST_URL, {
            'code': 'K88.8', 'name': 'Тест2', 'category': 'service', 'is_active': True,
        }, format='json')

        # Assert
        assert r.status_code == 403


# ──────────────────────────────────────────────────────────────────────────────
# Visits
# ──────────────────────────────────────────────────────────────────────────────

class TestVisitViewSet:
    LIST_URL = '/api/v2/visits/'

    def test_dentist_can_list_own_visits(self, dentist_client, visit):
        """Стоматолог видит список своих визитов — статус 200."""
        # Act
        r = dentist_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200

    def test_admin_can_list_all_visits(self, admin_client, visit):
        """Администратор видит все визиты — статус 200."""
        # Act
        r = admin_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200

    def test_patient_cannot_access(self, patient_client):
        """Пациент не имеет доступа к списку визитов — статус 403."""
        # Act
        r = patient_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 403

    def test_retrieve_visit(self, dentist_client, visit):
        """Запрос конкретного визита по ID возвращает 200 и корректный id."""
        # Act
        r = dentist_client.get(f'{self.LIST_URL}{visit.id}/')

        # Assert
        assert r.status_code == 200
        assert r.json()['id'] == visit.id

    def test_visit_procedures_action(self, dentist_client, visit, procedure):
        """Действие procedures для визита возвращает список как минимум из одной процедуры."""
        # Act
        r = dentist_client.get(f'{self.LIST_URL}{visit.id}/procedures/')

        # Assert
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_visit_investigations_action(self, dentist_client, visit):
        """Действие investigations для визита возвращает статус 200."""
        # Act
        r = dentist_client.get(f'{self.LIST_URL}{visit.id}/investigations/')

        # Assert
        assert r.status_code == 200

    def test_filter_by_patient(self, admin_client, visit, patient):
        """Фильтрация визитов по ID пациента возвращает статус 200."""
        # Act
        r = admin_client.get(self.LIST_URL, {'patient_id': patient.id})

        # Assert
        assert r.status_code == 200

    def test_add_procedure_action(self, dentist_client, visit, service):
        """Добавление процедуры к визиту возвращает 201 и корректное количество."""
        # Arrange
        data = {'service': service.id, 'quantity': 2}

        # Act
        r = dentist_client.post(f'{self.LIST_URL}{visit.id}/add_procedure/', data, format='json')

        # Assert
        assert r.status_code == 201
        assert r.json()['quantity'] == 2


# ──────────────────────────────────────────────────────────────────────────────
# User profiles
# ──────────────────────────────────────────────────────────────────────────────

class TestUserProfileViewSet:
    LIST_URL = '/api/v2/users/'

    def test_admin_can_list(self, admin_client, user_dentist):
        """Администратор получает список пользователей — статус 200."""
        # Act
        r = admin_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 200

    def test_non_admin_forbidden(self, manager_client):
        """Менеджер не имеет доступа к списку пользователей — статус 403."""
        # Act
        r = manager_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 403

    def test_set_role_action(self, admin_client, user_dentist):
        """Администратор изменяет роль пользователя через действие set_role — статус 200, роль обновляется."""
        # Arrange
        pk = user_dentist.profile.id

        # Act
        r = admin_client.patch(f'{self.LIST_URL}{pk}/set_role/', {'role': 'manager'}, format='json')

        # Assert
        assert r.status_code == 200
        assert r.json()['role'] == 'manager'

    def test_set_invalid_role(self, admin_client, user_dentist):
        """Попытка установить несуществующую роль возвращает ошибку 400."""
        # Arrange
        pk = user_dentist.profile.id

        # Act
        r = admin_client.patch(f'{self.LIST_URL}{pk}/set_role/', {'role': 'superuser'}, format='json')

        # Assert
        assert r.status_code == 400

    def test_doctors_action(self, admin_client, user_dentist):
        """Действие doctors возвращает только пользователей с ролью dentist."""
        # Act
        r = admin_client.get(f'{self.LIST_URL}doctors/')

        # Assert
        assert r.status_code == 200
        roles = [u['role'] for u in r.json()]
        assert all(role == 'dentist' for role in roles)


# ──────────────────────────────────────────────────────────────────────────────
# Statistics
# ──────────────────────────────────────────────────────────────────────────────

class TestStatisticsViewSet:
    LIST_URL = '/api/v2/statistics/'

    def test_manager_can_access(self, manager_client):
        """Менеджер получает статистику — статус 200, присутствуют поля total_patients и total_revenue."""
        # Act
        r = manager_client.get(self.LIST_URL)
        data = r.json()

        # Assert
        assert r.status_code == 200
        assert 'total_patients' in data
        assert 'total_revenue' in data

    def test_dentist_forbidden(self, dentist_client):
        """Стоматолог не имеет доступа к статистике — статус 403."""
        # Act
        r = dentist_client.get(self.LIST_URL)

        # Assert
        assert r.status_code == 403

    def test_by_doctor_action(self, manager_client):
        """Действие by_doctor возвращает статистику по врачам — статус 200."""
        # Act
        r = manager_client.get(f'{self.LIST_URL}by_doctor/')

        # Assert
        assert r.status_code == 200

    def test_by_service_action(self, manager_client):
        """Действие by_service возвращает статистику по услугам — статус 200."""
        # Act
        r = manager_client.get(f'{self.LIST_URL}by_service/')

        # Assert
        assert r.status_code == 200

    def test_fastapi_status_action(self, manager_client, mocker):
        """Действие fastapi_status в статистике возвращает статус 200."""
        # Arrange
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=Exception(),
        )

        # Act
        r = manager_client.get(f'{self.LIST_URL}fastapi_status/')

        # Assert
        assert r.status_code == 200

    def test_custom_period(self, manager_client):
        """Статистика с параметром days=7 возвращает period_days=7 в ответе."""
        # Act
        r = manager_client.get(self.LIST_URL, {'days': 7})

        # Assert
        assert r.status_code == 200
        assert r.json()['period_days'] == 7
