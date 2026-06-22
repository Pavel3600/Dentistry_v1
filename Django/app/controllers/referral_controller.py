import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class ReferralController:

    @staticmethod
    def get_all(page=1, size=50, patient_id=None):
        """Список направлений."""
        token = _get_token('dentist', 'dentist123')
        params = {"skip": (page - 1) * size, "limit": size}
        if patient_id:
            params["patient_id"] = patient_id
        resp = requests.get(
            f"{BASE_URL}/api/v2/referrals/",
            params=params,
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get('items', data) if isinstance(data, dict) else data

    @staticmethod
    def get_by_id(referral_id: int):
        """Получить направление по ID."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(
            f"{BASE_URL}/api/v2/referrals/{referral_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        """Создать направление."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.post(
            f"{BASE_URL}/api/v2/referrals/",
            json=_serialize(data),
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def delete(referral_id: int):
        """Удалить направление."""
        token = _get_token('dentist', 'dentist123')
        resp = requests.delete(
            f"{BASE_URL}/api/v2/referrals/{referral_id}",
            headers=_headers(token),
            timeout=10,
        )
        resp.raise_for_status()

