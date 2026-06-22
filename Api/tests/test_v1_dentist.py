"""Тесты v1 dentist-роутера (/api/v1/dentist/)."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
BASE = "/api/v1/dentist"
V2_PATIENTS = "/api/v2/patients"
V2_APPTS = "/api/v2/appointments"


def uid():
    return uuid.uuid4().hex[:8]


async def _make_patient(client, admin_token, manager_token) -> int:
    pu = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"v1p_{uid()}", "password": "pat12345", "role": "patient"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    pr = await client.post(
        f"{V2_PATIENTS}/",
        json={"full_name": f"V1 Пациент {uid()}", "birth_date": "1985-07-20T00:00:00",
              "gender": "F", "phone": f"+7918{uid()[:7]}", "user_id": pu.json()["id"]},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert pr.status_code == 201, pr.text
    return pr.json()["id"]


class TestDentistV1:

    async def test_get_schedule(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/schedule", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_appointment_by_doctor(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE}/appointments",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-12-10T10:00:00"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["patient_id"] == patient_id
        assert resp.json()["status"] == "scheduled"

    async def test_create_appointment_patient_not_found(self, client: AsyncClient, dentist_data):
        dentist_token, dentist_id = dentist_data
        resp = await client.post(
            f"{BASE}/appointments",
            json={"patient_id": 999999, "doctor_id": dentist_id, "datetime": "2026-12-11T10:00:00"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 404

    async def test_cancel_appointment_by_doctor(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        cr = await client.post(
            f"{BASE}/appointments",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-12-12T10:00:00"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        appt_id = cr.json()["id"]
        resp = await client.delete(f"{BASE}/appointments/{appt_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 204

    async def test_create_medical_record(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE}/medical-records",
            json={"patient_id": patient_id, "complaints": "Ноет зуб", "diagnosis": "Пульпит"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["diagnosis"] == "Пульпит"

    async def test_create_medical_record_patient_not_found(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.post(
            f"{BASE}/medical-records",
            json={"patient_id": 999999, "complaints": "Тест"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 404

    async def test_get_patient_medical_records(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        await client.post(
            f"{BASE}/medical-records",
            json={"patient_id": patient_id, "diagnosis": "Тест записи"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        resp = await client.get(f"{BASE}/medical-records/{patient_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    async def test_search_mkbs(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/mkbs/search?query=кариес", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_mkbs_diagnosis_category(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(
            f"{BASE}/mkbs/search?query=зуб&category=diagnosis",
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_mkbs_service_category(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(
            f"{BASE}/mkbs/search?query=пломб&category=service",
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200

    async def test_validate_mkbs_code(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE}/mkbs/validate/INVALID123", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert "valid" in resp.json()

    async def test_create_study(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE}/studies",
            json={"patient_id": patient_id, "study_type": "КТ", "result": "Норма"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["study_type"] == "КТ"

    async def test_get_patient_studies(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        await client.post(
            f"{BASE}/studies",
            json={"patient_id": patient_id, "study_type": "Рентген"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        resp = await client.get(f"{BASE}/studies/{patient_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_referral(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE}/referrals",
            json={"patient_id": patient_id, "to_specialist": "Хирург", "reason": "Удаление зуба мудрости"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["to_specialist"] == "Хирург"

    async def test_get_patient_referrals(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        await client.post(
            f"{BASE}/referrals",
            json={"patient_id": patient_id, "to_specialist": "Ортодонт", "reason": "Прикус"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        resp = await client.get(f"{BASE}/referrals/{patient_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_work_order(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE}/work-orders",
            json={"patient_id": patient_id, "manipulations": "Пломбирование", "materials": "Композит", "labor_cost": 2000.0},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["labor_cost"] == 2000.0

    async def test_get_patient_work_orders(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.get(f"{BASE}/work-orders/{patient_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_patients_by_visit_date(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(
            f"{BASE}/patients/search/by-visit-date?date=2026-12-01T00:00:00",
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_dentist_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/schedule")
        assert resp.status_code == 401
