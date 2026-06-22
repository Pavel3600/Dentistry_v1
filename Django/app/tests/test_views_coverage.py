"""
Coverage-targeted tests for views.py paths not covered by other test files.
Focuses on: AppointmentDetail, StartVisit, ProcedureCreate, PatientHistory,
SearchByDate, PatientDashboard, RevenueReport, RoleManager, ChangeRole,
CreateExtract, AdminDashboard helpers, AppointmentCreate form errors.
"""
import pytest
from django.urls import reverse
from django.utils import timezone


pytestmark = pytest.mark.django_db


class TestAppointmentDetailView:
    def test_dentist_can_see_appointment_detail(self, client, user_dentist, appointment):
        """Стоматолог может открыть страницу детали существующей записи."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:appointment_detail', args=[appointment.pk]))

        # Assert
        assert r.status_code == 200

    def test_404_for_nonexistent_appointment(self, client, user_dentist):
        """Запрос несуществующей записи возвращает 404."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:appointment_detail', args=[99999]))

        # Assert
        assert r.status_code == 404


class TestStartVisitView:
    def test_start_visit_creates_visit(self, client, user_dentist, appointment):
        """Отправка формы визита создаёт объект Visit и переводит запись в статус completed."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:start_visit', args=[appointment.pk]), {
            'anamnesis': 'Жалобы на боль',
            'examination_results': 'Кариес',
            'treatment_plan': 'Пломбирование',
            'tooth_formula': '',
        })

        # Assert
        assert r.status_code == 302
        from app.models import Visit
        assert Visit.objects.filter(appointment=appointment).exists()
        appointment.refresh_from_db()
        assert appointment.status == 'completed'

    def test_start_visit_creates_client_if_missing(self, client, user_dentist, appointment):
        """При начале визита автоматически создаётся запись Clients, если она отсутствует."""
        # Arrange
        from app.models import Clients
        Clients.objects.filter(login=user_dentist.username).delete()
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:start_visit', args=[appointment.pk]), {
            'anamnesis': 'test', 'examination_results': 'OK',
        })

        # Assert
        assert r.status_code == 302
        assert Clients.objects.filter(login=user_dentist.username).exists()


class TestProcedureCreateView:
    def test_add_procedure_redirects(self, client, user_dentist, visit, service):
        """Добавление процедуры к визиту перенаправляет на следующую страницу."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:add_procedure', args=[visit.pk]), {
            'service': service.id,
            'quantity': 1,
        })

        # Assert
        assert r.status_code == 302

    def test_procedure_form_get(self, client, user_dentist, visit):
        """GET-запрос на страницу добавления процедуры возвращает форму."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:add_procedure', args=[visit.pk]))

        # Assert
        assert r.status_code == 200


class TestPatientHistoryView:
    def test_dentist_can_see_patient_history(self, client, user_dentist, patient):
        """Стоматолог может просмотреть историю визитов пациента."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:patient_history', args=[patient.pk]))

        # Assert
        assert r.status_code == 200

    def test_404_for_nonexistent_patient(self, client, user_dentist):
        """Запрос истории несуществующего пациента возвращает 404."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:patient_history', args=[99999]))

        # Assert
        assert r.status_code == 404


class TestSearchByDateView:
    def test_search_page_renders(self, client, user_dentist):
        """Страница поиска по дате отображается без параметров."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:search_by_date'))

        # Assert
        assert r.status_code == 200

    def test_search_with_date_range(self, client, user_dentist):
        """Поиск с указанием диапазона дат возвращает результаты без ошибок."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:search_by_date'), {
            'date_from': '2026-01-01', 'date_to': '2026-12-31',
        })

        # Assert
        assert r.status_code == 200


class TestRevenueReportView:
    def test_revenue_report_manager(self, client, user_manager):
        """Менеджер может открыть страницу отчёта по выручке."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:revenue_report'))

        # Assert
        assert r.status_code == 200

    def test_revenue_report_with_period(self, client, user_manager):
        """Отчёт по выручке с фильтром по периоду возвращает страницу без ошибок."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:revenue_report'), {'period': 'week'})

        # Assert
        assert r.status_code == 200

    def test_revenue_denied_for_dentist(self, client, user_dentist):
        """Стоматолог не имеет доступа к отчёту по выручке."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:revenue_report'))

        # Assert
        assert r.status_code in (302, 403)


class TestRoleManagerView:
    def test_admin_can_see_roles(self, client, user_admin):
        """Администратор может открыть страницу управления ролями."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:role_manager'))

        # Assert
        assert r.status_code == 200

    def test_role_manager_denied_for_manager(self, client, user_manager):
        """Менеджер не имеет доступа к странице управления ролями."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:role_manager'))

        # Assert
        assert r.status_code in (302, 403)


class TestChangeRoleView:
    def test_admin_can_change_role(self, client, user_admin, user_dentist):
        """Администратор может изменить роль другого пользователя."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:change_role', args=[user_dentist.id]), {
            'role': 'manager',
        })

        # Assert
        assert r.status_code == 302
        from app.models import UserProfile
        profile = UserProfile.objects.get(user=user_dentist)
        assert profile.role == 'manager'


class TestCreateUserWithRoleView:
    def test_admin_creates_user_with_role(self, client, user_admin):
        """Администратор может создать нового пользователя с назначенной ролью."""
        # Arrange
        from django.contrib.auth.models import User
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:create_user_with_role'), {
            'username': 'rolenewuser',
            'email': 'role@x.com',
            'first_name': 'Role',
            'last_name': 'User',
            'password': 'ComplexPass123!',
            'role': 'dentist',
        })

        # Assert
        assert r.status_code == 302
        assert User.objects.filter(username='rolenewuser').exists()


class TestPatientDashboard:
    def test_patient_dashboard_renders(self, client, user_patient, patient):
        """Личный кабинет пациента отображается, когда профиль пациента привязан к пользователю."""
        # Arrange
        patient.user_id = user_patient.id
        patient.save()
        client.force_login(user_patient)

        # Act
        r = client.get(reverse('app:patient_dashboard'))

        # Assert
        assert r.status_code == 200

    def test_patient_dashboard_without_profile(self, client, user_patient):
        """Личный кабинет пациента отображается, даже если запись Patient не привязана."""
        # Arrange
        client.force_login(user_patient)

        # Act
        r = client.get(reverse('app:patient_dashboard'))

        # Assert
        assert r.status_code == 200


class TestAppointmentCreateFormError:
    def test_invalid_form_shows_errors(self, client, user_manager):
        """Отправка некорректных данных формы создания записи не вызывает 500."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.post(reverse('app:appointment_create'), {
            'patient_id': '',
            'doctor_id': '',
            'datetime': 'not-a-date',
        })

        # Assert
        # Should re-render form (200) or redirect — either is fine
        assert r.status_code in (200, 302)


class TestPatientUpdate:
    def test_manager_can_edit_patient(self, client, user_manager, patient):
        """Менеджер может изменить данные пациента через форму редактирования."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.post(reverse('app:patient_edit', args=[patient.pk]), {
            'full_name': 'Обновлённое Имя',
            'birth_date': '1990-01-01',
            'gender': 'M',
            'phone': '+79991234567',
        })

        # Assert
        assert r.status_code == 302
        patient.refresh_from_db()
        assert patient.full_name == 'Обновлённое Имя'


class TestMkbCRUD:
    def test_mkb_list_admin(self, client, user_admin, mkb):
        """Администратор видит список кодов МКБ."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:mkb_list'))

        # Assert
        assert r.status_code == 200

    def test_mkb_create_admin(self, client, user_admin):
        """Администратор может создать новый код МКБ."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:mkb_create'), {
            'code': 'K99.9', 'name': 'Тест', 'category': 'diagnosis', 'is_active': True,
        })

        # Assert
        assert r.status_code == 302
        from app.models import MKBSCode
        assert MKBSCode.objects.filter(code='K99.9').exists()

    def test_mkb_delete_admin(self, client, user_admin, mkb):
        """Администратор может удалить код МКБ."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.post(reverse('app:mkb_delete', args=[mkb.pk]))

        # Assert
        assert r.status_code == 302
        from app.models import MKBSCode
        assert not MKBSCode.objects.filter(pk=mkb.pk).exists()
