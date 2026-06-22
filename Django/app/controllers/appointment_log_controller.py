import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class AppointmentLogController:

    @staticmethod
    def get_all(appointment_id=None, **kwargs):
        token = _get_token('manager', 'manager123')
        params = {}
        if appointment_id:
            params['appointment_id'] = appointment_id
        resp = requests.get(
            f"{BASE_URL}/api/v2/clinic/appointment-logs/",
            params=params,
            headers=_headers(token), timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_by_appointment(appointment_id: int):
        token = _get_token('manager', 'manager123')
        resp = requests.get(
            f"{BASE_URL}/api/v2/clinic/appointment-logs/",
            params={"appointment_id": appointment_id},
            headers=_headers(token), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        token = _get_token('manager', 'manager123')
        resp = requests.post(
            f"{BASE_URL}/api/v2/clinic/appointment-logs/",
            json=_serialize(data),
            headers=_headers(token), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

