import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class ClientController:

    @staticmethod
    def get_all():
        """Список всех клиентов."""
        token = _get_token('manager', 'manager123')
        resp = requests.get(
            f"{BASE_URL}/api/v1/clients/",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_by_id(client_id: int):
        """Получить клиента по ID."""
        token = _get_token('manager', 'manager123')
        resp = requests.get(
            f"{BASE_URL}/api/v1/clients/{client_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        """Создать клиента."""
        token = _get_token('admin', 'admin123')
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=_serialize(data),
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def delete(client_id: int):
        """Удалить клиента."""
        token = _get_token('admin', 'admin123')
        resp = requests.delete(
            f"{BASE_URL}/api/v1/clients/{client_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()

    @staticmethod
    def get_doctors():
        """Список врачей (role=dentist)."""
        token = _get_token('manager', 'manager123')
        resp = requests.get(
            f"{BASE_URL}/api/v1/clients/",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        clients = resp.json()
        return [c for c in clients if c.get('role') == 'dentist']

