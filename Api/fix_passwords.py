# fix_passwords.py
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.client_models import Clients
from app.core.security import hash_password


async def fix_passwords():
    async with AsyncSessionLocal() as db:
        # Получаем всех пользователей
        result = await db.execute(select(Clients))
        users = result.scalars().all()

        # Обновляем пароли
        for user in users:
            # Проверяем, является ли пароль валидным Argon2 хешем
            if not user.password.startswith('$argon2'):
                if user.login == "admin":
                    user.password = hash_password("admin123")
                elif user.login == "manager":
                    user.password = hash_password("manager123")
                elif user.login == "dentist":
                    user.password = hash_password("dentist123")
                else:
                    # Для других пользователей можно установить временный пароль
                    user.password = hash_password("temp123")
                print(f"Обновлен пароль для {user.login}")

        await db.commit()
        print("Пароли обновлены")


if __name__ == "__main__":
    asyncio.run(fix_passwords())