# 🦷 DentaClinic — Django (веб-интерфейс + REST API)

«Жирный» Django-проект поверх той же PostgreSQL-базы (`Dentistry`), что и FastAPI.
Роли: администратор, менеджер, стоматолог, пациент.

## Технологии
- Django 6 + Django REST Framework
- PostgreSQL (общая БД с FastAPI; модели общих таблиц — `managed = False`)
- SimpleJWT, Bootstrap 5

## Быстрый запуск (рекомендуется)
Из корня репозитория (`V6`) — двойной клик:
```
setup.bat   :: один раз — БД, зависимости, миграции, базовые учётки
start.bat   :: запуск FastAPI (:8000) и Django (:8001) в двух окнах
```

## Ручной запуск
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

REM База Dentistry должна существовать (см. ../scripts/create_db.sql)
python manage.py migrate
python manage.py seed_accounts      REM базовые учётки admin/manager/dentist
python manage.py runserver 8001
```
Открыть: http://127.0.0.1:8001/  (вход: `/login/`, админка: `/admin/`).

> Django стартует, даже если FastAPI выключен — показывает баннер
> «Внешний API выключен», часть функций интеграции будет недоступна.

## Учётные записи
См. [../ACCOUNTS.md](../ACCOUNTS.md):
`admin/admin123`, `manager/manager123`, `dentist/dentist123`.

## Тесты
```
python -m pytest                 REM ~311 тестов, покрытие ~86%
pytest --cov=app --cov-report=html
pytest app/tests/selenium/      REM только Selenium
```
Обычные тесты идут на SQLite (`django_app/test_settings.py`) — PostgreSQL не нужна.

## Структура
- `app/models.py` — модели (общие с FastAPI таблицы — `managed=False`).
- `app/views.py` — веб-вьюхи (CBV) по ролям.
- `app/api/` — REST API v2 (DRF ViewSets).
- `app/services/` — интеграция с FastAPI (health-check, клиент).
- `app/management/commands/seed_accounts.py` — базовые учётки.
- `../NOTES.md`, `../CODE_ANALYSIS.md` — заметки и анализ.
