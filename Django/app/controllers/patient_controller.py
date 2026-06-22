import requests
from .base_controller import BASE_URL, _headers, _post, _put


class PatientController:

    @staticmethod
    def get_all(page=1, size=50):
        """Список пациентов с пагинацией."""
        skip = (page - 1) * size
        resp = requests.get(
            f"{BASE_URL}/api/v2/patients/",
            params={"skip": skip, "limit": size},
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_by_id(patient_id: int):
        """Получить пациента по ID."""
        resp = requests.get(
            f"{BASE_URL}/api/v2/patients/{patient_id}",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        """Создать пациента."""
        resp = _post(f"{BASE_URL}/api/v2/patients/", data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def update(patient_id: int, data: dict):
        """Обновить пациента."""
        resp = _put(f"{BASE_URL}/api/v2/patients/{patient_id}", data, timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def delete(patient_id: int):
        """Удалить пациента."""
        resp = requests.delete(
            f"{BASE_URL}/api/v2/patients/{patient_id}",
            headers=_headers(),
            timeout=10,
        )
        resp.raise_for_status()
