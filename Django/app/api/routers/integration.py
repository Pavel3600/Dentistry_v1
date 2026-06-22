from fastapi import APIRouter, Depends, HTTPException
import httpx
from app.core.roles import require_manager

router = APIRouter(prefix="/integration", tags=["Integration"])

@router.get("/django-patients")
async def get_django_patients(current_user=Depends(require_manager)):
    """Получить пациентов из Django"""
    async with httpx.AsyncClient() as client:
        try:
            # Django API для пациентов (нужно создать)
            response = await client.get("http://localhost:8000/api/patients/", timeout=5)
            return response.json()
        except:
            raise HTTPException(500, "Django не отвечает")

@router.get("/django-appointments")
async def get_django_appointments():
    """Получить записи из Django"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/appointments/", timeout=5)
        return response.json()