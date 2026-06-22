# app/utils.py
import requests
from django.conf import settings

def is_fastapi_available():
    """
    Проверяет, доступен ли сервер FastAPI.
    Возвращает True, если статус 200, иначе False.
    """
    fastapi_url = getattr(settings, 'FASTAPI_URL', 'http://localhost:8000')
    try:
        # Делаем быстрый запрос к корню или health-эндпоинту FastAPI
        response = requests.get(f"{fastapi_url}/", timeout=2)
        return response.status_code == 200
    except Exception:
        return False