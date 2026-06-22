import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class CategoryController:
    """Контроллер категорий МКБ (диагнозы и услуги)."""

    @staticmethod
    def get_all(category_type=None, search=None, page=1, size=100):
        """Список кодов МКБ. category_type: 'diagnosis' | 'service' | None."""
        token = _get_token('dentist', 'dentist123')
        params = {"skip": (page - 1) * size, "limit": size}
        if search:
            params["search"] = search
        if category_type == 'diagnosis':
            url = f"{BASE_URL}/api/v2/mkbs/diagnoses"
        elif category_type == 'service':
            url = f"{BASE_URL}/api/v2/mkbs/services"
        else:
            url = f"{BASE_URL}/api/v2/mkbs/diagnoses"
        resp = requests.get(url, params=params, headers=_headers(token), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_by_id(mkbs_id: int):
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
    def delete(mkbs_id: int):
        token = _get_token('admin', 'admin123')
        resp = requests.delete(
            f"{BASE_URL}/api/v2/mkbs/{mkbs_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()

