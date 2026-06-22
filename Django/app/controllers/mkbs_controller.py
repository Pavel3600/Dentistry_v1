import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class MKBSController:

    @staticmethod
    def get_diagnoses(search=None, page=1, size=100):
        """Список диагнозов МКБ."""
        token = _get_token('dentist', 'dentist123')
        params = {"skip": (page - 1) * size, "limit": size}
        if search:
            params["search"] = search
        resp = requests.get(
            f"{BASE_URL}/api/v2/mkbs/diagnoses",
            params=params,
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_services(search=None, page=1, size=100):
        """Список услуг МКБ."""
        token = _get_token('dentist', 'dentist123')
        params = {"skip": (page - 1) * size, "limit": size}
        if search:
            params["search"] = search
        resp = requests.get(
            f"{BASE_URL}/api/v2/mkbs/services",
            params=params,
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_all(search=None, category=None, page=1, size=100, **kwargs):
        """Список всех кодов МКБ."""
        token = _get_token('dentist', 'dentist123')
        params = {"skip": (page - 1) * size, "limit": size}
        if search:
            params["search"] = search
        if category:
            params["category"] = category
        resp = requests.get(
            f"{BASE_URL}/api/v2/mkbs/",
            params=params,
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_by_id(mkbs_id: int):
        """Получить код МКБ по ID."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(
            f"{BASE_URL}/api/v2/mkbs/{mkbs_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        """Создать код МКБ."""
        token = _get_token('admin', 'admin123')
        resp = requests.post(
            f"{BASE_URL}/api/v2/mkbs/",
            json=_serialize(data),
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def update(mkbs_id: int, data: dict):
        """Обновить код МКБ."""
        token = _get_token('admin', 'admin123')
        resp = requests.put(
            f"{BASE_URL}/api/v2/mkbs/{mkbs_id}",
            json=_serialize(data),
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def delete(mkbs_id: int):
        """Удалить код МКБ."""
        token = _get_token('admin', 'admin123')
        resp = requests.delete(
            f"{BASE_URL}/api/v2/mkbs/{mkbs_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()

