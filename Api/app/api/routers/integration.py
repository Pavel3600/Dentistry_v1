from fastapi import APIRouter, Depends, HTTPException
import httpx

from app.core.config import settings

router = APIRouter(prefix="/integration", tags=["Integration"])

DJANGO_URL = settings.DJANGO_URL


@router.get("/django-patients")
async def get_django_patients():
    """Получить пациентов из Django"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DJANGO_URL}/api/patients/", timeout=5)
            if response.status_code == 200:
                return {"status": "ok", "data": response.json()}
            else:
                return {"status": "error", "message": f"Django вернул {response.status_code}"}
        except Exception as e:
            raise HTTPException(500, f"Django не отвечает: {str(e)}")


@router.get("/django-appointments")
async def get_django_appointments():
    """Получить записи из Django"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DJANGO_URL}/api/appointments/", timeout=5)
            if response.status_code == 200:
                return {"status": "ok", "data": response.json()}
            else:
                return {"status": "error", "message": f"Django вернул {response.status_code}"}
        except Exception as e:
            raise HTTPException(500, f"Django не отвечает: {str(e)}")


@router.get("/django-status")
async def check_django_status():
    """Проверить, работает ли Django"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DJANGO_URL}/", timeout=3)
            return {"status": "online", "code": response.status_code}
        except Exception:
            return {"status": "offline", "message": f"Django не запущен ({DJANGO_URL})"}