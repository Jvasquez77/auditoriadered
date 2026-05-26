"""
Módulo de Auditoría de Red ODN — API Principal (FastAPI).

Bounded Context: network_audit
Arquitectura: Monolito Modular
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routers import (
    measurements_router,
    n1_router,
    n2_router,
    olt_ports_router,
    reports_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear directorio de medios si no existe
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="Módulo de Auditoría de Red ODN",
    description=(
        "API para el módulo de revisión y auditoría de la Red de Distribución Óptica (ODN). "
        "Gestiona la ingesta de datos de OLT, OTDR, NAPs y genera actas de entrega técnica."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS para SvelteKit local
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir archivos de media (fotos de campo)
if os.path.exists(settings.MEDIA_DIR):
    app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

# Registrar routers bajo el prefijo v1
prefix = settings.API_V1_PREFIX
app.include_router(olt_ports_router, prefix=prefix)
app.include_router(n1_router, prefix=prefix)
app.include_router(n2_router, prefix=prefix)
app.include_router(measurements_router, prefix=prefix)
app.include_router(reports_router, prefix=prefix)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "module": "network-audit-odn", "version": "1.0.0"}
