#!/usr/bin/env python3
"""
Общая инициализация базы данных Dentistry
Запуск: python init_all.py
"""

import asyncio
import asyncpg
import sys
import os

# Добавляем пути для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))

from app.core.config import settings
from app.core.security import hash_password
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select


# ========== 1. СОЗДАНИЕ БАЗЫ ДАННЫХ (если нет) ==========
async def create_database_if_not_exists():
    """Создаёт базу данных PostgreSQL, если она не существует"""
    # Парсим URL
    db_url = settings.DATABASE_URL
    # postgresql+asyncpg://postgres:admin@localhost/Dentistry

    # Извлекаем параметры
    import re
    match = re.match(r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(.+)', db_url)
    if not match:
        print("❌ Не удалось распарсить DATABASE_URL")
        return False

    user, password, host, port, database = match.groups()
    port = port or '5432'

    # Подключаемся к базе postgres (всегда существует)
    sys_db_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"

    try:
        conn = await asyncpg.connect(sys_db_url)

        # Проверяем, существует ли база
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", database
        )

        if not result:
            await conn.execute(f'CREATE DATABASE "{database}"')
            print(f"✅ База данных '{database}' создана")
        else:
            print(f"✅ База данных '{database}' уже существует")

        await conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка при создании базы: {e}")
        return False


# ========== 2. СОЗДАНИЕ ТАБЛИЦ ==========
async def create_tables():
    """Создаёт все таблицы через SQLAlchemy"""
    from app.core.database import engine, Base
    from app.models.client_models import Clients
    from app.models.medical_models import (
        Patient, Appointment, MedicalRecord,
        Study, Referral, WorkOrder, MKBSCode
    )

    print("📋 Создание таблиц...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы созданы (или уже существуют)")


# ========== 3. ЗАПОЛНЕНИЕ ТЕСТОВЫМИ ДАННЫМИ ==========
async def seed_database():
    """Заполняет базу тестовыми данными"""
    from app.core.database import AsyncSessionLocal
    from app.models.client_models import Clients
    from app.models.medical_models import Patient, MKBSCode
    from app.services.mkbs_dll import mkbs_emulator
    from datetime import datetime

    print("🌱 Заполнение тестовыми данными...")

    async with AsyncSessionLocal() as db:
        # ===== 3.1 ПОЛЬЗОВАТЕЛИ (Clients) =====
        users_data = [
            {"login": "admin", "password": "admin123", "role": "admin"},
            {"login": "manager", "password": "manager123", "role": "manager"},
            {"login": "dentist", "password": "dentist123", "role": "dentist"},
            {"login": "dentist2", "password": "dentist123", "role": "dentist"},
            {"login": "ivanov", "password": "patient123", "role": "patient"},
            {"login": "petrov", "password": "patient123", "role": "patient"},
            {"login": "sidorova", "password": "patient123", "role": "patient"},
        ]

        users_created = 0
        for user_data in users_data:
            result = await db.execute(
                select(Clients).where(Clients.login == user_data["login"])
            )
            if not result.scalar_one_or_none():
                new_user = Clients(
                    login=user_data["login"],
                    password=hash_password(user_data["password"]),
                    role=user_data["role"]
                )
                db.add(new_user)
                users_created += 1

        await db.flush()
        print(f"✅ Создано пользователей: {users_created}")

        # ===== 3.2 ПОЛУЧАЕМ ID ПОЛЬЗОВАТЕЛЕЙ =====
        result = await db.execute(select(Clients))
        all_users = {u.login: u for u in result.scalars().all()}

        # ===== 3.3 КОДЫ МКБ-С-3 =====
        mkbs_created = 0
        for code, info in mkbs_emulator._data.items():
            result = await db.execute(
                select(MKBSCode).where(MKBSCode.code == code)
            )
            if not result.scalar_one_or_none():
                mkbs = MKBSCode(
                    code=code,
                    name=info["name"],
                    category=info["category"],
                    is_active=True
                )
                db.add(mkbs)
                mkbs_created += 1

        await db.flush()
        print(f"✅ Создано кодов МКБ-С-3: {mkbs_created}")

        # ===== 3.4 ПАЦИЕНТЫ =====
        patients_data = [
            {
                "user": all_users.get("ivanov"),
                "full_name": "Иван Иванов",
                "birth_date": datetime(1985, 5, 15),
                "gender": "M",
                "phone": "+7 (916) 123-45-67",
                "address": "г. Москва, ул. Тверская, д. 10"
            },
            {
                "user": all_users.get("petrov"),
                "full_name": "Петр Петров",
                "birth_date": datetime(1990, 8, 20),
                "gender": "M",
                "phone": "+7 (916) 234-56-78",
                "address": "г. Москва, ул. Арбат, д. 5"
            },
            {
                "user": all_users.get("sidorova"),
                "full_name": "Мария Сидорова",
                "birth_date": datetime(1978, 3, 10),
                "gender": "F",
                "phone": "+7 (916) 345-67-89",
                "address": "г. Москва, ул. Новый Арбат, д. 15"
            },
        ]

        patients_created = 0
        for p_data in patients_data:
            if p_data["user"]:
                result = await db.execute(
                    select(Patient).where(Patient.user_id == p_data["user"].id)
                )
                if not result.scalar_one_or_none():
                    patient = Patient(
                        user_id=p_data["user"].id,
                        full_name=p_data["full_name"],
                        birth_date=p_data["birth_date"],
                        gender=p_data["gender"],
                        phone=p_data["phone"],
                        address=p_data["address"]
                    )
                    db.add(patient)
                    patients_created += 1

        await db.commit()
        print(f"✅ Создано пациентов: {patients_created}")

        # ===== 3.5 ЗАПИСИ НА ПРИЁМ (пример) =====
        # Получаем пациентов
        result = await db.execute(select(Patient))
        patients = result.scalars().all()

        dentist = all_users.get("dentist")
        dentist2 = all_users.get("dentist2")

        from datetime import timedelta
        appointments_created = 0

        if patients and dentist:
            from app.models.medical_models import Appointment

            # Создаём записи на ближайшие дни
            for i, patient in enumerate(patients[:3]):
                appointment_date = datetime.now() + timedelta(days=i + 1)
                appointment_date = appointment_date.replace(hour=10, minute=0, second=0, microsecond=0)

                result = await db.execute(
                    select(Appointment).where(
                        Appointment.patient_id == patient.id,
                        Appointment.datetime == appointment_date
                    )
                )
                if not result.scalar_one_or_none():
                    appointment = Appointment(
                        patient_id=patient.id,
                        doctor_id=dentist.id if i % 2 == 0 else dentist2.id,
                        datetime=appointment_date,
                        status="scheduled"
                    )
                    db.add(appointment)
                    appointments_created += 1

        await db.commit()
        print(f"✅ Создано записей на приём: {appointments_created}")

        # Итог
        print("\n" + "=" * 50)
        print("🎉 БАЗА ДАННЫХ ГОТОВА!")
        print("=" * 50)
        print("\n📊 Тестовые учётные записи:")
        print("   admin / admin123    - Администратор")
        print("   manager / manager123 - Менеджер")
        print("   dentist / dentist123 - Стоматолог 1")
        print("   dentist2 / dentist123 - Стоматолог 2")
        print("   ivanov / patient123   - Пациент")
        print("   petrov / patient123   - Пациент")
        print("   sidorova / patient123 - Пациент")
        print("\n🚀 Можно запускать:")
        print("   FastAPI: uvicorn app.main:main_app --reload")
        print("   Django: python manage.py runserver 8001")


# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
async def main():
    print("\n" + "=" * 50)
    print("🦷 ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ DENTISTRY")
    print("=" * 50 + "\n")

    # 1. Создаём базу
    if not await create_database_if_not_exists():
        print("❌ Не удалось создать базу данных")
        return

    # 2. Создаём таблицы
    await create_tables()

    # 3. Заполняем данными
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())