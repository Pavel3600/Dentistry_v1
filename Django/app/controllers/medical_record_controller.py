import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class MedicalRecordController:

    @staticmethod
    def get_all(page=1, size=50, patient_id=None):
        """Список медицинских записей."""
        token = _get_token('dentist', 'dentist123')
        params = {"skip": (page - 1) * size, "limit": size}
        if patient_id:
            params["patient_id"] = patient_id
        resp = requests.get(
            f"{BASE_URL}/api/v2/medical-records/",
            params=params,
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_by_id(record_id: int):
        """Получить запись по ID."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(
            f"{BASE_URL}/api/v2/medical-records/{record_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        """Создать медицинскую запись."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.post(
            f"{BASE_URL}/api/v2/medical-records/",
            json=_serialize(data),
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def update(record_id: int, data: dict):
        """Обновить медицинскую запись."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.put(
            f"{BASE_URL}/api/v2/medical-records/{record_id}",
            json=_serialize(data),
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

