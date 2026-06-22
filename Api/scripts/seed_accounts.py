"""
Создаёт/обновляет базовые учётки в FastAPI (таблица clients).
Запуск из папки Api/:  python scripts/seed_accounts.py

Логины и пароли совпадают с Django-учётками — один login работает в обоих сервисах.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.client_models import Clients
from app.models import medical_models  # импорт нужен чтобы Base.metadata знал все таблицы
from app.core.security import hash_password

ACCOUNTS = [
    # (login, password, role)
    ("admin",   "admin123",   "admin"),
    ("manager", "manager123", "manager"),
    ("dentist", "dentist123", "dentist"),
]


async def seed():
    # Создаём все таблицы если их нет (идемпотентно — CREATE TABLE IF NOT EXISTS)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        for login, password, role in ACCOUNTS:
            result = await db.execute(select(Clients).where(Clients.login == login))
            client = result.scalar_one_or_none()
            if client:
                client.password = hash_password(password)
                client.role = role
                action = "обновлён"
            else:
                db.add(Clients(login=login, password=hash_password(password), role=role))
                action = "создан"
            print(f"  [{role}] {login} / {password} — {action}")

        await db.commit()

    print("\nБазовые учётки готовы.")
    print("Запустите seed в Django отдельно: python manage.py seed_django_users")


if __name__ == "__main__":
    asyncio.run(seed())
