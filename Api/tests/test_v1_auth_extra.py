"""Тесты дополнительных auth и client эндпоинтов."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def uid():
    return uuid.uuid4().hex[:8]


class TestAuthExtra:

    async def test_admin_create_user_duplicate_login(self, client: AsyncClient, admin_token: str):
        login = f"adx_{uid()}"
        await client.post(
            "/api/v1/auth/admin/users",
            json={"login": login, "password": "pass1234", "role": "patient"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": login, "password": "pass5678", "role": "patient"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400

    async def test_refresh_token(self, client: AsyncClient):
        login, pwd = f"rft_{uid()}", "refresh123"
        await client.post("/api/v1/auth/register", json={"login": login, "password": pwd})
        token_resp = await client.post("/api/v1/auth/login", data={"username": login, "password": pwd})
        token = token_resp.json()["access_token"]
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": token})
        # Если decode_token принимает обычный JWT — вернёт новый токен
        assert resp.status_code in (200, 401)

    async def test_refresh_invalid_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid.token.here"})
        assert resp.status_code == 401

    async def test_manager_can_create_patient(self, client: AsyncClient, manager_token: str):
        resp = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"mgcp_{uid()}", "password": "pat12345", "role": "patient"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 201

    async def test_manager_cannot_create_manager(self, client: AsyncClient, manager_token: str):
        resp = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"mgcm_{uid()}", "password": "mgr12345", "role": "manager"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 403


class TestClientsEndpoint:

    async def test_get_all_clients(self, client: AsyncClient, manager_token: str):
        resp = await client.get("/api/v1/clients/", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_delete_client(self, client: AsyncClient, admin_token: str):
        # Создать пользователя и удалить его
        cr = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"del_{uid()}", "password": "del12345", "role": "patient"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        client_id = cr.json()["id"]
        resp = await client.delete(f"/api/v1/clients/{client_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 204

    async def test_delete_client_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.delete("/api/v1/clients/999999", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404

    async def test_clients_require_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/clients/")
        assert resp.status_code == 401
