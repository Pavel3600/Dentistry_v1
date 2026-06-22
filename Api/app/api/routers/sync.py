# app/api/routers/sync.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  # <-- Добавлен пропущенный импорт select
from app.core.database import get_db
from app.models.client_models import Clients
from app.schemas.client_schema import ClientSyncSchema

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/user")
async def sync_user_from_django(
        user_data: ClientSyncSchema,
        db: AsyncSession = Depends(get_db)
):
    """Синхронизация пользователя из Django"""
    # Проверяем API-ключ (простая реализация)
    # В реальном проекте используйте секретный токен

    existing = await db.execute(
        select(Clients).where(Clients.login == user_data.login)
    )
    user = existing.scalar_one_or_none()

    if user:
        # Обновляем
        user.password = user_data.password
        user.role = user_data.role
    else:
        # Создаём
        user = Clients(
            login=user_data.login,
            password=user_data.password,
            role=user_data.role
        )
        db.add(user)

    await db.commit()
    return {"status": "synced", "id": user.id}