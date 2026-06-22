import requests
from .base_controller import BASE_URL, _get_token, _headers, _serialize


class PatientMedicalInfoController:

    @staticmethod
    def get(patient_id: int):
        token = _get_token('dentist', 'dentist123')
        resp = requests.get(
            f"{BASE_URL}/api/v2/clinic/patient-medical-info/{patient_id}",
            headers=_headers(token), timeout=10
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def upsert(patient_id: int, data: dict):
        token = _get_token('dentist', 'dentist123')
        resp = requests.put(
            f"{BASE_URL}/api/v2/clinic/patient-medical-info/{patient_id}",
            json=_serialize(data),
            headers=_headers(token), timeout=10
        )
        resp.raise_for_status()
        return resp.json()

