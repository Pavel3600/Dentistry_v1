import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class ServiceController:

    @staticmethod
    def get_all(page=1, size=100):
        token = _get_token('manager', 'manager123')
        resp = requests.get(
            f"{BASE_URL}/api/v2/clinic/services/",
            params={"skip": (page - 1) * size, "limit": size},
            headers=_headers(token), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_by_id(service_id: int):
        token = _get_token('manager', 'manager123')
        resp = requests.get(f"{BASE_URL}/api/v2/clinic/services/{service_id}", headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        token = _get_token('manager', 'manager123')
        resp = requests.post(f"{BASE_URL}/api/v2/clinic/services/", json=_serialize(data), headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def update(service_id: int, data: dict):
        token = _get_token('manager', 'manager123')
        resp = requests.put(f"{BASE_URL}/api/v2/clinic/services/{service_id}", json=_serialize(data), headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def delete(service_id: int):
        token = _get_token('manager', 'manager123')
        resp = requests.delete(f"{BASE_URL}/api/v2/clinic/services/{service_id}", headers=_headers(token), timeout=10)
        resp.raise_for_status()

