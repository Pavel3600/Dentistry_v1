"""Тесты clinic-роутера (/api/v2/clinic/): Services, Materials, Visits, Patients CRUD."""
import uuid
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

BASE = "/api/v2/clinic"
PATIENTS = "/api/v2/patients"
APPTS = "/api/v2/appointments"


def uid():
    return uuid.uuid4().hex[:8]


async def _make_patient(client, admin_token, manager_token) -> int:
    pu = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"cp_{uid()}", "password": "pat12345", "role": "patient"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    pr = await client.post(
        f"{PATIENTS}/",
        json={"full_name": f"Клиник Пациент {uid()}", "birth_date": "1988-06-15T00:00:00",
              "gender": "M", "phone": f"+7914{uid()[:7]}", "user_id": pu.json()["id"]},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert pr.status_code == 201, pr.text
    return pr.json()["id"]


async def _make_dentist(client, admin_token) -> int:
    dr = await client.post(
        "/api/v1/auth/admin/users",
        json={"login": f"cd_{uid()}", "password": "dnt12345", "role": "dentist"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dr.status_code == 201, dr.text
    return dr.json()["id"]


async def _make_appointment(client, admin_token, manager_token) -> tuple[int, int, int]:
    """Returns (appointment_id, patient_id, dentist_id)."""
    patient_id = await _make_patient(client, admin_token, manager_token)
    dentist_id = await _make_dentist(client, admin_token)
    ar = await client.post(
        f"{APPTS}/",
        json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-10-15T11:00:00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert ar.status_code == 201, ar.text
    return ar.json()["id"], patient_id, dentist_id


class TestServices:

    async def test_list_services(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/services/", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_service(self, client: AsyncClient, manager_token: str):
        resp = await client.post(
            f"{BASE}/services/",
            json={"code": f"S{uid()[:4]}", "name": "Пломбирование", "cost": 2500.0, "duration_minutes": 45},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "Пломбирование"
        assert data["cost"] == 2500.0

    async def test_get_service_by_id(self, client: AsyncClient, manager_token: str):
        cr = await client.post(
            f"{BASE}/services/",
            json={"code": f"S{uid()[:4]}", "name": "Чистка зубов", "cost": 1500.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        svc_id = cr.json()["id"]
        resp = await client.get(f"{BASE}/services/{svc_id}", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == svc_id

    async def test_get_service_not_found(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/services/999999", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 404

    async def test_update_service(self, client: AsyncClient, manager_token: str):
        cr = await client.post(
            f"{BASE}/services/",
            json={"code": f"S{uid()[:4]}", "name": "Старое имя", "cost": 1000.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        svc_id = cr.json()["id"]
        resp = await client.put(
            f"{BASE}/services/{svc_id}",
            json={"name": "Новое имя", "cost": 1200.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Новое имя"

    async def test_delete_service(self, client: AsyncClient, manager_token: str):
        cr = await client.post(
            f"{BASE}/services/",
            json={"code": f"S{uid()[:4]}", "name": "Удалить меня", "cost": 500.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        svc_id = cr.json()["id"]
        resp = await client.delete(f"{BASE}/services/{svc_id}", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 204

    async def test_services_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/services/")
        assert resp.status_code == 401


class TestMaterials:

    async def test_list_materials(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/materials/", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_material(self, client: AsyncClient, manager_token: str):
        resp = await client.post(
            f"{BASE}/materials/",
            json={"name": f"Композит {uid()[:4]}", "unit": "г", "price_per_unit": 150.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["price_per_unit"] == 150.0

    async def test_get_material_by_id(self, client: AsyncClient, manager_token: str):
        cr = await client.post(
            f"{BASE}/materials/",
            json={"name": f"Анестетик {uid()[:4]}", "unit": "мл", "price_per_unit": 80.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        mat_id = cr.json()["id"]
        resp = await client.get(f"{BASE}/materials/{mat_id}", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == mat_id

    async def test_get_material_not_found(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/materials/999999", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 404

    async def test_update_material(self, client: AsyncClient, manager_token: str):
        cr = await client.post(
            f"{BASE}/materials/",
            json={"name": f"Мат {uid()[:4]}", "unit": "шт", "price_per_unit": 100.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        mat_id = cr.json()["id"]
        resp = await client.put(
            f"{BASE}/materials/{mat_id}",
            json={"price_per_unit": 120.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["price_per_unit"] == 120.0

    async def test_delete_material(self, client: AsyncClient, manager_token: str):
        cr = await client.post(
            f"{BASE}/materials/",
            json={"name": f"Удалить {uid()[:4]}", "unit": "шт", "price_per_unit": 50.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        mat_id = cr.json()["id"]
        resp = await client.delete(f"{BASE}/materials/{mat_id}", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 204

    async def test_materials_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/materials/")
        assert resp.status_code == 401


class TestVisits:

    async def test_list_visits(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/visits/", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_create_visit(self, client: AsyncClient, admin_token: str, manager_token: str, dentist_data):
        dentist_token, dentist_id = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        ar = await client.post(
            f"{APPTS}/",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-09-20T14:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        appt_id = ar.json()["id"]
        resp = await client.post(
            f"{BASE}/visits/",
            json={"appointment_id": appt_id, "patient_id": patient_id, "doctor_id": dentist_id,
                  "anamnesis": "Жалобы на боль", "diagnosis_id": None},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["appointment_id"] == appt_id

    async def test_create_visit_duplicate(self, client: AsyncClient, admin_token: str, manager_token: str, dentist_data):
        dentist_token, dentist_id = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        ar = await client.post(
            f"{APPTS}/",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-08-10T10:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        appt_id = ar.json()["id"]
        visit_data = {"appointment_id": appt_id, "patient_id": patient_id, "doctor_id": dentist_id}
        await client.post(f"{BASE}/visits/", json=visit_data, headers={"Authorization": f"Bearer {dentist_token}"})
        # Второй визит для той же записи — ошибка
        resp = await client.post(f"{BASE}/visits/", json=visit_data, headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 400

    async def test_get_visit_by_id(self, client: AsyncClient, admin_token: str, manager_token: str, dentist_data):
        dentist_token, dentist_id = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        ar = await client.post(
            f"{APPTS}/",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-07-05T09:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        appt_id = ar.json()["id"]
        cr = await client.post(
            f"{BASE}/visits/",
            json={"appointment_id": appt_id, "patient_id": patient_id, "doctor_id": dentist_id},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        visit_id = cr.json()["id"]
        resp = await client.get(f"{BASE}/visits/{visit_id}", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 200
        assert resp.json()["id"] == visit_id

    async def test_get_visit_not_found(self, client: AsyncClient, manager_token: str):
        resp = await client.get(f"{BASE}/visits/999999", headers={"Authorization": f"Bearer {manager_token}"})
        assert resp.status_code == 404

    async def test_get_visit_by_appointment(self, client: AsyncClient, admin_token: str, manager_token: str, dentist_data):
        dentist_token, dentist_id = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        ar = await client.post(
            f"{APPTS}/",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-06-15T08:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        appt_id = ar.json()["id"]
        await client.post(
            f"{BASE}/visits/",
            json={"appointment_id": appt_id, "patient_id": patient_id, "doctor_id": dentist_id},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        resp = await client.get(
            f"{BASE}/visits/by-appointment/{appt_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["appointment_id"] == appt_id

    async def test_visits_require_auth(self, client: AsyncClient):
        resp = await client.get(f"{BASE}/visits/")
        assert resp.status_code == 401


class TestPatientsV2Extended:
    """Дополнительные тесты v2/patients/ не покрытые в test_patients.py."""

    async def test_delete_patient(self, client: AsyncClient, admin_token: str, manager_token: str):
        pu = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"del_{uid()}", "password": "pat12345", "role": "patient"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pr = await client.post(
            f"{PATIENTS}/",
            json={"full_name": "Удалить Пациент", "birth_date": "1990-01-01T00:00:00",
                  "gender": "F", "phone": f"+7915{uid()[:7]}", "user_id": pu.json()["id"]},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        patient_id = pr.json()["id"]
        resp = await client.delete(
            f"{PATIENTS}/{patient_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204

    async def test_delete_patient_not_found(self, client: AsyncClient, admin_token: str):
        resp = await client.delete(f"{PATIENTS}/999999", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 404

    async def test_create_patient_duplicate_user(self, client: AsyncClient, admin_token: str, manager_token: str):
        pu = await client.post(
            "/api/v1/auth/admin/users",
            json={"login": f"dup_{uid()}", "password": "pat12345", "role": "patient"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        user_id = pu.json()["id"]
        payload = {"full_name": "Дубль Пациент", "birth_date": "1990-01-01T00:00:00",
                   "gender": "M", "phone": f"+7916{uid()[:7]}", "user_id": user_id}
        r1 = await client.post(f"{PATIENTS}/", json=payload, headers={"Authorization": f"Bearer {manager_token}"})
        assert r1.status_code == 201
        # Второй пациент с тем же user_id — ошибка
        payload["phone"] = f"+7917{uid()[:7]}"
        r2 = await client.post(f"{PATIENTS}/", json=payload, headers={"Authorization": f"Bearer {manager_token}"})
        assert r2.status_code == 400

    async def test_appointments_filter_by_patient(self, client: AsyncClient, admin_token: str, manager_token: str):
        patient_id = await _make_patient(client, admin_token, manager_token)
        dentist_id = await _make_dentist(client, admin_token)
        await client.post(
            f"{APPTS}/",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-10-01T10:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        resp = await client.get(
            f"{APPTS}/?patient_id={patient_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["patient_id"] == patient_id for a in data)

    async def test_appointments_filter_by_doctor(self, client: AsyncClient, admin_token: str, manager_token: str):
        patient_id = await _make_patient(client, admin_token, manager_token)
        dentist_id = await _make_dentist(client, admin_token)
        await client.post(
            f"{APPTS}/",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-10-02T10:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        resp = await client.get(
            f"{APPTS}/?doctor_id={dentist_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 200
        assert all(a["doctor_id"] == dentist_id for a in resp.json())


async def _create_visit(client, admin_token, manager_token, dentist_token, dentist_id) -> tuple[int, int, int]:
    """Returns (visit_id, appointment_id, patient_id)."""
    patient_id = await _make_patient(client, admin_token, manager_token)
    ar = await client.post(
        f"{APPTS}/",
        json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-11-05T16:00:00"},
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    appt_id = ar.json()["id"]
    vr = await client.post(
        f"{BASE}/visits/",
        json={"appointment_id": appt_id, "patient_id": patient_id, "doctor_id": dentist_id},
        headers={"Authorization": f"Bearer {dentist_token}"},
    )
    assert vr.status_code == 201, vr.text
    return vr.json()["id"], appt_id, patient_id


class TestProcedures:

    async def test_create_and_list_procedures(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        visit_id, _, _ = await _create_visit(client, admin_token, manager_token, dentist_token, dentist_id)
        # Создать услугу
        svc = await client.post(
            f"{BASE}/services/",
            json={"code": f"P{uid()[:4]}", "name": "Процедура тест", "cost": 3000.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        svc_id = svc.json()["id"]
        # Добавить процедуру к визиту
        resp = await client.post(
            f"{BASE}/visits/{visit_id}/procedures",
            json={"service_id": svc_id, "quantity": 2},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["total_cost"] == 6000.0

        # Список процедур
        lr = await client.get(f"{BASE}/visits/{visit_id}/procedures", headers={"Authorization": f"Bearer {manager_token}"})
        assert lr.status_code == 200
        assert isinstance(lr.json(), list)
        assert len(lr.json()) >= 1

    async def test_create_procedure_service_not_found(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        visit_id, _, _ = await _create_visit(client, admin_token, manager_token, dentist_token, dentist_id)
        resp = await client.post(
            f"{BASE}/visits/{visit_id}/procedures",
            json={"service_id": 999999, "quantity": 1},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 404

    async def test_delete_procedure(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        visit_id, _, _ = await _create_visit(client, admin_token, manager_token, dentist_token, dentist_id)
        svc = await client.post(
            f"{BASE}/services/",
            json={"code": f"D{uid()[:4]}", "name": "Удал процедура", "cost": 100.0},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        pr = await client.post(
            f"{BASE}/visits/{visit_id}/procedures",
            json={"service_id": svc.json()["id"], "quantity": 1},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        proc_id = pr.json()["id"]
        resp = await client.delete(f"{BASE}/procedures/{proc_id}", headers={"Authorization": f"Bearer {dentist_token}"})
        assert resp.status_code == 204


class TestInvestigations:

    async def test_create_and_list_investigations(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        visit_id, _, _ = await _create_visit(client, admin_token, manager_token, dentist_token, dentist_id)
        resp = await client.post(
            f"{BASE}/visits/{visit_id}/investigations",
            json={"type": "Рентген", "description": "Снимок зуба 16", "result": "Кариес"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["type"] == "Рентген"

        lr = await client.get(f"{BASE}/visits/{visit_id}/investigations", headers={"Authorization": f"Bearer {manager_token}"})
        assert lr.status_code == 200
        assert len(lr.json()) >= 1


class TestAppointmentLogs:

    async def test_create_and_list_logs(self, client: AsyncClient, admin_token, manager_token):
        patient_id = await _make_patient(client, admin_token, manager_token)
        dentist_id = await _make_dentist(client, admin_token)
        ar = await client.post(
            f"{APPTS}/",
            json={"patient_id": patient_id, "doctor_id": dentist_id, "datetime": "2026-12-05T10:00:00"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        appt_id = ar.json()["id"]
        resp = await client.post(
            f"{BASE}/appointment-logs/",
            json={"appointment_id": appt_id, "old_status": "scheduled", "new_status": "completed", "comment": "Готово"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["new_status"] == "completed"

        lr = await client.get(
            f"{BASE}/appointment-logs/?appointment_id={appt_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert lr.status_code == 200
        assert len(lr.json()) >= 1


class TestPatientMedicalInfo:

    async def test_upsert_and_get_medical_info(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, _ = dentist_data
        patient_id = await _make_patient(client, admin_token, manager_token)
        # Создать (upsert)
        resp = await client.put(
            f"{BASE}/patient-medical-info/{patient_id}",
            json={"allergies": "Пенициллин", "blood_type": "A+"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["allergies"] == "Пенициллин"

        # Получить
        gr = await client.get(
            f"{BASE}/patient-medical-info/{patient_id}",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert gr.status_code == 200
        assert gr.json()["blood_type"] == "A+"

    async def test_get_medical_info_not_found(self, client: AsyncClient, manager_token: str):
        resp = await client.get(
            f"{BASE}/patient-medical-info/999999",
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 404


class TestExtractsAndReports:

    async def test_create_and_list_extracts(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        visit_id, _, _ = await _create_visit(client, admin_token, manager_token, dentist_token, dentist_id)
        resp = await client.post(
            f"{BASE}/visits/{visit_id}/extracts",
            json={"visit_id": visit_id, "content": "Выписка из медкарты"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["content"] == "Выписка из медкарты"

        lr = await client.get(f"{BASE}/visits/{visit_id}/extracts", headers={"Authorization": f"Bearer {manager_token}"})
        assert lr.status_code == 200
        assert len(lr.json()) >= 1

    async def test_create_and_list_visit_reports(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        visit_id, _, _ = await _create_visit(client, admin_token, manager_token, dentist_token, dentist_id)
        resp = await client.post(
            f"{BASE}/visits/{visit_id}/reports",
            json={"visit_id": visit_id, "title": "Отчёт", "summary": "Всё хорошо", "recommendations": "Чистить зубы"},
            headers={"Authorization": f"Bearer {manager_token}"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["summary"] == "Всё хорошо"

        lr = await client.get(f"{BASE}/visits/{visit_id}/reports", headers={"Authorization": f"Bearer {manager_token}"})
        assert lr.status_code == 200
        assert len(lr.json()) >= 1


class TestVisitUpdate:

    async def test_update_visit(self, client: AsyncClient, admin_token, manager_token, dentist_data):
        dentist_token, dentist_id = dentist_data
        visit_id, _, _ = await _create_visit(client, admin_token, manager_token, dentist_token, dentist_id)
        resp = await client.put(
            f"{BASE}/visits/{visit_id}",
            json={"treatment_plan": "Пломбирование 2 зубов", "prescription": "Ибупрофен"},
            headers={"Authorization": f"Bearer {dentist_token}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["treatment_plan"] == "Пломбирование 2 зубов"
