import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class WorkOrderController:

    @staticmethod
    def get_all(page=1, size=50, patient_id=None, doctor_id=None):
        """Список нарядов на работу."""
        token = _get_token('dentist', 'dentist123')
        params = {"skip": (page - 1) * size, "limit": size}
        if patient_id:
            params["patient_id"] = patient_id
        if doctor_id:
            params["doctor_id"] = doctor_id
        resp = requests.get(
            f"{BASE_URL}/api/v2/work-orders/",
            params=params,
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_by_id(work_order_id: int):
        """Получить наряд по ID."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(
            f"{BASE_URL}/api/v2/work-orders/{work_order_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        """Создать наряд на работу."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.post(
            f"{BASE_URL}/api/v2/work-orders/",
            json=_serialize(data),
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def delete(work_order_id: int):
        """Удалить наряд."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.delete(
            f"{BASE_URL}/api/v2/work-orders/{work_order_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()

