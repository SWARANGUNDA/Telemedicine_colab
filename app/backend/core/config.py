"""
core/config.py — Pydantic Settings & Environment Configuration for TeleMed AI.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

def _get_default_db_url() -> str:
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.05)
        res = s.connect_ex(('127.0.0.1', 5432))
        s.close()
        if res == 0:
            return "postgresql://postgres:postgres@127.0.0.1:5432/telemed_db"
    except Exception:
        pass
    sqlite_path = BASE_DIR / "telemed_local.db"
    return f"sqlite:///{sqlite_path}"


class Settings(BaseSettings):
    DATABASE_URL: str = _get_default_db_url()
    SECRET_KEY: str = os.getenv("TELEMED_SECRET_KEY", "telemed_enterprise_secret_key_production_2026_super_secure")
    JWT_SECRET: str = os.getenv("TELEMED_JWT_SECRET", "telemed_jwt_super_secret_key_phase_6_prod_2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "telemed.ai"
    JWT_AUDIENCE: str = "telemed_app"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TELEMED_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("TELEMED_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
