# Заметки по проекту (для разработчика)

## Архитектура
- **Api/** — исходный FastAPI-сервис (SQLAlchemy, async). Источник истины по схеме БД.
- **Django/** — "жирный" Django-проект. Работает с ТОЙ ЖЕ PostgreSQL-базой (`Dentistry`).
- Роли: `admin`, `manager`, `dentist`, `patient` (см. `UserProfile.ROLE_CHOICES`).

## Запуск и окружение
- PostgreSQL 18, БД **`Dentistry`**, пользователь `postgres`, пароль `admin`, :5432.
- Тестовая БД FastAPI: **`Dentistry_test`** (имя регистрозависимо! conftest делает
  `replace("/Dentistry","/Dentistry_test")`). Создаётся вручную:
  `CREATE DATABASE "Dentistry_test";` (через `psql -f`, иначе кавычки теряются → lowercase).
- Порты: **FastAPI :8000**, **Django :8001**. Запуск обоих: `..\run_all.ps1`.
- FastAPI `.env` уже указывает на общую `Dentistry`.

## Тесты
- FastAPI: `Api> venv\Scripts\python -m pytest` — нужна PostgreSQL + `Dentistry_test`.
  Важно: override `get_db` ставится на `main_app` И на под-приложения `app_v1/app_v2`.
- Django: `Django> venv\Scripts\python -m pytest` (SQLite через test_settings).

## КРИТИЧЕСКИ ВАЖНО: `managed = False` модели
Таблицы `patients`, `appointments`, `clients`, `medical_records`, `mkbs_codes`,
`studies`, `referrals`, `work_orders` создаёт FastAPI (`Api/app/init_db.py`).
Django их НЕ мигрирует. **Нельзя** добавлять колонки в эти таблицы через Django.
Любые доп. поля (аллергии, заметки, отчёты) храним в ОТДЕЛЬНЫХ Django-managed
таблицах, связанных по `patient_id` / `visit_id`.

## Схема таблицы `patients` (Api/app/models/medical_models.py)
Реальные NOT NULL колонки, которых не хватало Django-модели:
- `card_number` String(50) NOT NULL UNIQUE  ← добавлено в Django Patient
- `user_id` Integer NOT NULL UNIQUE FK→clients.id  ← должен ссылаться на Clients(role='patient')

### Причина бага "добавление пациента вызывает ошибку"
`PatientForm` не задавал `card_number` и `user_id` → PostgreSQL IntegrityError
(null в NOT NULL колонке). Исправлено: `PatientCreateView` теперь
1) создаёт запись `Clients(role='patient')`, 2) генерирует `card_number`.

## Тесты
- `pytest.ini`: `asyncio_mode = auto`, цель покрытия ≥80% (сейчас ~84%).
- conftest создаёт таблицы managed=False из Django-моделей (SQLite в тестах),
  поэтому новые поля Django-модели автоматически попадают в тестовую БД.
- Запуск: `venv\Scripts\python -m pytest --no-cov -q`

## Новые возможности (эта итерация)
1. Фикс создания пациента (card_number + Clients).
2. Создание врача: `DoctorForm` / `DoctorCreateView` / `DoctorListView`.
3. Отчёт после приёма: модель `VisitReport`, `WriteReportView`.
4. Мед. предупреждения пациента (аллергии и пр.): модель `PatientMedicalInfo`,
   `PatientMedicalInfoView`. Видно врачу в карточке/истории.
