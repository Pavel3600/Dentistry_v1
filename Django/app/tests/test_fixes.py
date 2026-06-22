"""Tests for fixes: FastAPI banner context processor, login gating,
newly added templates (mkb_form, fastapi_services)."""
import pytest
from django.urls import reverse
from django.core.cache import cache
from django.core.management import call_command


pytestmark = pytest.mark.django_db


# ──────────────────────────────────────────────────────────────────────────────
# seed_accounts management command
# ──────────────────────────────────────────────────────────────────────────────

class TestSeedAccounts:
    def test_creates_three_accounts_with_roles(self):
        """Команда seed_accounts создаёт трёх пользователей с корректными ролями."""
        # Act
        from django.contrib.auth.models import User
        call_command('seed_accounts')

        # Assert
        for login, role in [('admin', 'admin'), ('manager', 'manager'), ('dentist', 'dentist')]:
            user = User.objects.get(username=login)
            assert user.profile.role == role

    def test_passwords_are_usable(self):
        """seed_accounts устанавливает рабочие пароли для созданных пользователей."""
        # Act
        from django.contrib.auth import authenticate
        call_command('seed_accounts')

        # Assert
        assert authenticate(username='admin', password='admin123') is not None
        assert authenticate(username='dentist', password='dentist123') is not None

    def test_admin_is_superuser(self):
        """seed_accounts создаёт пользователя admin с флагом is_superuser."""
        # Act
        from django.contrib.auth.models import User
        call_command('seed_accounts')

        # Assert
        assert User.objects.get(username='admin').is_superuser

    def test_idempotent(self):
        """Повторный запуск seed_accounts не создаёт дублирующихся пользователей."""
        # Act
        from django.contrib.auth.models import User
        call_command('seed_accounts')
        call_command('seed_accounts')

        # Assert
        assert User.objects.filter(username='manager').count() == 1


# ──────────────────────────────────────────────────────────────────────────────
# Context processor — FastAPI banner
# ──────────────────────────────────────────────────────────────────────────────

class TestFastapiStatusContextProcessor:
    def setup_method(self):
        cache.clear()

    def test_online_true_when_available(self, mocker):
        """Контекстный процессор возвращает fastapi_online=True, когда FastAPI доступен."""
        # Arrange
        from app.context_processors import fastapi_status
        mocker.patch('app.context_processors.get_fastapi_status', return_value={'available': True})

        # Act & Assert
        assert fastapi_status(None) == {'fastapi_online': True}

    def test_online_false_when_unavailable(self, mocker):
        """Контекстный процессор возвращает fastapi_online=False, когда FastAPI недоступен."""
        # Arrange
        from app.context_processors import fastapi_status
        mocker.patch('app.context_processors.get_fastapi_status', return_value={'available': False})

        # Act & Assert
        assert fastapi_status(None) == {'fastapi_online': False}

    def test_result_is_cached(self, mocker):
        """Результат контекстного процессора кэшируется, повторный вызов не обращается к FastAPI."""
        # Arrange
        from app.context_processors import fastapi_status
        m = mocker.patch('app.context_processors.get_fastapi_status', return_value={'available': True})

        # Act
        fastapi_status(None)
        fastapi_status(None)

        # Assert
        assert m.call_count == 1  # второй вызов берётся из кэша


# ──────────────────────────────────────────────────────────────────────────────
# CustomLoginView — gating by FastAPI availability
# ──────────────────────────────────────────────────────────────────────────────

class TestLoginGating:
    def test_login_blocked_when_fastapi_down(self, client, user_dentist, mocker):
        """Вход в систему блокируется, если FastAPI недоступен."""
        # Arrange
        mocker.patch('app.views.is_fastapi_available', return_value=False)

        # Act
        r = client.post(reverse('login'), {'username': 'dentist_test', 'password': 'pass123'})

        # Assert
        assert r.status_code == 200  # не редирект — вход заблокирован
        assert '_auth_user_id' not in client.session

    def test_login_allowed_when_fastapi_up(self, client, user_dentist, mocker):
        """Вход в систему разрешён, когда FastAPI доступен."""
        # Arrange
        mocker.patch('app.views.is_fastapi_available', return_value=True)

        # Act
        r = client.post(reverse('login'), {'username': 'dentist_test', 'password': 'pass123'})

        # Assert
        assert r.status_code == 302


# ──────────────────────────────────────────────────────────────────────────────
# Newly added templates render
# ──────────────────────────────────────────────────────────────────────────────

class TestNewTemplates:
    def test_mkb_create_form_renders(self, client, user_admin):
        """Форма создания кода МКБ отображается без ошибок."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:mkb_create'))

        # Assert
        assert r.status_code == 200

    def test_mkb_edit_form_renders(self, client, user_admin, mkb):
        """Форма редактирования кода МКБ отображается без ошибок."""
        # Arrange
        client.force_login(user_admin)

        # Act
        r = client.get(reverse('app:mkb_edit', args=[mkb.pk]))

        # Assert
        assert r.status_code == 200

    def test_fastapi_services_page_renders(self, client, mocker):
        """Страница сервисов FastAPI отображается, даже если FastAPI недоступен."""
        # Act
        r = client.get(reverse('app:fastapi_services'))

        # Assert
        assert r.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# Appointment list / detail / cancel
# ──────────────────────────────────────────────────────────────────────────────

class TestAppointmentListAndCancel:
    def test_list_shows_patient_name(self, client, user_manager, appointment, patient):
        """Список записей содержит имя пациента."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:appointment_list'))

        # Assert
        assert r.status_code == 200
        assert patient.full_name in r.content.decode()

    def test_cancel_via_post_works(self, client, user_manager, appointment):
        """POST-запрос на отмену записи переводит её в статус cancelled."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.post(reverse('app:appointment_cancel', args=[appointment.pk]))

        # Assert
        assert r.status_code == 302
        appointment.refresh_from_db()
        assert appointment.status == 'cancelled'

    def test_cancel_via_get_not_allowed(self, client, user_manager, appointment):
        """GET-запрос на отмену записи не разрешён — возвращает 405."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:appointment_cancel', args=[appointment.pk]))

        # Assert
        assert r.status_code == 405  # отмена только POST


class TestAppointmentDetailWithVisit:
    def test_detail_with_visit_renders_report_links(self, client, user_dentist, appointment, visit):
        """Страница детали записи с визитом содержит ссылки на выписку и отчёт."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:appointment_detail', args=[appointment.pk]))

        # Assert
        assert r.status_code == 200
        body = r.content.decode()
        assert reverse('app:create_extract', args=[visit.pk]) in body
        assert reverse('app:visit_report', args=[visit.pk]) in body


class TestAppointmentActions:
    def test_complete_redirects_to_visit_form(self, client, user_manager, appointment):
        """Попытка завершить запись без визита перенаправляет на форму ввода медданных."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.post(reverse('app:appointment_change_status', args=[appointment.pk]),
                        {'status': 'completed'})

        # Assert
        assert r.status_code == 302
        assert reverse('app:start_visit', args=[appointment.pk]) in r.url
        appointment.refresh_from_db()
        assert appointment.status == 'scheduled'  # ещё не завершён — данные не введены

    def test_complete_via_visit_form_sets_completed(self, client, user_dentist, appointment, mkb):
        """Заполнение формы визита переводит запись в статус completed и создаёт Visit."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:start_visit', args=[appointment.pk]), {
            'anamnesis': 'боль', 'examination_results': 'кариес',
            'diagnosis': mkb.id, 'treatment_plan': 'пломба', 'prescription': 'анальгин',
            'tooth_formula': '46',
        })

        # Assert
        assert r.status_code == 302
        appointment.refresh_from_db()
        assert appointment.status == 'completed'
        from app.models import Visit
        assert Visit.objects.filter(appointment=appointment).exists()

    def test_complete_visit_form_renders(self, client, user_dentist, appointment, mkb):
        """GET-запрос на форму визита отображает страницу с кодом МКБ в выпадающем списке."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:start_visit', args=[appointment.pk]))

        # Assert
        assert r.status_code == 200
        assert mkb.code in r.content.decode()

    def test_change_status_creates_log(self, client, user_manager, appointment):
        """Смена статуса записи создаёт запись в журнале AppointmentLog."""
        # Arrange
        from app.models import AppointmentLog
        client.force_login(user_manager)

        # Act
        client.post(reverse('app:appointment_change_status', args=[appointment.pk]),
                    {'status': 'cancelled'})

        # Assert
        assert AppointmentLog.objects.filter(appointment=appointment, new_status='cancelled').exists()

    def test_change_status_invalid_rejected(self, client, user_manager, appointment):
        """Смена статуса на недопустимое значение не изменяет статус записи."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.post(reverse('app:appointment_change_status', args=[appointment.pk]),
                        {'status': 'bogus'})

        # Assert
        assert r.status_code == 302
        appointment.refresh_from_db()
        assert appointment.status == 'scheduled'  # не изменился

    def test_delete_appointment(self, client, user_manager, appointment):
        """Менеджер может удалить запись на приём."""
        # Arrange
        from app.models import Appointment
        client.force_login(user_manager)

        # Act
        r = client.post(reverse('app:appointment_delete', args=[appointment.pk]))

        # Assert
        assert r.status_code == 302
        assert not Appointment.objects.filter(pk=appointment.pk).exists()

    def test_delete_cascades_visit(self, client, user_manager, appointment, visit):
        """Удаление записи на приём каскадно удаляет связанный визит."""
        # Arrange
        from app.models import Appointment, Visit
        client.force_login(user_manager)

        # Act
        client.post(reverse('app:appointment_delete', args=[appointment.pk]))

        # Assert
        assert not Appointment.objects.filter(pk=appointment.pk).exists()
        assert not Visit.objects.filter(pk=visit.pk).exists()

    def test_dentist_cannot_change_status(self, client, user_dentist, appointment):
        """Стоматолог не может менять статус записи — доступ запрещён."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:appointment_change_status', args=[appointment.pk]),
                        {'status': 'completed'})

        # Assert
        assert r.status_code in (302, 403)  # не менеджер/админ

    def test_manager_can_write_report(self, client, user_manager, visit):
        """Менеджер может открыть страницу отчёта по визиту."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:visit_report', args=[visit.pk]))

        # Assert
        assert r.status_code == 200

    def test_list_shows_status_filter(self, client, user_manager, appointment):
        """Фильтрация списка записей по статусу возвращает страницу без ошибок."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:appointment_list'), {'status': 'scheduled'})

        # Assert
        assert r.status_code == 200


class TestExtractDownload:
    def test_dentist_can_download_extract(self, client, user_dentist, visit):
        """Стоматолог может скачать выписку в формате Word."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:create_extract', args=[visit.pk]))

        # Assert
        assert r.status_code == 200
        assert 'wordprocessingml' in r['Content-Type']

    def test_manager_can_download_extract(self, client, user_manager, visit):
        """Менеджер может скачать выписку по визиту."""
        # Arrange
        client.force_login(user_manager)

        # Act
        r = client.get(reverse('app:create_extract', args=[visit.pk]))

        # Assert
        assert r.status_code == 200

    def test_patient_can_download_own_extract(self, client, user_patient, patient, visit):
        """Пациент может скачать выписку по своему визиту."""
        # Arrange
        patient.user_id = user_patient.id
        patient.save()
        client.force_login(user_patient)

        # Act
        r = client.get(reverse('app:create_extract', args=[visit.pk]))

        # Assert
        assert r.status_code == 200

    def test_patient_cannot_download_foreign_extract(self, client, visit):
        """Пациент не может скачать выписку по чужому визиту — возвращается 403."""
        # Arrange
        from django.contrib.auth.models import User
        other = User.objects.create_user(username='other_patient', password='x')
        other.profile.role = 'patient'
        other.profile.save()
        client.force_login(other)

        # Act
        r = client.get(reverse('app:create_extract', args=[visit.pk]))

        # Assert
        assert r.status_code == 403


class TestVisitReportEditDelete:
    def _make_report(self, visit, user):
        from app.models import VisitReport
        return VisitReport.objects.create(visit=visit, author=user, summary='старое')

    def test_edit_form_renders(self, client, user_dentist, visit):
        """Форма редактирования отчёта по визиту отображается без ошибок."""
        # Arrange
        report = self._make_report(visit, user_dentist)
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:report_edit', args=[report.pk]))

        # Assert
        assert r.status_code == 200

    def test_edit_updates_report(self, client, user_dentist, visit):
        """Отправка формы редактирования обновляет содержимое отчёта."""
        # Arrange
        report = self._make_report(visit, user_dentist)
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:report_edit', args=[report.pk]),
                        {'title': 'Отчёт', 'summary': 'новое', 'recommendations': '', 'complications': ''})

        # Assert
        assert r.status_code == 302
        report.refresh_from_db()
        assert report.summary == 'новое'

    def test_delete_report(self, client, user_dentist, visit):
        """Стоматолог может удалить собственный отчёт по визиту."""
        # Arrange
        from app.models import VisitReport
        report = self._make_report(visit, user_dentist)
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:report_delete', args=[report.pk]))

        # Assert
        assert r.status_code == 302
        assert not VisitReport.objects.filter(pk=report.pk).exists()

    def test_patient_cannot_delete_report(self, client, user_patient, visit, user_dentist):
        """Пациент не может удалить отчёт по визиту."""
        # Arrange
        report = self._make_report(visit, user_dentist)
        client.force_login(user_patient)

        # Act
        r = client.post(reverse('app:report_delete', args=[report.pk]))

        # Assert
        assert r.status_code in (302, 403)


class TestApiParityEndpoints:
    """REST-эндпоинты, добавленные для паритета с FastAPI."""

    def test_studies_crud(self, dentist_client, patient):
        """Стоматолог может создать и получить список исследований пациента через API."""
        # Act — создаём исследование
        r = dentist_client.post('/api/v2/studies/', {
            'patient_id': patient.id, 'study_type': 'Рентген', 'result': 'норма',
        }, format='json')

        # Assert — исследование создано
        assert r.status_code == 201

        # Act — получаем список
        r2 = dentist_client.get('/api/v2/studies/', {'patient_id': patient.id})

        # Assert — список доступен
        assert r2.status_code == 200

    def test_studies_patient_forbidden(self, patient_client):
        """Пациент не имеет доступа к списку исследований через API."""
        # Act
        r = patient_client.get('/api/v2/studies/')

        # Assert
        assert r.status_code == 403

    def test_referrals_create(self, dentist_client, patient, user_dentist):
        """Стоматолог может создать направление к специалисту через API."""
        # Act
        r = dentist_client.post('/api/v2/referrals/', {
            'patient_id': patient.id, 'doctor_id': user_dentist.profile.id,
            'to_specialist': 'Ортодонт', 'reason': 'консультация',
        }, format='json')

        # Assert
        assert r.status_code == 201

    def test_work_orders_create(self, dentist_client, patient, user_dentist):
        """Стоматолог может создать наряд-заказ через API."""
        # Act
        r = dentist_client.post('/api/v2/work-orders/', {
            'patient_id': patient.id, 'doctor_id': user_dentist.profile.id,
            'manipulations': 'пломбирование', 'materials': 'композит', 'labor_cost': 1500,
        }, format='json')

        # Assert
        assert r.status_code == 201

    def test_mkbs_validate_known_code(self, dentist_client):
        """Валидация известного кода МКБ возвращает valid=True."""
        # Act
        r = dentist_client.get('/api/v2/mkbs/validate/K02.0/')

        # Assert
        assert r.status_code == 200
        assert r.json()['valid'] is True

    def test_mkbs_validate_unknown_code(self, dentist_client):
        """Валидация неизвестного кода МКБ возвращает valid=False."""
        # Act
        r = dentist_client.get('/api/v2/mkbs/validate/Z99.9/')

        # Assert
        assert r.status_code == 200
        assert r.json()['valid'] is False

    def test_me_endpoint(self, dentist_client):
        """Эндпоинт /me/ возвращает роль текущего авторизованного пользователя."""
        # Act
        r = dentist_client.get('/api/v2/me/')

        # Assert
        assert r.status_code == 200
        assert r.json()['role'] == 'dentist'

    def test_me_requires_auth(self, api_client):
        """Эндпоинт /me/ требует аутентификации — анонимный запрос отклоняется."""
        # Act
        r = api_client.get('/api/v2/me/')

        # Assert
        assert r.status_code in (401, 403)


class TestDiagnosisFromMkb:
    def test_detail_renders_diagnosis_datalist(self, client, user_dentist, appointment, mkb):
        """Страница детали записи содержит список диагнозов МКБ для выбора."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.get(reverse('app:appointment_detail', args=[appointment.pk]))

        # Assert
        assert r.status_code == 200
        body = r.content.decode()
        assert 'mkbDiagnoses' in body
        assert mkb.code in body  # код МКБ есть в выпадающем списке

    def test_start_visit_saves_diagnosis_fk(self, client, user_dentist, appointment, mkb):
        """При создании визита диагноз МКБ сохраняется как внешний ключ."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:start_visit', args=[appointment.pk]), {
            'anamnesis': 'боль', 'examination_results': 'кариес',
            'diagnosis': mkb.id, 'treatment_plan': 'пломба', 'tooth_formula': '46',
        })

        # Assert
        assert r.status_code == 302
        from app.models import Visit
        visit = Visit.objects.get(appointment=appointment)
        assert visit.diagnosis_id == mkb.id

    def test_start_visit_without_diagnosis_ok(self, client, user_dentist, appointment):
        """Визит можно создать без указания диагноза — поле diagnosis остаётся None."""
        # Arrange
        client.force_login(user_dentist)

        # Act
        r = client.post(reverse('app:start_visit', args=[appointment.pk]), {
            'anamnesis': 'боль', 'examination_results': 'осмотр',
        })

        # Assert
        assert r.status_code == 302
        from app.models import Visit
        visit = Visit.objects.get(appointment=appointment)
        assert visit.diagnosis_id is None
