from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import auth, client, manager, dentist, extended, mkb_codes, patients, endpoints
from app.api.routers.v2 import (
    patients_router,
    appointments_router,
    medical_records_router,
    studies_router,
    referrals_router,
    work_orders_router,
    statistics_router,
    clinic_router,
)
from app.api.routers import mkbs
from app.init_db import init_database

# ========== V1 ==========
app_v1 = FastAPI(
    title="Dentistry API v1",
    description="REST API для управления стоматологической клиникой. Версия 1 (базовая).",
    version="1.0.0",
    contact={
        "name": "Support Team",
        "email": "support@dentistry.com",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)
app_v1.include_router(auth.router)
app_v1.include_router(client.router)
app_v1.include_router(manager.router)
app_v1.include_router(dentist.router)
app_v1.include_router(patients.router)
app_v1.include_router(endpoints.router)
app_v1.include_router(extended.router)
app_v1.include_router(mkb_codes.router)

# ========== ИМПОРТ ИНТЕГРАЦИИ ПОСЛЕ СОЗДАНИЯ app_v1 ==========
from app.api.routers.integration import router as integration_router
app_v1.include_router(integration_router)  # <-- ТЕПЕРЬ РАБОТАЕТ


# ========== V2 ==========
app_v2 = FastAPI(
    title="Dentistry API v2",
    description="REST API для управления стоматологической клиникой. Версия 2 (расширенная с пагинацией).",
    version="2.0.0",
    contact={
        "name": "Support Team",
        "email": "support@dentistry.com",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)
app_v2.include_router(auth.router)
app_v2.include_router(patients_router, prefix="/patients", tags=["Patients v2"])
app_v2.include_router(appointments_router, prefix="/appointments", tags=["Appointments v2"])
app_v2.include_router(medical_records_router, prefix="/medical-records", tags=["Medical Records v2"])
app_v2.include_router(studies_router, prefix="/studies", tags=["Studies v2"])
app_v2.include_router(referrals_router, prefix="/referrals", tags=["Referrals v2"])
app_v2.include_router(work_orders_router, prefix="/work-orders", tags=["Work Orders v2"])
app_v2.include_router(statistics_router, prefix="/stats", tags=["Statistics"])
app_v2.include_router(mkbs.router)
app_v2.include_router(mkb_codes.router)
app_v2.include_router(clinic_router, prefix="/clinic", tags=["Clinic"])


# ========== ОСНОВНОЕ ПРИЛОЖЕНИЕ ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_database()
    yield

main_app = FastAPI(
    title="Dentistry API Gateway",
    description="API Gateway для стоматологической клиники. Объединяет версии v1 и v2.",
    version="2.0.0",
    lifespan=lifespan
)
main_app.mount("/api/v1", app_v1)
main_app.mount("/api/v2", app_v2)

main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@main_app.get("/")
def root():
    return {
        "message": "Dentistry API",
        "versions": {
            "v1": "/api/v1/docs",
            "v2": "/api/v2/docs"
        }
    }

# Alias для uvicorn
app = main_app