"""Тесты МКБ-С-3 эндпоинтов (/api/v2/mkbs/)."""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
BASE = "/api/v2/mkbs"


class TestMKBS:

    async def test_get_diagnosis_codes(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/diagnoses", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_diagnosis(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/diagnoses?search=K", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_service_codes(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/services", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_mkbs_global(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/search?query=зуб", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_validate_invalid_code(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/validate/XXX99", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert resp.json()["valid"] == False

    async def test_mkbs_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/diagnoses")
        assert resp.status_code == 401

    async def test_manager_cannot_access_mkbs(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/diagnoses", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 403
