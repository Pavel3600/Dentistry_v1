"""Тесты эндпоинтов записей на приём (/api/v2/appointments/)."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v2/appointments"
PATIENTS = "/api/v2/patients"


def uid():
    return uuid.uuid4().hex[:8]


async def _setup(client: AsyncClient, admin_token: str, manager_token: str) -> tuple[int, int]:
    """Создаёт пациента и врача, возвращает (patient_id, dentist_client_id)."""
    # patient user
    pu = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"ap_{uid()}", "password": "pat12345", "role": "patient"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    patient_client_id = pu.json()["id"]
    pr = await client.post(
        f"{PATIENTS}/",
        json={
            "full_name": f"Апп Пациент {uid()}",
            "birth_date": "1992-06-15T00:00:00",
            "gender": "F",
            "phone": f"+7910{uid()[:7]}",
            "user_id": patient_client_id,
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert pr.status_code == 201, pr.text
    patient_id = pr.json()["id"]

    # dentist
    dr = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"ad_{uid()}", "password": "dnt12345", "role": "dentist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    dentist_id = dr.json()["id"]
    return patient_id, dentist_id


async def test_create_appointment(client: AsyncClient, manager_token: str, admin_token: str):
    """Менеджер создаёт запись на приём."""
    patient_id, dentist_id = await _setup(client, admin_token, manager_token)
    resp = await client.post(
        f"{BASE}/",
        json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-09-01T10:00:00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["patient_id"] == patient_id
    assert data["doctor_id"] == dentist_id
    assert data["status"] == "scheduled"


async def test_create_appointment_invalid_patient(client: AsyncClient, manager_token: str, admin_token: str):
    """Несуществующий пациент — 404."""
    _, dentist_id = await _setup(client, admin_token, manager_token)
    resp = await client.post(
        f"{BASE}/",
        json={"patient_id": 999999, "doctor_id": dentist_id, "datetime": "2026-09-02T10:00:00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 404


async def test_create_appointment_wrong_doctor_role(client: AsyncClient, manager_token: str, admin_token: str):
    """ID клиента не с ролью dentist — 400."""
    patient_id, _ = await _setup(client, admin_token, manager_token)
    # Используем patient_id как doctor_id (роль patient, не dentist)
    # Сначала получим id самого пациента-клиента
    pu = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"nondnt_{uid()}", "password": "pat12345", "role": "patient"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    wrong_id = pu.json()["id"]
    resp = await client.post(
        f"{BASE}/",
        json={"patient_id": patient_id, "doctor_id": wrong_id, "datetime": "2026-09-03T10:00:00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 400


async def test_get_appointments_list(client: AsyncClient, manager_token: str):
    """Список записей — 200."""
    resp = await client.get(f"{BASE}/", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_get_appointment_by_id(client: AsyncClient, manager_token: str, admin_token: str):
    """Получить запись по ID."""
    patient_id, dentist_id = await _setup(client, admin_token, manager_token)
    cr = await client.post(
        f"{BASE}/",
        json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-10-01T09:00:00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    appt_id = cr.json()["id"]
    resp = await client.get(f"{BASE}/{appt_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == appt_id


async def test_get_appointment_not_found(client: AsyncClient, manager_token: str):
    """Несуществующая запись — 404."""
    resp = await client.get(f"{BASE}/999999", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 404


async def test_cancel_appointment(client: AsyncClient, manager_token: str, admin_token: str):
    """Отмена записи через DELETE."""
    patient_id, dentist_id = await _setup(client, admin_token, manager_token)
    cr = await client.post(
        f"{BASE}/",
        json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-11-01T14:00:00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    appt_id = cr.json()["id"]
    resp = await client.delete(f"{BASE}/{appt_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 204


async def test_appointments_require_auth(client: AsyncClient):
    """Без токена — 401."""
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 401


async def test_dentist_cannot_create_appointment(client: AsyncClient, dentist_data):
    """Врач не может создать запись (только менеджер)."""
    dentist_token, _ = dentist_data
    resp = await client.post(
        f"{BASE}/",
        json={"patient_id": 1, "doctor_id": 1, "datetime": "2026-12-01T11:00:00"},
        headers={"Authorization": f"Bearer {dentist_token}"},
    )
    assert resp.status_code == 403
