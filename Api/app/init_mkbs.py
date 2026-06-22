"""
Скрипт для инициализации таблицы mkbs_codes
Запуск: python -m app.init_mkbs
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal, engine, Base
from app.models.medical_models import MKBSCode
from app.services.mkbs_dll import mkbs_emulator
from sqlalchemy import select


async def init_mkbs_codes():
    """Заполнить таблицу кодами МКБ-С-3"""
    async with engine.begin() as conn:
        # Создаем таблицы, если их нет
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Получаем существующие коды
        existing = await db.execute(select(MKBSCode.code))
        existing_codes = set(row[0] for row in existing.all())

        # Добавляем новые коды
        added = 0
        for code, info in mkbs_emulator._data.items():
            if code not in existing_codes:
                mkbs_code = MKBSCode(
                    code=code,
                    name=info["name"],
                    category=info["category"]
                )
                db.add(mkbs_code)
                added += 1

        await db.commit()
        print(f"Добавлено {added} новых записей МКБ-С-3")
        print(f"Всего записей: {len(mkbs_emulator._data)}")


if __name__ == "__main__":
    asyncio.run(init_mkbs_codes())