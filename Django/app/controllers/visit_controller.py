import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class VisitController:

    @staticmethod
    def get_all(page=1, size=50, patient_id=None, doctor_id=None):
        token = _get_token('dentist', 'dentist123')
        params = {"skip": (page - 1) * size, "limit": size}
        if patient_id:
            params["patient_id"] = patient_id
        if doctor_id:
            params["doctor_id"] = doctor_id
        resp = requests.get(f"{BASE_URL}/api/v2/clinic/visits/", params=params, headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_by_id(visit_id: int):
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}", headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_by_appointment(appointment_id: int):
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(
            f"{BASE_URL}/api/v2/clinic/visits/by-appointment/{appointment_id}",
            headers=_headers(token), timeout=10
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create(data: dict):
        token = _get_token('dentist', 'dentist123')
        resp = requests.post(f"{BASE_URL}/api/v2/clinic/visits/", json=_serialize(data), headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def update(visit_id: int, data: dict):
        token = _get_token('dentist', 'dentist123')
        resp = requests.put(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}", json=_serialize(data), headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_procedures(visit_id: int):
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}/procedures", headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def add_procedure(visit_id: int, data: dict):
        token = _get_token('dentist', 'dentist123')
        resp = requests.post(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}/procedures", json=_serialize(data), headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_investigations(visit_id: int):
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}/investigations", headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def add_investigation(visit_id: int, data: dict):
        token = _get_token('dentist', 'dentist123')
        resp = requests.post(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}/investigations", json=_serialize(data), headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_extracts(visit_id: int):
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}/extracts", headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create_extract(visit_id: int, data: dict):
        token = _get_token('dentist', 'dentist123')
        resp = requests.post(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}/extracts", json=_serialize(data), headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_reports(visit_id: int):
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}/reports", headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def create_report(visit_id: int, data: dict):
        token = _get_token('dentist', 'dentist123')
        resp = requests.post(f"{BASE_URL}/api/v2/clinic/visits/{visit_id}/reports", json=_serialize(data), headers=_headers(token), timeout=10)
        resp.raise_for_status()
        return resp.json()
