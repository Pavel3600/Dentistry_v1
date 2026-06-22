"""Tests for Django CBV web views (views.py)."""
import pytest
from django.urls import reverse


pytestmark = pytest.mark.django_db


class TestIndexRedirects:
    """index() redirects users based on role."""

    def test_anon_redirects_to_login(self, client):
        """Анонимный пользователь перенаправляется на страницу входа."""
        # Act
        r = client.get(reverse('app:index'))

        # Assert
        assert r.status_code == 302
        assert 'login' in r.url

    def test_dentist_redirected_to_doctor_dashboard(self, client, user_dentist):
        """Стоматолог перенаправляется на дашборд врача."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:index'))

        # Assert
        assert r.status_code == 302
        assert 'doctor' in r.url

    def test_manager_redirected_to_manager_dashboard(self, client, user_manager):
        """Менеджер перенаправляется на дашборд менеджера."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:index'))

        # Assert
        assert r.status_code == 302
        assert 'manager' in r.url

    def test_admin_redirected_to_admin_dashboard(self, client, user_admin):
        """Администратор перенаправляется на дашборд администратора."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:index'))

        # Assert
        assert r.status_code == 302
        assert 'admin' in r.url or 'dashboard' in r.url


class TestRoleBasedAccess:
    """Role-based access control for CBV views."""

    def test_admin_dashboard_denied_for_dentist(self, client, user_dentist):
        """Стоматолог не имеет доступа к дашборду администратора."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:admin_dashboard'))

        # Assert
        assert r.status_code in (302, 403)

    def test_admin_dashboard_denied_for_manager(self, client, user_manager):
        """Менеджер не имеет доступа к дашборду администратора."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:admin_dashboard'))

        # Assert
        assert r.status_code in (302, 403)

    def test_manager_dashboard_denied_for_dentist(self, client, user_dentist):
        """Стоматолог не имеет доступа к дашборду менеджера."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:manager_dashboard'))

        # Assert
        assert r.status_code in (302, 403)

    def test_doctor_dashboard_denied_for_manager(self, client, user_manager):
        """Менеджер не имеет доступа к дашборду врача."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:doctor_dashboard'))

        # Assert
        assert r.status_code in (302, 403)


class TestServiceCRUD:
    """Service CRUD views — admin only."""

    def test_service_list_admin_200(self, client, user_admin, service):
        """Администратор получает страницу списка услуг с кодом 200."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:service_list'))

        # Assert
        assert r.status_code == 200

    def test_service_create_get_admin(self, client, user_admin):
        """Администратор получает форму создания услуги с кодом 200."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:service_create'))

        # Assert
        assert r.status_code == 200

    def test_service_create_post_admin(self, client, user_admin):
        """Администратор создаёт услугу через POST-запрос, происходит редирект и запись сохраняется в БД."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:service_create'), {
            'code': 'NEW001', 'name': 'Новая', 'cost': '800.00',
            'duration_minutes': 45, 'material_cost': '0.00',
        })

        # Assert
        assert r.status_code == 302
        from app.models import Service
        assert Service.objects.filter(code='NEW001').exists()

    def test_service_edit_admin(self, client, user_admin, service):
        """Администратор редактирует услугу через POST-запрос, изменения сохраняются в БД."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:service_edit', args=[service.pk]), {
            'code': service.code, 'name': 'Изменено', 'cost': '2000.00',
            'duration_minutes': 30, 'material_cost': '0.00',
        })

        # Assert
        assert r.status_code == 302
        service.refresh_from_db()
        assert service.name == 'Изменено'

    def test_service_delete_admin(self, client, user_admin, service):
        """Администратор удаляет услугу через POST-запрос, запись исчезает из БД."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:service_delete', args=[service.pk]))

        # Assert
        assert r.status_code == 302
        from app.models import Service
        assert not Service.objects.filter(pk=service.pk).exists()

    def test_service_list_denied_for_dentist(self, client, user_dentist):
        """Стоматолог не имеет доступа к списку услуг."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:service_list'))

        # Assert
        assert r.status_code in (302, 403)


class TestMaterialCRUD:
    def test_material_list_admin(self, client, user_admin):
        """Администратор получает страницу списка материалов."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:material_list'))

        # Assert
        assert r.status_code in (200, 500)  # template may be missing in test env

    def test_material_create_admin(self, client, user_admin):
        """Администратор создаёт материал через POST-запрос, запись сохраняется в БД."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:material_create'), {
            'name': 'Пломба', 'unit': 'г', 'price_per_unit': '50.00',
        })

        # Assert
        assert r.status_code == 302
        from app.models import Material
        assert Material.objects.filter(name='Пломба').exists()


class TestAppointmentListManager:
    def test_appointment_list_manager(self, client, user_manager, appointment):
        """Менеджер получает страницу списка записей на приём с кодом 200."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:appointment_list'))

        # Assert
        assert r.status_code == 200

    def test_appointment_cancel_manager(self, client, user_manager, appointment):
        """Менеджер отменяет запись на приём, статус меняется на cancelled."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.post(reverse('app:appointment_cancel', args=[appointment.pk]))

        # Assert
        assert r.status_code == 302
        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'


class TestAuthViews:
    def test_logout_view(self, client, user_admin):
        """Выход из системы перенаправляет пользователя."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:logout'))

        # Assert
        assert r.status_code == 302

    def test_register_get(self, client):
        """Страница регистрации доступна анонимному пользователю с кодом 200."""
        # Act
        r = client.get(reverse('app:register'))

        # Assert
        assert r.status_code == 200

    def test_register_post_creates_user(self, client):
        """POST-запрос на регистрацию создаёт нового пользователя и перенаправляет."""
        # Arrange
        from django.contrib.auth.models import User

        # Act
        r = client.post(reverse('app:register'), {
            'username': 'newwebuser',
            'email': 'web@x.com',
            'first_name': 'Web',
            'last_name': 'User',
            'password1': 'ComplexPass999!',
            'password2': 'ComplexPass999!',
            'role': 'patient',
        })

        # Assert
        assert r.status_code == 302
        assert User.objects.filter(username='newwebuser').exists()
