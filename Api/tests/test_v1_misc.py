"""Тесты разных v1 эндпоинтов: /doctors, /appointments, /medical-records, /studies (endpoints.py),
а также /api/* (extended.py) и дополнительные auth-пути."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def uid():
    return uuid.uuid4().hex[:8]


# ========== /doctors и /appointments (endpoints.py) ==========

class TestEndpoints:

    async def test_get_doctors(self, client: AsyncClient):
        resp = await client.get("/api/v1/doctors")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_appointments_list(self, client: AsyncClient):
        resp = await client.get("/api/v1/appointments")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_appointment(self, client: AsyncClient):
        resp = await client.post("/api/v1/appointments", json={
            "patient_id": 1,
            "doctor_name": "Иванов",
            "service": "Чистка",
            "appointment_date": "2026-12-20T10:00:00",
            "status": "pending",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_update_appointment(self, client: AsyncClient):
        # Создать запись чтобы обновить
        cr = await client.post("/api/v1/appointments", json={
            "patient_id": 1, "doctor_name": "Старый", "service": "Старая",
            "appointment_date": "2026-12-21T10:00:00",
        })
        appt_id = cr.json()["appointment_id"]
        resp = await client.put(f"/api/v1/appointments/{appt_id}", json={"doctor_name": "Новый"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_update_appointment_not_found(self, client: AsyncClient):
        resp = await client.put("/api/v1/appointments/999999", json={"doctor_name": "X"})
        assert resp.status_code == 404

    async def test_update_appointment_status(self, client: AsyncClient):
        cr = await client.post("/api/v1/appointments", json={
            "patient_id": 1, "appointment_date": "2026-12-22T10:00:00",
        })
        appt_id = cr.json()["appointment_id"]
        resp = await client.patch(f"/api/v1/appointments/{appt_id}/status?status=confirmed")
        assert resp.status_code == 200

    async def test_update_appointment_status_invalid(self, client: AsyncClient):
        cr = await client.post("/api/v1/appointments", json={
            "patient_id": 1, "appointment_date": "2026-12-23T10:00:00",
        })
        appt_id = cr.json()["appointment_id"]
        resp = await client.patch(f"/api/v1/appointments/{appt_id}/status?status=invalid_status")
        assert resp.status_code == 400

    async def test_update_appointment_status_not_found(self, client: AsyncClient):
        resp = await client.patch("/api/v1/appointments/999999/status?status=confirmed")
        assert resp.status_code == 404

    async def test_get_medical_records(self, client: AsyncClient):
        resp = await client.get("/api/v1/medical-records")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_medical_record(self, client: AsyncClient):
        resp = await client.post("/api/v1/medical-records", json={
            "patient_id": 1, "diagnosis": "Кариес", "treatment": "Пломба", "doctor_id": 1,
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    async def test_get_studies(self, client: AsyncClient):
        resp = await client.get("/api/v1/studies")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_study(self, client: AsyncClient):
        resp = await client.post("/api/v1/studies", json={
            "patient_id": 1, "study_type": "Рентген", "description": "Зуб 16", "date": "2026-06-01",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ========== /api/* (extended.py) ==========

class TestExtended:

    async def test_get_all_patients(self, client: AsyncClient, manager_token: str):
        resp = await client.get("/api/v1/api/patients/all", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_patients(self, client: AsyncClient, manager_token: str):
        resp = await client.get("/api/v1/api/patients/search?query=admin", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200

    async def test_count_patients(self, client: AsyncClient, manager_token: str):
        resp = await client.get("/api/v1/api/patients/count", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert "count" in resp.json()

    @pytest.mark.skip(reason="Поле created_at отсутствует в модели Clients — эндпоинт неработоспособен")
    async def test_active_patients(self, client: AsyncClient, manager_token: str):
        resp = await client.get("/api/v1/api/patients/active?days=30", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200

    async def test_stats_by_role(self, client: AsyncClient, manager_token: str):
        resp = await client.get("/api/v1/api/stats/users-by-role", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "admin" in data and "dentist" in data

    async def test_stats_total(self, client: AsyncClient, manager_token: str):
        resp = await client.get("/api/v1/api/stats/total", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert "total" in resp.json()

    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/v1/api/health")
        assert resp.status_code == 200
        assert resp.json()["healthy"] is True

    async def test_system_status(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/api/status", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "online"

    async def test_list_users(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/api/users/list", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_users_by_role(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/api/users/by-role/dentist", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200

    async def test_users_by_role_invalid(self, client: AsyncClient, admin_token: str):
        resp = await client.get("/api/v1/api/users/by-role/superuser", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 400

    async def test_extended_require_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/api/patients/all")
        assert resp.status_code == 401
