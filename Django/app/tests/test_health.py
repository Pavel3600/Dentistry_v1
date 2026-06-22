"""Tests for FastAPI health check service and permissions."""
import pytest
import requests as req

from app.services.fastapi_health import get_fastapi_status, require_fastapi
from app.api.permissions import (
    IsAdminRole, IsManagerOrAdmin, IsDentistOrAdmin,
    IsManagerDentistOrAdmin, ReadOnlyOrAdmin, _role,
)


# ──────────────────────────────────────────────────────────────────────────────
# get_fastapi_status
# ──────────────────────────────────────────────────────────────────────────────

class TestGetFastapiStatus:
    def test_available_when_200(self, mocker):
        """Статус FastAPI помечается как доступный при HTTP 200."""
        # Arrange
        mock = mocker.MagicMock()
        mock.status_code = 200
        mocker.patch('app.services.fastapi_health.requests.get', return_value=mock)

        # Act
        result = get_fastapi_status()

        # Assert
        assert result['available'] is True
        assert result['status_code'] == 200
        assert result['error'] is None

    def test_available_false_on_500(self, mocker):
        """Статус FastAPI помечается как недоступный при HTTP 500."""
        # Arrange
        mock = mocker.MagicMock()
        mock.status_code = 500
        mocker.patch('app.services.fastapi_health.requests.get', return_value=mock)

        # Act
        result = get_fastapi_status()

        # Assert
        assert result['available'] is False

    def test_connection_refused(self, mocker):
        """При ConnectionError статус содержит available=False и сообщение об отказе соединения."""
        # Arrange
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=req.exceptions.ConnectionError(),
        )

        # Act
        result = get_fastapi_status()

        # Assert
        assert result['available'] is False
        assert result['error'] == 'Connection refused'

    def test_timeout(self, mocker):
        """При Timeout статус содержит available=False и сообщение о таймауте."""
        # Arrange
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=req.exceptions.Timeout(),
        )

        # Act
        result = get_fastapi_status()

        # Assert
        assert result['available'] is False
        assert result['error'] == 'Timeout'

    def test_generic_exception(self, mocker):
        """При произвольном исключении статус содержит текст ошибки в поле error."""
        # Arrange
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=Exception('weird error'),
        )

        # Act
        result = get_fastapi_status()

        # Assert
        assert result['available'] is False
        assert 'weird error' in result['error']

    def test_response_time_measured(self, mocker):
        """Статус FastAPI включает измеренное время ответа в миллисекундах."""
        # Arrange
        mock = mocker.MagicMock()
        mock.status_code = 200
        mocker.patch('app.services.fastapi_health.requests.get', return_value=mock)

        # Act
        result = get_fastapi_status()

        # Assert
        assert result['response_time_ms'] is not None
        assert result['response_time_ms'] >= 0

    def test_url_in_result(self, mocker, settings):
        """Статус FastAPI содержит URL, взятый из настройки FASTAPI_URL."""
        # Arrange
        settings.FASTAPI_URL = 'http://test-api:9000'
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=req.exceptions.ConnectionError(),
        )

        # Act
        result = get_fastapi_status()

        # Assert
        assert result['url'] == 'http://test-api:9000'


# ──────────────────────────────────────────────────────────────────────────────
# require_fastapi decorator
# ──────────────────────────────────────────────────────────────────────────────

class TestRequireFastapi:
    def test_passes_through_when_available(self, mocker):
        """Декоратор require_fastapi пропускает вызов метода, когда FastAPI доступен."""
        # Arrange
        mock = mocker.MagicMock()
        mock.status_code = 200
        mocker.patch('app.services.fastapi_health.requests.get', return_value=mock)

        called = []

        class FakeView:
            @require_fastapi
            def my_action(self, request):
                called.append(True)
                from rest_framework.response import Response
                return Response({'ok': True})

        # Act
        FakeView().my_action(mocker.MagicMock())

        # Assert
        assert called

    def test_blocks_when_unavailable(self, mocker):
        """Декоратор require_fastapi возвращает 503, когда FastAPI недоступен."""
        # Arrange
        mocker.patch(
            'app.services.fastapi_health.requests.get',
            side_effect=req.exceptions.ConnectionError(),
        )

        class FakeView:
            @require_fastapi
            def my_action(self, request):
                raise AssertionError("Should not reach here")

        # Act
        resp = FakeView().my_action(mocker.MagicMock())

        # Assert
        assert resp.status_code == 503
        assert 'FastAPI' in str(resp.data.get('error', ''))


# ──────────────────────────────────────────────────────────────────────────────
# Permissions
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPermissions:
    def _make_request(self, mocker, user):
        req_mock = mocker.MagicMock()
        req_mock.user = user
        req_mock.method = 'GET'
        return req_mock

    def test_role_helper_returns_role(self, user_admin):
        """Вспомогательная функция _role возвращает роль из профиля пользователя."""
        # Arrange
        # (объект user_admin создан фикстурой)

        # Act & Assert
        assert _role(user_admin) == 'admin'

    def test_role_helper_defaults_to_patient(self, mocker):
        """Функция _role возвращает patient, если у пользователя нет профиля."""
        # Arrange
        user = mocker.MagicMock()
        del user.profile

        # Act & Assert
        assert _role(user) == 'patient'

    def test_admin_role_allows_admin(self, mocker, user_admin):
        """Разрешение IsAdminRole пропускает пользователя с ролью admin."""
        # Arrange
        perm = IsAdminRole()

        # Act & Assert
        assert perm.has_permission(self._make_request(mocker, user_admin), None)

    def test_admin_role_denies_manager(self, mocker, user_manager):
        """Разрешение IsAdminRole запрещает пользователя с ролью manager."""
        # Arrange
        perm = IsAdminRole()

        # Act & Assert
        assert not perm.has_permission(self._make_request(mocker, user_manager), None)

    def test_manager_or_admin_allows_manager(self, mocker, user_manager):
        """Разрешение IsManagerOrAdmin пропускает пользователя с ролью manager."""
        # Arrange
        perm = IsManagerOrAdmin()

        # Act & Assert
        assert perm.has_permission(self._make_request(mocker, user_manager), None)

    def test_manager_or_admin_allows_admin(self, mocker, user_admin):
        """Разрешение IsManagerOrAdmin пропускает пользователя с ролью admin."""
        # Arrange
        perm = IsManagerOrAdmin()

        # Act & Assert
        assert perm.has_permission(self._make_request(mocker, user_admin), None)

    def test_manager_or_admin_denies_dentist(self, mocker, user_dentist):
        """Разрешение IsManagerOrAdmin запрещает пользователя с ролью dentist."""
        # Arrange
        perm = IsManagerOrAdmin()

        # Act & Assert
        assert not perm.has_permission(self._make_request(mocker, user_dentist), None)

    def test_dentist_or_admin_allows_dentist(self, mocker, user_dentist):
        """Разрешение IsDentistOrAdmin пропускает пользователя с ролью dentist."""
        # Arrange
        perm = IsDentistOrAdmin()

        # Act & Assert
        assert perm.has_permission(self._make_request(mocker, user_dentist), None)

    def test_manager_dentist_or_admin_allows_all_privileged(self, mocker, user_manager, user_dentist, user_admin):
        """Разрешение IsManagerDentistOrAdmin пропускает manager, dentist и admin."""
        # Arrange
        perm = IsManagerDentistOrAdmin()

        # Act & Assert
        for user in (user_manager, user_dentist, user_admin):
            assert perm.has_permission(self._make_request(mocker, user), None)

    def test_manager_dentist_or_admin_denies_patient(self, mocker, user_patient):
        """Разрешение IsManagerDentistOrAdmin запрещает пользователя с ролью patient."""
        # Arrange
        perm = IsManagerDentistOrAdmin()

        # Act & Assert
        assert not perm.has_permission(self._make_request(mocker, user_patient), None)

    def test_read_only_or_admin_allows_safe_method_for_any(self, mocker, user_manager):
        """Разрешение ReadOnlyOrAdmin пропускает GET-запрос для любого пользователя."""
        # Arrange
        perm = ReadOnlyOrAdmin()
        req_mock = self._make_request(mocker, user_manager)
        req_mock.method = 'GET'

        # Act & Assert
        assert perm.has_permission(req_mock, None)

    def test_read_only_or_admin_denies_write_for_non_admin(self, mocker, user_manager):
        """Разрешение ReadOnlyOrAdmin запрещает POST-запрос для не-администратора."""
        # Arrange
        perm = ReadOnlyOrAdmin()
        req_mock = self._make_request(mocker, user_manager)
        req_mock.method = 'POST'

        # Act & Assert
        assert not perm.has_permission(req_mock, None)

    def test_read_only_or_admin_allows_write_for_admin(self, mocker, user_admin):
        """Разрешение ReadOnlyOrAdmin пропускает POST-запрос для администратора."""
        # Arrange
        perm = ReadOnlyOrAdmin()
        req_mock = self._make_request(mocker, user_admin)
        req_mock.method = 'POST'

        # Act & Assert
        assert perm.has_permission(req_mock, None)
