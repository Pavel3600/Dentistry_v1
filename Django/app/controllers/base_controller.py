import requests
from django.conf import settings
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, 'FASTAPI_URL', 'http://localhost:8000')


def _serialize(data: dict) -> dict:
    """Конвертирует datetime/date в ISO-строки без tzinfo для JSON-сериализации."""
    result = {}
    for k, v in data.items():
        if isinstance(v, datetime):
            result[k] = v.replace(tzinfo=None).isoformat()
        elif isinstance(v, date):
            result[k] = v.isoformat()
        elif isinstance(v, dict):
            result[k] = _serialize(v)
        elif isinstance(v, list):
            result[k] = [_serialize(i) if isinstance(i, dict) else i for i in v]
        else:
            result[k] = v
    return result


def _get_token(username='manager', password='manager123'):
    """Получить JWT токен от FastAPI."""
    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={'username': username, 'password': password},
            timeout=5,
        )
        resp.raise_for_status()
        return resp.json().get('access_token')
    except Exception as e:
        logger.error(f"Ошибка получения токена: {e}")
        return None


def _headers(token=None):
    if token is None:
        token = _get_token()
    return {'Authorization': f'Bearer {token}'} if token else {}


def _post(url, data: dict, token=None, **kwargs):
    return requests.post(url, json=_serialize(data), headers=_headers(token), **kwargs)


def _put(url, data: dict, token=None, **kwargs):
    return requests.put(url, json=_serialize(data), headers=_headers(token), **kwargs)


def _patch(url, data: dict, token=None, **kwargs):
    return requests.patch(url, json=_serialize(data), headers=_headers(token), **kwargs)
