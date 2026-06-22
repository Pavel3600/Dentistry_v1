"""Тесты эндпоинтов стоматолога (/api/v2/medical-records/, studies, referrals, work-orders)."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio
BASE_MR = "/api/v2/medical-records"
BASE_ST = "/api/v2/studies"
BASE_RF = "/api/v2/referrals"
BASE_WO = "/api/v2/work-orders"


def uid():
    return uuid.uuid4().hex[:8]


async def _make_patient(client, admin_token, manager_token) -> int:
    pu = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"dp_{uid()}", "password": "pat12345", "role": "patient"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pu.status_code == 201, pu.text
    pr = await client.post(
        "/api/v2/patients/",
        json={
            "full_name": f"Дент Пациент {uid()}",
            "birth_date": "1990-01-01T00:00:00",
            "gender": "M",
            "phone": f"+7911{uid()[:7]}",
            "user_id": pu.json()["id"],
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert pr.status_code == 201, pr.text
    return pr.json()["id"]


class TestMedicalRecords:

    async def test_create_medical_record(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE_MR}/",
            json={"patient_id": patient_id, "complaints": "Боль в зубе", "diagnosis": "Кариес"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["complaints"] == "Боль в зубе"
        assert data["diagnosis"] == "Кариес"
        assert "id" in data

    async def test_create_medical_record_patient_not_found(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.post(
            f"{BASE_MR}/",
            json={"patient_id": 999999, "complaints": "Тест"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 404

    async def test_get_medical_records_list(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE_MR}/", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_medical_records_filter_by_patient(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        await client.post(
            f"{BASE_MR}/",
            json={"patient_id": patient_id, "diagnosis": "Фильтр-тест"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        resp = await client.get(
            f"{BASE_MR}/?patient_id={patient_id}",
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(r["patient_id"] == patient_id for r in data)

    async def test_get_single_medical_record(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        cr = await client.post(
            f"{BASE_MR}/",
            json={"patient_id": patient_id, "diagnosis": "Тест одиночная"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        record_id = cr.json()["id"]
        resp = await client.get(f"{BASE_MR}/{record_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == record_id

    async def test_get_medical_record_not_found(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE_MR}/999999", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 404

    async def test_medical_records_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE_MR}/")
        assert resp.status_code == 401

    async def test_manager_cannot_create_medical_record(self, client: AsyncClient, admin_token, manager_token):
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE_MR}/",
            json={"patient_id": patient_id, "diagnosis": "Тест"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 403


class TestStudies:

    async def test_create_study(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE_ST}/",
            json={"patient_id": patient_id, "study_type": "Рентген", "result": "Без патологий"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["study_type"] == "Рентген"

    async def test_get_studies_list(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE_ST}/", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_study_by_id(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        cr = await client.post(
            f"{BASE_ST}/",
            json={"patient_id": patient_id, "study_type": "КТ"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        study_id = cr.json()["id"]
        resp = await client.get(f"{BASE_ST}/{study_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == study_id

    async def test_get_study_not_found(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE_ST}/999999", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 404

    async def test_studies_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE_ST}/")
        assert resp.status_code == 401


class TestReferrals:

    async def test_create_referral(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE_RF}/",
            json={"patient_id": patient_id, "to_specialist": "Хирург", "reason": "Удаление зуба"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["to_specialist"] == "Хирург"

    async def test_get_referrals_list(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE_RF}/", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_referral_by_id(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        cr = await client.post(
            f"{BASE_RF}/",
            json={"patient_id": patient_id, "to_specialist": "Ортодонт", "reason": "Коррекция прикуса"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        ref_id = cr.json()["id"]
        resp = await client.get(f"{BASE_RF}/{ref_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == ref_id

    async def test_get_referral_not_found(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE_RF}/999999", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 404

    async def test_referrals_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE_RF}/")
        assert resp.status_code == 401


class TestWorkOrders:

    async def test_create_work_order(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        resp = await client.post(
            f"{BASE_WO}/",
            json={"patient_id": patient_id, "manipulations": "Пломбирование", "materials": "Композит", "labor_cost": 1500.0},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["labor_cost"] == 1500.0

    async def test_get_work_orders_list(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE_WO}/", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_work_order_by_id(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        cr = await client.post(
            f"{BASE_WO}/",
            json={"patient_id": patient_id, "manipulations": "Чистка", "materials": "Паста", "labor_cost": 800.0},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        order_id = cr.json()["id"]
        resp = await client.get(f"{BASE_WO}/{order_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    async def test_get_work_order_not_found(self, client: AsyncClient, dentist_data):
        dentist_token, _ = dentist_data
        resp = await client.get(f"{BASE_WO}/999999", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 404

    async def test_work_orders_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE_WO}/")
        assert resp.status_code == 401
