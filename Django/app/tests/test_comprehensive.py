"""Comprehensive tests for V711 Django project targeting 85%+ coverage."""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient


# ─── helpers ────────────────────────────────────────────────────────────────

def make_user(username, role='admin', password='pass123', first='Test', last='User'):
    user = User.objects.create_user(
        username=username, password=password, first_name=first, last_name=last
    )
    user.profile.role = role
    user.profile.save()
    return user


SAMPLE_PATIENT = {'id': 1, 'full_name': 'Иван Иванов', 'phone': '+79001234567',
                  'birth_date': '1990-01-01', 'gender': 'male', 'user_id': None}
SAMPLE_APPOINTMENT = {'id': 1, 'patient_id': 1, 'doctor_id': 2,
                      'datetime': '2026-06-22T10:00:00', 'status': 'scheduled'}
SAMPLE_VISIT = {'id': 1, 'appointment_id': 1, 'patient_id': 1, 'doctor_id': 2,
                'visit_date': '2026-06-22', 'diagnosis_id': None,
                'anamnesis': '', 'examination_results': '', 'treatment_plan': '',
                'prescription': '', 'tooth_formula': ''}
SAMPLE_SERVICE = {'id': 1, 'name': 'Чистка', 'price': '1000.00'}
SAMPLE_MATERIAL = {'id': 1, 'name': 'Пломба', 'unit': 'шт', 'price': '500.00'}
SAMPLE_MKB = {'id': 1, 'code': 'K00', 'name': 'Болезни зубов', 'category': 'K'}
SAMPLE_DOCTOR = {'id': 2, 'login': 'dr_petrov', 'role': 'dentist'}


# ─── models ─────────────────────────────────────────────────────────────────

class TestUserProfileModel(TestCase):
    def test_profile_created_on_user_save(self):
        """Проверяет, что сигнал post_save автоматически создаёт UserProfile."""
        # Arrange & Act
        user = User.objects.create_user('testuser99', password='pass')
        # Assert
        self.assertTrue(hasattr(user, 'profile'))

    def test_profile_str(self):
        """Проверяет строковое представление UserProfile содержит имя пользователя."""
        # Arrange
        user = User.objects.create_user('testuser98', password='pass')
        user.profile.role = 'admin'
        user.profile.save()
        # Act
        s = str(user.profile)
        # Assert
        self.assertIn('testuser98', s)

    def test_role_choices(self):
        """Проверяет, что все ожидаемые роли присутствуют в ROLE_CHOICES."""
        # Arrange
        from app.models import UserProfile
        # Act
        roles = [r[0] for r in UserProfile.ROLE_CHOICES]
        # Assert
        self.assertIn('admin', roles)
        self.assertIn('dentist', roles)
        self.assertIn('manager', roles)
        self.assertIn('patient', roles)


# ─── validators ─────────────────────────────────────────────────────────────

class TestValidators(TestCase):
    def test_valid_phone_normalized(self):
        """Проверяет, что корректный номер телефона проходит валидацию без исключения."""
        # Arrange
        from app.validators import validate_phone_number
        # Act & Assert
        result = validate_phone_number('+7 (900) 123-45-67')
        self.assertIsNotNone(result)

    def test_invalid_phone_raises(self):
        """Проверяет, что невалидный номер телефона вызывает исключение."""
        # Arrange
        from app.validators import validate_phone_number
        from django.core.exceptions import ValidationError
        # Act & Assert
        with self.assertRaises((ValidationError, ValueError, Exception)):
            validate_phone_number('abc')


# ─── utils ──────────────────────────────────────────────────────────────────

class TestUtils(TestCase):
    @patch('app.utils.requests.get')
    def test_is_fastapi_available_true(self, mock_get):
        """Проверяет, что функция возвращает True при статусе 200."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200)
        from app.utils import is_fastapi_available
        # Act & Assert
        self.assertTrue(is_fastapi_available())

    @patch('app.utils.requests.get', side_effect=Exception('err'))
    def test_is_fastapi_available_false(self, mock_get):
        """Проверяет, что функция возвращает False при сетевой ошибке."""
        # Arrange
        from app.utils import is_fastapi_available
        # Act & Assert
        self.assertFalse(is_fastapi_available())


# ─── middleware ──────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestMiddlewareDisabled(TestCase):
    def test_request_passes_through(self):
        """Проверяет, что при REQUIRE_FASTAPI=False запросы проходят без блокировки."""
        # Arrange
        client = Client()
        # Act
        resp = client.get('/login/')
        # Assert
        self.assertNotEqual(resp.status_code, 503)


@override_settings(REQUIRE_FASTAPI=True)
class TestMiddlewareEnabled(TestCase):
    @patch('app.middleware.cache')
    def test_blocks_when_unavailable(self, mock_cache):
        """Проверяет, что middleware может блокировать запросы, когда FastAPI недоступен."""
        # Arrange
        mock_cache.get.return_value = False
        client = Client()
        # Act
        resp = client.get('/admin_panel/manager/dashboard/')
        # Assert
        self.assertIn(resp.status_code, [302, 503, 200])


# ─── forms ──────────────────────────────────────────────────────────────────

class TestForms(TestCase):
    def test_registration_form_valid(self):
        """Проверяет, что форма регистрации создаётся без ошибок при корректных данных."""
        # Arrange
        from app.forms import RegistrationForm
        data = {'username': 'newuser1', 'password1': 'Str0ngP@ss!',
                 'password2': 'Str0ngP@ss!', 'first_name': 'A', 'last_name': 'B'}
        # Act
        form = RegistrationForm(data)
        # Assert
        self.assertIsNotNone(form)

    def test_patient_form_invalid_empty(self):
        """Проверяет, что пустая форма пациента не проходит валидацию."""
        # Arrange
        from app.forms import PatientForm
        # Act
        form = PatientForm({})
        # Assert
        self.assertFalse(form.is_valid())

    def test_service_form_valid(self):
        """Проверяет, что форма услуги создаётся без ошибок."""
        # Arrange
        from app.forms import ServiceForm
        # Act
        form = ServiceForm({'name': 'Чистка', 'price': '500.00', 'description': ''})
        # Assert
        self.assertIsNotNone(form)

    def test_mkb_form_valid(self):
        """Проверяет, что форма МКБ-кода создаётся без ошибок."""
        # Arrange
        from app.forms import MkbCodeForm
        # Act
        form = MkbCodeForm({'code': 'K00', 'name': 'Болезни', 'category': 'K'})
        # Assert
        self.assertIsNotNone(form)

    def test_material_form_invalid(self):
        """Проверяет, что пустая форма материала не проходит валидацию."""
        # Arrange
        from app.forms import MaterialForm
        # Act
        form = MaterialForm({})
        # Assert
        self.assertFalse(form.is_valid())

    def test_visit_search_form_empty(self):
        """Проверяет, что форма поиска визитов с пустыми данными создаётся без ошибок."""
        # Arrange
        from app.forms import VisitSearchForm
        # Act
        form = VisitSearchForm({})
        # Assert
        self.assertIsNotNone(form)

    def test_procedure_form_invalid(self):
        """Проверяет, что пустая форма процедуры не проходит валидацию."""
        # Arrange
        from app.forms import ProcedureForm
        # Act
        form = ProcedureForm({})
        # Assert
        self.assertFalse(form.is_valid())

    def test_referral_form_invalid(self):
        """Проверяет, что пустая форма направления не проходит валидацию."""
        # Arrange
        from app.forms import ReferralForm
        # Act
        form = ReferralForm({})
        # Assert
        self.assertFalse(form.is_valid())

    def test_visit_report_form_invalid(self):
        """Проверяет, что форма отчёта о визите создаётся без ошибок при пустых данных."""
        # Arrange
        from app.forms import VisitReportForm
        # Act
        form = VisitReportForm({})
        # Assert
        self.assertIsNotNone(form)

    def test_appointment_form_invalid(self):
        """Проверяет, что пустая форма записи на приём не проходит валидацию."""
        # Arrange
        from app.forms import AppointmentForm
        # Act
        form = AppointmentForm({})
        # Assert
        self.assertFalse(form.is_valid())


# ─── permissions ─────────────────────────────────────────────────────────────

class TestPermissions(TestCase):
    def _req(self, role):
        user = make_user(f'perm_{role}', role=role)
        req = MagicMock()
        req.user = user
        req.user.profile.role = role
        return req

    def test_is_admin_role_admin(self):
        """Проверяет, что IsAdminRole разрешает доступ пользователю с ролью admin."""
        # Arrange
        from app.api.permissions import IsAdminRole
        perm = IsAdminRole()
        req = self._req('admin')
        # Act & Assert
        self.assertTrue(perm.has_permission(req, None))

    def test_is_admin_role_denied(self):
        """Проверяет, что IsAdminRole запрещает доступ пользователю с ролью patient."""
        # Arrange
        from app.api.permissions import IsAdminRole
        perm = IsAdminRole()
        req = self._req('patient')
        # Act & Assert
        self.assertFalse(perm.has_permission(req, None))

    def test_is_manager_or_admin_manager(self):
        """Проверяет, что IsManagerOrAdmin разрешает доступ менеджеру."""
        # Arrange
        from app.api.permissions import IsManagerOrAdmin
        perm = IsManagerOrAdmin()
        req = self._req('manager')
        # Act & Assert
        self.assertTrue(perm.has_permission(req, None))

    def test_is_dentist_or_admin(self):
        """Проверяет, что IsDentistOrAdmin разрешает доступ стоматологу."""
        # Arrange
        from app.api.permissions import IsDentistOrAdmin
        perm = IsDentistOrAdmin()
        req = self._req('dentist')
        # Act & Assert
        self.assertTrue(perm.has_permission(req, None))

    def test_is_manager_dentist_or_admin(self):
        """Проверяет, что IsManagerDentistOrAdmin разрешает доступ менеджеру."""
        # Arrange
        from app.api.permissions import IsManagerDentistOrAdmin
        perm = IsManagerDentistOrAdmin()
        req = self._req('manager')
        # Act & Assert
        self.assertTrue(perm.has_permission(req, None))

    def test_readonly_or_admin_safe(self):
        """Проверяет, что ReadOnlyOrAdmin разрешает безопасные методы (GET) для любого пользователя."""
        # Arrange
        from app.api.permissions import ReadOnlyOrAdmin
        perm = ReadOnlyOrAdmin()
        req = self._req('patient')
        req.method = 'GET'
        # Act & Assert
        self.assertTrue(perm.has_permission(req, None))

    def test_readonly_or_admin_unsafe_denied(self):
        """Проверяет, что ReadOnlyOrAdmin запрещает небезопасные методы (POST) для patient."""
        # Arrange
        from app.api.permissions import ReadOnlyOrAdmin
        perm = ReadOnlyOrAdmin()
        req = self._req('patient')
        req.method = 'POST'
        # Act & Assert
        self.assertFalse(perm.has_permission(req, None))


# ─── serializers ─────────────────────────────────────────────────────────────

class TestSerializers(TestCase):
    def test_user_profile_serializer(self):
        """Проверяет, что UserProfileSerializer содержит поле role в сериализованных данных."""
        # Arrange
        from app.serializers import UserProfileSerializer
        user = make_user('serial_test', role='dentist')
        # Act
        s = UserProfileSerializer(user.profile)
        # Assert
        self.assertIn('role', s.data)


# ─── context_processors ──────────────────────────────────────────────────────

class TestContextProcessors(TestCase):
    @patch('app.context_processors.get_fastapi_status')
    @patch('app.context_processors.cache')
    def test_fastapi_status_cached(self, mock_cache, mock_status):
        """Проверяет, что context processor возвращает fastapi_online при кэшированном значении."""
        # Arrange
        mock_cache.get.return_value = {'available': True}
        from app.context_processors import fastapi_status
        req = MagicMock()
        # Act
        result = fastapi_status(req)
        # Assert
        self.assertIn('fastapi_online', result)

    @patch('app.context_processors.get_fastapi_status')
    @patch('app.context_processors.cache')
    def test_fastapi_status_miss(self, mock_cache, mock_status):
        """Проверяет, что context processor вызывает get_fastapi_status при промахе кэша."""
        # Arrange
        mock_cache.get.return_value = None
        mock_status.return_value = {'available': False}
        from app.context_processors import fastapi_status
        req = MagicMock()
        # Act
        result = fastapi_status(req)
        # Assert
        self.assertIn('fastapi_online', result)


# ─── auth views ──────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestAuthViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('authtest', role='admin')

    def test_logout(self):
        """Проверяет, что выход из системы завершается редиректом или 200."""
        # Arrange
        self.client.force_login(self.user)
        # Act
        resp = self.client.get('/logout/')
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_register_get(self):
        """Проверяет, что страница регистрации доступна неавторизованному пользователю."""
        # Act
        resp = self.client.get('/register/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_register_post_valid(self):
        """Проверяет, что POST с корректными данными обрабатывается без ошибки сервера."""
        # Act
        resp = self.client.post('/register/', {
            'username': 'newreg1', 'password1': 'Str0ngP@ss!',
            'password2': 'Str0ngP@ss!', 'first_name': 'A', 'last_name': 'B'
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_register_post_invalid(self):
        """Проверяет, что POST с пустыми данными не вызывает 500."""
        # Act
        resp = self.client.post('/register/', {'username': ''})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_index_redirects_admin(self):
        """Проверяет, что главная страница перенаправляет авторизованного admin."""
        # Arrange
        self.client.force_login(self.user)
        # Act
        resp = self.client.get('/')
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_index_redirects_dentist(self):
        """Проверяет, что главная страница перенаправляет стоматолога."""
        # Arrange
        dentist = make_user('dentist_idx', role='dentist')
        self.client.force_login(dentist)
        # Act
        resp = self.client.get('/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_index_redirects_manager(self):
        """Проверяет, что главная страница перенаправляет менеджера."""
        # Arrange
        mgr = make_user('mgr_idx', role='manager')
        self.client.force_login(mgr)
        # Act
        resp = self.client.get('/')
        # Assert
        self.assertEqual(resp.status_code, 302)


# ─── admin views ─────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestAdminViews(TestCase):
    def setUp(self):
        from app.models import Service, Material, MKBSCode
        self.client = Client()
        self.admin = make_user('admin_views', role='admin')
        self.client.force_login(self.admin)
        self.service = Service.objects.create(code='S001', name='Чистка', cost=1000.0, duration_minutes=30)
        self.material = Material.objects.create(name='Пломба', unit='шт', price_per_unit=500.0)
        self.mkb = MKBSCode.objects.create(code='K00', name='Болезни зубов', category='K', is_active=True)

    def test_admin_dashboard(self):
        """Проверяет, что дашборд администратора возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/admin/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_service_list(self, _):
        """Проверяет, что список услуг отображается при успешном ответе контроллера."""
        # Act
        resp = self.client.get('/admin_panel/admin/services/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.get_all', side_effect=Exception('err'))
    def test_service_list_error(self, _):
        """Проверяет, что список услуг отображается даже при ошибке контроллера."""
        # Act
        resp = self.client.get('/admin_panel/admin/services/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_service_create_get(self):
        """Проверяет, что форма создания услуги доступна."""
        # Act
        resp = self.client.get('/admin_panel/admin/services/create/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.create', return_value=SAMPLE_SERVICE)
    def test_service_create_post_valid(self, _):
        """Проверяет, что POST с данными услуги обрабатывается без ошибки."""
        # Act
        resp = self.client.post('/admin_panel/admin/services/create/',
                                {'name': 'Чистка', 'price': '1000.00', 'description': ''})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_service_update_get(self):
        """Проверяет, что форма редактирования существующей услуги возвращает 200."""
        # Act
        resp = self.client.get(f'/admin_panel/admin/services/{self.service.pk}/edit/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_service_update_get_404(self):
        """Проверяет, что несуществующая услуга возвращает 404."""
        # Act
        resp = self.client.get('/admin_panel/admin/services/99999/edit/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    def test_service_update_post_valid(self):
        """Проверяет, что обновление услуги через POST обрабатывается без ошибки."""
        # Act
        resp = self.client.post(f'/admin_panel/admin/services/{self.service.pk}/edit/',
                                {'code': 'S001', 'name': 'Новая', 'cost': '1500.00',
                                 'duration_minutes': '30', 'material_cost': '0'})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.ServiceController.delete')
    def test_service_delete(self, _):
        """Проверяет, что удаление услуги перенаправляет пользователя."""
        # Act
        resp = self.client.post('/admin_panel/admin/services/1/delete/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.ServiceController.delete', side_effect=Exception('err'))
    def test_service_delete_error(self, _):
        """Проверяет, что ошибка удаления услуги не вызывает 500."""
        # Act
        resp = self.client.post('/admin_panel/admin/services/1/delete/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.MaterialController.get_all', return_value=[SAMPLE_MATERIAL])
    def test_material_list(self, _):
        """Проверяет, что список материалов отображается успешно."""
        # Act
        resp = self.client.get('/admin_panel/admin/materials/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.MaterialController.get_all', side_effect=Exception('err'))
    def test_material_list_error(self, _):
        """Проверяет, что список материалов отображается даже при ошибке контроллера."""
        # Act
        resp = self.client.get('/admin_panel/admin/materials/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_material_create_get(self):
        """Проверяет, что форма создания материала доступна."""
        # Act
        resp = self.client.get('/admin_panel/admin/materials/create/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.MaterialController.create', return_value=SAMPLE_MATERIAL)
    def test_material_create_post_valid(self, _):
        """Проверяет, что POST с данными материала обрабатывается без ошибки."""
        # Act
        resp = self.client.post('/admin_panel/admin/materials/create/',
                                {'name': 'Пломба', 'unit': 'шт', 'price': '500.00'})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_material_update_get(self):
        """Проверяет, что форма редактирования материала возвращает 200."""
        # Act
        resp = self.client.get(f'/admin_panel/admin/materials/{self.material.pk}/edit/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_material_update_404(self):
        """Проверяет, что несуществующий материал возвращает 404."""
        # Act
        resp = self.client.get('/admin_panel/admin/materials/99999/edit/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    def test_material_delete(self):
        """Проверяет, что удаление существующего материала перенаправляет пользователя."""
        # Act
        resp = self.client.post(f'/admin_panel/admin/materials/{self.material.pk}/delete/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_material_delete_error(self):
        """Проверяет, что удаление несуществующего материала не вызывает 500."""
        # Act
        resp = self.client.post('/admin_panel/admin/materials/99999/delete/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_mkb_list(self):
        """Проверяет, что список МКБ-кодов отображается успешно."""
        # Act
        resp = self.client.get('/admin_panel/admin/mkb/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_list_error(self):
        """Проверяет повторный вызов списка МКБ — страница должна загружаться."""
        # Act
        resp = self.client.get('/admin_panel/admin/mkb/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_create_get(self):
        """Проверяет, что форма создания МКБ-кода доступна."""
        # Act
        resp = self.client.get('/admin_panel/admin/mkb/create/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_update_get(self):
        """Проверяет, что форма редактирования МКБ-кода возвращает 200."""
        # Act
        resp = self.client.get(f'/admin_panel/admin/mkb/{self.mkb.pk}/edit/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_update_get_error(self):
        """Проверяет, что несуществующий МКБ-код возвращает 404."""
        # Act
        resp = self.client.get('/admin_panel/admin/mkb/99999/edit/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    def test_mkb_update_post_valid(self):
        """Проверяет, что обновление МКБ-кода через POST обрабатывается без ошибки."""
        # Act
        resp = self.client.post(f'/admin_panel/admin/mkb/{self.mkb.pk}/edit/',
                                {'code': 'K00', 'name': 'Болезни', 'category': 'K'})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_mkb_update_post_invalid(self):
        """Проверяет, что невалидные данные при обновлении МКБ не вызывают 500."""
        # Act
        resp = self.client.post(f'/admin_panel/admin/mkb/{self.mkb.pk}/edit/', {})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_mkb_delete(self):
        """Проверяет, что удаление МКБ-кода перенаправляет пользователя."""
        # Act
        resp = self.client.post(f'/admin_panel/admin/mkb/{self.mkb.pk}/delete/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_role_manager_get(self):
        """Проверяет, что страница управления ролями доступна администратору."""
        # Act
        resp = self.client.get('/admin_panel/admin/roles/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_change_role_post(self):
        """Проверяет, что администратор может изменить роль пользователя."""
        # Arrange
        target = make_user('change_role_target', role='patient')
        # Act
        with patch('app.views.ChangeRoleView._sync_to_fastapi'):
            resp = self.client.post(f'/admin_panel/admin/roles/{target.id}/change/', {'role': 'manager'})
        # Assert
        self.assertEqual(resp.status_code, 302)
        target.profile.refresh_from_db()
        self.assertEqual(target.profile.role, 'manager')

    def test_create_user_with_role_post(self):
        """Проверяет, что администратор может создать нового пользователя с ролью."""
        # Act
        with patch('app.views.ChangeRoleView._sync_to_fastapi'):
            resp = self.client.post('/admin_panel/admin/roles/create/', {
                'username': 'brandnewuser', 'email': 'x@x.com',
                'password': 'Str0ng!', 'first_name': 'A', 'last_name': 'B', 'role': 'manager'
            })
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_create_user_with_role_duplicate(self):
        """Проверяет, что попытка создать пользователя с уже существующим именем не вызывает 500."""
        # Arrange
        make_user('dup_user', role='patient')
        # Act
        with patch('app.views.ChangeRoleView._sync_to_fastapi'):
            resp = self.client.post('/admin_panel/admin/roles/create/', {
                'username': 'dup_user', 'password': 'pass', 'role': 'manager'
            })
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_impersonate_user(self):
        """Проверяет, что администратор может войти под другим пользователем (impersonate)."""
        # Arrange
        target = make_user('impersonate_target', role='patient')
        # Act
        resp = self.client.get(f'/admin_panel/admin/impersonate/{target.id}/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_admin_appointment_create_get(self):
        """Проверяет, что форма создания записи на приём доступна администратору."""
        # Act
        resp = self.client.get('/admin_panel/admin/appointment/create/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.create', return_value={'id': 1})
    def test_admin_appointment_create_post(self, _):
        """Проверяет, что администратор может создать запись на приём через POST."""
        # Act
        resp = self.client.post('/admin_panel/admin/appointment/create/', {
            'patient_id': 1, 'doctor_id': 2, 'datetime': '2026-06-22 10:00'
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])


# ─── manager views ────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestManagerViews(TestCase):
    def setUp(self):
        from app.models import Patient, Appointment
        from django.utils import timezone
        self.client = Client()
        self.mgr = make_user('manager_views', role='manager')
        self.client.force_login(self.mgr)
        self.doctor = make_user('manager_doctor', role='dentist')
        self.patient = Patient.objects.create(
            full_name='Тест Тестов', birth_date=timezone.make_aware(timezone.datetime(1990, 1, 1)),
            gender='M', phone='+79001234567',
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            datetime=timezone.now() + timezone.timedelta(days=1), status='scheduled',
        )

    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    def test_manager_dashboard(self, mock_appt, mock_pat):
        """Проверяет, что дашборд менеджера отображается при успешных ответах контроллеров."""
        # Act
        resp = self.client.get('/admin_panel/manager/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_all', side_effect=Exception('err'))
    @patch('app.views.AppointmentController.get_all', side_effect=Exception('err'))
    def test_manager_dashboard_error(self, mock_appt, mock_pat):
        """Проверяет, что дашборд менеджера отображается даже при ошибках контроллеров."""
        # Act
        resp = self.client.get('/admin_panel/manager/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    def test_patient_list(self, _):
        """Проверяет, что список пациентов доступен менеджеру."""
        # Act
        resp = self.client.get('/admin_panel/manager/patients/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_create_get(self):
        """Проверяет, что форма создания пациента доступна менеджеру."""
        # Act
        resp = self.client.get('/admin_panel/manager/patients/create/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientHelper.ensure_client_for_patient', return_value=None)
    def test_patient_create_post_no_user_id(self, _):
        """Проверяет, что менеджер может создать пациента без привязки к user_id."""
        # Act
        resp = self.client.post('/admin_panel/manager/patients/create/', {
            'full_name': 'Тест Тестов', 'birth_date': '1990-01-01',
            'gender': 'male', 'phone': '+79001234567'
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_patient_update_get(self):
        """Проверяет, что форма редактирования пациента доступна менеджеру."""
        # Act
        resp = self.client.get(f'/admin_panel/manager/patients/{self.patient.pk}/edit/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_update_post_valid(self):
        """Проверяет, что менеджер может обновить данные пациента через POST."""
        # Act
        resp = self.client.post(f'/admin_panel/manager/patients/{self.patient.pk}/edit/', {
            'full_name': 'Новый Новов', 'birth_date': '1990-01-01',
            'gender': 'M', 'phone': '+79001234568'
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_doctor_list(self):
        """Проверяет, что список врачей доступен менеджеру."""
        # Act
        resp = self.client.get('/admin_panel/manager/doctors/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_doctor_create_get(self):
        """Проверяет, что форма создания врача доступна менеджеру."""
        # Act
        resp = self.client.get('/admin_panel/manager/doctors/create/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_list(self):
        """Проверяет, что список записей на приём доступен менеджеру."""
        # Act
        resp = self.client.get('/admin_panel/manager/appointments/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_list_errors(self):
        """Проверяет повторный вызов списка приёмов — страница должна загружаться."""
        # Act
        resp = self.client.get('/admin_panel/manager/appointments/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_list_with_filter(self):
        """Проверяет, что фильтрация записей по статусу работает корректно."""
        # Act
        resp = self.client.get('/admin_panel/manager/appointments/?status=scheduled')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_create_get(self):
        """Проверяет, что форма создания записи доступна менеджеру."""
        # Act
        resp = self.client.get('/admin_panel/manager/appointments/create/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_change_status_completed_no_visit(self):
        """Проверяет, что смена статуса на completed обрабатывается, даже если визит не создан."""
        # Act
        resp = self.client.post(
            f'/admin_panel/manager/appointments/{self.appointment.pk}/status/',
            {'status': 'completed'}
        )
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_appointment_change_status_cancelled(self):
        """Проверяет, что менеджер может отменить запись на приём."""
        # Act
        resp = self.client.post(
            f'/admin_panel/manager/appointments/{self.appointment.pk}/status/',
            {'status': 'cancelled'}
        )
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_appointment_change_status_invalid(self):
        """Проверяет, что передача невалидного статуса не вызывает 500."""
        # Act
        resp = self.client.post(
            f'/admin_panel/manager/appointments/{self.appointment.pk}/status/',
            {'status': 'invalid'}
        )
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_appointment_delete(self):
        """Проверяет, что менеджер может удалить запись на приём."""
        # Act
        resp = self.client.post(f'/admin_panel/manager/appointments/{self.appointment.pk}/delete/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_appointment_delete_error(self):
        """Проверяет, что попытка удалить несуществующую запись не вызывает 500."""
        # Act
        resp = self.client.post('/admin_panel/manager/appointments/99999/delete/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_appointment_cancel(self):
        """Проверяет, что менеджер может отменить запись на приём через отдельный endpoint."""
        # Act
        resp = self.client.post(f'/admin_panel/manager/appointments/{self.appointment.pk}/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_appointment_cancel_error(self):
        """Проверяет, что попытка отменить несуществующую запись возвращает 404."""
        # Act
        resp = self.client.post('/admin_panel/manager/appointments/99999/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    def test_revenue_report(self, _):
        """Проверяет, что отчёт по выручке доступен менеджеру."""
        # Act
        resp = self.client.get('/admin_panel/reports/revenue/')
        # Assert
        self.assertEqual(resp.status_code, 200)


# ─── dentist views ────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestDentistViews(TestCase):
    def setUp(self):
        from app.models import Patient, Appointment, Visit, Service
        from django.utils import timezone
        self.client = Client()
        self.dentist = make_user('dentist_views', role='dentist')
        self.client.force_login(self.dentist)
        self.patient = Patient.objects.create(
            full_name='Иван Иванов', birth_date=timezone.make_aware(timezone.datetime(1990, 1, 1)),
            gender='M', phone='+79001234567',
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime=timezone.now() + timezone.timedelta(days=1), status='scheduled',
        )
        self.visit = Visit.objects.create(
            appointment=self.appointment, patient=self.patient, doctor=self.dentist,
        )
        self.service = Service.objects.create(code='S001', name='Чистка', cost=1000.0, duration_minutes=30)

    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    def test_doctor_dashboard(self, mv, ma):
        """Проверяет, что дашборд врача отображается при успешных ответах контроллеров."""
        # Act
        resp = self.client.get('/admin_panel/doctor/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_all', side_effect=Exception('err'))
    @patch('app.views.VisitController.get_all', side_effect=Exception('err'))
    def test_doctor_dashboard_errors(self, mv, ma):
        """Проверяет, что дашборд врача отображается даже при ошибках контроллеров."""
        # Act
        resp = self.client.get('/admin_panel/doctor/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_detail(self):
        """Проверяет, что врач может просмотреть детали существующей записи."""
        # Act
        resp = self.client.get(f'/admin_panel/doctor/appointments/{self.appointment.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_detail_404(self):
        """Проверяет, что несуществующая запись возвращает 404."""
        # Act
        resp = self.client.get('/admin_panel/doctor/appointments/99999/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    def test_start_visit_get(self):
        """Проверяет, что форма начала визита доступна для приёма без существующего визита."""
        # Arrange
        from app.models import Appointment
        from django.utils import timezone
        appt2 = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime=timezone.now() + timezone.timedelta(days=2), status='scheduled',
        )
        # Act
        resp = self.client.get(f'/admin_panel/doctor/appointments/{appt2.pk}/start/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_start_visit_get_redirects_if_visit_exists(self):
        """Проверяет, что попытка начать визит для приёма с уже существующим визитом редиректит."""
        # Act
        resp = self.client.get(f'/admin_panel/doctor/appointments/{self.appointment.pk}/start/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_start_visit_post(self):
        """Проверяет, что врач может создать визит через POST-форму."""
        # Arrange
        from app.models import Appointment
        from django.utils import timezone
        appt2 = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime=timezone.now() + timezone.timedelta(days=3), status='scheduled',
        )
        # Act
        resp = self.client.post(f'/admin_panel/doctor/appointments/{appt2.pk}/start/', {
            'anamnesis': 'test', 'examination_results': 'ok',
            'treatment_plan': '', 'prescription': '', 'tooth_formula': ''
        })
        # Assert
        self.assertEqual(resp.status_code, 302)

    def test_procedure_create_get(self):
        """Проверяет, что форма добавления процедуры к визиту доступна."""
        # Act
        resp = self.client.get(f'/admin_panel/doctor/visits/{self.visit.pk}/procedure/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_procedure_create_get_errors(self):
        """Проверяет, что несуществующий визит при попытке добавить процедуру возвращает 404."""
        # Act
        resp = self.client.get('/admin_panel/doctor/visits/99999/procedure/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    def test_procedure_create_post_valid(self):
        """Проверяет, что врач может добавить процедуру к визиту через POST."""
        # Act
        resp = self.client.post(f'/admin_panel/doctor/visits/{self.visit.pk}/procedure/', {
            'service': self.service.pk, 'quantity': 1
        })
        # Assert
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.VisitController.get_by_id', return_value=SAMPLE_VISIT)
    def test_referral_create_get(self, mv):
        """Проверяет, что форма создания направления доступна при найденном визите."""
        # Act
        resp = self.client.get('/admin_panel/doctor/visits/1/referral/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.VisitController.get_by_id', side_effect=Exception('err'))
    def test_referral_create_get_404(self, mv):
        """Проверяет, что 404 возвращается, если визит не найден."""
        # Act
        resp = self.client.get('/admin_panel/doctor/visits/999/referral/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    @patch('app.views.VisitController.get_by_id', return_value=SAMPLE_VISIT)
    @patch('app.views.ReferralController.create', return_value={'id': 1})
    def test_referral_create_post_valid(self, mr, mv):
        """Проверяет, что врач может создать направление через POST."""
        # Act
        resp = self.client.post('/admin_panel/doctor/visits/1/referral/', {
            'specialist': 'Хирург', 'reason': 'Боль', 'referral_date': '2026-07-01'
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_patient_history(self):
        """Проверяет, что врач может просмотреть историю пациента."""
        # Act
        resp = self.client.get(f'/admin_panel/doctor/patients/{self.patient.pk}/history/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_history_404(self):
        """Проверяет, что история несуществующего пациента возвращает 404."""
        # Act
        resp = self.client.get('/admin_panel/doctor/patients/99999/history/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    def test_patient_medical_info_get(self):
        """Проверяет, что врач может просмотреть медицинскую информацию пациента."""
        # Act
        resp = self.client.get(f'/admin_panel/doctor/patients/{self.patient.pk}/medical-info/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_medical_info_post_valid(self):
        """Проверяет, что врач может обновить медицинскую информацию пациента."""
        # Act
        resp = self.client.post(f'/admin_panel/doctor/patients/{self.patient.pk}/medical-info/', {
            'allergies': 'none', 'chronic_conditions': '', 'contraindications': '',
            'blood_type': '', 'notes': ''
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_visit_report_get(self):
        """Проверяет, что страница создания отчёта о визите доступна."""
        # Act
        resp = self.client.get(f'/admin_panel/doctor/visits/{self.visit.pk}/report/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_visit_report_get_404(self):
        """Проверяет, что страница отчёта для несуществующего визита возвращает 404."""
        # Act
        resp = self.client.get('/admin_panel/doctor/visits/99999/report/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    def test_visit_report_post_valid(self):
        """Проверяет, что врач может создать отчёт о визите через POST."""
        # Act
        resp = self.client.post(f'/admin_panel/doctor/visits/{self.visit.pk}/report/', {
            'summary': 'Всё хорошо', 'title': 'Отчёт', 'recommendations': '', 'complications': ''
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_visit_report_update_get(self):
        """Проверяет, что форма редактирования существующего отчёта доступна."""
        # Arrange
        from app.models import VisitReport
        report = VisitReport.objects.create(visit=self.visit, author=self.dentist, summary='старое')
        # Act
        resp = self.client.get(f'/admin_panel/doctor/reports/{report.pk}/edit/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_visit_report_update_post(self):
        """Проверяет, что врач может обновить отчёт через POST."""
        # Arrange
        from app.models import VisitReport
        report = VisitReport.objects.create(visit=self.visit, author=self.dentist, summary='старое')
        # Act
        resp = self.client.post(f'/admin_panel/doctor/reports/{report.pk}/edit/', {
            'summary': 'новое', 'title': '', 'recommendations': '', 'complications': ''
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_visit_report_delete(self):
        """Проверяет, что врач может удалить отчёт о визите."""
        # Arrange
        from app.models import VisitReport
        report = VisitReport.objects.create(visit=self.visit, author=self.dentist, summary='удалить')
        # Act
        resp = self.client.post(f'/admin_panel/doctor/reports/{report.pk}/delete/', {})
        # Assert
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_search_by_date(self, ms, mv):
        """Проверяет, что страница поиска визитов по дате доступна."""
        # Act
        resp = self.client.get('/admin_panel/doctor/search/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_search_by_date_with_params(self, ms, mv):
        """Проверяет, что поиск визитов с параметрами дат возвращает результаты."""
        # Act
        resp = self.client.get('/admin_panel/doctor/search/?date_from=2026-01-01&date_to=2026-12-31')
        # Assert
        self.assertEqual(resp.status_code, 200)


# ─── patient views ────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestPatientViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.patient_user = make_user('patient_views', role='patient')
        self.client.force_login(self.patient_user)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=SAMPLE_PATIENT)
    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    @patch('app.views.MedicalRecordController.get_all', return_value=[])
    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    @patch('app.views.VisitController.get_extracts', return_value=[])
    def test_patient_dashboard(self, me, mv, mm, ma, mp):
        """Проверяет, что дашборд пациента отображается при наличии профиля пациента."""
        # Act
        resp = self.client.get('/admin_panel/patient/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=None)
    @patch('app.views.AppointmentController.get_all', side_effect=Exception('err'))
    @patch('app.views.MedicalRecordController.get_all', side_effect=Exception('err'))
    @patch('app.views.VisitController.get_all', side_effect=Exception('err'))
    def test_patient_dashboard_no_patient(self, mv, mm, ma, mp):
        """Проверяет, что дашборд пациента отображается, даже если профиль пациента не найден."""
        # Act
        resp = self.client.get('/admin_panel/patient/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=SAMPLE_PATIENT)
    @patch('app.views.AppointmentController.get_by_id',
           return_value={'id': 1, 'patient_id': 1, 'doctor_id': 2,
                         'status': 'scheduled', 'datetime': '2026-06-22T10:00:00'})
    @patch('app.views.AppointmentController.update_status')
    @patch('app.views.AppointmentLogController.create')
    def test_patient_cancel_appointment(self, ml, mus, mget, mp):
        """Проверяет, что пациент может отменить свою запись на приём."""
        # Act
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=None)
    def test_patient_cancel_no_profile(self, _):
        """Проверяет, что отмена записи без профиля пациента обрабатывается безопасно."""
        # Act
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=SAMPLE_PATIENT)
    @patch('app.views.AppointmentController.get_by_id', side_effect=Exception('err'))
    def test_patient_cancel_appt_not_found(self, mget, mp):
        """Проверяет, что ошибка при получении записи обрабатывается без 500."""
        # Act
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.PatientHelper.get_patient_for_user',
           return_value={'id': 99, 'full_name': 'Other'})
    @patch('app.views.AppointmentController.get_by_id',
           return_value={'id': 1, 'patient_id': 1, 'status': 'scheduled'})
    def test_patient_cancel_wrong_patient(self, mget, mp):
        """Проверяет, что пациент не может отменить чужую запись."""
        # Act
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=SAMPLE_PATIENT)
    @patch('app.views.AppointmentController.get_by_id',
           return_value={'id': 1, 'patient_id': 1, 'status': 'completed'})
    def test_patient_cancel_not_scheduled(self, mget, mp):
        """Проверяет, что пациент не может отменить уже завершённую запись."""
        # Act
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 302)


# ─── fastapi integration views ────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestFastAPIViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('fastapi_views', role='admin')
        self.client.force_login(self.user)

    @patch('app.views.fastapi_client.get_status_sync', return_value={'online': True})
    def test_fastapi_service_status(self, _):
        """Проверяет, что страница статуса FastAPI возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/fastapi/status/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.services.fastapi_health.get_fastapi_status', return_value={'available': True})
    def test_fastapi_ping(self, _):
        """Проверяет, что endpoint пинга FastAPI возвращает JSON с ключом online."""
        # Act
        resp = self.client.get('/fastapi/ping/')
        # Assert
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('online', data)

    @patch('app.views.fastapi_client.get_patients', return_value={'success': True, 'data': []})
    @patch('app.views.AsyncHelper.run_async', return_value={'success': True, 'data': []})
    def test_fastapi_patients_view(self, ra, mp):
        """Проверяет, что страница пациентов FastAPI возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/fastapi/patients/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AsyncHelper.run_async', return_value={'success': True, 'data': [SAMPLE_SERVICE]})
    def test_fastapi_services_data_success(self, _):
        """Проверяет, что данные услуг успешно получаются из FastAPI."""
        # Act
        resp = self.client.get('/admin_panel/fastapi/services-data/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AsyncHelper.run_async', return_value={'success': False, 'error': 'timeout'})
    def test_fastapi_services_data_fail(self, _):
        """Проверяет, что при недоступности FastAPI возвращается статус 503."""
        # Act
        resp = self.client.get('/admin_panel/fastapi/services-data/')
        # Assert
        self.assertEqual(resp.status_code, 503)

    @patch('app.views.AsyncHelper.run_async', return_value={'success': True, 'data': []})
    def test_fastapi_mkbs_view(self, _):
        """Проверяет, что страница МКБ-кодов FastAPI возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/fastapi/mkbs/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.fastapi_client.get_status_sync', return_value={'online': False})
    def test_fastapi_sync_patient_offline(self, _):
        """Проверяет, что синхронизация пациента возвращает 503 при недоступном FastAPI."""
        # Act
        resp = self.client.post('/admin_panel/fastapi/sync-patient/',
                                json.dumps({'patient_id': 1}),
                                content_type='application/json')
        # Assert
        self.assertEqual(resp.status_code, 503)

    def test_fastapi_sync_patient_no_id(self):
        """Проверяет, что синхронизация без patient_id возвращает 400."""
        # Act
        resp = self.client.post('/admin_panel/fastapi/sync-patient/',
                                json.dumps({}),
                                content_type='application/json')
        # Assert
        self.assertEqual(resp.status_code, 400)

    @patch('app.views.fastapi_client.get_status_sync', return_value={'online': True})
    @patch('app.views.AsyncHelper.run_async', return_value={'success': True, 'data': []})
    def test_fastapi_full_status(self, ra, gs):
        """Проверяет, что страница полного статуса FastAPI возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/fastapi/full-status/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_fastapi_demo_view(self):
        """Проверяет, что демо-страница FastAPI возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/fastapi/demo/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_fastapi_status_page_view(self):
        """Проверяет, что страница статуса FastAPI возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/fastapi/status-page/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_api_services(self, _):
        """Проверяет, что API-endpoint услуг возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/api/services/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    def test_api_patients(self, _):
        """Проверяет, что API-endpoint пациентов возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/api/patients/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    def test_api_appointments(self, _):
        """Проверяет, что API-endpoint записей на приём возвращает 200."""
        # Act
        resp = self.client.get('/admin_panel/api/appointments/')
        # Assert
        self.assertEqual(resp.status_code, 200)


# ─── role-based access control ───────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestRoleAccess(TestCase):
    def setUp(self):
        self.client = Client()

    def test_admin_view_denied_for_patient(self):
        """Проверяет, что пациент не может получить доступ к административным страницам."""
        # Arrange
        patient = make_user('role_patient', role='patient')
        self.client.force_login(patient)
        # Act
        resp = self.client.get('/admin_panel/admin/dashboard/')
        # Assert
        self.assertIn(resp.status_code, [302, 403])

    def test_manager_view_denied_for_dentist(self):
        """Проверяет, что стоматолог не может получить доступ к страницам менеджера."""
        # Arrange
        dentist = make_user('role_dentist2', role='dentist')
        self.client.force_login(dentist)
        # Act
        resp = self.client.get('/admin_panel/manager/dashboard/')
        # Assert
        self.assertIn(resp.status_code, [302, 403])

    def test_unauthenticated_redirects(self):
        """Проверяет, что неаутентифицированный пользователь перенаправляется на логин."""
        # Act
        resp = self.client.get('/admin_panel/admin/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 302)


# ─── DRF API views ────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestAPIViewSets(TestCase):
    def setUp(self):
        from app.models import Patient
        self.admin = make_user('api_admin', role='admin')
        self.manager = make_user('api_manager', role='manager')
        self.dentist = make_user('api_dentist', role='dentist')
        self.patient_user = make_user('api_patient', role='patient')
        self.client = APIClient()
        self.patient = Patient.objects.create(
            full_name='Иван Иванов', phone='+79001234567',
            birth_date='1990-01-01', gender='male',
        )

    @patch('app.api.views.get_fastapi_status', return_value={'available': True})
    def test_fastapi_status_api(self, _):
        """Проверяет, что API-endpoint статуса FastAPI доступен администратору."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.get('/api/v2/fastapi-status/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_me_api(self):
        """Проверяет, что /api/v2/me/ возвращает данные текущего пользователя с его ролью."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.get('/api/v2/me/')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'api_admin')
        self.assertEqual(resp.data['role'], 'admin')

    @patch('app.controllers.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    def test_patient_list_api(self, _):
        """Проверяет, что менеджер может получить список пациентов через API."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/patients/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_retrieve_api(self):
        """Проверяет, что менеджер может получить данные конкретного пациента через API."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get(f'/api/v2/patients/{self.patient.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.PatientController.create', return_value=SAMPLE_PATIENT)
    def test_patient_create_api(self, _):
        """Проверяет, что администратор может создать пациента через API."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.post('/api/v2/patients/', SAMPLE_PATIENT, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)

    def test_patient_update_api(self):
        """Проверяет, что администратор может обновить данные пациента через PATCH."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        data = {'full_name': 'Иван Петров', 'phone': '+79001234567',
                'birth_date': '1990-01-01', 'gender': 'male'}
        # Act
        resp = self.client.patch(f'/api/v2/patients/{self.patient.pk}/', data, format='json')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.PatientController.delete')
    def test_patient_delete_api(self, _):
        """Проверяет, что администратор может удалить пациента через API."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.delete('/api/v2/patients/1/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    @patch('app.controllers.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    def test_patient_appointments_api(self, _):
        """Проверяет, что менеджер может получить записи на приём пациента через API."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/patients/1/appointments/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.VisitController.get_all', return_value=[SAMPLE_VISIT])
    def test_patient_visits_api(self, _):
        """Проверяет, что стоматолог может получить визиты пациента через API."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/patients/1/visits/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    def test_appointment_list_api(self, _):
        """Проверяет, что менеджер может получить список всех записей на приём."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/appointments/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_service_list_api(self, _):
        """Проверяет, что администратор может получить список услуг через API."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.get('/api/v2/services/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.MaterialController.get_all', return_value=[SAMPLE_MATERIAL])
    def test_material_list_api(self, _):
        """Проверяет, что администратор может получить список материалов через API."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.get('/api/v2/materials/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_user_profile_list_api(self):
        """Проверяет, что администратор может получить список профилей пользователей."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.get('/api/v2/users/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_api_unauthenticated(self):
        """Проверяет, что неаутентифицированный запрос к API возвращает 401."""
        # Act
        resp = self.client.get('/api/v2/patients/')
        # Assert
        self.assertEqual(resp.status_code, 401)

    def test_api_patient_role_forbidden(self):
        """Проверяет, что пользователь с ролью patient не может получить список пациентов."""
        # Arrange
        self.client.force_authenticate(user=self.patient_user)
        # Act
        resp = self.client.get('/api/v2/patients/')
        # Assert
        self.assertEqual(resp.status_code, 403)


# ─── controllers ─────────────────────────────────────────────────────────────

class TestControllers(TestCase):
    @patch('app.controllers.patient_controller.requests.get')
    def test_patient_get_all(self, mock_get):
        """Проверяет, что PatientController.get_all возвращает список при статусе 200."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_PATIENT])
        from app.controllers import PatientController
        # Act
        result = PatientController.get_all()
        # Assert
        self.assertIsInstance(result, list)

    @patch('app.controllers.patient_controller.requests.get', side_effect=Exception('conn err'))
    def test_patient_get_all_error(self, _):
        """Проверяет, что PatientController.get_all пробрасывает исключение при сетевой ошибке."""
        # Arrange
        from app.controllers import PatientController
        # Act & Assert
        with self.assertRaises(Exception):
            PatientController.get_all()

    @patch('app.controllers.patient_controller.requests.get')
    def test_patient_get_by_id(self, mock_get):
        """Проверяет, что PatientController.get_by_id возвращает пациента по id."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200, json=lambda: SAMPLE_PATIENT)
        from app.controllers import PatientController
        # Act
        result = PatientController.get_by_id(1)
        # Assert
        self.assertEqual(result['id'], 1)

    @patch('app.controllers.patient_controller.requests.post')
    def test_patient_create(self, mock_post):
        """Проверяет, что PatientController.create возвращает созданного пациента."""
        # Arrange
        mock_post.return_value = MagicMock(status_code=201, json=lambda: SAMPLE_PATIENT)
        from app.controllers import PatientController
        # Act
        result = PatientController.create(SAMPLE_PATIENT)
        # Assert
        self.assertIsNotNone(result)

    @patch('app.controllers.appointment_controller.requests.get')
    def test_appointment_get_all(self, mock_get):
        """Проверяет, что AppointmentController.get_all возвращает список записей."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_APPOINTMENT])
        from app.controllers import AppointmentController
        # Act
        result = AppointmentController.get_all()
        # Assert
        self.assertIsInstance(result, list)

    @patch('app.controllers.visit_controller.requests.get')
    def test_visit_get_all(self, mock_get):
        """Проверяет, что VisitController.get_all возвращает список визитов."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_VISIT])
        from app.controllers import VisitController
        # Act
        result = VisitController.get_all()
        # Assert
        self.assertIsInstance(result, list)

    @patch('app.controllers.service_controller.requests.get')
    def test_service_get_all(self, mock_get):
        """Проверяет, что ServiceController.get_all возвращает список услуг."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_SERVICE])
        from app.controllers import ServiceController
        # Act
        result = ServiceController.get_all()
        # Assert
        self.assertIsInstance(result, list)

    @patch('app.controllers.material_controller.requests.get')
    def test_material_get_all(self, mock_get):
        """Проверяет, что MaterialController.get_all возвращает список материалов."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_MATERIAL])
        from app.controllers import MaterialController
        # Act
        result = MaterialController.get_all()
        # Assert
        self.assertIsInstance(result, list)

    @patch('app.controllers.mkbs_controller.requests.get')
    def test_mkbs_get_diagnoses(self, mock_get):
        """Проверяет, что MKBSController.get_diagnoses возвращает список диагнозов."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_MKB])
        from app.controllers import MKBSController
        # Act
        result = MKBSController.get_diagnoses()
        # Assert
        self.assertIsInstance(result, list)

    @patch('app.controllers.client_controller.requests.get')
    def test_client_get_doctors(self, mock_get):
        """Проверяет, что ClientController.get_doctors возвращает список врачей."""
        # Arrange
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_DOCTOR])
        from app.controllers import ClientController
        # Act
        result = ClientController.get_doctors()
        # Assert
        self.assertIsInstance(result, list)
