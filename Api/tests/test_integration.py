"""Интеграционные тесты: сквозные сценарии и проверка ролей."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def uid():
    return uuid.uuid4().hex[:8]


class TestIntegration:

    async def test_full_patient_flow(self, client: AsyncClient, admin_token: str, manager_token: str, dentist_data):
        """Полный цикл: создание пациента → запись → медкарта → смена статуса."""
        dentist_token, dentist_id = dentist_data

        # Создать пациента
        pu = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"fp_{uid()}", "password": "pat12345", "role": "patient"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert pu.status_code == 201, pu.text
        pr = await client.post(
            "/api/v2/patients/",
            json={"full_name": f"Полный Поток {uid()}", "birth_date": "1985-03-15T00:00:00",
                  "gender": "M", "phone": f"+7912{uid()[:7]}", "user_id": pu.json()["id"]},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert pr.status_code == 201, pr.text
        patient_id = pr.json()["id"]

        # Создать запись на приём
        ar = await client.post(
            "/api/v2/appointments/",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-12-25T10:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert ar.status_code == 201, ar.text
        appointment_id = ar.json()["id"]
        assert ar.json()["status"] == "scheduled"

        # Сменить статус записи
        patch_r = await client.patch(
            f"/api/v2/appointments/{appointment_id}",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert patch_r.status_code == 200, patch_r.text
        assert patch_r.json()["status"] == "completed"

        # Создать медицинскую запись
        mr = await client.post(
            "/api/v2/medical-records/",
            json={"patient_id": patient_id, "complaints": "Боль", "diagnosis": "Кариес K02"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert mr.status_code == 201, mr.text

    async def test_role_permissions(self, client: AsyncClient, admin_token: str, manager_token: str, dentist_data):
        """Разные роли получают корректные ответы на защищённые эндпоинты."""
        dentist_token, _ = dentist_data

        # Менеджер не может создавать медзаписи (только dentist)
        r = await client.post(
            "/api/v2/medical-records/",
            json={"patient_id": 1, "diagnosis": "Тест"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 403

        # Стоматолог не может создавать записи на приём (только manager)
        r = await client.post(
            "/api/v2/appointments/",
            json={"patient_id": 1, "doctor_id": 1, "datetime": "2026-12-01T10:00:00"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert r.status_code == 403

        # Стоматолог не может просматривать статистику (только manager)
        r = await client.get(
            "/api/v2/stats/appointments-count",
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert r.status_code == 403

        # Менеджер не может просматривать МКБ (только dentist)
        r = await client.get(
            "/api/v2/mkbs/diagnoses",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert r.status_code == 403

    async def test_cors_headers(self, client: AsyncClient):
        resp = await client.options(
            "/api/v1/",
            headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
        )
        assert "access-control-allow-origin" in resp.headers

    async def test_appointment_patch_invalid_status(self, client: AsyncClient, admin_token: str, manager_token: str):
        """Попытка поставить недопустимый статус — 400."""
        pu = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"ps_{uid()}", "password": "pat12345", "role": "patient"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pr = await client.post(
            "/api/v2/patients/",
            json={"full_name": "Статус Тест", "birth_date": "1990-01-01T00:00:00",
                  "gender": "F", "phone": f"+7913{uid()[:7]}", "user_id": pu.json()["id"]},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        dr = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"sd_{uid()}", "password": "dnt12345", "role": "dentist"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ar = await client.post(
            "/api/v2/appointments/",
            json={"patient_id": pr.json()["id"], "doctor_id": dr.json()["id"], "datetime": "2026-11-10T09:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        appt_id = ar.json()["id"]
        resp = await client.patch(
            f"/api/v2/appointments/{appt_id}",
            json={"status": "unknown_status"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 400
