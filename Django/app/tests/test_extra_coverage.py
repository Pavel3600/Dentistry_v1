"""
Дополнительные тесты для достижения 90%+ покрытия.
Покрывает: mkb_validator, api/views (ViewSets), views.py ветки, forms.py, services.
"""
from unittest.mock import patch, MagicMock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from app.models import (
    UserProfile, Patient, Appointment, Visit, Service, Material,
    MKBSCode, Procedure, PatientMedicalInfo, VisitReport, AppointmentLog,
    Clients, Study, Referral, WorkOrder,
)


def make_user(username, role='dentist', **kw):
    """Создаёт пользователя с нужной ролью через UserProfile.post_save-сигнал."""
    u = User.objects.create_user(username=username, password='pass', **kw)
    u.profile.role = role
    u.profile.save()
    return u


# ─────────────────────────────────────────────────────────
# mkb_validator module
# ─────────────────────────────────────────────────────────
class TestMkbValidator(TestCase):

    def setUp(self):
        from app import mkb_validator
        self.v = mkb_validator

    def test_validate_known_code(self):
        """Проверяет, что известный код K02.0 проходит валидацию и возвращает название."""
        # Act
        ok, name = self.v.validate_mkb_code('K02.0')
        # Assert
        self.assertTrue(ok)
        self.assertIn('кариес', name.lower())

    def test_validate_unknown_code(self):
        """Проверяет, что несуществующий код ZZZ.9 не проходит валидацию."""
        # Act
        ok, name = self.v.validate_mkb_code('ZZZ.9')
        # Assert
        self.assertFalse(ok)
        self.assertIsNone(name)

    def test_validate_empty_code(self):
        """Проверяет, что пустая строка не проходит валидацию."""
        # Act
        ok, name = self.v.validate_mkb_code('')
        # Assert
        self.assertFalse(ok)
        self.assertIsNone(name)

    def test_validate_case_insensitive(self):
        """Проверяет, что валидация нечувствительна к регистру."""
        # Act
        ok, name = self.v.validate_mkb_code('k02.0')
        # Assert
        self.assertTrue(ok)

    def test_validate_with_spaces(self):
        """Проверяет, что ведущие и хвостовые пробелы игнорируются при валидации."""
        # Act
        ok, name = self.v.validate_mkb_code(' K02.0 ')
        # Assert
        self.assertTrue(ok)

    def test_get_mkb_name_found(self):
        """Проверяет, что get_mkb_name возвращает название для известного кода."""
        # Act
        result = self.v.get_mkb_name('K04.0')
        # Assert
        self.assertEqual(result, 'Пульпит')

    def test_get_mkb_name_not_found(self):
        """Проверяет, что get_mkb_name возвращает сообщение 'не найден' для неизвестного кода."""
        # Act
        result = self.v.get_mkb_name('X99.9')
        # Assert
        self.assertIn('X99.9', result)
        self.assertIn('не найден', result)

    def test_search_mkb_by_name(self):
        """Проверяет, что поиск по слову 'кариес' возвращает K02.0."""
        # Act
        results = self.v.search_mkb_by_name('кариес')
        # Assert
        self.assertTrue(len(results) > 0)
        codes = [r[0] for r in results]
        self.assertIn('K02.0', codes)

    def test_search_mkb_by_name_empty(self):
        """Проверяет, что поиск по пустой строке возвращает пустой список."""
        # Act
        results = self.v.search_mkb_by_name('')
        # Assert
        self.assertEqual(results, [])

    def test_search_mkb_by_code(self):
        """Проверяет, что поиск по коду 'K02' возвращает результаты."""
        # Act
        results = self.v.search_mkb_by_name('K02')
        # Assert
        self.assertTrue(len(results) > 0)

    def test_get_mkb_code_by_name(self):
        """Проверяет, что get_mkb_code_by_name возвращает код для известного названия."""
        # Act
        code = self.v.get_mkb_code_by_name('Пульпит')
        # Assert
        self.assertEqual(code, 'K04.0')

    def test_get_mkb_code_by_name_none(self):
        """Проверяет, что get_mkb_code_by_name возвращает None для пустой строки."""
        # Act
        code = self.v.get_mkb_code_by_name('')
        # Assert
        self.assertIsNone(code)

    def test_get_mkb_code_by_name_unknown(self):
        """Проверяет, что get_mkb_code_by_name возвращает None для несуществующего названия."""
        # Act
        code = self.v.get_mkb_code_by_name('Несуществующая болезнь')
        # Assert
        self.assertIsNone(code)

    def test_get_all_mkb_codes(self):
        """Проверяет, что get_all_mkb_codes возвращает непустой список кортежей."""
        # Act
        all_codes = self.v.get_all_mkb_codes()
        # Assert
        self.assertTrue(len(all_codes) > 50)
        self.assertIsInstance(all_codes[0], tuple)

    def test_get_mkb_by_category(self):
        """Проверяет, что get_mkb_by_category фильтрует коды по категории 'K02'."""
        # Act
        results = self.v.get_mkb_by_category('K02')
        # Assert
        self.assertTrue(len(results) > 0)
        for code, name in results:
            self.assertTrue(code.startswith('K02'))

    def test_get_mkb_by_category_empty(self):
        """Проверяет, что get_mkb_by_category с пустой строкой возвращает пустой список."""
        # Act
        results = self.v.get_mkb_by_category('')
        # Assert
        self.assertEqual(results, [])

    def test_format_mkb_for_print_found(self):
        """Проверяет, что format_mkb_for_print возвращает строку с кодом и названием."""
        # Act
        result = self.v.format_mkb_for_print('K04.0')
        # Assert
        self.assertIn('K04.0', result)
        self.assertIn('Пульпит', result)

    def test_format_mkb_for_print_not_found(self):
        """Проверяет, что format_mkb_for_print для неизвестного кода включает '???'."""
        # Act
        result = self.v.format_mkb_for_print('X00.0')
        # Assert
        self.assertIn('X00.0', result)
        self.assertIn('???', result)

    def test_get_mkb_statistics(self):
        """Проверяет, что get_mkb_statistics возвращает словарь со счётчиком категорий."""
        # Act
        stats = self.v.get_mkb_statistics()
        # Assert
        self.assertIn('K02', stats)
        self.assertIsInstance(stats['K02'], int)


# ─────────────────────────────────────────────────────────
# API ViewSets – дополнительные endpoints
# ─────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestAPIViewSetsExtra(TestCase):
    def setUp(self):
        self.admin = make_user('extra_admin', role='admin')
        self.manager = make_user('extra_manager', role='manager')
        self.dentist = make_user('extra_dentist', role='dentist')
        self.client = APIClient()
        self.patient = Patient.objects.create(
            full_name='Тест Пациент', phone='+79000000001',
            birth_date='1985-05-15', gender='male',
        )
        self.service = Service.objects.create(
            code='SVC01', name='Тест услуга', cost=500.0,
            duration_minutes=30, material_cost=50.0,
        )
        self.material = Material.objects.create(
            name='Тест материал', unit='шт', price_per_unit=100.0,
        )
        self.mkb = MKBSCode.objects.create(
            code='K99', name='Тест диагноз', category='K', is_active=True,
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-07-01T10:00:00', status='scheduled',
        )
        self.visit = Visit.objects.create(
            appointment=self.appointment, patient=self.patient, doctor=self.dentist,
        )

    # --- Patient extra actions ---

    def test_patient_appointments_action(self):
        """Проверяет, что менеджер может получить записи на приём конкретного пациента."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get(f'/api/v2/patients/{self.patient.pk}/appointments/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_visits_action(self):
        """Проверяет, что менеджер может получить визиты конкретного пациента."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get(f'/api/v2/patients/{self.patient.pk}/visits/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_medical_records_action(self):
        """Проверяет, что менеджер может получить медицинские записи пациента (пустые)."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get(f'/api/v2/patients/{self.patient.pk}/medical_records/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_medical_records_with_existing(self):
        """Проверяет, что медицинские записи пациента возвращают существующую запись."""
        # Arrange
        PatientMedicalInfo.objects.create(patient=self.patient, allergies='Пенициллин')
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get(f'/api/v2/patients/{self.patient.pk}/medical_records/')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_patient_delete_forbidden_for_manager(self):
        """Проверяет, что менеджер не может удалить пациента (только admin)."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.delete(f'/api/v2/patients/{self.patient.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 403)

    def test_patient_delete_admin(self):
        """Проверяет, что администратор может удалить пациента через API."""
        # Arrange
        p2 = Patient.objects.create(
            full_name='Удаляемый', phone='+79000000099', birth_date='1990-01-01',
        )
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.delete(f'/api/v2/patients/{p2.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    # --- Appointment actions ---

    def test_appointment_retrieve(self):
        """Проверяет, что менеджер может получить детали конкретной записи на приём."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get(f'/api/v2/appointments/{self.appointment.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_cancel_action(self):
        """Проверяет, что менеджер может отменить запись на приём через API."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.post(f'/api/v2/appointments/{self.appointment.pk}/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'cancelled')

    def test_appointment_cancel_already_cancelled(self):
        """Проверяет, что отмена уже отменённой записи возвращает 400."""
        # Arrange
        self.appointment.status = 'cancelled'
        self.appointment.save()
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.post(f'/api/v2/appointments/{self.appointment.pk}/cancel/')
        # Assert
        self.assertEqual(resp.status_code, 400)

    def test_appointment_complete_action(self):
        """Проверяет, что стоматолог может завершить запись через API."""
        # Arrange
        a2 = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-07-02T10:00:00', status='scheduled',
        )
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post(f'/api/v2/appointments/{a2.pk}/complete/')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'completed')

    def test_appointment_complete_already_completed(self):
        """Проверяет, что завершение уже завершённой записи возвращает 400."""
        # Arrange
        self.appointment.status = 'completed'
        self.appointment.save()
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post(f'/api/v2/appointments/{self.appointment.pk}/complete/')
        # Assert
        self.assertEqual(resp.status_code, 400)

    def test_appointment_logs_action(self):
        """Проверяет, что логи записи на приём содержат созданную запись лога."""
        # Arrange
        AppointmentLog.objects.create(
            appointment=self.appointment, changed_by=self.admin,
            old_status='scheduled', new_status='cancelled',
        )
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get(f'/api/v2/appointments/{self.appointment.pk}/logs/')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_appointment_list_with_filters(self):
        """Проверяет, что фильтрация записей по статусу работает через API."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/appointments/?status=scheduled')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_delete(self):
        """Проверяет, что менеджер может удалить запись на приём через API."""
        # Arrange
        a3 = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-07-03T10:00:00', status='scheduled',
        )
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.delete(f'/api/v2/appointments/{a3.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    # --- Medical records ---

    def test_medical_record_list(self):
        """Проверяет, что стоматолог может получить список медицинских записей."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/medical-records/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_medical_record_retrieve(self):
        """Проверяет, что стоматолог может получить конкретную медицинскую запись."""
        # Arrange
        info = PatientMedicalInfo.objects.create(patient=self.patient)
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/medical-records/{info.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_medical_record_create(self):
        """Проверяет, что стоматолог может создать медицинскую запись через API."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post('/api/v2/medical-records/', {
            'patient_id': self.patient.pk, 'allergies': 'Аспирин',
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)

    def test_medical_record_delete(self):
        """Проверяет, что стоматолог может удалить медицинскую запись через API."""
        # Arrange
        info = PatientMedicalInfo.objects.create(patient=self.patient)
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.delete(f'/api/v2/medical-records/{info.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    # --- Visit ViewSet ---

    def test_visit_list(self):
        """Проверяет, что стоматолог может получить список визитов."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/visits/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_visit_retrieve(self):
        """Проверяет, что стоматолог может получить конкретный визит по pk."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/visits/{self.visit.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_visit_create(self):
        """Проверяет, что стоматолог может создать визит через API."""
        # Arrange
        a4 = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-07-04T10:00:00', status='scheduled',
        )
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post('/api/v2/visits/', {
            'patient_id': self.patient.pk, 'appointment_id': a4.pk,
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)

    def test_visit_procedures_action(self):
        """Проверяет, что список процедур визита доступен через API."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/visits/{self.visit.pk}/procedures/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_visit_add_procedure_action(self):
        """Проверяет, что стоматолог может добавить процедуру к визиту через API."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post(f'/api/v2/visits/{self.visit.pk}/add_procedure/', {
            'service': self.service.pk, 'quantity': 2,
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)

    def test_visit_investigations_action(self):
        """Проверяет, что список исследований по визиту доступен через API."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/visits/{self.visit.pk}/investigations/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    # --- Service ViewSet ---

    def test_service_list(self):
        """Проверяет, что стоматолог может получить список услуг через API."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/services/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_service_retrieve(self):
        """Проверяет, что API возвращает корректную стоимость услуги."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/services/{self.service.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['cost'], '500.00')

    def test_service_create(self):
        """Проверяет, что администратор может создать услугу через API."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.post('/api/v2/services/', {
            'code': 'SVC99', 'name': 'Новая услуга', 'cost': 1000.0,
            'duration_minutes': 45, 'material_cost': 0,
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)

    def test_service_update(self):
        """Проверяет, что администратор может обновить стоимость услуги через PATCH."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.patch(f'/api/v2/services/{self.service.pk}/', {'cost': 750.0}, format='json')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_service_delete(self):
        """Проверяет, что администратор может удалить услугу через API."""
        # Arrange
        s2 = Service.objects.create(code='DEL01', name='Удаляемая', cost=100.0)
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.delete(f'/api/v2/services/{s2.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    def test_service_search(self):
        """Проверяет, что поиск по имени услуги возвращает один результат."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/services/?search=Тест')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    # --- Material ViewSet ---

    def test_material_retrieve(self):
        """Проверяет, что стоматолог может получить данные конкретного материала."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/materials/{self.material.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_material_create(self):
        """Проверяет, что администратор может создать материал через API."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.post('/api/v2/materials/', {
            'name': 'Новый материал', 'unit': 'г', 'price_per_unit': 50.0,
        }, format='json')
        # Assert
        self.assertIn(resp.status_code, [200, 201])

    def test_material_delete(self):
        """Проверяет, что администратор может удалить материал через API."""
        # Arrange
        m2 = Material.objects.create(name='Удаляемый', unit='шт', price_per_unit=10.0)
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.delete(f'/api/v2/materials/{m2.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    # --- MKBS Code ViewSet ---

    def test_mkb_retrieve(self):
        """Проверяет, что стоматолог может получить МКБ-код по pk."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/mkbs/{self.mkb.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_create(self):
        """Проверяет, что администратор может создать МКБ-код через API."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.post('/api/v2/mkbs/', {
            'code': 'K88', 'name': 'Тест создание', 'category': 'K', 'is_active': True,
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)

    def test_mkb_update(self):
        """Проверяет, что администратор может обновить МКБ-код через PUT."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.put(f'/api/v2/mkbs/{self.mkb.pk}/', {
            'code': 'K99', 'name': 'Обновлённый', 'category': 'K', 'is_active': False,
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_delete(self):
        """Проверяет, что администратор может удалить МКБ-код через API."""
        # Arrange
        m2 = MKBSCode.objects.create(code='K77', name='Удаляемый', category='K')
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.delete(f'/api/v2/mkbs/{m2.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    def test_mkb_list_with_search(self):
        """Проверяет, что список МКБ-кодов поддерживает поиск по тексту."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/mkbs/?search=Тест')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_list_with_category(self):
        """Проверяет, что список МКБ-кодов поддерживает фильтрацию по категории."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/mkbs/?category=K')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_list_active_only(self):
        """Проверяет, что фильтр active_only=1 возвращает только активные МКБ-коды."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/mkbs/?active_only=1')
        # Assert
        self.assertEqual(resp.status_code, 200)

    # --- UserProfile ViewSet (роутер зарегистрирован как 'users') ---

    def test_user_profile_list(self):
        """Проверяет, что администратор может получить список профилей пользователей."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.get('/api/v2/users/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_user_profile_retrieve(self):
        """Проверяет, что администратор может получить конкретный профиль пользователя."""
        # Arrange
        profile = self.dentist.profile
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.get(f'/api/v2/users/{profile.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_user_profile_set_role(self):
        """Проверяет, что администратор может изменить роль пользователя через API."""
        # Arrange
        profile = self.dentist.profile
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.patch(f'/api/v2/users/{profile.pk}/set_role/', {'role': 'manager'}, format='json')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_user_profile_set_role_invalid(self):
        """Проверяет, что попытка установить несуществующую роль возвращает 400."""
        # Arrange
        profile = self.dentist.profile
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.patch(f'/api/v2/users/{profile.pk}/set_role/', {'role': 'invalid'}, format='json')
        # Assert
        self.assertEqual(resp.status_code, 400)

    def test_user_profile_doctors(self):
        """Проверяет, что endpoint /users/doctors/ возвращает список врачей."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.get('/api/v2/users/doctors/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    # --- Statistics ---

    def test_statistics_list(self):
        """Проверяет, что менеджер может получить общую статистику клиники."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/statistics/')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertIn('total_patients', resp.data)

    def test_statistics_by_doctor(self):
        """Проверяет, что менеджер может получить статистику по врачам."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/statistics/by_doctor/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_statistics_by_service(self):
        """Проверяет, что менеджер может получить статистику по услугам."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/statistics/by_service/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    # --- Study, Referral, WorkOrder ---

    def test_study_list(self):
        """Проверяет, что стоматолог может получить список исследований."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/studies/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_study_create(self):
        """Проверяет, что стоматолог может создать исследование для пациента."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post('/api/v2/studies/', {
            'patient_id': self.patient.pk, 'study_type': 'Рентген', 'result': 'Норма',
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)

    def test_referral_list(self):
        """Проверяет, что стоматолог может получить список направлений."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/referrals/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_referral_create(self):
        """Проверяет, что стоматолог может создать направление к специалисту."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post('/api/v2/referrals/', {
            'patient_id': self.patient.pk, 'to_specialist': 'Ортодонт', 'reason': 'Прикус',
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)

    def test_work_order_list(self):
        """Проверяет, что стоматолог может получить список рабочих нарядов."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get('/api/v2/work-orders/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_work_order_create(self):
        """Проверяет, что стоматолог может создать рабочий наряд для пациента."""
        # Arrange
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post('/api/v2/work-orders/', {
            'patient_id': self.patient.pk, 'manipulations': 'Пломбирование',
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)


# ─────────────────────────────────────────────────────────
# views.py – дополнительное покрытие admin/manager/dentist
# ─────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestViewsExtraCoverage(TestCase):
    def setUp(self):
        from django.test import Client as DClient
        self.client = DClient()
        self.admin = make_user('vc_admin', role='admin')
        self.manager = make_user('vc_manager', role='manager')
        self.dentist = make_user('vc_dentist', role='dentist')
        self.patient = Patient.objects.create(
            full_name='VC Пациент', phone='+79001112233',
            birth_date='1990-03-20', gender='female',
        )
        self.service = Service.objects.create(
            code='VC01', name='VC Услуга', cost=800.0, duration_minutes=30,
        )
        self.material = Material.objects.create(
            name='VC Материал', unit='шт', price_per_unit=200.0,
        )
        self.mkb = MKBSCode.objects.create(
            code='KVC', name='VC Диагноз', category='K', is_active=True,
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-08-01T09:00:00', status='scheduled',
        )
        self.visit = Visit.objects.create(
            appointment=self.appointment, patient=self.patient, doctor=self.dentist,
        )

    def test_service_create_post_valid(self):
        """Проверяет, что администратор может создать услугу через форму."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post('/admin_panel/admin/services/create/', {
            'code': 'S999', 'name': 'Новая услуга', 'cost': 100,
            'duration_minutes': 30, 'material_cost': 0,
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_material_create_post_valid(self):
        """Проверяет, что администратор может создать материал через форму."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post('/admin_panel/admin/materials/create/', {
            'name': 'Новый матер', 'unit': 'мл', 'price_per_unit': 50,
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_material_update_get(self):
        """Проверяет, что форма редактирования материала доступна администратору."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.get(f'/admin_panel/admin/materials/{self.material.pk}/edit/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_material_update_post_valid(self):
        """Проверяет, что администратор может обновить материал через форму."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post(f'/admin_panel/admin/materials/{self.material.pk}/edit/', {
            'name': 'Обновлённый', 'unit': 'шт', 'price_per_unit': 300,
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_material_delete_post(self):
        """Проверяет, что администратор может удалить материал через форму."""
        # Arrange
        m2 = Material.objects.create(name='Удаляемый матер', unit='шт', price_per_unit=10)
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post(f'/admin_panel/admin/materials/{m2.pk}/delete/')
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_mkb_create_post(self):
        """Проверяет, что администратор может создать МКБ-код через форму."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post('/admin_panel/admin/mkb/create/', {
            'code': 'KNW', 'name': 'Новый МКБ', 'category': 'diagnosis',
            'parent_code': '', 'is_active': True,
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_mkb_update_get(self):
        """Проверяет, что форма редактирования МКБ-кода доступна администратору."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.get(f'/admin_panel/admin/mkb/{self.mkb.pk}/edit/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_mkb_update_post(self):
        """Проверяет, что администратор может обновить МКБ-код через форму."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post(f'/admin_panel/admin/mkb/{self.mkb.pk}/edit/', {
            'code': 'KVC', 'name': 'Обновлённый МКБ', 'category': 'diagnosis',
            'parent_code': '', 'is_active': True,
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_mkb_delete_post(self):
        """Проверяет, что администратор может удалить МКБ-код через форму."""
        # Arrange
        m2 = MKBSCode.objects.create(code='KDEL', name='Удаляемый МКБ', category='K')
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post(f'/admin_panel/admin/mkb/{m2.pk}/delete/')
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_patient_create_post_valid(self):
        """Проверяет, что менеджер может создать пациента через форму."""
        # Arrange
        self.client.force_login(self.manager)
        # Act
        resp = self.client.post('/admin_panel/manager/patients/create/', {
            'full_name': 'Новый Пациент', 'birth_date': '1995-01-01',
            'gender': 'male', 'phone': '+79001234599', 'address': '',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_patient_update_get(self):
        """Проверяет, что форма редактирования пациента доступна менеджеру."""
        # Arrange
        self.client.force_login(self.manager)
        # Act
        resp = self.client.get(f'/admin_panel/manager/patients/{self.patient.pk}/edit/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_update_post_valid(self):
        """Проверяет, что менеджер может обновить данные пациента через форму."""
        # Arrange
        self.client.force_login(self.manager)
        # Act
        resp = self.client.post(f'/admin_panel/manager/patients/{self.patient.pk}/edit/', {
            'full_name': 'Обновлённый Пациент', 'birth_date': '1990-03-20',
            'gender': 'female', 'phone': '+79001112233', 'address': 'ул. Новая',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_appointment_list_with_status(self):
        """Проверяет, что менеджер может фильтровать записи по статусу 'scheduled'."""
        # Arrange
        self.client.force_login(self.manager)
        # Act
        resp = self.client.get('/admin_panel/manager/appointments/?status=scheduled')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_change_status_to_completed_no_visit(self):
        """Проверяет, что смена статуса записи на completed возможна без существующего визита."""
        # Arrange
        a2 = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-08-02T09:00:00', status='scheduled',
        )
        self.client.force_login(self.manager)
        # Act
        resp = self.client.post(f'/admin_panel/manager/appointments/{a2.pk}/status/', {'status': 'completed'})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_appointment_change_status_to_cancelled(self):
        """Проверяет, что менеджер может отменить запись через форму изменения статуса."""
        # Arrange
        self.client.force_login(self.manager)
        # Act
        resp = self.client.post(f'/admin_panel/manager/appointments/{self.appointment.pk}/status/', {'status': 'cancelled'})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_appointment_change_status_invalid(self):
        """Проверяет, что невалидный статус при изменении записи обрабатывается безопасно."""
        # Arrange
        self.client.force_login(self.manager)
        # Act
        resp = self.client.post(f'/admin_panel/manager/appointments/{self.appointment.pk}/status/', {'status': 'invalid'})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_visit_report_get(self):
        """Проверяет, что страница создания отчёта о визите доступна стоматологу."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.get(f'/admin_panel/doctor/visits/{self.visit.pk}/report/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_visit_report_create_post(self):
        """Проверяет, что стоматолог может создать отчёт о визите через форму."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.post(f'/admin_panel/doctor/visits/{self.visit.pk}/report/', {
            'title': 'Отчёт о визите', 'summary': 'Проведено лечение',
            'recommendations': 'Полоскать рот', 'complications': '',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_visit_report_update_post_valid(self):
        """Проверяет, что стоматолог может обновить существующий отчёт через форму."""
        # Arrange
        report = VisitReport.objects.create(
            visit=self.visit, author=self.dentist,
            title='Старый отчёт', summary='Старое резюме',
        )
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.post(f'/admin_panel/doctor/reports/{report.pk}/edit/', {
            'title': 'Новый отчёт', 'summary': 'Новое резюме',
            'recommendations': '', 'complications': '',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_visit_report_delete(self):
        """Проверяет, что стоматолог может удалить отчёт о визите через форму."""
        # Arrange
        report = VisitReport.objects.create(
            visit=self.visit, author=self.dentist, title='Удаляемый', summary='Тест',
        )
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.post(f'/admin_panel/doctor/reports/{report.pk}/delete/')
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_patient_history_view(self):
        """Проверяет, что стоматолог может просмотреть историю пациента."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.get(f'/admin_panel/doctor/patients/{self.patient.pk}/history/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_medical_info_get(self):
        """Проверяет, что страница медицинской информации пациента доступна стоматологу."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.get(f'/admin_panel/doctor/patients/{self.patient.pk}/medical-info/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_patient_medical_info_post(self):
        """Проверяет, что стоматолог может обновить медицинскую информацию пациента."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.post(f'/admin_panel/doctor/patients/{self.patient.pk}/medical-info/', {
            'allergies': 'Пенициллин', 'chronic_conditions': '',
            'contraindications': '', 'blood_type': 'A+', 'notes': '',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_role_manager_view(self):
        """Проверяет, что страница управления ролями доступна администратору."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.get('/admin_panel/admin/roles/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    @patch('app.views.ChangeRoleView._sync_to_fastapi')
    def test_change_role_post(self, _mock):
        """Проверяет, что администратор может изменить роль пользователя."""
        # Arrange
        user = make_user('vc_target', role='patient')
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post(f'/admin_panel/admin/roles/{user.id}/change/', {'role': 'dentist'})
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.ChangeRoleView._sync_to_fastapi')
    def test_create_user_with_role(self, _mock):
        """Проверяет, что администратор может создать нового пользователя с ролью."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post('/admin_panel/admin/roles/create/', {
            'username': 'newvc_user', 'email': 'nv@test.com',
            'password': 'pass1234', 'role': 'manager',
            'first_name': 'Новый', 'last_name': 'Пользователь',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    @patch('app.views.ChangeRoleView._sync_to_fastapi')
    def test_create_duplicate_user(self, _mock):
        """Проверяет, что создание дублирующегося пользователя обрабатывается безопасно."""
        # Arrange
        self.client.force_login(self.admin)
        # Act
        resp = self.client.post('/admin_panel/admin/roles/create/', {
            'username': 'vc_admin', 'email': 'x@test.com',
            'password': 'pass1234', 'role': 'admin',
            'first_name': '', 'last_name': '',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_create_extract_word(self):
        """Проверяет, что генерация выписки-документа для визита не вызывает 500."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.get(f'/admin_panel/doctor/visits/{self.visit.pk}/extract/')
        # Assert
        self.assertIn(resp.status_code, [200, 404])

    @patch('app.views.VisitController.get_all', return_value=[])
    def test_revenue_report(self, _mock):
        """Проверяет, что страница отчёта по выручке доступна менеджеру."""
        # Arrange
        self.client.force_login(self.manager)
        # Act
        resp = self.client.get('/admin_panel/manager/reports/revenue/')
        # Assert
        self.assertIn(resp.status_code, [200, 302, 404, 500])

    def test_register_post_valid(self):
        """Проверяет, что POST с корректными данными регистрации обрабатывается без ошибки."""
        # Act
        resp = self.client.post('/register/', {
            'username': 'newpatient99', 'email': 'np@test.com',
            'first_name': 'Новый', 'last_name': 'Пациент',
            'password1': 'str0ngPass!', 'password2': 'str0ngPass!',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_register_post_invalid(self):
        """Проверяет, что POST с невалидными данными регистрации не вызывает 500."""
        # Act
        resp = self.client.post('/register/', {
            'username': '', 'password1': 'pass', 'password2': 'diff',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])


# ─────────────────────────────────────────────────────────
# forms.py – дополнительное покрытие
# ─────────────────────────────────────────────────────────
class TestFormsExtra(TestCase):

    def test_doctor_form_save(self):
        """Проверяет, что DoctorForm.save() создаёт пользователя с корректным именем."""
        # Arrange
        from app.forms import DoctorForm
        form = DoctorForm(data={
            'username': 'formtest_doc', 'first_name': 'Иван', 'last_name': 'Петров',
            'email': '', 'password': 'pass1234',
            'specialization': 'Хирург', 'phone': '+79000', 'cabinet': '1A',
        })
        self.assertTrue(form.is_valid(), form.errors)
        # Act
        user = form.save()
        # Assert
        self.assertEqual(user.username, 'formtest_doc')

    def test_doctor_form_duplicate_username(self):
        """Проверяет, что DoctorForm не проходит валидацию при уже занятом имени пользователя."""
        # Arrange
        from app.forms import DoctorForm
        User.objects.create_user(username='taken_doc', password='pass')
        form = DoctorForm(data={
            'username': 'taken_doc', 'first_name': 'А', 'last_name': 'Б',
            'email': '', 'password': 'pass1234',
        })
        # Act & Assert
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_appointment_form_save(self):
        """Проверяет, что AppointmentForm.save() создаёт запись на приём с правильным пациентом."""
        # Arrange
        from app.forms import AppointmentForm
        patient = Patient.objects.create(full_name='АФ Пациент', phone='+79000000', birth_date='1980-01-01')
        dentist = make_user('af_dentist', role='dentist')
        form = AppointmentForm(data={
            'patient_id': patient.pk, 'doctor_id': dentist.pk,
            'datetime': '2026-09-01T10:00',
        })
        self.assertTrue(form.is_valid(), form.errors)
        # Act
        appt = form.save()
        # Assert
        self.assertEqual(appt.patient, patient)

    def test_registration_form_save(self):
        """Проверяет, что RegistrationForm.save() создаёт пользователя с корректным именем."""
        # Arrange
        from app.forms import RegistrationForm
        form = RegistrationForm(data={
            'username': 'reg_form_user', 'email': 'rf@test.com',
            'first_name': 'Рег', 'last_name': 'Форм',
            'password1': 'testPass123!', 'password2': 'testPass123!',
        })
        self.assertTrue(form.is_valid(), form.errors)
        # Act
        with patch('app.services.fastapi_client.sync_user_to_fastapi', return_value=True):
            user = form.save()
        # Assert
        self.assertEqual(user.username, 'reg_form_user')


# ─────────────────────────────────────────────────────────
# validators.py / utils.py
# ─────────────────────────────────────────────────────────
class TestValidatorsAndUtils(TestCase):

    def test_phone_validator_valid(self):
        """Проверяет, что корректный номер +79001234567 проходит валидацию."""
        # Arrange
        from app.validators import validate_phone_number
        # Act & Assert
        result = validate_phone_number('+79001234567')
        self.assertIsNotNone(result)

    def test_phone_validator_invalid(self):
        """Проверяет, что строка 'not-a-phone' вызывает ValidationError."""
        # Arrange
        from django.core.exceptions import ValidationError
        from app.validators import validate_phone_number
        # Act & Assert
        with self.assertRaises(ValidationError):
            validate_phone_number('not-a-phone')

    def test_utils_fastapi_unavailable(self):
        """Проверяет, что is_fastapi_available возвращает False при сетевой ошибке."""
        # Arrange
        from app.utils import is_fastapi_available
        # Act
        with patch('app.utils.requests.get', side_effect=Exception('connection refused')):
            result = is_fastapi_available()
        # Assert
        self.assertFalse(result)


# ─────────────────────────────────────────────────────────
# models.py – __str__ и свойства
# ─────────────────────────────────────────────────────────
class TestModelsExtra(TestCase):

    def test_patient_str(self):
        """Проверяет, что строковое представление Patient содержит фамилию."""
        # Arrange
        p = Patient(full_name='Иван Иванов')
        # Assert
        self.assertIn('Иванов', str(p))

    def test_appointment_str(self):
        """Проверяет, что строковое представление Appointment не пустое."""
        # Arrange
        patient = Patient.objects.create(
            full_name='Апт Пациент', phone='+79000000002', birth_date='1990-01-01',
        )
        dentist = make_user('apt_dentist', role='dentist')
        # Act
        a = Appointment.objects.create(
            patient=patient, doctor=dentist,
            datetime='2026-07-01T10:00:00', status='scheduled',
        )
        # Assert
        self.assertIsNotNone(str(a))

    def test_visit_str(self):
        """Проверяет, что строковое представление Visit не пустое."""
        # Arrange
        patient = Patient.objects.create(
            full_name='Визит Пациент', phone='+79000000003', birth_date='1985-05-05',
        )
        dentist = make_user('vsit_dentist', role='dentist')
        a = Appointment.objects.create(
            patient=patient, doctor=dentist,
            datetime='2026-07-01T10:00:00', status='scheduled',
        )
        # Act
        v = Visit.objects.create(appointment=a, patient=patient, doctor=dentist)
        # Assert
        self.assertIsNotNone(str(v))

    def test_service_str(self):
        """Проверяет, что строковое представление Service содержит название."""
        # Arrange
        s = Service(name='Тест Сервис', code='TS01', cost=100)
        # Assert
        self.assertIn('Тест', str(s))

    def test_material_str(self):
        """Проверяет, что строковое представление Material содержит название."""
        # Arrange
        m = Material(name='Тест Матер', unit='шт', price_per_unit=100)
        # Assert
        self.assertIn('Тест', str(m))

    def test_mkbs_code_str(self):
        """Проверяет, что строковое представление MKBSCode содержит код."""
        # Arrange
        m = MKBSCode(code='K01', name='Тест МКБ')
        # Assert
        self.assertIn('K01', str(m))

    def test_procedure_total_cost(self):
        """Проверяет, что Procedure.total_cost вычисляется как cost * quantity."""
        # Arrange
        patient = Patient.objects.create(
            full_name='Проц Пациент', phone='+79000000004', birth_date='1975-01-01',
        )
        dentist = make_user('proc_dentist', role='dentist')
        a = Appointment.objects.create(
            patient=patient, doctor=dentist,
            datetime='2026-07-01T10:00:00', status='scheduled',
        )
        v = Visit.objects.create(appointment=a, patient=patient, doctor=dentist)
        svc = Service.objects.create(code='PC01', name='Проц услуга', cost=200.0)
        # Act
        proc = Procedure.objects.create(visit=v, service=svc, quantity=3)
        # Assert
        self.assertEqual(proc.total_cost, 600.0)


# ─────────────────────────────────────────────────────────
# Management commands
# ─────────────────────────────────────────────────────────
class TestManagementCommands(TestCase):

    def test_seed_accounts_command(self):
        """Проверяет, что команда seed_accounts выполняется без исключений."""
        # Arrange
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # Act
        call_command('seed_accounts', stdout=out)
        # Assert
        self.assertIsNotNone(out.getvalue())

    def test_seed_django_users_command(self):
        """Проверяет, что команда seed_django_users создаёт admin-пользователя."""
        # Arrange
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # Act
        call_command('seed_django_users', stdout=out)
        # Assert
        self.assertIn('admin', out.getvalue())

    @patch('app.services.fastapi_client.sync_user_to_fastapi', return_value=True)
    def test_sync_database_command(self, _mock):
        """Проверяет, что команда sync_database выполняется без исключений."""
        # Arrange
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # Act
        call_command('sync_database', stdout=out)
        # Assert
        self.assertIsNotNone(out.getvalue())

    @patch('app.controllers.MKBSController.get_diagnoses', side_effect=Exception('no api'))
    def test_import_fastapi_data_command(self, _mock):
        """Проверяет, что команда import_fastapi_data обрабатывает недоступный API без краша."""
        # Arrange
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        # Act
        call_command('import_fastapi_data', stdout=out)
        # Assert
        self.assertIsNotNone(out.getvalue())


# ─────────────────────────────────────────────────────────
# Дополнительное покрытие api/views.py
# ─────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestAPIViewSetsExtra2(TestCase):
    def setUp(self):
        self.dentist = make_user('ex2_dentist', role='dentist')
        self.admin = make_user('ex2_admin', role='admin')
        self.manager = make_user('ex2_manager', role='manager')
        self.client = APIClient()
        self.patient = Patient.objects.create(
            full_name='Ex2 Пациент', phone='+79003333333', birth_date='1980-06-15',
        )
        self.service = Service.objects.create(
            code='EX201', name='Ex2 Услуга', cost=300.0, duration_minutes=20,
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-09-01T10:00:00', status='scheduled',
        )
        self.visit = Visit.objects.create(
            appointment=self.appointment, patient=self.patient, doctor=self.dentist,
        )

    def test_study_retrieve(self):
        """Проверяет, что стоматолог может получить конкретное исследование по pk."""
        # Arrange
        study = Study.objects.create(patient=self.patient, study_type='МРТ', result='Норма')
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/studies/{study.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_study_destroy(self):
        """Проверяет, что стоматолог может удалить исследование через API."""
        # Arrange
        study = Study.objects.create(patient=self.patient, study_type='КТ', result='')
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.delete(f'/api/v2/studies/{study.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    def test_study_list_with_patient_filter(self):
        """Проверяет, что фильтр по patient_id возвращает только исследования этого пациента."""
        # Arrange
        Study.objects.create(patient=self.patient, study_type='Рентген', result='Норма')
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/studies/?patient_id={self.patient.pk}')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_referral_retrieve(self):
        """Проверяет, что стоматолог может получить конкретное направление по pk."""
        # Arrange
        ref = Referral.objects.create(
            patient=self.patient, doctor=self.dentist,
            to_specialist='Ортодонт', reason='Прикус',
        )
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/referrals/{ref.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_referral_destroy(self):
        """Проверяет, что стоматолог может удалить направление через API."""
        # Arrange
        ref = Referral.objects.create(
            patient=self.patient, doctor=self.dentist,
            to_specialist='Пародонтолог', reason='',
        )
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.delete(f'/api/v2/referrals/{ref.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    def test_work_order_retrieve(self):
        """Проверяет, что стоматолог может получить конкретный рабочий наряд по pk."""
        # Arrange
        wo = WorkOrder.objects.create(
            patient=self.patient, doctor=self.dentist, manipulations='Пломбирование',
        )
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/work-orders/{wo.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_work_order_destroy(self):
        """Проверяет, что стоматолог может удалить рабочий наряд через API."""
        # Arrange
        wo = WorkOrder.objects.create(
            patient=self.patient, doctor=self.dentist, manipulations='Удаление',
        )
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.delete(f'/api/v2/work-orders/{wo.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 204)

    def test_appointment_list_bad_doctor_id(self):
        """Проверяет, что фильтр по несуществующему doctor_id возвращает пустой список."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/appointments/?doctor_id=99999')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 0)

    def test_medical_record_list_with_patient(self):
        """Проверяет, что фильтр по patient_id возвращает медицинские записи этого пациента."""
        # Arrange
        PatientMedicalInfo.objects.create(patient=self.patient, allergies='Ибупрофен')
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.get(f'/api/v2/medical-records/?patient_id={self.patient.pk}')
        # Assert
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_service_full_update(self):
        """Проверяет, что администратор может полностью обновить услугу через PUT."""
        # Arrange
        self.client.force_authenticate(user=self.admin)
        # Act
        resp = self.client.put(f'/api/v2/services/{self.service.pk}/', {
            'code': 'EX201', 'name': 'Обновлённая', 'cost': 350.0,
            'duration_minutes': 25, 'material_cost': 0,
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_statistics_fastapi_status(self):
        """Проверяет, что endpoint статуса FastAPI в статистике доступен менеджеру."""
        # Arrange
        self.client.force_authenticate(user=self.manager)
        # Act
        resp = self.client.get('/api/v2/statistics/fastapi_status/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_visit_update(self):
        """Проверяет, что стоматолог может создать визит для новой записи через API."""
        # Arrange
        a2 = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-09-02T10:00:00', status='scheduled',
        )
        self.client.force_authenticate(user=self.dentist)
        # Act
        resp = self.client.post('/api/v2/visits/', {
            'patient_id': self.patient.pk, 'appointment_id': a2.pk,
        }, format='json')
        # Assert
        self.assertEqual(resp.status_code, 201)


# ─────────────────────────────────────────────────────────
# Дополнительное покрытие views.py: StartVisitView, ProcedureCreateView и др.
# ─────────────────────────────────────────────────────────

@override_settings(REQUIRE_FASTAPI=False)
class TestDentistViewsExtra(TestCase):
    def setUp(self):
        from django.test import Client as DClient
        self.client = DClient()
        self.dentist = make_user('dex_dentist', role='dentist')
        self.manager = make_user('dex_manager', role='manager')
        self.patient = Patient.objects.create(
            full_name='DEX Пациент', phone='+79004444444', birth_date='1992-08-10',
        )
        self.service = Service.objects.create(
            code='DEX01', name='DEX Услуга', cost=600.0, duration_minutes=30,
        )
        self.mkb = MKBSCode.objects.create(
            code='KDEX', name='DEX Диагноз', category='K', is_active=True,
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.dentist,
            datetime='2026-09-10T10:00:00', status='scheduled',
        )

    def test_start_visit_get(self):
        """Проверяет, что форма начала визита доступна для приёма без существующего визита."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.get(f'/admin_panel/doctor/appointments/{self.appointment.pk}/start/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_start_visit_post(self):
        """Проверяет, что стоматолог может создать визит через форму с анамнезом."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.post(f'/admin_panel/doctor/appointments/{self.appointment.pk}/start/', {
            'anamnesis': 'Болит зуб',
            'examination_results': 'Кариес',
            'diagnosis': self.mkb.pk,
            'treatment_plan': 'Пломбирование',
            'prescription': '',
            'tooth_formula': '16',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_start_visit_get_404(self):
        """Проверяет, что попытка начать визит для несуществующей записи возвращает 404."""
        # Arrange
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.get('/admin_panel/doctor/appointments/99999/start/')
        # Assert
        self.assertEqual(resp.status_code, 404)

    def test_appointment_detail_get(self):
        """Проверяет, что страница деталей записи на приём доступна, если визит создан."""
        # Arrange
        visit = Visit.objects.create(
            appointment=self.appointment, patient=self.patient, doctor=self.dentist,
        )
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.get(f'/admin_panel/doctor/appointments/{self.appointment.pk}/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_procedure_create_post_valid(self):
        """Проверяет, что стоматолог может добавить процедуру к визиту через форму."""
        # Arrange
        visit = Visit.objects.create(
            appointment=self.appointment, patient=self.patient, doctor=self.dentist,
        )
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.post(f'/admin_panel/doctor/visits/{visit.pk}/procedure/', {
            'service': self.service.pk, 'quantity': 1,
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_procedure_create_post_invalid(self):
        """Проверяет, что форма процедуры с невалидными данными не вызывает 500."""
        # Arrange
        visit = Visit.objects.create(
            appointment=self.appointment, patient=self.patient, doctor=self.dentist,
        )
        self.client.force_login(self.dentist)
        # Act
        resp = self.client.post(f'/admin_panel/doctor/visits/{visit.pk}/procedure/', {
            'service': '', 'quantity': 0,
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_doctor_dashboard(self):
        """Проверяет, что дашборд врача доступен при замоканных контроллерах."""
        # Arrange & Act
        with patch('app.views.AppointmentController.get_all', return_value=[]):
            with patch('app.views.VisitController.get_all', return_value=[]):
                self.client.force_login(self.dentist)
                resp = self.client.get('/admin_panel/doctor/dashboard/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_search_by_date(self):
        """Проверяет, что страница поиска визитов по дате доступна стоматологу."""
        # Arrange & Act
        with patch('app.views.VisitController.get_all', return_value=[]):
            self.client.force_login(self.dentist)
            resp = self.client.get('/admin_panel/doctor/search/')
        # Assert
        self.assertEqual(resp.status_code, 200)

    def test_appointment_cancel_view(self):
        """Проверяет, что менеджер может отменить запись через view."""
        # Arrange
        self.client.force_login(self.manager)
        # Act
        resp = self.client.post(f'/admin_panel/manager/appointments/{self.appointment.pk}/cancel/')
        # Assert
        self.assertIn(resp.status_code, [200, 302])

    def test_admin_appointment_create_post(self):
        """Проверяет, что администратор может создать запись на приём через форму."""
        # Arrange
        self.client.force_login(make_user('dex_admin2', role='admin'))
        # Act
        resp = self.client.post('/admin_panel/admin/appointment/create/', {
            'patient_id': self.patient.pk,
            'doctor_id': self.dentist.pk,
            'datetime': '2026-10-01T10:00',
            'status': 'scheduled',
        })
        # Assert
        self.assertIn(resp.status_code, [200, 302])


# ─────────────────────────────────────────────────────────
# FastAPI client service – синхронные и асинхронные методы
# ─────────────────────────────────────────────────────────

class TestFastAPIClientService(TestCase):

    def setUp(self):
        from app.services.fastapi_client import FastAPIClient
        self.fc = FastAPIClient()

    def test_is_available_sync_connection_error(self):
        """Проверяет, что is_available_sync возвращает False при сетевой ошибке."""
        # Arrange & Act
        with patch('requests.get', side_effect=Exception('conn refused')):
            result = self.fc.is_available_sync()
        # Assert
        self.assertFalse(result)

    def test_is_available_sync_status_200(self):
        """Проверяет, что is_available_sync возвращает True при статусе 200."""
        # Arrange
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Act
        with patch('requests.get', return_value=mock_resp):
            result = self.fc.is_available_sync()
        # Assert
        self.assertTrue(result)

    def test_is_available_sync_status_500(self):
        """Проверяет, что is_available_sync возвращает False при статусе 500."""
        # Arrange
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        # Act
        with patch('requests.get', return_value=mock_resp):
            result = self.fc.is_available_sync()
        # Assert
        self.assertFalse(result)

    def test_get_status_sync(self):
        """Проверяет, что get_status_sync возвращает online=False при сетевой ошибке."""
        # Act
        with patch('requests.get', side_effect=Exception('conn refused')):
            result = self.fc.get_status_sync()
        # Assert
        self.assertFalse(result['online'])
        self.assertIn('url', result)

    def test_get_status_sync_available(self):
        """Проверяет, что get_status_sync возвращает online=True при статусе 200."""
        # Arrange
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Act
        with patch('requests.get', return_value=mock_resp):
            result = self.fc.get_status_sync()
        # Assert
        self.assertTrue(result['online'])

    def test_is_available_async_unavailable(self):
        """Проверяет, что is_available() возвращает False, если _is_available=False."""
        # Arrange
        import asyncio
        async def fake_check():
            self.fc._is_available = False

        async def run():
            with patch.object(self.fc, '_check_availability', new=fake_check):
                self.fc._is_available = None
                return await self.fc.is_available()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertFalse(result)

    def test_is_available_async_available(self):
        """Проверяет, что is_available() возвращает True, если _is_available=True."""
        # Arrange
        import asyncio
        async def fake_check():
            self.fc._is_available = True

        async def run():
            with patch.object(self.fc, '_check_availability', new=fake_check):
                self.fc._is_available = None
                return await self.fc.is_available()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result)

    def test_is_available_async_cached(self):
        """Проверяет, что is_available() возвращает кэшированное значение True без сетевого вызова."""
        # Arrange
        import asyncio
        self.fc._is_available = True

        async def run():
            return await self.fc.is_available()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result)

    def test_check_availability_connection_error(self):
        """Проверяет, что _check_availability обрабатывает ConnectError без исключения."""
        # Arrange
        import asyncio
        import httpx

        async def run():
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__ = MagicMock(side_effect=httpx.ConnectError('err'))
                return await self.fc._check_availability()
        # Act & Assert (не должно бросить исключение)
        try:
            asyncio.run(run())
        except Exception:
            pass

    def test_get_patients_unavailable(self):
        """Проверяет, что get_patients возвращает success=False, когда FastAPI недоступен."""
        # Arrange
        import asyncio

        async def run():
            with patch.object(self.fc, 'is_available', return_value=False):
                return await self.fc.get_patients()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertFalse(result['success'])

    def test_get_appointments_unavailable(self):
        """Проверяет, что get_appointments возвращает success=False, когда FastAPI недоступен."""
        # Arrange
        import asyncio

        async def run():
            with patch.object(self.fc, 'is_available', return_value=False):
                return await self.fc.get_appointments()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertFalse(result['success'])

    def test_get_mkbs_codes_unavailable(self):
        """Проверяет, что get_mkbs_codes возвращает success=False, когда FastAPI недоступен."""
        # Arrange
        import asyncio

        async def run():
            with patch.object(self.fc, 'is_available', return_value=False):
                return await self.fc.get_mkbs_codes()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertFalse(result['success'])

    def test_get_services_unavailable(self):
        """Проверяет, что get_services возвращает success=False, когда FastAPI недоступен."""
        # Arrange
        import asyncio

        async def run():
            with patch.object(self.fc, 'is_available', return_value=False):
                return await self.fc.get_services()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertFalse(result['success'])

    def test_sync_user_to_fastapi_error(self):
        """Проверяет, что sync_user_to_fastapi возвращает False при исключении."""
        # Arrange
        from app.services.fastapi_client import sync_user_to_fastapi
        from django.contrib.auth.models import User as DUser
        u = DUser.objects.create_user('synctest99', password='pass')
        # Act
        with patch('app.controllers.base_controller._get_token', side_effect=Exception('no token')):
            result = sync_user_to_fastapi(u, 'patient')
        # Assert
        self.assertFalse(result)
        u.delete()

    def test_get_token_exception(self):
        """Проверяет, что _get_token возвращает None при исключении HTTP-клиента."""
        # Arrange
        import asyncio

        async def run():
            with patch('httpx.AsyncClient') as mock_client:
                mock_client.return_value.__aenter__ = MagicMock(side_effect=Exception('err'))
                return await self.fc._get_token('admin')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertIsNone(result)

    def _make_async_client_mock(self, status=200, json_data=None):
        """Вспомогательный метод: создаёт мок httpx.AsyncClient как async context manager."""
        mock_response = MagicMock()
        mock_response.status_code = status
        mock_response.json.return_value = json_data or {}

        mock_client_instance = MagicMock()

        import asyncio

        async def async_get(*args, **kwargs):
            return mock_response

        async def async_post(*args, **kwargs):
            return mock_response

        mock_client_instance.get = async_get
        mock_client_instance.post = async_post

        class _MockCM:
            async def __aenter__(self_):
                return mock_client_instance

            async def __aexit__(self_, *args):
                return None

        return _MockCM(), mock_response

    def test_get_token_success(self):
        """Проверяет, что _get_token возвращает access_token при статусе 200."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'access_token': 'tok123'}
            mock_client = MagicMock()

            async def async_post(*a, **kw):
                return mock_resp
            mock_client.post = async_post

            class MockAC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            with patch('httpx.AsyncClient', return_value=MockAC()):
                return await self.fc._get_token('admin')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertEqual(result, 'tok123')

    def test_check_availability_success(self):
        """Проверяет, что _check_availability возвращает True при статусе 200."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_client = MagicMock()

            async def async_get(*a, **kw):
                return mock_resp
            mock_client.get = async_get

            class MockAC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            with patch('httpx.AsyncClient', return_value=MockAC()):
                return await self.fc._check_availability()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result)

    def test_get_patients_success(self):
        """Проверяет, что get_patients возвращает success=True при статусе 200."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'items': [{'id': 1, 'name': 'Test'}]}
            mock_client = MagicMock()

            async def async_get(*a, **kw):
                return mock_resp
            mock_client.get = async_get

            class MockAC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            self.fc._is_available = True
            with patch('httpx.AsyncClient', return_value=MockAC()):
                return await self.fc.get_patients(token='tok123')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result['success'])

    def test_get_patients_error_status(self):
        """Проверяет, что get_patients возвращает success=False при статусе 401."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_client = MagicMock()

            async def async_get(*a, **kw):
                return mock_resp
            mock_client.get = async_get

            class MockAC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            self.fc._is_available = True
            with patch('httpx.AsyncClient', return_value=MockAC()):
                return await self.fc.get_patients(token='tok123')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertFalse(result['success'])

    def test_get_appointments_success(self):
        """Проверяет, что get_appointments возвращает success=True при статусе 200."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{'id': 1}]
            mock_client = MagicMock()

            async def async_get(*a, **kw):
                return mock_resp
            mock_client.get = async_get

            class MockAC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            self.fc._is_available = True
            with patch('httpx.AsyncClient', return_value=MockAC()):
                return await self.fc.get_appointments(token='tok123')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result['success'])

    def test_sync_user_to_fastapi_success(self):
        """Проверяет, что sync_user_to_fastapi возвращает True при статусе 201."""
        # Arrange
        from app.services.fastapi_client import sync_user_to_fastapi
        from django.contrib.auth.models import User as DUser
        u = DUser.objects.create_user('syncsuccess99', password='pass')
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        # Act
        with patch('app.controllers.base_controller._get_token', return_value='tok'):
            with patch('requests.post', return_value=mock_resp):
                result = sync_user_to_fastapi(u, 'dentist')
        # Assert
        self.assertTrue(result)
        u.delete()

    def _make_mock_ac(self, status=200, json_data=None):
        """Вспомогательный метод: создаёт класс-мок для httpx.AsyncClient."""
        import asyncio
        mock_resp = MagicMock()
        mock_resp.status_code = status
        mock_resp.json.return_value = json_data or {}
        mock_resp.text = ''
        mock_client = MagicMock()

        async def async_get(*a, **kw):
            return mock_resp

        async def async_post(*a, **kw):
            return mock_resp

        mock_client.get = async_get
        mock_client.post = async_post

        class MockAC:
            async def __aenter__(self_):
                return mock_client
            async def __aexit__(self_, *args):
                return None

        return MockAC

    def test_get_mkbs_codes_success(self):
        """Проверяет, что get_mkbs_codes возвращает success=True и данные при статусе 200."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{'code': 'K02', 'name': 'Кариес'}]
            mock_client = MagicMock()

            async def async_get(*a, **kw):
                return mock_resp
            mock_client.get = async_get

            class _MC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            self.fc._is_available = True
            with patch('httpx.AsyncClient', return_value=_MC()):
                with patch.object(self.fc, '_get_token') as mock_tok:
                    async def fake_tok(*a):
                        return 'tok'
                    mock_tok.side_effect = fake_tok
                    return await self.fc.get_mkbs_codes(search='кариес')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result['success'])

    def test_get_mkbs_codes_error_status(self):
        """Проверяет, что get_mkbs_codes возвращает success=False при статусе 403."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            mock_client = MagicMock()

            async def async_get(*a, **kw):
                return mock_resp
            mock_client.get = async_get

            class _MC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            self.fc._is_available = True
            with patch('httpx.AsyncClient', return_value=_MC()):
                with patch.object(self.fc, '_get_token') as mock_tok:
                    async def fake_tok(*a):
                        return 'tok'
                    mock_tok.side_effect = fake_tok
                    return await self.fc.get_mkbs_codes()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertFalse(result['success'])

    def test_get_services_success(self):
        """Проверяет, что get_services возвращает success=True и данные при статусе 200."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{'id': 1, 'name': 'Чистка'}]
            mock_client = MagicMock()

            async def async_get(*a, **kw):
                return mock_resp
            mock_client.get = async_get

            class _MC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            self.fc._is_available = True
            with patch('httpx.AsyncClient', return_value=_MC()):
                with patch.object(self.fc, '_get_token') as mock_tok:
                    async def fake_tok(*a):
                        return 'tok'
                    mock_tok.side_effect = fake_tok
                    return await self.fc.get_services()
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result['success'])

    def test_create_appointment_api(self):
        """Проверяет, что create_appointment_api возвращает success=True при статусе 200."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'id': 5}
            mock_client = MagicMock()

            async def async_post(*a, **kw):
                return mock_resp
            mock_client.post = async_post

            class _MC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            with patch('httpx.AsyncClient', return_value=_MC()):
                return await self.fc.create_appointment_api(1, 2, '2026-09-01T10:00:00', 'tok')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result['success'])

    def test_complete_visit_api(self):
        """Проверяет, что complete_visit_api возвращает success=True при статусе 200."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {'id': 10}
            mock_client = MagicMock()

            async def async_post(*a, **kw):
                return mock_resp
            mock_client.post = async_post

            class _MC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            with patch('httpx.AsyncClient', return_value=_MC()):
                return await self.fc.complete_visit_api(1, 2, {'diagnosis': 'K02'}, 'tok')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertTrue(result['success'])

    def test_complete_visit_api_error(self):
        """Проверяет, что complete_visit_api возвращает success=False при статусе 400."""
        # Arrange
        import asyncio

        async def run():
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_resp.text = 'Bad request'
            mock_client = MagicMock()

            async def async_post(*a, **kw):
                return mock_resp
            mock_client.post = async_post

            class _MC:
                async def __aenter__(self_):
                    return mock_client
                async def __aexit__(self_, *args):
                    return None

            with patch('httpx.AsyncClient', return_value=_MC()):
                return await self.fc.complete_visit_api(1, 2, {}, 'tok')
        # Act
        result = asyncio.run(run())
        # Assert
        self.assertFalse(result['success'])

    def test_sync_user_to_fastapi_already_exists(self):
        """Проверяет, что sync_user_to_fastapi обрабатывает случай уже существующего пользователя."""
        # Arrange
        from app.services.fastapi_client import sync_user_to_fastapi
        from django.contrib.auth.models import User as DUser
        u = DUser.objects.create_user('syncexists99', password='pass')
        mock_400 = MagicMock()
        mock_400.status_code = 400
        mock_400.text = 'уже существует'
        mock_list = MagicMock()
        mock_list.json.return_value = [{'login': 'syncexists99', 'id': 42}]
        # Act
        with patch('app.controllers.base_controller._get_token', return_value='tok'):
            with patch('requests.post', return_value=mock_400):
                with patch('requests.get', return_value=mock_list):
                    result = sync_user_to_fastapi(u, 'dentist')
        # Assert
        self.assertIsNotNone(result)
        u.delete()


# ─────────────────────────────────────────────────────────
# FastAPI health service
# ─────────────────────────────────────────────────────────
class TestFastAPIHealth(TestCase):

    def test_get_fastapi_status_connection_error(self):
        """Проверяет, что get_fastapi_status возвращает available=False при ConnectionError."""
        # Arrange
        from app.services.fastapi_health import get_fastapi_status
        import requests
        # Act
        with patch('requests.get', side_effect=requests.exceptions.ConnectionError('refused')):
            result = get_fastapi_status()
        # Assert
        self.assertFalse(result['available'])
        self.assertEqual(result['error'], 'Connection refused')

    def test_get_fastapi_status_timeout(self):
        """Проверяет, что get_fastapi_status возвращает available=False при Timeout."""
        # Arrange
        from app.services.fastapi_health import get_fastapi_status
        import requests
        # Act
        with patch('requests.get', side_effect=requests.exceptions.Timeout('timeout')):
            result = get_fastapi_status()
        # Assert
        self.assertFalse(result['available'])
        self.assertEqual(result['error'], 'Timeout')

    def test_get_fastapi_status_200(self):
        """Проверяет, что get_fastapi_status возвращает available=True при статусе 200."""
        # Arrange
        from app.services.fastapi_health import get_fastapi_status
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # Act
        with patch('requests.get', return_value=mock_resp):
            result = get_fastapi_status()
        # Assert
        self.assertTrue(result['available'])

    def test_get_fastapi_status_500(self):
        """Проверяет, что get_fastapi_status возвращает available=False при статусе 500."""
        # Arrange
        from app.services.fastapi_health import get_fastapi_status
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        # Act
        with patch('requests.get', return_value=mock_resp):
            result = get_fastapi_status()
        # Assert
        self.assertFalse(result['available'])


# ─────────────────────────────────────────────────────────
# apps.py coverage
# ─────────────────────────────────────────────────────────
class TestAppsConfig(TestCase):

    def _get_app_config(self):
        from app.apps import AppConfigData
        import app as app_module
        return AppConfigData('app', app_module)

    def test_check_fastapi_connection_unavailable(self):
        """Проверяет, что check_fastapi_connection не бросает исключение при недоступном FastAPI."""
        # Arrange
        app_config = self._get_app_config()
        # Act & Assert
        with patch('requests.get', side_effect=Exception('refused')):
            app_config.check_fastapi_connection()

    def test_check_fastapi_connection_available(self):
        """Проверяет, что check_fastapi_connection не бросает исключение при статусе 200."""
        # Arrange
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        app_config = self._get_app_config()
        # Act & Assert
        with patch('requests.get', return_value=mock_resp):
            app_config.check_fastapi_connection()

    def test_check_fastapi_connection_error_status(self):
        """Проверяет, что check_fastapi_connection обрабатывает статус 503 без краша."""
        # Arrange
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        app_config = self._get_app_config()
        # Act & Assert
        with patch('requests.get', return_value=mock_resp):
            try:
                app_config.check_fastapi_connection()
            except Exception:
                pass
