"""Тесты аутентификации и административных функций (переписано под session-fixtures)."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def uid():
    return uuid.uuid4().hex[:8]


class TestAuth:

    async def test_register_success(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={"login": f"reg_{uid()}", "password": "pass1234"})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert data["login"].startswith("reg_")

    async def test_register_duplicate_login(self, client: AsyncClient):
        login = f"dup_{uid()}"
        await client.post("/api/v1/auth/register", json={"login": login, "password": "pass1234"})
        resp = await client.post("/api/v1/auth/register", json={"login": login, "password": "other1234"})
        assert resp.status_code == 400

    async def test_register_weak_password(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={"login": f"wp_{uid()}", "password": "123"})
        assert resp.status_code == 422

    async def test_login_success(self, client: AsyncClient):
        login, pwd = f"lg_{uid()}", "login1234"
        await client.post("/api/v1/auth/register", json={"login": login, "password": pwd})
        resp = await client.post("/api/v1/auth/login", data={"username": login, "password": pwd})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client: AsyncClient):
        login = f"lw_{uid()}"
        await client.post("/api/v1/auth/register", json={"login": login, "password": "correct1"})
        resp = await client.post("/api/v1/auth/login", data={"username": login, "password": "wrong999"})
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", data={"username": f"nobody_{uid()}", "password": "any1234"})
        assert resp.status_code == 401

    async def test_get_me(self, client: AsyncClient, manager_token: str):
        resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert resp.json()["login"] == "manager"

    async def test_get_me_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_logout(self, client: AsyncClient, manager_token: str):
        resp = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert "вышли" in resp.json()["message"].lower()


class TestAdmin:

    async def test_create_user_by_admin(self, client: AsyncClient, admin_token: str):
        resp = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"adm_{uid()}", "password": "dentist12", "role": "dentist"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201

    async def test_create_user_by_non_admin(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"fa_{uid()}", "password": "admin1234", "role": "admin"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 403
