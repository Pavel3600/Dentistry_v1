# app/core/config.py
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Настройки базы данных
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/dentistry")

    # Настройки безопасности
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-min-32-characters-long-change-this")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = "HS256"

    # Адрес Django-сервиса (для обратной интеграции). Django работает на :8001.
    DJANGO_URL: str = os.getenv("DJANGO_URL", "http://localhost:8001")

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()