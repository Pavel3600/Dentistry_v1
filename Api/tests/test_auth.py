"""Тесты аутентификации и управления пользователями."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def uid():
    return uuid.uuid4().hex[:8]


async def test_register_success(client: AsyncClient):
    """Регистрация нового пользователя возвращает 201."""
    resp = await client.post("/api/v1/auth/register", json={"login": f"usr_{uid()}", "password": "pass1234"})
    assert resp.status_code == 201
    assert "id" in resp.json()
    assert resp.json()["login"].startswith("usr_")


async def test_register_duplicate_login(client: AsyncClient):
    """Повторная регистрация с тем же логином — 400."""
    login = f"dup_{uid()}"
    await client.post("/api/v1/auth/register", json={"login": login, "password": "pass1234"})
    resp = await client.post("/api/v1/auth/register", json={"login": login, "password": "pass5678"})
    assert resp.status_code == 400


async def test_register_short_password(client: AsyncClient):
    """Пароль < 4 символов — 422 (валидация Pydantic)."""
    resp = await client.post("/api/v1/auth/register", json={"login": f"sp_{uid()}", "password": "abc"})
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient):
    """Успешный вход возвращает access_token."""
    login, pwd = f"lg_{uid()}", "login1234"
    await client.post("/api/v1/auth/register", json={"login": login, "password": pwd})
    resp = await client.post("/api/v1/auth/login", data={"username": login, "password": pwd})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient):
    """Неверный пароль — 401."""
    login = f"wp_{uid()}"
    await client.post("/api/v1/auth/register", json={"login": login, "password": "correct1"})
    resp = await client.post("/api/v1/auth/login", data={"username": login, "password": "wrong999"})
    assert resp.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    """Несуществующий пользователь — 401."""
    resp = await client.post("/api/v1/auth/login", data={"username": f"nobody_{uid()}", "password": "any1234"})
    assert resp.status_code == 401


async def test_get_me(client: AsyncClient):
    """GET /auth/me возвращает данные текущего пользователя."""
    login, pwd = f"me_{uid()}", "me123456"
    await client.post("/api/v1/auth/register", json={"login": login, "password": pwd})
    token = (await client.post("/api/v1/auth/login", data={"username": login, "password": pwd})).json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["login"] == login


async def test_get_me_no_token(client: AsyncClient):
    """Без токена — 401."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_admin_create_user(client: AsyncClient, admin_token: str):
    """Admin создаёт пользователя с ролью dentist."""
    resp = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"nd_{uid()}", "password": "dentist12", "role": "dentist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["login"].startswith("nd_")


async def test_non_admin_cannot_create_admin(client: AsyncClient, manager_token: str):
    """Manager не может создать admin — 403."""
    resp = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"fa_{uid()}", "password": "admin1234", "role": "admin"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 403
