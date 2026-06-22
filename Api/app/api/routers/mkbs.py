from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.client_models import Clients
from app.models.medical_models import MKBSCode
from app.schemas.medical_schemas import MKBSCodeOut, MKBSCodeCreate
from app.core.roles import require_dentist
from app.services.mkbs_dll import mkbs_emulator
from app.services.diagnosis_autocomplete import DiagnosisAutocompleteService

router = APIRouter(prefix="/mkbs", tags=["MKB-S-3"])


@router.get("/diagnoses", response_model=List[MKBSCodeOut])
async def get_diagnosis_codes(
    search: Optional[str] = Query(None, description="Поиск по коду или названию"),
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    """Получить список кодов диагнозов МКБ-С-3"""
    query = select(MKBSCode).where(
        MKBSCode.category == "diagnosis",
        MKBSCode.is_active == True
    )
    if search:
        query = query.where(
            (MKBSCode.code.ilike(f"%{search}%")) |
            (MKBSCode.name.ilike(f"%{search}%"))
        )
    result = await db.execute(query.order_by(MKBSCode.code))
    return result.scalars().all()


@router.get("/services", response_model=List[MKBSCodeOut])
async def get_service_codes(
    search: Optional[str] = Query(None, description="Поиск по коду или названию"),
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    """Получить список кодов стоматологических услуг МКБ-С-3"""
    query = select(MKBSCode).where(
        MKBSCode.category == "service",
        MKBSCode.is_active == True
    )
    if search:
        query = query.where(
            (MKBSCode.code.ilike(f"%{search}%")) |
            (MKBSCode.name.ilike(f"%{search}%"))
        )
    result = await db.execute(query.order_by(MKBSCode.code))
    return result.scalars().all()


@router.get("/search", response_model=List[dict])
async def search_mkbs(
    query: str = Query(..., description="Поисковый запрос"),
    category: Optional[str] = Query(None, description="diagnosis или service"),
    current_user: Clients = Depends(require_dentist)
):
    """Поиск по справочнику МКБ-С-3 (с использованием эмулятора DLL)"""
    if category == "diagnosis":
        results = DiagnosisAutocompleteService.search_diagnosis(query)
    elif category == "service":
        results = DiagnosisAutocompleteService.search_services(query)
    else:
        results = DiagnosisAutocompleteService.search_diagnosis(query) + \
                  DiagnosisAutocompleteService.search_services(query)
    return results[:50]


@router.get("/validate/{code}", response_model=dict)
async def validate_code(
    code: str,
    category: Optional[str] = Query(None, description="diagnosis или service"),
    current_user: Clients = Depends(require_dentist)
):
    """Проверить валидность кода МКБ-С-3"""
    info = mkbs_emulator.get_code_info(code)
    if not info:
        return {"code": code, "valid": False, "name": None}
    if category and info.get("category") != category:
        return {"code": code, "valid": False, "name": None}
    return {"code": code, "valid": True, "name": info.get("name")}


@router.get("/{code_id}", response_model=MKBSCodeOut)
async def get_code_by_id(
    code_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    code = await db.get(MKBSCode, code_id)
    if not code:
        raise HTTPException(404, "Код МКБ-С-3 не найден")
    return code


@router.post("/", response_model=MKBSCodeOut, status_code=status.HTTP_201_CREATED)
async def create_mkbs_code(
    data: MKBSCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Clients = Depends(require_dentist)
):
    """Добавить новый код в справочник (для администрирования)"""
    existing = await db.execute(select(MKBSCode).where(MKBSCode.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Код уже существует")
    new_code = MKBSCode(**data.model_dump())
    db.add(new_code)
    await db.commit()
    await db.refresh(new_code)
    return new_code
# Добавьте эти эндпоинты в конец файла mkbs.py

@router.get("/public/diagnoses", response_model=List[MKBSCodeOut], tags=["Public"])
async def get_diagnosis_codes_public(
    search: Optional[str] = Query(None, description="Поиск по коду или названию"),
    db: AsyncSession = Depends(get_db)
):
    """Публичный список кодов диагнозов МКБ-С-3 (без авторизации)"""
    query = select(MKBSCode).where(
        MKBSCode.category == "diagnosis",
        MKBSCode.is_active == True
    )
    if search:
        query = query.where(
            (MKBSCode.code.ilike(f"%{search}%")) |
            (MKBSCode.name.ilike(f"%{search}%"))
        )
    result = await db.execute(query.order_by(MKBSCode.code))
    return result.scalars().all()


@router.get("/public/services", response_model=List[MKBSCodeOut], tags=["Public"])
async def get_service_codes_public(
    search: Optional[str] = Query(None, description="Поиск по коду или названию"),
    db: AsyncSession = Depends(get_db)
):
    """Публичный список кодов услуг МКБ-С-3 (без авторизации)"""
    query = select(MKBSCode).where(
        MKBSCode.category == "service",
        MKBSCode.is_active == True
    )
    if search:
        query = query.where(
            (MKBSCode.code.ilike(f"%{search}%")) |
            (MKBSCode.name.ilike(f"%{search}%"))
        )
    result = await db.execute(query.order_by(MKBSCode.code))
    return result.scalars().all()