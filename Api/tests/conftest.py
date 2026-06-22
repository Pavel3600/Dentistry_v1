"""
Конфигурация тестов FastAPI.
Требует засиянных учёток в БД: python scripts/seed_accounts.py
Все фикстуры — session scope, один event loop на весь запуск тестов.
"""
import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Windows: SelectorEventLoop совместим с asyncpg
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import main_app


def uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest_asyncio.fixture(scope="session")
async def client():
    """Один ASGI-клиент на всю сессию тестов (один event loop = один пул соединений)."""
    async with AsyncClient(transport=ASGITransport(app=main_app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="session")
async def admin_token(client: AsyncClient):
    """Токен admin (из seed_accounts.py)."""
    resp = await client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 200, "Запустите: python scripts/seed_accounts.py"
    return resp.json()["access_token"]


@pytest_asyncio.fixture(scope="session")
async def manager_token(client: AsyncClient):
    """Токен manager (из seed_accounts.py)."""
    resp = await client.post("/api/v1/auth/login", data={"username": "manager", "password": "manager123"})
    assert resp.status_code == 200, "Запустите: python scripts/seed_accounts.py"
    return resp.json()["access_token"]


@pytest_asyncio.fixture(scope="session")
async def dentist_data(client: AsyncClient):
    """(token, dentist_id) для dentist из seed."""
    resp = await client.post("/api/v1/auth/login", data={"username": "dentist", "password": "dentist123"})
    assert resp.status_code == 200, "Запустите: python scripts/seed_accounts.py"
    token = resp.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, me.json()["id"]
