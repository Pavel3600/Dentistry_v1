import time
import logging
from functools import wraps

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)

_FASTAPI_DOWN_BODY = {
    "error": "Внешний API выключен. Пожалуйста, запустите FastAPI сервис.",
    "detail": "FastAPI service unavailable",
}


def get_fastapi_status() -> dict:
    """Return detailed availability info for the FastAPI service."""
    url = getattr(settings, 'FASTAPI_URL', 'http://localhost:8000')
    result = {
        'available': False,
        'url': url,
        'error': None,
        'response_time_ms': None,
        'status_code': None,
    }
    start = time.monotonic()
    try:
        r = requests.get(f"{url}/", timeout=3)
        elapsed = round((time.monotonic() - start) * 1000)
        result.update(
            available=r.status_code < 500,
            response_time_ms=elapsed,
            status_code=r.status_code,
        )
    except requests.exceptions.ConnectionError:
        result['error'] = 'Connection refused'
        logger.warning("FastAPI connection refused at %s", url)
    except requests.exceptions.Timeout:
        result['error'] = 'Timeout'
        logger.warning("FastAPI timeout at %s", url)
    except Exception as exc:
        result['error'] = str(exc)
        logger.exception("FastAPI health check failed: %s", exc)
    return result


def require_fastapi(view_func):
    """DRF view decorator — returns HTTP 503 when FastAPI is down."""
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        info = get_fastapi_status()
        if not info['available']:
            return Response(
                {**_FASTAPI_DOWN_BODY, 'fastapi_url': info['url'], 'reason': info['error']},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return view_func(self, request, *args, **kwargs)
    return wrapper
