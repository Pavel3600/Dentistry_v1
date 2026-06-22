"""Тесты статистики (/api/v2/stats/)."""
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
BASE = "/api/v2/stats"


class TestStatistics:

    async def test_appointments_count(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/appointments-count", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_appointments" in data
        assert isinstance(data["total_appointments"], int)

    async def test_popular_doctor(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/popular-doctor", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "doctor" in data or "detail" in data

    async def test_statistics_unauthorized(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/appointments-count")
        assert resp.status_code == 401

    async def test_statistics_as_dentist_forbidden(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/appointments-count", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 403
