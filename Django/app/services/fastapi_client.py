import httpx
import asyncio
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class FastAPIClient:
    """Клиент для работы с FastAPI с автоматическим определением статуса"""

    def __init__(self):
        self.base_url = getattr(settings, 'FASTAPI_URL', 'http://localhost:8000')
        self.timeout = 5.0
        self._is_available = None

        # Тестовые учетные данные для FastAPI (из вашего README)
        self.test_credentials = {
            'admin': {'username': 'admin', 'password': 'admin123'},
            'manager': {'username': 'manager', 'password': 'manager123'},
            'dentist': {'username': 'dentist', 'password': 'dentist123'},
        }
        self._cached_token = None
        self._token_expiry = None

    async def _get_token(self, role: str = 'dentist') -> Optional[str]:
        """Получить JWT токен для доступа к FastAPI"""
        import time

        # Проверяем кэшированный токен
        if self._cached_token and self._token_expiry and time.time() < self._token_expiry:
            return self._cached_token

        creds = self.test_credentials.get(role, self.test_credentials['dentist'])

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/auth/login",
                    data={
                        'username': creds['username'],
                        'password': creds['password']
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    self._cached_token = data.get('access_token')
                    self._token_expiry = time.time() + 3500  # ~58 минут
                    return self._cached_token
        except Exception as e:
            logger.error(f"Ошибка получения токена: {e}")

        return None

    async def _check_availability(self) -> bool:
        """Проверяет, доступен ли FastAPI"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/")
                if response.status_code == 200:
                    self._is_available = True
                    return True
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError) as e:
            logger.warning(f"FastAPI недоступен: {e}")

        self._is_available = False
        return False

    async def is_available(self, force_check: bool = False) -> bool:
        """Возвращает статус доступности FastAPI (с кэшированием)"""
        if force_check or self._is_available is None:
            await self._check_availability()

        if self._is_available:
            cache.set('fastapi_status', True, 10)
        else:
            cache.set('fastapi_status', False, 5)

        return self._is_available

    def is_available_sync(self) -> bool:
        """Синхронная версия проверки доступности"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/", timeout=3)
            if response.status_code == 200:
                cache.set('fastapi_status', True, 10)
                return True
        except Exception:
            cache.set('fastapi_status', False, 5)
            return False
        return False

    async def get_patients(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Получить список пациентов из FastAPI"""
        if not await self.is_available():
            return {
                'success': False,
                'error': 'FastAPI сервер недоступен',
                'data': []
            }

        try:
            # Получаем токен, если не передан
            if not token:
                token = await self._get_token('manager')

            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v2/patients/?limit=100",
                    headers=headers
                )

                if response.status_code == 200:
                    data = response.json()
                    # Обрабатываем пагинированный ответ Page
                    items = data.get('items', data) if isinstance(data, dict) else data
                    return {
                        'success': True,
                        'data': items if isinstance(items, list) else [],
                        'error': None
                    }
                else:
                    return {
                        'success': False,
                        'error': f'FastAPI вернул ошибку {response.status_code}',
                        'data': []
                    }
        except Exception as e:
            logger.error(f"Ошибка при запросе к FastAPI: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    async def get_appointments(self, token: Optional[str] = None) -> Dict[str, Any]:
        """Получить список записей из FastAPI"""
        if not await self.is_available():
            return {'success': False, 'error': 'FastAPI сервер недоступен', 'data': []}

        try:
            if not token:
                token = await self._get_token('manager')

            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v2/appointments/?limit=100",
                    headers=headers
                )

                if response.status_code == 200:
                    return {'success': True, 'data': response.json(), 'error': None}
                else:
                    return {'success': False, 'error': f'FastAPI вернул ошибку {response.status_code}', 'data': []}
        except Exception as e:
            return {'success': False, 'error': str(e), 'data': []}

    async def get_mkbs_codes(self, search: Optional[str] = None) -> Dict[str, Any]:
        """Получить коды МКБ из FastAPI"""
        if not await self.is_available():
            return {'success': False, 'error': 'FastAPI сервер недоступен', 'data': []}

        try:
            # Для МКБ используем роль dentist
            token = await self._get_token('dentist')

            url = f"{self.base_url}/api/v2/mkbs/diagnoses"
            if search:
                url += f"?search={search}"

            headers = {'Authorization': f'Bearer {token}'} if token else {}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return {'success': True, 'data': response.json(), 'error': None}
                else:
                    return {'success': False, 'error': f'FastAPI вернул ошибку {response.status_code}', 'data': []}
        except Exception as e:
            return {'success': False, 'error': str(e), 'data': []}

    async def get_services(self) -> Dict[str, Any]:
        """Получить услуги из FastAPI"""
        if not await self.is_available():
            return {'success': False, 'error': 'FastAPI сервер недоступен', 'data': []}

        try:
            # Для услуг используем роль dentist
            token = await self._get_token('dentist')

            url = f"{self.base_url}/api/v2/mkbs/services"
            headers = {'Authorization': f'Bearer {token}'} if token else {}

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    return {'success': True, 'data': response.json(), 'error': None}
                else:
                    return {'success': False, 'error': f'FastAPI вернул ошибку {response.status_code}', 'data': []}
        except Exception as e:
            return {'success': False, 'error': str(e), 'data': []}

    def get_status_sync(self) -> Dict[str, Any]:
        """Синхронное получение статуса (для использования в шаблонах)"""
        is_online = self.is_available_sync()
        return {
            'online': is_online,
            'url': self.base_url,
            'message': 'FastAPI работает' if is_online else 'FastAPI НЕ ДОСТУПЕН'
        }

    async def create_appointment_api(self, patient_id: int, doctor_id: int, datetime_str: str, token: str) -> Dict[
        str, Any]:
        """Создание записи через FastAPI"""
        headers = {'Authorization': f'Bearer {token}'}
        payload = {"patient_id": patient_id, "doctor_id": doctor_id, "datetime": datetime_str}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/v2/appointments/", json=payload, headers=headers)
                return {'success': response.status_code == 200,
                        'data': response.json() if response.status_code == 200 else None}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def complete_visit_api(self, patient_id: int, doctor_id: int, record_data: dict, token: str) -> Dict[str, Any]:
        """Завершение приема и создание мед. записи через FastAPI"""
        headers = {'Authorization': f'Bearer {token}'}
        record_data['patient_id'] = patient_id
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/v2/medical-records/", json=record_data, headers=headers)
                if response.status_code == 200:
                    return {'success': True, 'data': response.json()}
                return {'success': False, 'error': response.text}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Глобальный экземпляр клиента
fastapi_client = FastAPIClient()


def sync_user_to_fastapi(user, role):
    """Создаёт пользователя в FastAPI через эндпоинт admin/users."""
    import requests
    from django.conf import settings
    from app.controllers.base_controller import _get_token, BASE_URL
    try:
        token = _get_token('admin', 'admin123')
        headers = {'Authorization': f'Bearer {token}'} if token else {}
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/admin/users",
            json={"login": user.username, "password": "changeme123", "role": role},
            headers=headers,
            timeout=3,
        )
        if resp.status_code in (200, 201):
            return True
        if resp.status_code == 400 and "уже существует" in resp.text.lower():
            # Уже есть — найдём ID
            all_clients = requests.get(f"{BASE_URL}/api/v1/clients/", headers=headers, timeout=3).json()
            for c in all_clients:
                if c.get('login') == user.username:
                    return c.get('id')
    except Exception as e:
        print(f"FastAPI sync error: {e}")
    return False