"""Тесты v1 manager-роутера (/api/v1/manager/)."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
BASE = "/api/v1/manager"
V2_PATIENTS = "/api/v2/patients"


def uid():
    return uuid.uuid4().hex[:8]


async def _make_patient_user(client, admin_token) -> int:
    r = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"mp_{uid()}", "password": "pat12345", "role": "patient"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


class TestManagerV1:

    async def test_create_patient(self, client: AsyncClient, admin_token, manager_token):
        user_id = await _make_patient_user(client, admin_token)
        resp = await client.post(
            f"{BASE}/patients",
            json={"full_name": "V1 Менеджер Пациент", "birth_date": "1990-05-10T00:00:00",
                  "gender": "M", "phone": f"+7919{uid()[:7]}", "user_id": user_id},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["full_name"] == "V1 Менеджер Пациент"

    async def test_create_patient_wrong_role(self, client: AsyncClient, admin_token, manager_token):
        r = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"wrl_{uid()}", "password": "mgr12345", "role": "manager"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        mgr_id = r.json()["id"]
        resp = await client.post(
            f"{BASE}/patients",
            json={"full_name": "Не пациент", "birth_date": "1990-01-01T00:00:00",
                  "gender": "F", "phone": f"+7920{uid()[:7]}", "user_id": mgr_id},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 400

    async def test_get_patient(self, client: AsyncClient, admin_token, manager_token):
        user_id = await _make_patient_user(client, admin_token)
        cr = await client.post(
            f"{BASE}/patients",
            json={"full_name": "Получить пациента", "birth_date": "1992-03-15T00:00:00",
                  "gender": "M", "phone": f"+7921{uid()[:7]}", "user_id": user_id},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        patient_id = cr.json()["id"]
        resp = await client.get(f"{BASE}/patients/{patient_id}", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == patient_id

    async def test_get_patient_not_found(self, client: AsyncClient, manager_token):
        resp = await client.get(f"{BASE}/patients/999999", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 404

    async def test_update_patient(self, client: AsyncClient, admin_token, manager_token):
        user_id = await _make_patient_user(client, admin_token)
        cr = await client.post(
            f"{BASE}/patients",
            json={"full_name": "Обновить пациента", "birth_date": "1975-11-20T00:00:00",
                  "gender": "F", "phone": f"+7922{uid()[:7]}", "user_id": user_id},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        patient_id = cr.json()["id"]
        resp = await client.put(
            f"{BASE}/patients/{patient_id}",
            json={"full_name": "Обновлённое имя"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "Обновлённое имя"

    async def test_delete_patient(self, client: AsyncClient, admin_token, manager_token):
        user_id = await _make_patient_user(client, admin_token)
        cr = await client.post(
            f"{BASE}/patients",
            json={"full_name": "Удалить пациента", "birth_date": "1980-08-25T00:00:00",
                  "gender": "M", "phone": f"+7923{uid()[:7]}", "user_id": user_id},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        patient_id = cr.json()["id"]
        resp = await client.delete(f"{BASE}/patients/{patient_id}", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 204

    async def test_create_appointment(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        user_id = await _make_patient_user(client, admin_token)
        pr = await client.post(
            f"{BASE}/patients",
            json={"full_name": "Запись Пациент", "birth_date": "1988-04-10T00:00:00",
                  "gender": "F", "phone": f"+7924{uid()[:7]}", "user_id": user_id},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        patient_id = pr.json()["id"]
        resp = await client.post(
            f"{BASE}/appointments",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-11-15T09:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["patient_id"] == patient_id

    async def test_create_appointment_patient_not_found(self, client: AsyncClient, manager_token, dentist_data):
        _, dentist_id = dentist_data
        resp = await client.post(
            f"{BASE}/appointments",
            json={"patient_id": 999999, "doctor_id": dentist_id, "datetime": "2026-11-16T09:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 404

    async def test_cancel_appointment(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        user_id = await _make_patient_user(client, admin_token)
        pr = await client.post(
            f"{BASE}/patients",
            json={"full_name": "Отмена Пациент", "birth_date": "1995-02-14T00:00:00",
                  "gender": "M", "phone": f"+7925{uid()[:7]}", "user_id": user_id},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        patient_id = pr.json()["id"]
        ar = await client.post(
            f"{BASE}/appointments",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-11-20T11:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        appt_id = ar.json()["id"]
        resp = await client.delete(f"{BASE}/appointments/{appt_id}", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 204

    async def test_manager_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/patients/1")
        assert resp.status_code == 401
