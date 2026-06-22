from .patients import router as patients_router
from .appointments import router as appointments_router
from .medical_records import router as medical_records_router
from .studies import router as studies_router
from .referrals import router as referrals_router
from .work_orders import router as work_orders_router
from .statistics import router as statistics_router
from .clinic import router as clinic_router

__all__ = [
    "patients_router",
    "appointments_router",
    "medical_records_router",
    "studies_router",
    "referrals_router",
    "work_orders_router",
    "statistics_router",
    "clinic_router",
]