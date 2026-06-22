from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.client_models import Clients
from app.models.medical_models import Patient
from app.schemas.medical_schemas import PatientCreate


async def generate_card_number(db: AsyncSession) -> str:
    """Уникальный номер мед. карты вида K-2026-00042."""
    prefix = f"K-{datetime.now().year}-"
    count = await db.scalar(
        select(func.count()).select_from(Patient).where(Patient.card_number.like(f"{prefix}%"))
    )
    return f"{prefix}{(count or 0) + 1:05d}"


async def delete_patient_cascade(db: AsyncSession, patient: Patient) -> None:
    """Удаляет пациента вместе с зависимыми записями.
    В async ORM каскад через lazy-load недоступен, поэтому удаляем зависимые
    строки явно (FK patient_id NOT NULL, обнуление невозможно)."""
    from sqlalchemy import delete
    from app.models.medical_models import (
        Appointment, MedicalRecord, Study, Referral, WorkOrder,
    )
    for model in (Appointment, MedicalRecord, Study, Referral, WorkOrder):
        await db.execute(delete(model).where(model.patient_id == patient.id))
    await db.delete(patient)
    await db.commit()


class PatientService:
    @staticmethod
    async def create_patient(db: AsyncSession, user_id: int, patient_data: PatientCreate) -> Patient:
        # Проверка существования пользователя
        user = await db.get(Clients, user_id)
        if not user or user.role != "patient":
            raise ValueError("Invalid user_id or user is not a patient")
        # Проверка дублирования
        existing = await db.execute(select(Patient).where(Patient.user_id == user_id))
        if existing.scalar_one_or_none():
            raise ValueError("Patient already linked to this user")
        patient = Patient(**patient_data.model_dump())
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        return patient