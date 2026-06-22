# app/auth/fastapi_auth.py (новый файл)
from django.conf import settings
import jwt
import requests


def get_fastapi_token_for_user(user):
    """Получить JWT токен FastAPI для пользователя Django"""
    # Вариант 1: Прямой запрос к FastAPI
    try:
        response = requests.post(
            f"{settings.FASTAPI_URL}/api/v1/auth/login",
            data={
                "username": user.username,
                "password": "___SYNC_PASSWORD___"  # нужно сохранять пароль в синхронизации
            },
            timeout=2
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except:
        pass

    # Вариант 2: Создать локальный JWT (если секреты общие)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": getattr(user, 'profile', None).role if hasattr(user, 'profile') else 'patient'
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")