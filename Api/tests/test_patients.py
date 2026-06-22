"""Тесты эндпоинтов пациентов (/api/v2/patients/)."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v2/patients"


def uid():
    return uuid.uuid4().hex[:8]


async def _make_patient_user(client: AsyncClient, admin_token: str) -> tuple[int, int]:
    """Создаёт FastAPI-клиента с ролью patient и запись пациента. Возвращает (client_id, patient_id)."""
    login = f"pu_{uid()}"
    r = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": login, "password": "pat12345", "role": "patient"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"], login


async def test_create_patient(client: AsyncClient, manager_token: str, admin_token: str):
    """Менеджер создаёт пациента."""
    client_id, _ = await _make_patient_user(client, admin_token)
    resp = await client.post(
        f"{BASE}/",
        json={
            "full_name": "Тест Иванов",
            "birth_date": "1990-05-20T00:00:00",
            "gender": "M",
            "phone": f"+7900{uid()[:7]}",
            "user_id": client_id,
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["full_name"] == "Тест Иванов"
    assert data["user_id"] == client_id
    assert "card_number" in data and data["card_number"]


async def test_create_patient_wrong_role(client: AsyncClient, manager_token: str, admin_token: str):
    """Нельзя создать пациента с user_id менеджера (роль manager, не patient)."""
    login = f"mgr2_{uid()}"
    r = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": login, "password": "mgr12345", "role": "manager"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    mgr_id = r.json()["id"]
    resp = await client.post(
        f"{BASE}/",
        json={
            "full_name": "Не пациент",
            "birth_date": "1985-01-01T00:00:00",
            "gender": "F",
            "phone": "+70000000000",
            "user_id": mgr_id,
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 400


async def test_get_patients_list(client: AsyncClient, manager_token: str):
    """Список пациентов возвращает 200 с пагинацией."""
    resp = await client.get(f"{BASE}/", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data or isinstance(data, list)


async def test_get_patient_by_id(client: AsyncClient, manager_token: str, admin_token: str):
    """Получить конкретного пациента по id."""
    client_id, _ = await _make_patient_user(client, admin_token)
    create_resp = await client.post(
        f"{BASE}/",
        json={
            "full_name": "Петров Пётр",
            "birth_date": "1980-03-15T00:00:00",
            "gender": "M",
            "phone": f"+7901{uid()[:7]}",
            "user_id": client_id,
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    patient_id = create_resp.json()["id"]
    resp = await client.get(f"{BASE}/{patient_id}", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 200
    assert resp.json()["id"] == patient_id


async def test_get_patient_not_found(client: AsyncClient, manager_token: str):
    """Несуществующий пациент — 404."""
    resp = await client.get(f"{BASE}/999999", headers={"Authorization": f"Bearer {manager_token}"})
    assert resp.status_code == 404


async def test_update_patient(client: AsyncClient, manager_token: str, admin_token: str):
    """Обновление данных пациента."""
    client_id, _ = await _make_patient_user(client, admin_token)
    cr = await client.post(
        f"{BASE}/",
        json={
            "full_name": "Сидоров Сидор",
            "birth_date": "1975-07-10T00:00:00",
            "gender": "M",
            "phone": f"+7902{uid()[:7]}",
            "user_id": client_id,
        },
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    patient_id = cr.json()["id"]
    resp = await client.put(
        f"{BASE}/{patient_id}",
        json={"full_name": "Сидоров Иван", "phone": f"+7903{uid()[:7]}"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Сидоров Иван"


async def test_patients_require_auth(client: AsyncClient):
    """Без токена — 401."""
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 401
