from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.core.database import get_db
from app.models.client_models import Clients
from app.models.medical_models import Patient
from app.schemas.medical_schemas import PatientOut, PatientCreate, PatientUpdate
from app.schemas.common import Page
from app.core.roles import require_manager, require_manager_or_dentist, require_admin
from app.api.deps import PaginationParams
from app.services.patient_service import generate_card_number, delete_patient_cascade

router = APIRouter()

@router.get("/", response_model=Page[PatientOut])
async def get_patients_paginated(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_manager_or_dentist)
):
    # Общее количество записей
    total = await db.scalar(select(func.count()).select_from(Patient))
    # Пагинация
    result = await db.execute(
        select(Patient).offset(pagination.skip).limit(pagination.limit)
    )
    patients = result.scalars().all()
    # Формирование ответа Page
    return Page.create(
        items=patients,
        total=total,
        page=(pagination.skip // pagination.limit) + 1 if pagination.limit > 0 else 1,
        size=pagination.limit
    )

@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_manager_or_dentist)
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    return patient

@router.post("/", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_manager_or_dentist)
):
    try:
        user = await db.get(Clients, data.user_id)
        if not user or user.role != "patient":
            raise HTTPException(status_code=400, detail="Неверный user_id или пользователь не пациент")
        existing = await db.execute(select(Patient).where(Patient.user_id == data.user_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Пациент уже привязан к этому пользователю")
        payload = data.model_dump()
        if not payload.get("card_number"):
            payload["card_number"] = await generate_card_number(db)
        # PostgreSQL TIMESTAMP WITHOUT TIME ZONE не принимает timezone-aware datetime
        if payload.get("birth_date") and hasattr(payload["birth_date"], "tzinfo") and payload["birth_date"].tzinfo:
            payload["birth_date"] = payload["birth_date"].replace(tzinfo=None)
        patient = Patient(**payload)
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        return PatientOut.model_validate(patient)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_manager_or_dentist)
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    await db.commit()
    await db.refresh(patient)
    return patient

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_admin)  # удаление пациента — только администратор
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    await delete_patient_cascade(db, patient)
    return None