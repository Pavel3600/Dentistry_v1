from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.client_models import Clients
from app.models.medical_models import Study, Patient
from app.schemas.medical_schemas import StudyOut, StudyCreate
from app.core.roles import require_dentist
from app.api.deps import PaginationParams

router = APIRouter()

@router.get("/", response_model=List[StudyOut])
async def get_studies_paginated(
    pagination: PaginationParams = Depends(),
    patient_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    query = select(Study)
    if patient_id:
        query = query.where(Study.patient_id == patient_id)
    result = await db.execute(query.offset(pagination.skip).limit(pagination.limit))
    studies = result.scalars().all()
    return studies

@router.get("/{study_id}", response_model=StudyOut)
async def get_study(
    study_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    study = await db.get(Study, study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Исследование не найдено")
    return study

@router.post("/", response_model=StudyOut, status_code=status.HTTP_201_CREATED)
async def create_study(
    data: StudyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    study = Study(**data.model_dump())
    db.add(study)
    await db.commit()
    await db.refresh(study)
    return study