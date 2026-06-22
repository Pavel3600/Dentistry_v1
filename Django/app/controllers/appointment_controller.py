import requests
from .base_controller import BASE_URL, _headers, _post, _put, _patch, _serialize


class AppointmentController:

    @staticmethod
    def get_all(page=1, size=50, patient_id=None, doctor_id=None):
        """Список записей на приём."""
        params = {"skip": (page - 1) * size, "limit": size}
        if patient_id:
            params["patient_id"] = patient_id
        if doctor_id:
            params["doctor_id"] = doctor_id
        resp = requests.get(
            f"{BASE_URL}/api/v2/appointments/",
            params=params,
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_by_id(appointment_id: int):
        """Получить запись по ID."""
        resp = requests.get(
            f"{BASE_URL}/api/v2/appointments/{appointment_id}",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        """Создать запись на приём."""
        resp = _post(f"{BASE_URL}/api/v2/appointments/", data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def update(appointment_id: int, data: dict):
        """Обновить запись на приём."""
        resp = _put(f"{BASE_URL}/api/v2/appointments/{appointment_id}", data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def update_status(appointment_id: int, status: str):
        """Изменить статус записи."""
        resp = _patch(f"{BASE_URL}/api/v2/appointments/{appointment_id}", {"status": status}, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def delete(appointment_id: int):
        """Удалить запись."""
        resp = requests.delete(
            f"{BASE_URL}/api/v2/appointments/{appointment_id}",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
