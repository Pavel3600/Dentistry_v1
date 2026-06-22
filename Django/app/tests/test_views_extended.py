"""Extended tests for Django CBV views — dashboard access, CRUD, FastAPI status."""
import pytest
from django.urls import reverse
from app.models import Patient, Appointment, Service, Material


@pytest.mark.django_db
class TestDashboardAccess:
    def test_admin_dashboard_accessible(self, client, user_admin):
        """Администратор успешно открывает свой дашборд."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:admin_dashboard'))

        # Assert
        assert r.status_code == 200

    def test_manager_dashboard_accessible(self, client, user_manager):
        """Менеджер успешно открывает свой дашборд."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:manager_dashboard'))

        # Assert
        assert r.status_code == 200

    def test_doctor_dashboard_accessible(self, client, user_dentist):
        """Стоматолог успешно открывает свой дашборд."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:doctor_dashboard'))

        # Assert
        assert r.status_code == 200


@pytest.mark.django_db
class TestServiceCRUDExtended:
    def test_service_list_contains_service(self, client, user_admin, service):
        """Список услуг содержит созданную услугу в контексте шаблона."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:service_list'))

        # Assert
        assert r.status_code == 200
        assert service in r.context['services']

    def test_service_create_admin(self, client, user_admin):
        """Администратор создаёт новую услугу, запись появляется в БД."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:service_create'), {
            'code': 'NEW001', 'name': 'Новая услуга', 'cost': '1000.00',
            'duration_minutes': 60, 'material_cost': '0.00',
        })

        # Assert
        assert r.status_code == 302
        assert Service.objects.filter(code='NEW001').exists()

    def test_service_delete_admin(self, client, user_admin, service):
        """Администратор удаляет услугу, запись исчезает из БД."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:service_delete', args=[service.pk]))

        # Assert
        assert r.status_code == 302
        assert not Service.objects.filter(pk=service.pk).exists()


@pytest.mark.django_db
class TestMaterialCRUDExtended:
    def test_material_list_admin(self, client, user_admin):
        """Администратор получает страницу списка материалов с кодом 200."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:material_list'))

        # Assert
        assert r.status_code == 200

    def test_material_create_admin(self, client, user_admin):
        """Администратор создаёт материал через POST-запрос, запись сохраняется в БД."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:material_create'), {
            'name': 'Пломбировочный материал', 'unit': 'гр', 'price_per_unit': '500.00',
        })

        # Assert
        assert r.status_code == 302
        assert Material.objects.filter(name='Пломбировочный материал').exists()


@pytest.mark.django_db
class TestPatientCRUDExtended:
    def test_patient_list_manager(self, client, user_manager, patient):
        """Менеджер получает список пациентов, который содержит созданного пациента."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:patient_list'))

        # Assert
        assert r.status_code == 200
        assert patient in r.context['patients']

    def test_patient_create_manager(self, client, user_manager):
        """Менеджер создаёт пациента через POST-запрос, запись сохраняется в БД."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.post(reverse('app:patient_create'), {
            'full_name': 'Новый Пациент Иванович',
            'birth_date': '1990-01-01',
            'gender': 'M',
            'phone': '+79991112233',
        })

        # Assert
        assert r.status_code == 302
        assert Patient.objects.filter(full_name='Новый Пациент Иванович').exists()


@pytest.mark.django_db
class TestAppointmentCRUDExtended:
    def test_appointment_create_manager(self, client, user_manager, patient, user_dentist):
        """Менеджер создаёт запись на приём, запись появляется в БД."""
        # Arrange
        from django.utils import timezone
        client.force_login(user_manager)
        future = (timezone.now() + timezone.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M')

        # Act
        r = client.post(reverse('app:appointment_create'), {
            'patient_id': patient.id,
            'doctor_id': user_dentist.id,
            'datetime': future,
        })

        # Assert
        assert r.status_code == 302
        assert Appointment.objects.filter(patient_id=patient.id).exists()


@pytest.mark.django_db
class TestFastAPIStatusPage:
    def test_fastapi_status_page(self, client, user_manager):
        """Менеджер получает страницу статуса FastAPI с кодом 200."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('fastapi_full_status'))

        # Assert
        assert r.status_code == 200
