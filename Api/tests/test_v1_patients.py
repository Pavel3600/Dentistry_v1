"""Тесты v1 /patients/ роутера (patients.py) — без авторизации, in-memory/БД через Patient model."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
BASE = "/api/v1/patients"


def uid():
    return uuid.uuid4().hex[:8]


class TestPatientsV1:

    async def test_get_patients_list(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_patient(self, client: AsyncClient):
        email = f"pt_{uid()}@test.com"
        resp = await client.post(f"{BASE}/", json={
            "full_name": f"Пациент Тест {uid()}",
            "email": email,
            "phone": f"+7930{uid()[:7]}",
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["success"] is True
        assert "patient_id" in data

    async def test_create_patient_missing_fields(self, client: AsyncClient):
        resp = await client.post(f"{BASE}/", json={"full_name": "", "email": "", "phone": ""})
        assert resp.status_code == 400

    async def test_create_patient_duplicate_email(self, client: AsyncClient):
        email = f"dup_{uid()}@test.com"
        await client.post(f"{BASE}/", json={"full_name": "Первый", "email": email, "phone": f"+7931{uid()[:7]}"})
        resp = await client.post(f"{BASE}/", json={"full_name": "Дубль", "email": email, "phone": f"+7932{uid()[:7]}"})
        assert resp.status_code == 400

    async def test_get_patient_by_id(self, client: AsyncClient):
        email = f"gp_{uid()}@test.com"
        cr = await client.post(f"{BASE}/", json={
            "full_name": "Получить Пациента", "email": email, "phone": f"+7933{uid()[:7]}",
        })
        patient_id = cr.json()["patient_id"]
        resp = await client.get(f"{BASE}/{patient_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == patient_id

    async def test_get_patient_not_found(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/999999")
        assert resp.status_code == 404

    async def test_update_patient(self, client: AsyncClient):
        email = f"up_{uid()}@test.com"
        cr = await client.post(f"{BASE}/", json={
            "full_name": "Обновить Пациента", "email": email, "phone": f"+7934{uid()[:7]}",
        })
        patient_id = cr.json()["patient_id"]
        resp = await client.put(f"{BASE}/{patient_id}", json={
            "full_name": "Новое Имя", "email": email, "phone": f"+7935{uid()[:7]}",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_update_patient_not_found(self, client: AsyncClient):
        resp = await client.put(f"{BASE}/999999", json={
            "full_name": "Кто-то", "email": "x@x.com", "phone": "+79000000001",
        })
        assert resp.status_code == 404

    async def test_delete_patient(self, client: AsyncClient):
        email = f"del_{uid()}@test.com"
        cr = await client.post(f"{BASE}/", json={
            "full_name": "Удалить Пациента", "email": email, "phone": f"+7936{uid()[:7]}",
        })
        patient_id = cr.json()["patient_id"]
        resp = await client.delete(f"{BASE}/{patient_id}")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_delete_patient_not_found(self, client: AsyncClient):
        resp = await client.delete(f"{BASE}/999999")
        assert resp.status_code == 404
