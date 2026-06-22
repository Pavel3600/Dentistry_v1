"""Tests for app/services/fastapi_client.py — FastAPIClient and sync helpers."""
import pytest

from app.services.fastapi_client import FastAPIClient, sync_user_to_fastapi


# ──────────────────────────────────────────────────────────────────────────────
# is_available_sync
# ──────────────────────────────────────────────────────────────────────────────

class TestIsAvailableSync:
    def test_returns_true_on_200(self, mocker):
        """Синхронная проверка доступности возвращает True при ответе 200."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mocker.patch('requests.get', return_value=mock_resp)
        client = FastAPIClient()

        # Act / Assert
        assert client.is_available_sync() is True

    def test_returns_false_on_non_200(self, mocker):
        """Синхронная проверка доступности возвращает False при ответе не 200."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 503
        mocker.patch('requests.get', return_value=mock_resp)
        client = FastAPIClient()

        # Act / Assert
        assert client.is_available_sync() is False

    def test_returns_false_on_exception(self, mocker):
        """Синхронная проверка доступности возвращает False при любом исключении."""
        # Arrange
        mocker.patch('requests.get', side_effect=Exception('down'))
        client = FastAPIClient()

        # Act / Assert
        assert client.is_available_sync() is False


# ──────────────────────────────────────────────────────────────────────────────
# get_status_sync
# ──────────────────────────────────────────────────────────────────────────────

class TestGetStatusSync:
    def test_online_status(self, mocker):
        """При ответе 200 статус содержит online=True, url и message."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mocker.patch('requests.get', return_value=mock_resp)
        client = FastAPIClient()

        # Act
        status = client.get_status_sync()

        # Assert
        assert status['online'] is True
        assert 'url' in status
        assert 'message' in status

    def test_offline_status(self, mocker):
        """При исключении статус содержит online=False и сообщение «НЕ ДОСТУПЕН»."""
        # Arrange
        mocker.patch('requests.get', side_effect=Exception())
        client = FastAPIClient()

        # Act
        status = client.get_status_sync()

        # Assert
        assert status['online'] is False
        assert 'НЕ ДОСТУПЕН' in status['message']

    def test_url_in_status(self, mocker, settings):
        """Статус содержит URL, соответствующий FASTAPI_URL из настроек."""
        # Arrange
        settings.FASTAPI_URL = 'http://test:8888'
        mocker.patch('requests.get', side_effect=Exception())
        client = FastAPIClient()
        client.base_url = 'http://test:8888'

        # Act
        status = client.get_status_sync()

        # Assert
        assert status['url'] == 'http://test:8888'


# ──────────────────────────────────────────────────────────────────────────────
# async: _check_availability
# ──────────────────────────────────────────────────────────────────────────────

class TestCheckAvailability:
    async def test_available_on_200(self, mocker):
        """Асинхронная проверка возвращает True и устанавливает _is_available=True при ответе 200."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200

        mock_client = mocker.AsyncMock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_client.get = mocker.AsyncMock(return_value=mock_resp)

        mocker.patch('app.services.fastapi_client.httpx.AsyncClient', return_value=mock_client)

        client = FastAPIClient()

        # Act
        result = await client._check_availability()

        # Assert
        assert result is True
        assert client._is_available is True

    async def test_unavailable_on_connect_error(self, mocker):
        """Асинхронная проверка возвращает False и устанавливает _is_available=False при ConnectError."""
        # Arrange
        import httpx

        mock_client = mocker.AsyncMock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_client.get = mocker.AsyncMock(side_effect=httpx.ConnectError('refused'))

        mocker.patch('app.services.fastapi_client.httpx.AsyncClient', return_value=mock_client)

        client = FastAPIClient()

        # Act
        result = await client._check_availability()

        # Assert
        assert result is False
        assert client._is_available is False


# ──────────────────────────────────────────────────────────────────────────────
# async: is_available
# ──────────────────────────────────────────────────────────────────────────────

class TestIsAvailable:
    async def test_caches_true_in_django_cache(self, mocker):
        """При успешной проверке результат True кэшируется в Django cache под ключом fastapi_status."""
        # Arrange
        from django.core.cache import cache
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200

        mock_client = mocker.AsyncMock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_client.get = mocker.AsyncMock(return_value=mock_resp)

        mocker.patch('app.services.fastapi_client.httpx.AsyncClient', return_value=mock_client)
        client = FastAPIClient()

        # Act
        result = await client.is_available(force_check=True)

        # Assert
        assert result is True
        assert cache.get('fastapi_status') is True

    async def test_caches_false_in_django_cache(self, mocker):
        """При неудачной проверке результат False кэшируется в Django cache под ключом fastapi_status."""
        # Arrange
        import httpx
        from django.core.cache import cache

        mock_client = mocker.AsyncMock()
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_client.get = mocker.AsyncMock(side_effect=httpx.ConnectError('x'))

        mocker.patch('app.services.fastapi_client.httpx.AsyncClient', return_value=mock_client)
        client = FastAPIClient()

        # Act
        result = await client.is_available(force_check=True)

        # Assert
        assert result is False
        assert cache.get('fastapi_status') is False


# ──────────────────────────────────────────────────────────────────────────────
# async: get_patients (unavailable path)
# ──────────────────────────────────────────────────────────────────────────────

class TestGetPatients:
    async def test_returns_error_when_unavailable(self, mocker):
        """Если FastAPI недоступен, get_patients возвращает success=False и пустой data."""
        # Arrange
        client = FastAPIClient()
        mocker.patch.object(client, 'is_available', mocker.AsyncMock(return_value=False))

        # Act
        result = await client.get_patients()

        # Assert
        assert result['success'] is False
        assert result['data'] == []
        assert 'недоступен' in result['error']

    async def test_returns_data_on_success(self, mocker):
        """При успешном ответе 200 get_patients возвращает success=True и список пациентов."""
        # Arrange
        patients_data = {'items': [{'id': 1, 'full_name': 'Иванов'}]}
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = patients_data

        mock_http = mocker.AsyncMock()
        mock_http.__aenter__ = mocker.AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_http.get = mocker.AsyncMock(return_value=mock_resp)
        mock_http.post = mocker.AsyncMock(return_value=mocker.MagicMock(status_code=401))

        mocker.patch('app.services.fastapi_client.httpx.AsyncClient', return_value=mock_http)

        client = FastAPIClient()
        mocker.patch.object(client, 'is_available', mocker.AsyncMock(return_value=True))
        mocker.patch.object(client, '_get_token', mocker.AsyncMock(return_value='tok'))

        # Act
        result = await client.get_patients(token='tok')

        # Assert
        assert result['success'] is True
        assert len(result['data']) == 1

    async def test_returns_error_on_non_200(self, mocker):
        """При ответе не 200 get_patients возвращает success=False."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 403

        mock_http = mocker.AsyncMock()
        mock_http.__aenter__ = mocker.AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_http.get = mocker.AsyncMock(return_value=mock_resp)

        mocker.patch('app.services.fastapi_client.httpx.AsyncClient', return_value=mock_http)

        client = FastAPIClient()
        mocker.patch.object(client, 'is_available', mocker.AsyncMock(return_value=True))
        mocker.patch.object(client, '_get_token', mocker.AsyncMock(return_value='tok'))

        # Act
        result = await client.get_patients(token='tok')

        # Assert
        assert result['success'] is False


# ──────────────────────────────────────────────────────────────────────────────
# async: get_appointments
# ──────────────────────────────────────────────────────────────────────────────

class TestGetAppointments:
    async def test_returns_error_when_unavailable(self, mocker):
        """Если FastAPI недоступен, get_appointments возвращает success=False."""
        # Arrange
        client = FastAPIClient()
        mocker.patch.object(client, 'is_available', mocker.AsyncMock(return_value=False))

        # Act
        result = await client.get_appointments()

        # Assert
        assert result['success'] is False

    async def test_returns_data_on_200(self, mocker):
        """При ответе 200 get_appointments возвращает success=True."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{'id': 1}]

        mock_http = mocker.AsyncMock()
        mock_http.__aenter__ = mocker.AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_http.get = mocker.AsyncMock(return_value=mock_resp)

        mocker.patch('app.services.fastapi_client.httpx.AsyncClient', return_value=mock_http)

        client = FastAPIClient()
        mocker.patch.object(client, 'is_available', mocker.AsyncMock(return_value=True))
        mocker.patch.object(client, '_get_token', mocker.AsyncMock(return_value='tok'))

        # Act
        result = await client.get_appointments(token='tok')

        # Assert
        assert result['success'] is True


# ──────────────────────────────────────────────────────────────────────────────
# async: get_services
# ──────────────────────────────────────────────────────────────────────────────

class TestGetServices:
    async def test_unavailable_returns_error(self, mocker):
        """Если FastAPI недоступен, get_services возвращает success=False."""
        # Arrange
        client = FastAPIClient()
        mocker.patch.object(client, 'is_available', mocker.AsyncMock(return_value=False))

        # Act
        result = await client.get_services()

        # Assert
        assert result['success'] is False

    async def test_200_returns_data(self, mocker):
        """При ответе 200 get_services возвращает success=True."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{'code': 'S001'}]

        mock_http = mocker.AsyncMock()
        mock_http.__aenter__ = mocker.AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = mocker.AsyncMock(return_value=False)
        mock_http.get = mocker.AsyncMock(return_value=mock_resp)

        mocker.patch('app.services.fastapi_client.httpx.AsyncClient', return_value=mock_http)

        client = FastAPIClient()
        mocker.patch.object(client, 'is_available', mocker.AsyncMock(return_value=True))
        mocker.patch.object(client, '_get_token', mocker.AsyncMock(return_value='tok'))

        # Act
        result = await client.get_services()

        # Assert
        assert result['success'] is True


# ──────────────────────────────────────────────────────────────────────────────
# sync_user_to_fastapi
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSyncUserToFastapi:
    def test_returns_false_when_fastapi_down(self, mocker):
        """Если FastAPI недоступен (исключение), синхронизация возвращает False."""
        # Arrange
        mocker.patch('requests.post', side_effect=Exception('refused'))
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='sync_test_u1', password='x')

        # Act
        result = sync_user_to_fastapi(user, 'dentist')

        # Assert
        assert result is False

    def test_returns_true_on_200(self, mocker):
        """При успешном ответе 200 синхронизация возвращает True."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mocker.patch('requests.post', return_value=mock_resp)
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='sync_test_u2', password='x')

        # Act
        result = sync_user_to_fastapi(user, 'manager')

        # Assert
        assert result is True

    def test_returns_false_on_non_200(self, mocker):
        """При ответе не 200 синхронизация возвращает False."""
        # Arrange
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 404
        mocker.patch('requests.post', return_value=mock_resp)
        from django.contrib.auth.models import User
        user = User.objects.create_user(username='sync_test_u3', password='x')

        # Act
        result = sync_user_to_fastapi(user, 'admin')

        # Assert
        assert result is False
