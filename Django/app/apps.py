# app/apps.py
import sys
from django.apps import AppConfig
import requests
from django.conf import settings


def _create_admin_on_migrate(sender, **kwargs):
    """Создаёт суперпользователя admin после каждой миграции (идемпотентно)."""
    try:
        from django.contrib.auth.models import User
        from app.models import UserProfile

        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@dentaclinic.local',
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        user.set_password('admin123')
        user.is_staff = True
        user.is_superuser = True
        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'admin'
        profile.save()

        if created:
            print('[OK] Суперпользователь admin создан (пароль: admin123)')
    except Exception as e:
        print(f'[!] Не удалось создать admin: {e}')


class AppConfigData(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        import app.models
        from django.db.models.signals import post_migrate
        post_migrate.connect(_create_admin_on_migrate, sender=self)

        skip_cmds = {'test', 'check', 'migrate', 'makemigrations', 'collectstatic',
                     'shell', 'seed_accounts', 'createsuperuser', 'loaddata'}
        if not (set(sys.argv) & skip_cmds) and 'pytest' not in sys.modules:
            self.check_fastapi_connection()

    def check_fastapi_connection(self):
        """Проверяет подключение к FastAPI при старте сервера"""
        fastapi_url = getattr(settings, 'FASTAPI_URL', 'http://localhost:8000')
        health_check_url = f"{fastapi_url}/"  # Или /docs, или специальный эндпоинт /health

        print(f"[*] Проверка подключения к FastAPI по адресу: {fastapi_url}...")

        try:
            response = requests.get(health_check_url, timeout=3)

            if response.status_code == 200:
                print("[OK] FastAPI доступен. Сервер Django запущен успешно.")
            else:
                raise ConnectionError(f"FastAPI вернул статус {response.status_code}")

        except requests.exceptions.ConnectionError:
            # НЕ останавливаем Django: он должен стартовать и показать понятную ошибку
            # (баннер на страницах + 503 для API-эндпоинтов, зависящих от FastAPI).
            warning_msg = (
                    "\n" + "=" * 50 +
                    "\n[ВНИМАНИЕ] Внешний API (FastAPI) выключен." +
                    "\nDjango запущен, но функции, зависящие от FastAPI, недоступны." +
                    "\nЗапустите FastAPI на порту 8000:" +
                    "\n   cd Api" +
                    "\n   uvicorn app.main:main_app --reload" +
                    "\n" + "=" * 50
            )
            print(warning_msg)

        except Exception as e:
            print(f"[!] Предупреждение при проверке FastAPI: {e}")