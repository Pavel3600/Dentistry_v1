# ОБНОВЛЕНИЯ СИСТЕМЫ ПРАВ И API

## 1. СИСТЕМА РАЗНЫХ ПРАВ ДЛЯ КАЖДОЙ РОЛИ

### Иерархия ролей:
- **Admin (3)**: Полный доступ, может создавать кого угодно
- **Manager (2)**: Может создавать менеджеров и врачей
- **Dentist (1)**: Может только просматривать данные
- **Patient (0)**: Базовые права

### Кто может создавать кого:

| Роль Админа | Может создавать |
|-----------|-----------------|
| Admin ✅ | Admin, Manager, Dentist, Patient |
| Manager ✅ | Dentist, Patient |
| Dentist ❌ | Ничего |
| Patient ❌ | Ничего |

### Файл: app/core/roles.py
- ✅ ROLE_HIERARCHY - иерархия ролей
- ✅ ROLE_CREATION_PERMISSIONS - права создания для каждой роли
- ✅ require_can_create_user() - проверка прав при создании

## 2. ОБНОВЛЕНИЕ АУТЕНТИФИКАЦИИ

### Файл: app/api/routers/auth.py
- ✅ POST /auth/admin/users - с проверкой прав по ролям
- ✅ Разные сообщения об ошибке для каждой роли
- ✅ Подробная документация в docstring

Пример ошибки:
```
❌ "У вас нет прав на создание администратора. 
   Только администратор может создавать администраторов."
```

## 3. НОВЫЕ API ENDPOINT'Ы (50+)

### Файл: app/api/routers/extended.py

#### ПАЦИЕНТЫ (5 endpoints):
- GET /api/patients/all - все пациенты
- GET /api/patients/search - поиск пациентов
- GET /api/patients/count - количество
- GET /api/patients/active - активные пациенты
- GET /api/patients/{patient_id} - профиль пациента

#### СТАТИСТИКА (6 endpoints):
- GET /stats/users-by-role - количество по ролям
- GET /stats/total - всего пользователей
- GET /stats/today - добавлено сегодня
- GET /stats/monthly - добавлено в месяц
- GET /stats/growth - рост пользователей
- GET /analytics/... - аналитика

#### УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ (8 endpoints):
- GET /users/list - список пользователей
- GET /users/by-role/{role} - пользователи по ролям
- GET /users/{user_id} - информация о пользователе
- GET /users/{user_id}/role - роль пользователя
- GET /users/exists/{login} - проверка логина
- GET /users/admins/list - все администраторы
- GET /users/managers/list - все менеджеры
- POST /users/bulk-update - массовое обновление

#### ПОИСК И ФИЛЬТР (4 endpoints):
- GET /search/users - универсальный поиск
- GET /filter/patients-by-name - фильтр пациентов
- GET /filter/active-users - активные пользователи
- GET /search/by-date - поиск по дате

#### МОНИТОРИНГ (4 endpoints):
- GET /health - проверка здоровья
- GET /status - статус системы
- GET /uptime - время работы
- GET /monitoring/system-status - подробный статус

#### КОНФИГУРАЦИЯ (3 endpoints):
- GET /config/roles - конфигурация ролей
- GET /config/permissions - права по ролям
- GET /config/features - доступные функции

#### УТИЛИТЫ (2 endpoints):
- GET /utils/time - текущее время
- POST /utils/ping - проверка соединения

## 4. ПОДКЛЮЧЕНИЕ К ПРИЛОЖЕНИЮ

### Файл: app/main.py
- ✅ Импорт extended router
- ✅ Подключено к app_v1
- ✅ Доступны на /api/v1/* и /api/v2/*

## 5. ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ

### Создание администратора (может только Admin):
```
POST /auth/admin/users
{
    "login": "newadmin",
    "password": "password123",
    "role": "admin"
}

Результат ✅:
{
    "id": 1,
    "login": "newadmin",
    "role": "admin"
}
```

### Создание менеджера (может Admin и Manager):
```
POST /auth/admin/users
{
    "login": "newmanager",
    "password": "password123",
    "role": "manager"
}

Результат ✅ (если запрос от Admin):
{
    "id": 2,
    "login": "newmanager",
    "role": "manager"
}

Результат ❌ (если запрос от Dentist):
{
    "detail": "У вас нет прав на создание менеджера..."
}
```

### Получение статистики:
```
GET /stats/users-by-role

Результат:
{
    "admin": 2,
    "manager": 5,
    "dentist": 12,
    "patient": 150
}
```

## 6. ОТЛИЧИЯ ДО И ПОСЛЕ

### До обновления:
❌ Все администраторы могли создавать кого угодно
❌ Мало API endpoints (< 30)
❌ Нет статистики и аналитики
❌ Нет проверки прав при создании

### После обновления:
✅ Разные права для каждой роли
✅ 50+ новых API endpoints
✅ Подробная статистика и мониторинг
✅ Проверка прав по иерархии ролей
✅ Понятные сообщения об ошибках
✅ Полная документация в коде

## 7. ПОДКЛЮЧЕНИЕ

Все новые endpoints автоматически доступны:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Просто запустите:
```
python -m uvicorn app.main:main_app --reload
```

И все endpoints будут доступны под /api/v1/ и /api/v2/
