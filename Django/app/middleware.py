"""Middleware: block all views when FastAPI is unavailable."""
from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string
from django.http import HttpResponse

from .services.fastapi_health import get_fastapi_status

_CACHE_KEY = 'fastapi_available_middleware'
_CACHE_TTL = 3  # seconds between re-checks (короткий — чтобы блок срабатывал быстро)

# /fastapi/ping — liveness-пробник для фронтенд-поллера: должен быть доступен
# всегда, даже когда API выключен, иначе страница не сможет узнать что API вернулся.
_BYPASS_PREFIXES = ('/static/', '/favicon.ico', '/media/', '/fastapi/ping')


class FastAPIRequiredMiddleware:
    """Return HTTP 503 on every request when FastAPI is unreachable.

    Disabled when settings.REQUIRE_FASTAPI is False (tests, local dev without API).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'REQUIRE_FASTAPI', True):
            return self.get_response(request)

        path = request.path_info
        if any(path.startswith(p) for p in _BYPASS_PREFIXES):
            return self.get_response(request)

        available = cache.get(_CACHE_KEY)
        if available is None:
            available = get_fastapi_status().get('available', False)
            cache.set(_CACHE_KEY, available, _CACHE_TTL)

        if not available:
            fastapi_url = getattr(settings, 'FASTAPI_URL', 'http://localhost:8000')
            html = render_to_string('503_fastapi.html', {
                'fastapi_url': fastapi_url,
                'request': request,
            })
            return HttpResponse(html, status=503)

        return self.get_response(request)
