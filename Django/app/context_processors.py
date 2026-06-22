"""Контекст-процессоры для шаблонов."""
from django.core.cache import cache

from .services.fastapi_health import get_fastapi_status

_CACHE_KEY = 'fastapi_online_banner'
_CACHE_TTL = 10  # сек — не дёргаем FastAPI на каждом запросе


def fastapi_status(request):
    """Отдаёт в шаблоны флаг доступности FastAPI для баннера-предупреждения."""
    online = cache.get(_CACHE_KEY)
    if online is None:
        online = get_fastapi_status().get('available', False)
        cache.set(_CACHE_KEY, online, _CACHE_TTL)
    return {'fastapi_online': online}
