# 🦷 Dental Clinic REST API

## Описание проекта
REST API для управления стоматологической клиникой. Поддерживает роли: Admin, Manager, Dentist, Patient.

## ⚡ Быстрый запуск (через батник, из корня репозитория V6)
```
setup.bat   :: один раз — БД, зависимости, МКБ, базовые clients, миграции Django, учётки
start.bat   :: запуск FastAPI (:8000) и Django (:8001)
```
Учётные записи — в [../ACCOUNTS.md](../ACCOUNTS.md). Ниже — ручной запуск.

## Технологии
- FastAPI 0.136.1
- PostgreSQL + SQLAlchemy 2.0 (async)
- Alembic для миграций
- JWT + OAuth2 для аутентификации
- Argon2 для хеширования паролей

# Запуск программы
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt

Создать файл .env в корне проекта
DATABASE_URL=postgresql+asyncpg://postgres:admin@localhost/Dentistry
SECRET_KEY=supersecretkeychangethis1234567890
ACCESS_TOKEN_EXPIRE_MINUTES=60

Создать базу данных PostgreSQL Dentistry

# 1. Инициализировать коды МКБ-С-3 в БД
python -m app.init_mkbs
python -m app.init_db

python.exe -m uvicorn app.main:main_app --reload
cd C:\Users\Pavel\OneDrive\Desktop\Api
✅ Добавил алиас! Теперь запусти:

```bash
cd C:\Users\Pavel\OneDrive\Desktop\Api
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Если всё работает - попробуй добавить пациента снова! 🚀
#Открыть эту сылку
http://localhost:8000/api/v1/docs

Версия	Swagger UI	ReDoc
v1	http://localhost:8000/api/v1/docs	http://localhost:8000/api/v1/redoc
v2	http://localhost:8000/api/v2/docs	http://localhost:8000/api/v2/redoc

Офлайн

# Экспорт Swagger JSON
curl http://localhost:8000/api/v1/openapi.json > openapi_v1.json
curl http://localhost:8000/api/v2/openapi.json > openapi_v2.json

🔐 Тестовые учетные записи
Логин	Пароль	Роль
admin	admin123	Admin
manager	manager123	Manager
dentist	dentist123	Dentist

# Запуск всех тестов 
python -m pytest -v