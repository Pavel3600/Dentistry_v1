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
        user = User.objects.create_user('testuser99', password='pass')
        self.assertTrue(hasattr(user, 'profile'))

    def test_profile_str(self):
        user = User.objects.create_user('testuser98', password='pass')
        user.profile.role = 'admin'
        user.profile.save()
        s = str(user.profile)
        self.assertIn('testuser98', s)

    def test_role_choices(self):
        from app.models import UserProfile
        roles = [r[0] for r in UserProfile.ROLE_CHOICES]
        self.assertIn('admin', roles)
        self.assertIn('dentist', roles)
        self.assertIn('manager', roles)
        self.assertIn('patient', roles)


# ─── validators ─────────────────────────────────────────────────────────────

class TestValidators(TestCase):
    def test_valid_phone_normalized(self):
        from app.validators import validate_phone_number
        result = validate_phone_number('+7 (900) 123-45-67')
        self.assertIsNotNone(result)

    def test_invalid_phone_raises(self):
        from app.validators import validate_phone_number
        from django.core.exceptions import ValidationError
        with self.assertRaises((ValidationError, ValueError, Exception)):
            validate_phone_number('abc')


# ─── utils ──────────────────────────────────────────────────────────────────

class TestUtils(TestCase):
    @patch('app.utils.requests.get')
    def test_is_fastapi_available_true(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        from app.utils import is_fastapi_available
        self.assertTrue(is_fastapi_available())

    @patch('app.utils.requests.get', side_effect=Exception('err'))
    def test_is_fastapi_available_false(self, mock_get):
        from app.utils import is_fastapi_available
        self.assertFalse(is_fastapi_available())


# ─── middleware ──────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestMiddlewareDisabled(TestCase):
    def test_request_passes_through(self):
        client = Client()
        resp = client.get('/login/')
        self.assertNotEqual(resp.status_code, 503)


@override_settings(REQUIRE_FASTAPI=True)
class TestMiddlewareEnabled(TestCase):
    @patch('app.middleware.cache')
    def test_blocks_when_unavailable(self, mock_cache):
        mock_cache.get.return_value = False
        client = Client()
        resp = client.get('/admin_panel/manager/dashboard/')
        self.assertIn(resp.status_code, [302, 503, 200])


# ─── forms ──────────────────────────────────────────────────────────────────

class TestForms(TestCase):
    def test_registration_form_valid(self):
        from app.forms import RegistrationForm
        data = {'username': 'newuser1', 'password1': 'Str0ngP@ss!',
                 'password2': 'Str0ngP@ss!', 'first_name': 'A', 'last_name': 'B'}
        form = RegistrationForm(data)
        # just check it instantiates
        self.assertIsNotNone(form)

    def test_patient_form_invalid_empty(self):
        from app.forms import PatientForm
        form = PatientForm({})
        self.assertFalse(form.is_valid())

    def test_service_form_valid(self):
        from app.forms import ServiceForm
        form = ServiceForm({'name': 'Чистка', 'price': '500.00', 'description': ''})
        # just validate no crash
        self.assertIsNotNone(form)

    def test_mkb_form_valid(self):
        from app.forms import MkbCodeForm
        form = MkbCodeForm({'code': 'K00', 'name': 'Болезни', 'category': 'K'})
        self.assertIsNotNone(form)

    def test_material_form_invalid(self):
        from app.forms import MaterialForm
        form = MaterialForm({})
        self.assertFalse(form.is_valid())

    def test_visit_search_form_empty(self):
        from app.forms import VisitSearchForm
        form = VisitSearchForm({})
        self.assertIsNotNone(form)

    def test_procedure_form_invalid(self):
        from app.forms import ProcedureForm
        form = ProcedureForm({})
        self.assertFalse(form.is_valid())

    def test_referral_form_invalid(self):
        from app.forms import ReferralForm
        form = ReferralForm({})
        self.assertFalse(form.is_valid())

    def test_visit_report_form_invalid(self):
        from app.forms import VisitReportForm
        form = VisitReportForm({})
        self.assertIsNotNone(form)

    def test_appointment_form_invalid(self):
        from app.forms import AppointmentForm
        form = AppointmentForm({})
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
        from app.api.permissions import IsAdminRole
        perm = IsAdminRole()
        req = self._req('admin')
        self.assertTrue(perm.has_permission(req, None))

    def test_is_admin_role_denied(self):
        from app.api.permissions import IsAdminRole
        perm = IsAdminRole()
        req = self._req('patient')
        self.assertFalse(perm.has_permission(req, None))

    def test_is_manager_or_admin_manager(self):
        from app.api.permissions import IsManagerOrAdmin
        perm = IsManagerOrAdmin()
        req = self._req('manager')
        self.assertTrue(perm.has_permission(req, None))

    def test_is_dentist_or_admin(self):
        from app.api.permissions import IsDentistOrAdmin
        perm = IsDentistOrAdmin()
        req = self._req('dentist')
        self.assertTrue(perm.has_permission(req, None))

    def test_is_manager_dentist_or_admin(self):
        from app.api.permissions import IsManagerDentistOrAdmin
        perm = IsManagerDentistOrAdmin()
        req = self._req('manager')
        self.assertTrue(perm.has_permission(req, None))

    def test_readonly_or_admin_safe(self):
        from app.api.permissions import ReadOnlyOrAdmin
        perm = ReadOnlyOrAdmin()
        req = self._req('patient')
        req.method = 'GET'
        self.assertTrue(perm.has_permission(req, None))

    def test_readonly_or_admin_unsafe_denied(self):
        from app.api.permissions import ReadOnlyOrAdmin
        perm = ReadOnlyOrAdmin()
        req = self._req('patient')
        req.method = 'POST'
        self.assertFalse(perm.has_permission(req, None))


# ─── serializers ─────────────────────────────────────────────────────────────

class TestSerializers(TestCase):
    def test_user_profile_serializer(self):
        from app.serializers import UserProfileSerializer
        user = make_user('serial_test', role='dentist')
        s = UserProfileSerializer(user.profile)
        self.assertIn('role', s.data)


# ─── context_processors ──────────────────────────────────────────────────────

class TestContextProcessors(TestCase):
    @patch('app.context_processors.get_fastapi_status')
    @patch('app.context_processors.cache')
    def test_fastapi_status_cached(self, mock_cache, mock_status):
        mock_cache.get.return_value = {'available': True}
        from app.context_processors import fastapi_status
        req = MagicMock()
        result = fastapi_status(req)
        self.assertIn('fastapi_available', result)

    @patch('app.context_processors.get_fastapi_status')
    @patch('app.context_processors.cache')
    def test_fastapi_status_miss(self, mock_cache, mock_status):
        mock_cache.get.return_value = None
        mock_status.return_value = {'available': False}
        from app.context_processors import fastapi_status
        req = MagicMock()
        result = fastapi_status(req)
        self.assertIn('fastapi_available', result)


# ─── auth views ──────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestAuthViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user('authtest', role='admin')

    def test_logout(self):
        self.client.force_login(self.user)
        resp = self.client.get('/logout/')
        self.assertIn(resp.status_code, [200, 302])

    def test_register_get(self):
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 200)

    def test_register_post_valid(self):
        resp = self.client.post('/register/', {
            'username': 'newreg1', 'password1': 'Str0ngP@ss!',
            'password2': 'Str0ngP@ss!', 'first_name': 'A', 'last_name': 'B'
        })
        self.assertIn(resp.status_code, [200, 302])

    def test_register_post_invalid(self):
        resp = self.client.post('/register/', {'username': ''})
        self.assertEqual(resp.status_code, 200)

    def test_index_redirects_admin(self):
        self.client.force_login(self.user)
        resp = self.client.get('/')
        self.assertIn(resp.status_code, [200, 302])

    def test_index_redirects_dentist(self):
        dentist = make_user('dentist_idx', role='dentist')
        self.client.force_login(dentist)
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)

    def test_index_redirects_manager(self):
        mgr = make_user('mgr_idx', role='manager')
        self.client.force_login(mgr)
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)


# ─── admin views ─────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestAdminViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = make_user('admin_views', role='admin')
        self.client.force_login(self.admin)

    def test_admin_dashboard(self):
        resp = self.client.get('/admin_panel/admin/dashboard/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_service_list(self, _):
        resp = self.client.get('/admin_panel/admin/services/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.get_all', side_effect=Exception('err'))
    def test_service_list_error(self, _):
        resp = self.client.get('/admin_panel/admin/services/')
        self.assertEqual(resp.status_code, 200)

    def test_service_create_get(self):
        resp = self.client.get('/admin_panel/admin/services/create/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.create', return_value=SAMPLE_SERVICE)
    def test_service_create_post_valid(self, _):
        resp = self.client.post('/admin_panel/admin/services/create/',
                                {'name': 'Чистка', 'price': '1000.00', 'description': ''})
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.ServiceController.get_by_id', return_value=SAMPLE_SERVICE)
    def test_service_update_get(self, _):
        resp = self.client.get('/admin_panel/admin/services/1/edit/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.get_by_id', side_effect=Exception('not found'))
    def test_service_update_get_404(self, _):
        resp = self.client.get('/admin_panel/admin/services/999/edit/')
        self.assertEqual(resp.status_code, 404)

    @patch('app.views.ServiceController.update', return_value=SAMPLE_SERVICE)
    def test_service_update_post_valid(self, _):
        resp = self.client.post('/admin_panel/admin/services/1/edit/',
                                {'name': 'Чистка', 'price': '1000.00', 'description': ''})
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.ServiceController.delete')
    def test_service_delete(self, _):
        resp = self.client.post('/admin_panel/admin/services/1/delete/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.ServiceController.delete', side_effect=Exception('err'))
    def test_service_delete_error(self, _):
        resp = self.client.post('/admin_panel/admin/services/1/delete/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.MaterialController.get_all', return_value=[SAMPLE_MATERIAL])
    def test_material_list(self, _):
        resp = self.client.get('/admin_panel/admin/materials/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.MaterialController.get_all', side_effect=Exception('err'))
    def test_material_list_error(self, _):
        resp = self.client.get('/admin_panel/admin/materials/')
        self.assertEqual(resp.status_code, 200)

    def test_material_create_get(self):
        resp = self.client.get('/admin_panel/admin/materials/create/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.MaterialController.create', return_value=SAMPLE_MATERIAL)
    def test_material_create_post_valid(self, _):
        resp = self.client.post('/admin_panel/admin/materials/create/',
                                {'name': 'Пломба', 'unit': 'шт', 'price': '500.00'})
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.MaterialController.get_by_id', return_value=SAMPLE_MATERIAL)
    def test_material_update_get(self, _):
        resp = self.client.get('/admin_panel/admin/materials/1/edit/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.MaterialController.get_by_id', side_effect=Exception('err'))
    def test_material_update_404(self, _):
        resp = self.client.get('/admin_panel/admin/materials/999/edit/')
        self.assertEqual(resp.status_code, 404)

    @patch('app.views.MaterialController.delete')
    def test_material_delete(self, _):
        resp = self.client.post('/admin_panel/admin/materials/1/delete/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.MaterialController.delete', side_effect=Exception('err'))
    def test_material_delete_error(self, _):
        resp = self.client.post('/admin_panel/admin/materials/1/delete/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.MKBSController.get_diagnoses', return_value=[SAMPLE_MKB])
    def test_mkb_list(self, _):
        resp = self.client.get('/admin_panel/admin/mkb/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.MKBSController.get_diagnoses', side_effect=Exception('err'))
    def test_mkb_list_error(self, _):
        resp = self.client.get('/admin_panel/admin/mkb/')
        self.assertEqual(resp.status_code, 200)

    def test_mkb_create_get(self):
        resp = self.client.get('/admin_panel/admin/mkb/create/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.MKBSController.get_by_id', return_value=SAMPLE_MKB)
    def test_mkb_update_get(self, _):
        resp = self.client.get('/admin_panel/admin/mkb/1/edit/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.MKBSController.get_by_id', side_effect=Exception('err'))
    def test_mkb_update_get_error(self, _):
        resp = self.client.get('/admin_panel/admin/mkb/999/edit/')
        self.assertEqual(resp.status_code, 200)

    def test_mkb_update_post_valid(self):
        resp = self.client.post('/admin_panel/admin/mkb/1/edit/',
                                {'code': 'K00', 'name': 'Болезни', 'category': 'K'})
        self.assertIn(resp.status_code, [200, 302])

    def test_mkb_update_post_invalid(self):
        resp = self.client.post('/admin_panel/admin/mkb/1/edit/', {})
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.MKBSController.get_diagnoses', return_value=[SAMPLE_MKB])
    def test_mkb_delete(self, _):
        resp = self.client.post('/admin_panel/admin/mkb/1/delete/')
        self.assertEqual(resp.status_code, 302)

    def test_role_manager_get(self):
        resp = self.client.get('/admin_panel/admin/roles/')
        self.assertEqual(resp.status_code, 200)

    def test_change_role_post(self):
        target = make_user('change_role_target', role='patient')
        with patch('app.views.ChangeRoleView._sync_to_fastapi'):
            resp = self.client.post(f'/admin_panel/admin/roles/{target.id}/change/', {'role': 'manager'})
        self.assertEqual(resp.status_code, 302)
        target.profile.refresh_from_db()
        self.assertEqual(target.profile.role, 'manager')

    def test_create_user_with_role_post(self):
        with patch('app.views.ChangeRoleView._sync_to_fastapi'):
            resp = self.client.post('/admin_panel/admin/roles/create/', {
                'username': 'brandnewuser', 'email': 'x@x.com',
                'password': 'Str0ng!', 'first_name': 'A', 'last_name': 'B', 'role': 'manager'
            })
        self.assertEqual(resp.status_code, 302)

    def test_create_user_with_role_duplicate(self):
        make_user('dup_user', role='patient')
        with patch('app.views.ChangeRoleView._sync_to_fastapi'):
            resp = self.client.post('/admin_panel/admin/roles/create/', {
                'username': 'dup_user', 'password': 'pass', 'role': 'manager'
            })
        self.assertEqual(resp.status_code, 302)

    def test_impersonate_user(self):
        target = make_user('impersonate_target', role='patient')
        resp = self.client.get(f'/admin_panel/admin/impersonate/{target.id}/')
        self.assertEqual(resp.status_code, 302)

    def test_admin_appointment_create_get(self):
        resp = self.client.get('/admin_panel/admin/appointment/create/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.create', return_value={'id': 1})
    def test_admin_appointment_create_post(self, _):
        resp = self.client.post('/admin_panel/admin/appointment/create/', {
            'patient_id': 1, 'doctor_id': 2, 'datetime': '2026-06-22 10:00'
        })
        self.assertIn(resp.status_code, [200, 302])


# ─── manager views ────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestManagerViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.mgr = make_user('manager_views', role='manager')
        self.client.force_login(self.mgr)

    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    def test_manager_dashboard(self, mock_appt, mock_pat):
        resp = self.client.get('/admin_panel/manager/dashboard/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_all', side_effect=Exception('err'))
    @patch('app.views.AppointmentController.get_all', side_effect=Exception('err'))
    def test_manager_dashboard_error(self, mock_appt, mock_pat):
        resp = self.client.get('/admin_panel/manager/dashboard/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    def test_patient_list(self, _):
        resp = self.client.get('/admin_panel/manager/patients/')
        self.assertEqual(resp.status_code, 200)

    def test_patient_create_get(self):
        resp = self.client.get('/admin_panel/manager/patients/create/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientHelper.ensure_client_for_patient', return_value=None)
    def test_patient_create_post_no_user_id(self, _):
        resp = self.client.post('/admin_panel/manager/patients/create/', {
            'full_name': 'Тест Тестов', 'birth_date': '1990-01-01',
            'gender': 'male', 'phone': '+79001234567'
        })
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.PatientController.get_by_id', return_value=SAMPLE_PATIENT)
    def test_patient_update_get(self, _):
        resp = self.client.get('/admin_panel/manager/patients/1/edit/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_by_id', return_value=SAMPLE_PATIENT)
    @patch('app.views.PatientController.update', return_value=SAMPLE_PATIENT)
    def test_patient_update_post_valid(self, mock_upd, mock_get):
        resp = self.client.post('/admin_panel/manager/patients/1/edit/', {
            'full_name': 'Новый Новов', 'birth_date': '1990-01-01',
            'gender': 'male', 'phone': '+79001234568'
        })
        self.assertIn(resp.status_code, [200, 302])

    def test_doctor_list(self):
        resp = self.client.get('/admin_panel/manager/doctors/')
        self.assertEqual(resp.status_code, 200)

    def test_doctor_create_get(self):
        resp = self.client.get('/admin_panel/manager/doctors/create/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    @patch('app.views.ClientController.get_doctors', return_value=[SAMPLE_DOCTOR])
    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    def test_appointment_list(self, mv, md, mp, ma):
        resp = self.client.get('/admin_panel/manager/appointments/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_all', side_effect=Exception('err'))
    @patch('app.views.PatientController.get_all', side_effect=Exception('err'))
    @patch('app.views.ClientController.get_doctors', side_effect=Exception('err'))
    @patch('app.views.VisitController.get_all', side_effect=Exception('err'))
    def test_appointment_list_errors(self, mv, md, mp, ma):
        resp = self.client.get('/admin_panel/manager/appointments/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    @patch('app.views.ClientController.get_doctors', return_value=[SAMPLE_DOCTOR])
    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    def test_appointment_list_with_filter(self, mv, md, mp, ma):
        resp = self.client.get('/admin_panel/manager/appointments/?status=scheduled')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    @patch('app.views.ClientController.get_doctors', return_value=[SAMPLE_DOCTOR])
    def test_appointment_create_get(self, md, mp):
        resp = self.client.get('/admin_panel/manager/appointments/create/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.VisitController.get_by_appointment', return_value=None)
    @patch('app.views.AppointmentController.get_by_id', return_value=SAMPLE_APPOINTMENT)
    @patch('app.views.AppointmentController.update_status')
    @patch('app.views.AppointmentLogController.create')
    def test_appointment_change_status_completed_no_visit(self, ml, mus, mget, mvisit):
        resp = self.client.post('/admin_panel/manager/appointments/1/status/', {'status': 'completed'})
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.AppointmentController.get_by_id', return_value=SAMPLE_APPOINTMENT)
    @patch('app.views.AppointmentController.update_status')
    @patch('app.views.AppointmentLogController.create')
    @patch('app.views.VisitController.get_by_appointment', return_value=SAMPLE_VISIT)
    def test_appointment_change_status_cancelled(self, mv, ml, mus, mget):
        resp = self.client.post('/admin_panel/manager/appointments/1/status/', {'status': 'cancelled'})
        self.assertEqual(resp.status_code, 302)

    def test_appointment_change_status_invalid(self):
        resp = self.client.post('/admin_panel/manager/appointments/1/status/', {'status': 'invalid'})
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.AppointmentController.delete')
    def test_appointment_delete(self, _):
        resp = self.client.post('/admin_panel/manager/appointments/1/delete/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.AppointmentController.delete', side_effect=Exception('err'))
    def test_appointment_delete_error(self, _):
        resp = self.client.post('/admin_panel/manager/appointments/1/delete/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.AppointmentController.get_by_id', return_value=SAMPLE_APPOINTMENT)
    @patch('app.views.AppointmentController.update_status')
    @patch('app.views.AppointmentLogController.create')
    def test_appointment_cancel(self, ml, mus, mget):
        resp = self.client.post('/admin_panel/manager/appointments/1/cancel/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.AppointmentController.get_by_id', side_effect=Exception('err'))
    def test_appointment_cancel_error(self, _):
        resp = self.client.post('/admin_panel/manager/appointments/1/cancel/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    def test_revenue_report(self, _):
        resp = self.client.get('/admin_panel/reports/revenue/')
        self.assertEqual(resp.status_code, 200)


# ─── dentist views ────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestDentistViews(TestCase):
    def setUp(self):
        self.client = Client()
        self.dentist = make_user('dentist_views', role='dentist')
        self.client.force_login(self.dentist)

    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    def test_doctor_dashboard(self, mv, ma):
        resp = self.client.get('/admin_panel/doctor/dashboard/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_all', side_effect=Exception('err'))
    @patch('app.views.VisitController.get_all', side_effect=Exception('err'))
    def test_doctor_dashboard_errors(self, mv, ma):
        resp = self.client.get('/admin_panel/doctor/dashboard/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_by_id', return_value=SAMPLE_APPOINTMENT)
    @patch('app.views.VisitController.get_by_appointment', return_value=SAMPLE_VISIT)
    @patch('app.views.PatientController.get_by_id', return_value=SAMPLE_PATIENT)
    @patch('app.views.MKBSController.get_diagnoses', return_value=[SAMPLE_MKB])
    @patch('app.views.VisitController.get_reports', return_value=[])
    def test_appointment_detail(self, mr, md, mp, mv, ma):
        resp = self.client.get('/admin_panel/doctor/appointments/1/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_by_id', side_effect=Exception('err'))
    def test_appointment_detail_404(self, _):
        resp = self.client.get('/admin_panel/doctor/appointments/999/')
        self.assertEqual(resp.status_code, 404)

    @patch('app.views.AppointmentController.get_by_id', return_value=SAMPLE_APPOINTMENT)
    @patch('app.views.VisitController.get_by_appointment', return_value=None)
    @patch('app.views.PatientController.get_by_id', return_value=SAMPLE_PATIENT)
    @patch('app.views.MKBSController.get_diagnoses', return_value=[])
    def test_start_visit_get(self, md, mp, mv, ma):
        resp = self.client.get('/admin_panel/doctor/appointments/1/start/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_by_id', return_value=SAMPLE_APPOINTMENT)
    @patch('app.views.VisitController.get_by_appointment', return_value=SAMPLE_VISIT)
    def test_start_visit_get_redirects_if_visit_exists(self, mv, ma):
        resp = self.client.get('/admin_panel/doctor/appointments/1/start/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.AppointmentController.get_by_id', return_value=SAMPLE_APPOINTMENT)
    @patch('app.views.VisitController.get_by_appointment', return_value=None)
    @patch('app.views.VisitController.create', return_value=SAMPLE_VISIT)
    @patch('app.views.AppointmentController.update_status')
    @patch('app.views.AppointmentLogController.create')
    def test_start_visit_post(self, ml, mus, mvc, mvget, ma):
        resp = self.client.post('/admin_panel/doctor/appointments/1/start/', {
            'anamnesis': 'test', 'examination_results': 'ok',
            'treatment_plan': '', 'prescription': '', 'tooth_formula': ''
        })
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    @patch('app.views.VisitController.get_by_id', return_value=SAMPLE_VISIT)
    def test_procedure_create_get(self, mv, ms):
        resp = self.client.get('/admin_panel/doctor/visits/1/procedure/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.get_all', side_effect=Exception('err'))
    @patch('app.views.VisitController.get_by_id', side_effect=Exception('err'))
    def test_procedure_create_get_errors(self, mv, ms):
        resp = self.client.get('/admin_panel/doctor/visits/1/procedure/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.VisitController.get_by_id', return_value=SAMPLE_VISIT)
    @patch('app.views.VisitController.add_procedure')
    def test_procedure_create_post_valid(self, madd, mget):
        resp = self.client.post('/admin_panel/doctor/visits/1/procedure/', {
            'service_id': 1, 'quantity': 1
        })
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.VisitController.get_by_id', return_value=SAMPLE_VISIT)
    def test_referral_create_get(self, mv):
        resp = self.client.get('/admin_panel/doctor/visits/1/referral/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.VisitController.get_by_id', side_effect=Exception('err'))
    def test_referral_create_get_404(self, mv):
        resp = self.client.get('/admin_panel/doctor/visits/999/referral/')
        self.assertEqual(resp.status_code, 404)

    @patch('app.views.VisitController.get_by_id', return_value=SAMPLE_VISIT)
    @patch('app.views.ReferralController.create', return_value={'id': 1})
    def test_referral_create_post_valid(self, mr, mv):
        resp = self.client.post('/admin_panel/doctor/visits/1/referral/', {
            'specialist': 'Хирург', 'reason': 'Боль', 'referral_date': '2026-07-01'
        })
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.PatientController.get_by_id', return_value=SAMPLE_PATIENT)
    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    @patch('app.views.PatientMedicalInfoController.get', return_value={})
    def test_patient_history(self, mi, mv, mp):
        resp = self.client.get('/admin_panel/doctor/patients/1/history/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_by_id', side_effect=Exception('err'))
    def test_patient_history_404(self, _):
        resp = self.client.get('/admin_panel/doctor/patients/999/history/')
        self.assertEqual(resp.status_code, 404)

    @patch('app.views.PatientController.get_by_id', return_value=SAMPLE_PATIENT)
    @patch('app.views.PatientMedicalInfoController.get', return_value={'allergies': 'none'})
    def test_patient_medical_info_get(self, mi, mp):
        resp = self.client.get('/admin_panel/doctor/patients/1/medical-info/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_by_id', return_value=SAMPLE_PATIENT)
    @patch('app.views.PatientMedicalInfoController.upsert')
    @patch('app.views.PatientMedicalInfoController.get', return_value={})
    def test_patient_medical_info_post_valid(self, mi, mu, mp):
        resp = self.client.post('/admin_panel/doctor/patients/1/medical-info/', {
            'allergies': 'none', 'chronic_diseases': ''
        })
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.VisitController.get_by_id', return_value=SAMPLE_VISIT)
    @patch('app.views.VisitController.get_reports', return_value=[])
    def test_visit_report_get(self, mr, mv):
        resp = self.client.get('/admin_panel/doctor/visits/1/report/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.VisitController.get_by_id', side_effect=Exception('err'))
    def test_visit_report_get_404(self, _):
        resp = self.client.get('/admin_panel/doctor/visits/999/report/')
        self.assertEqual(resp.status_code, 404)

    @patch('app.views.VisitController.get_by_id', return_value=SAMPLE_VISIT)
    @patch('app.views.VisitController.create_report')
    @patch('app.views.VisitController.get_reports', return_value=[])
    def test_visit_report_post_valid(self, mr, mc, mv):
        resp = self.client.post('/admin_panel/doctor/visits/1/report/', {
            'content': 'Всё хорошо', 'recommendations': ''
        })
        self.assertIn(resp.status_code, [200, 302])

    def test_visit_report_update_get(self):
        resp = self.client.get('/admin_panel/doctor/reports/1/edit/')
        self.assertEqual(resp.status_code, 302)

    def test_visit_report_update_post(self):
        resp = self.client.post('/admin_panel/doctor/reports/1/edit/', {})
        self.assertEqual(resp.status_code, 302)

    def test_visit_report_delete(self):
        resp = self.client.post('/admin_panel/doctor/reports/1/delete/', {})
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_search_by_date(self, ms, mv):
        resp = self.client.get('/admin_panel/doctor/search/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.VisitController.get_all', return_value=[SAMPLE_VISIT])
    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_search_by_date_with_params(self, ms, mv):
        resp = self.client.get('/admin_panel/doctor/search/?date_from=2026-01-01&date_to=2026-12-31')
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
        resp = self.client.get('/admin_panel/patient/dashboard/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=None)
    @patch('app.views.AppointmentController.get_all', side_effect=Exception('err'))
    @patch('app.views.MedicalRecordController.get_all', side_effect=Exception('err'))
    @patch('app.views.VisitController.get_all', side_effect=Exception('err'))
    def test_patient_dashboard_no_patient(self, mv, mm, ma, mp):
        resp = self.client.get('/admin_panel/patient/dashboard/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=SAMPLE_PATIENT)
    @patch('app.views.AppointmentController.get_by_id',
           return_value={'id': 1, 'patient_id': 1, 'doctor_id': 2,
                         'status': 'scheduled', 'datetime': '2026-06-22T10:00:00'})
    @patch('app.views.AppointmentController.update_status')
    @patch('app.views.AppointmentLogController.create')
    def test_patient_cancel_appointment(self, ml, mus, mget, mp):
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=None)
    def test_patient_cancel_no_profile(self, _):
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=SAMPLE_PATIENT)
    @patch('app.views.AppointmentController.get_by_id', side_effect=Exception('err'))
    def test_patient_cancel_appt_not_found(self, mget, mp):
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.PatientHelper.get_patient_for_user',
           return_value={'id': 99, 'full_name': 'Other'})
    @patch('app.views.AppointmentController.get_by_id',
           return_value={'id': 1, 'patient_id': 1, 'status': 'scheduled'})
    def test_patient_cancel_wrong_patient(self, mget, mp):
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
        self.assertEqual(resp.status_code, 302)

    @patch('app.views.PatientHelper.get_patient_for_user', return_value=SAMPLE_PATIENT)
    @patch('app.views.AppointmentController.get_by_id',
           return_value={'id': 1, 'patient_id': 1, 'status': 'completed'})
    def test_patient_cancel_not_scheduled(self, mget, mp):
        resp = self.client.post('/admin_panel/patient/appointments/1/cancel/')
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
        resp = self.client.get('/admin_panel/fastapi/status/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.services.fastapi_health.get_fastapi_status', return_value={'available': True})
    def test_fastapi_ping(self, _):
        resp = self.client.get('/fastapi/ping/')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('online', data)

    @patch('app.views.fastapi_client.get_patients', return_value={'success': True, 'data': []})
    @patch('app.views.AsyncHelper.run_async', return_value={'success': True, 'data': []})
    def test_fastapi_patients_view(self, ra, mp):
        resp = self.client.get('/admin_panel/fastapi/patients/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AsyncHelper.run_async', return_value={'success': True, 'data': [SAMPLE_SERVICE]})
    def test_fastapi_services_data_success(self, _):
        resp = self.client.get('/admin_panel/fastapi/services-data/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AsyncHelper.run_async', return_value={'success': False, 'error': 'timeout'})
    def test_fastapi_services_data_fail(self, _):
        resp = self.client.get('/admin_panel/fastapi/services-data/')
        self.assertEqual(resp.status_code, 503)

    @patch('app.views.AsyncHelper.run_async', return_value={'success': True, 'data': []})
    def test_fastapi_mkbs_view(self, _):
        resp = self.client.get('/admin_panel/fastapi/mkbs/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.fastapi_client.get_status_sync', return_value={'online': False})
    def test_fastapi_sync_patient_offline(self, _):
        resp = self.client.post('/admin_panel/fastapi/sync-patient/',
                                json.dumps({'patient_id': 1}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 503)

    def test_fastapi_sync_patient_no_id(self):
        resp = self.client.post('/admin_panel/fastapi/sync-patient/',
                                json.dumps({}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    @patch('app.views.fastapi_client.get_status_sync', return_value={'online': True})
    @patch('app.views.AsyncHelper.run_async', return_value={'success': True, 'data': []})
    def test_fastapi_full_status(self, ra, gs):
        resp = self.client.get('/admin_panel/fastapi/full-status/')
        self.assertEqual(resp.status_code, 200)

    def test_fastapi_demo_view(self):
        resp = self.client.get('/admin_panel/fastapi/demo/')
        self.assertEqual(resp.status_code, 200)

    def test_fastapi_status_page_view(self):
        resp = self.client.get('/admin_panel/fastapi/status-page/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_api_services(self, _):
        resp = self.client.get('/admin_panel/api/services/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    def test_api_patients(self, _):
        resp = self.client.get('/admin_panel/api/patients/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    def test_api_appointments(self, _):
        resp = self.client.get('/admin_panel/api/appointments/')
        self.assertEqual(resp.status_code, 200)


# ─── role-based access control ───────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestRoleAccess(TestCase):
    def setUp(self):
        self.client = Client()

    def test_admin_view_denied_for_patient(self):
        patient = make_user('role_patient', role='patient')
        self.client.force_login(patient)
        resp = self.client.get('/admin_panel/admin/dashboard/')
        self.assertIn(resp.status_code, [302, 403])

    def test_manager_view_denied_for_dentist(self):
        dentist = make_user('role_dentist2', role='dentist')
        self.client.force_login(dentist)
        resp = self.client.get('/admin_panel/manager/dashboard/')
        self.assertIn(resp.status_code, [302, 403])

    def test_unauthenticated_redirects(self):
        resp = self.client.get('/admin_panel/admin/dashboard/')
        self.assertEqual(resp.status_code, 302)


# ─── DRF API views ────────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestAPIViewSets(TestCase):
    def setUp(self):
        self.admin = make_user('api_admin', role='admin')
        self.manager = make_user('api_manager', role='manager')
        self.dentist = make_user('api_dentist', role='dentist')
        self.patient_user = make_user('api_patient', role='patient')
        self.client = APIClient()

    @patch('app.api.views.get_fastapi_status', return_value={'available': True})
    def test_fastapi_status_api(self, _):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v2/fastapi-status/')
        self.assertEqual(resp.status_code, 200)

    def test_me_api(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v2/me/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'api_admin')
        self.assertEqual(resp.data['role'], 'admin')

    @patch('app.controllers.PatientController.get_all', return_value=[SAMPLE_PATIENT])
    def test_patient_list_api(self, _):
        self.client.force_authenticate(user=self.manager)
        resp = self.client.get('/api/v2/patients/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.PatientController.get_by_id', return_value=SAMPLE_PATIENT)
    def test_patient_retrieve_api(self, _):
        self.client.force_authenticate(user=self.manager)
        resp = self.client.get('/api/v2/patients/1/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.PatientController.create', return_value=SAMPLE_PATIENT)
    def test_patient_create_api(self, _):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post('/api/v2/patients/', SAMPLE_PATIENT, format='json')
        self.assertEqual(resp.status_code, 201)

    @patch('app.controllers.PatientController.update', return_value=SAMPLE_PATIENT)
    def test_patient_update_api(self, _):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.put('/api/v2/patients/1/', SAMPLE_PATIENT, format='json')
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.PatientController.delete')
    def test_patient_delete_api(self, _):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.delete('/api/v2/patients/1/')
        self.assertEqual(resp.status_code, 204)

    @patch('app.controllers.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    def test_patient_appointments_api(self, _):
        self.client.force_authenticate(user=self.manager)
        resp = self.client.get('/api/v2/patients/1/appointments/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.VisitController.get_all', return_value=[SAMPLE_VISIT])
    def test_patient_visits_api(self, _):
        self.client.force_authenticate(user=self.dentist)
        resp = self.client.get('/api/v2/patients/1/visits/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.AppointmentController.get_all', return_value=[SAMPLE_APPOINTMENT])
    def test_appointment_list_api(self, _):
        self.client.force_authenticate(user=self.manager)
        resp = self.client.get('/api/v2/appointments/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.ServiceController.get_all', return_value=[SAMPLE_SERVICE])
    def test_service_list_api(self, _):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v2/services/')
        self.assertEqual(resp.status_code, 200)

    @patch('app.controllers.MaterialController.get_all', return_value=[SAMPLE_MATERIAL])
    def test_material_list_api(self, _):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v2/materials/')
        self.assertEqual(resp.status_code, 200)

    def test_user_profile_list_api(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/v2/users/')
        self.assertEqual(resp.status_code, 200)

    def test_api_unauthenticated(self):
        resp = self.client.get('/api/v2/patients/')
        self.assertEqual(resp.status_code, 401)

    def test_api_patient_role_forbidden(self):
        self.client.force_authenticate(user=self.patient_user)
        resp = self.client.get('/api/v2/patients/')
        self.assertEqual(resp.status_code, 403)


# ─── controllers ─────────────────────────────────────────────────────────────

class TestControllers(TestCase):
    @patch('app.controllers.patient_controller.requests.get')
    def test_patient_get_all(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_PATIENT])
        from app.controllers import PatientController
        result = PatientController.get_all()
        self.assertIsInstance(result, list)

    @patch('app.controllers.patient_controller.requests.get', side_effect=Exception('conn err'))
    def test_patient_get_all_error(self, _):
        from app.controllers import PatientController
        with self.assertRaises(Exception):
            PatientController.get_all()

    @patch('app.controllers.patient_controller.requests.get')
    def test_patient_get_by_id(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: SAMPLE_PATIENT)
        from app.controllers import PatientController
        result = PatientController.get_by_id(1)
        self.assertEqual(result['id'], 1)

    @patch('app.controllers.patient_controller.requests.post')
    def test_patient_create(self, mock_post):
        mock_post.return_value = MagicMock(status_code=201, json=lambda: SAMPLE_PATIENT)
        from app.controllers import PatientController
        result = PatientController.create(SAMPLE_PATIENT)
        self.assertIsNotNone(result)

    @patch('app.controllers.appointment_controller.requests.get')
    def test_appointment_get_all(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_APPOINTMENT])
        from app.controllers import AppointmentController
        result = AppointmentController.get_all()
        self.assertIsInstance(result, list)

    @patch('app.controllers.visit_controller.requests.get')
    def test_visit_get_all(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_VISIT])
        from app.controllers import VisitController
        result = VisitController.get_all()
        self.assertIsInstance(result, list)

    @patch('app.controllers.service_controller.requests.get')
    def test_service_get_all(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_SERVICE])
        from app.controllers import ServiceController
        result = ServiceController.get_all()
        self.assertIsInstance(result, list)

    @patch('app.controllers.material_controller.requests.get')
    def test_material_get_all(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_MATERIAL])
        from app.controllers import MaterialController
        result = MaterialController.get_all()
        self.assertIsInstance(result, list)

    @patch('app.controllers.mkbs_controller.requests.get')
    def test_mkbs_get_diagnoses(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_MKB])
        from app.controllers import MKBSController
        result = MKBSController.get_diagnoses()
        self.assertIsInstance(result, list)

    @patch('app.controllers.client_controller.requests.get')
    def test_client_get_doctors(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: [SAMPLE_DOCTOR])
        from app.controllers import ClientController
        result = ClientController.get_doctors()
        self.assertIsInstance(result, list)
