"""Router: Puertos OLT — Ingesta A y B (Smart OLT + SFP)."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.network_audit import OltPort
from app.schemas.network_audit import (
    OltPortCreate,
    OltPortRead,
    OltPortSyncRequest,
    OltPortUpdate,
)
from app.services.sfp_service import process_sfp_evaluation

router = APIRouter(prefix="/olt-ports", tags=["OLT Ports"])


@router.get("/", response_model=List[OltPortRead])
async def list_olt_ports(
    localidad: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OltPort)
    if localidad:
        stmt = stmt.where(OltPort.localidad == localidad)
    result = await db.execute(stmt)
    ports = result.scalars().all()
    return [OltPortRead.model_validate(p) for p in ports]


@router.post("/", response_model=OltPortRead, status_code=status.HTTP_201_CREATED)
async def create_olt_port(
    payload: OltPortCreate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OltPort).where(
        OltPort.olt_id == payload.olt_id,
        OltPort.port_id == payload.port_id,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        for field, value in payload.model_dump().items():
            setattr(existing, field, value)
        port = existing
    else:
        port = OltPort(**payload.model_dump())
        db.add(port)

    await db.flush()
    await db.refresh(port)
    return OltPortRead.model_validate(port)


@router.get("/{port_id}", response_model=OltPortRead)
async def get_olt_port(port_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(OltPort).where(OltPort.id == port_id)
    result = await db.execute(stmt)
    port = result.scalar_one_or_none()
    if not port:
        raise HTTPException(status_code=404, detail="Puerto OLT no encontrado")
    return OltPortRead.model_validate(port)


@router.patch("/{port_id}", response_model=OltPortRead)
async def update_olt_port(
    port_id: str,
    payload: OltPortUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(OltPort).where(OltPort.id == port_id)
    result = await db.execute(stmt)
    port = result.scalar_one_or_none()
    if not port:
        raise HTTPException(status_code=404, detail="Puerto OLT no encontrado")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(port, field, value)

    await db.flush()
    await db.refresh(port)
    return OltPortRead.model_validate(port)


@router.post("/{port_id}/sync-sfp", status_code=status.HTTP_200_OK)
async def sync_sfp_evaluation(
    port_id: str,
    payload: OltPortSyncRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Consume el vector de potencias de ONTs y evalúa si el SFP debe agregarse
    al Reporte Acumulado de SFPs por Cambiar.
    """
    stmt = select(OltPort).where(OltPort.id == port_id)
    result = await db.execute(stmt)
    port = result.scalar_one_or_none()
    if not port:
        raise HTTPException(status_code=404, detail="Puerto OLT no encontrado")

    replacement = await process_sfp_evaluation(db, port, payload.client_powers)
    await db.flush()

    return {
        "sfp_alert": port.sfp_alert,
        "replacement_created": replacement is not None,
        "replacement_id": replacement.id if replacement else None,
    }
