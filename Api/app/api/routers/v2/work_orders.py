from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.client_models import Clients
from app.models.medical_models import WorkOrder, Patient
from app.schemas.medical_schemas import WorkOrderOut, WorkOrderCreate
from app.core.roles import require_dentist
from app.api.deps import PaginationParams

router = APIRouter()

@router.get("/", response_model=List[WorkOrderOut])
async def get_work_orders_paginated(
    pagination: PaginationParams = Depends(),
    patient_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    query = select(WorkOrder)
    if patient_id:
        query = query.where(WorkOrder.patient_id == patient_id)
    result = await db.execute(query.offset(pagination.skip).limit(pagination.limit))
    orders = result.scalars().all()
    return orders

@router.get("/{order_id}", response_model=WorkOrderOut)
async def get_work_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    order = await db.get(WorkOrder, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Наряд не найден")
    return order

@router.post("/", response_model=WorkOrderOut, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    data: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    order = WorkOrder(doctor_id=current_user.id, **data.model_dump())
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order