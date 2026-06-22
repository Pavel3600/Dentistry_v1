from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.models.client_models import Clients
from app.models.medical_models import Appointment, Patient
from app.schemas.medical_schemas import AppointmentOut, AppointmentCreate
from app.core.roles import require_manager, require_manager_or_dentist
from app.api.deps import PaginationParams


class AppointmentStatusUpdate(BaseModel):
    status: str

router = APIRouter()

@router.get("/", response_model=List[AppointmentOut])
async def get_appointments_paginated(
        pagination: PaginationParams = Depends(),
        patient_id: Optional[int] = Query(None),
        doctor_id: Optional[int] = Query(None),
        date_from: Optional[datetime] = Query(None),
        date_to: Optional[datetime] = Query(None),
        db: AsyncSession = Depends(get_db),
        current_user: Clients = Depends(require_manager_or_dentist)
):
    query = select(Appointment)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    if doctor_id:
        query = query.where(Appointment.doctor_id == doctor_id)
    if date_from:
        query = query.where(Appointment.datetime >= date_from)
    if date_to:
        query = query.where(Appointment.datetime <= date_to)

    result = await db.execute(query.offset(pagination.skip).limit(pagination.limit))
    appointments = result.scalars().all()
    return appointments

@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(
        appointment_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: Clients = Depends(require_manager_or_dentist)
):
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return appointment

@router.post("/", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
        data: AppointmentCreate,
        db: AsyncSession = Depends(get_db),
        current_user: Clients = Depends(require_manager)
):
    patient = await db.get(Patient, data.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Пациент не найден")
    doctor = await db.get(Clients, data.doctor_id)
    if not doctor or doctor.role != "dentist":
        raise HTTPException(status_code=400, detail="Врач не является стоматологом")
    payload = data.model_dump()
    # PostgreSQL TIMESTAMP WITHOUT TIME ZONE не принимает timezone-aware datetime
    if payload.get("datetime") and hasattr(payload["datetime"], "tzinfo") and payload["datetime"].tzinfo:
        payload["datetime"] = payload["datetime"].replace(tzinfo=None)
    appointment = Appointment(**payload)
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment

@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment_status(
        appointment_id: int,
        data: AppointmentStatusUpdate,
        db: AsyncSession = Depends(get_db),
        current_user: Clients = Depends(require_manager_or_dentist)
):
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    valid_statuses = {"scheduled", "completed", "cancelled"}
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Недопустимый статус: {data.status}")
    appointment.status = data.status
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
        appointment_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: Clients = Depends(require_manager)
):
    appointment = await db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    appointment.status = "cancelled"
    await db.commit()
    return None