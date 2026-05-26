from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── Conexión PostgreSQL ──────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/network_audit_db"
    )

    # ── Umbrales operacionales (sobreescribibles por variables de entorno) ───
    # Compuerta OTDR
    OTDR_MAX_FUSION_LOSS_DB: float = 0.1

    # Módulo óptico SFP (clase C++)
    SFP_MIN_TX_POWER_DBM: float = 6.0

    # Potencia promedio de ONTs por puerto
    CLIENT_AVG_MIN_POWER_DBM: float = -26.5

    # Umbrales críticos en calle (N2)
    CLIENT_CRITICAL_POWER_DBM: float = -25.4
    CLIENT_CRITICAL_SEVERE_POWER_DBM: float = -27.01

    # Reservas técnicas de planta externa
    RESERVE_BOX_METERS: float = 15.0
    RESERVE_POLE_METERS: float = 40.0
    RESERVE_POLE_INTERVAL_METERS: float = 400.0

    # ── Servidor ─────────────────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # ── Almacenamiento local (Object Storage simulado) ───────────────────────
    MEDIA_DIR: str = "media"
    BASE_MEDIA_URL: str = "http://localhost:8000/media"


@lru_cache
def get_settings() -> Settings:
    return Settings()
