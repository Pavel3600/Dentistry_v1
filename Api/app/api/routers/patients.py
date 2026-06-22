from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.client_models import Clients
from app.models.medical_models import Patient

router = APIRouter(prefix="/patients", tags=["Patients"])

class PatientCreateSchema(BaseModel):
    full_name: str
    email: str
    phone: str
    allergies: Optional[str] = ""
    notes: Optional[str] = ""
    created_by_username: Optional[str] = None

class PatientResponseSchema(BaseModel):
    id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[PatientResponseSchema], summary="Получить всех пациентов")
async def get_patients(db: AsyncSession = Depends(get_db)):
    """Получить список всех пациентов"""
    try:
        result = await db.execute(select(Patient))
        patients = result.scalars().all()
        return [
            PatientResponseSchema(
                id=p.id,
                full_name=p.full_name,
                phone=p.phone,
                email=p.email,
                created_at=p.created_at.strftime("%Y-%m-%d") if p.created_at else "—"
            )
            for p in patients
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")

@router.post("/", response_model=dict, summary="Добавить пациента")
async def create_patient(patient: PatientCreateSchema, db: AsyncSession = Depends(get_db)):
    """Добавить нового пациента"""
    if not patient.full_name or not patient.email or not patient.phone:
        raise HTTPException(status_code=400, detail="Обязательные поля: full_name, email, phone")

    try:
        print(f"[DEBUG] Создание пациента: {patient.full_name}")

        # Проверить существует ли уже пациент с этим email
        existing_client = await db.execute(
            select(Clients).where(Clients.login == patient.email)
        )
        client = existing_client.scalar_one_or_none()

        if client:
            print(f"[DEBUG] Clients уже существует: ID {client.id}")
            # Проверить существует ли Patient для этого Clients
            existing_patient = await db.execute(
                select(Patient).where(Patient.user_id == client.id)
            )
            existing_pat = existing_patient.scalar_one_or_none()

            if existing_pat:
                raise HTTPException(
                    status_code=400,
                    detail=f"Пациент с email {patient.email} уже существует"
                )
        else:
            # Создать Clients пользователя
            new_client = Clients(
                login=patient.email,
                password="temp_password",
                role="patient"
            )
            print(f"[DEBUG] Clients создан: {new_client.login}")
            db.add(new_client)
            await db.flush()
            print(f"[DEBUG] Clients ID: {new_client.id}")
            client = new_client

        # Создать Patient запись
        card_num = f"P-{client.id}-{int(datetime.now().timestamp())}"
        new_patient = Patient(
            card_number=card_num,
            user_id=client.id,
            full_name=patient.full_name,
            birth_date=datetime.now(),
            gender="unknown",
            phone=patient.phone,
            email=patient.email,
            address=None,
            created_at=datetime.now()
        )
        print(f"[DEBUG] Patient объект создан: {card_num}")

        db.add(new_patient)
        await db.commit()
        await db.refresh(new_patient)

        print(f"[DEBUG] Patient ID: {new_patient.id}")

        return {
            "success": True,
            "message": f"Пациент {patient.full_name} добавлен",
            "patient_id": new_patient.id
        }
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        error_str = str(e.orig).lower() if e.orig else str(e)
        if "login" in error_str or "email" in error_str:
            raise HTTPException(status_code=400, detail=f"Пациент с таким email уже существует в базе")
        elif "phone" in error_str:
            raise HTTPException(status_code=400, detail=f"Пациент с таким телефоном уже существует в базе")
        else:
            raise HTTPException(status_code=400, detail=f"Пациент с такими данными уже существует в базе")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сервера: {str(e)}")

@router.get("/{patient_id}", response_model=PatientResponseSchema, summary="Получить пациента")
async def get_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Получить информацию о конкретном пациенте"""
    try:
        result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = result.scalar_one_or_none()
        if not patient:
            raise HTTPException(status_code=404, detail="Пациент не найден")

        return PatientResponseSchema(
            id=patient.id,
            full_name=patient.full_name,
            phone=patient.phone
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка БД: {str(e)}")

@router.put("/{patient_id}", response_model=dict, summary="Обновить пациента")
async def update_patient(patient_id: int, patient: PatientCreateSchema, db: AsyncSession = Depends(get_db)):
    """Обновить данные пациента"""
    try:
        result = await db.execute(select(Patient).where(Patient.id == patient_id))
        existing = result.scalar_one_or_none()
        if not existing:
            raise HTTPException(status_code=404, detail="Пациент не найден")

        existing.full_name = patient.full_name
        existing.phone = patient.phone

        await db.commit()
        return {"success": True, "message": "Пациент обновлен"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении: {str(e)}")

@router.delete("/{patient_id}", response_model=dict, summary="Удалить пациента")
async def delete_patient(patient_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить пациента"""
    try:
        result = await db.execute(select(Patient).where(Patient.id == patient_id))
        patient = result.scalar_one_or_none()
        if not patient:
            raise HTTPException(status_code=404, detail="Пациент не найден")

        await db.delete(patient)
        await db.commit()
        return {"success": True, "message": "Пациент удален"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")
