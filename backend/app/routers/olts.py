"""Router: Dispositivos OLT — entidad raíz de la jerarquía de red ODN."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.network_audit import Olt, OltPort
from app.schemas.network_audit import (
    OltCreate,
    OltDetailRead,
    OltPortForOltCreate,
    OltPortRead,
    OltRead,
    OltUpdate,
)
from app.services.sfp_service import process_sfp_evaluation

router = APIRouter(prefix="/olts", tags=["OLTs"])


def _to_read(olt: Olt, port_count: int) -> OltRead:
    return OltRead(
        id=olt.id,
        olt_id=olt.olt_id,
        name=olt.name,
        hub_id=olt.hub_id,
        localidad=olt.localidad,
        ip_address=olt.ip_address,
        brand=olt.brand,
        model=olt.model,
        total_ports=olt.total_ports,
        status=olt.status,
        created_at=olt.created_at,
        port_count=port_count,
    )


# ---------------------------------------------------------------------------
# Listado de OLTs
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[OltRead])
async def list_olts(
    localidad: str | None = None,
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Olt)
    if localidad:
        stmt = stmt.where(Olt.localidad == localidad)
    if status_filter:
        stmt = stmt.where(Olt.status == status_filter)

    result = await db.execute(stmt)
    olts = result.scalars().all()

    # Conteo de puertos por OLT en una sola query
    counts_stmt = select(OltPort.olt_pk_id, func.count(OltPort.id)).group_by(OltPort.olt_pk_id)
    counts_result = await db.execute(counts_stmt)
    port_counts: dict[str, int] = {row[0]: row[1] for row in counts_result.all() if row[0]}

    return [_to_read(o, port_counts.get(o.id, 0)) for o in olts]


# ---------------------------------------------------------------------------
# Crear OLT
# ---------------------------------------------------------------------------
@router.post("/", response_model=OltRead, status_code=status.HTTP_201_CREATED)
async def create_olt(payload: OltCreate, db: AsyncSession = Depends(get_db)):
    existing = (
        await db.execute(select(Olt).where(Olt.olt_id == payload.olt_id))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un OLT con olt_id='{payload.olt_id}'",
        )

    olt = Olt(**payload.model_dump())
    db.add(olt)
    await db.flush()
    await db.refresh(olt)
    return _to_read(olt, 0)


# ---------------------------------------------------------------------------
# Detalle de OLT con todos sus puertos
# ---------------------------------------------------------------------------
@router.get("/{olt_id}", response_model=OltDetailRead)
async def get_olt(olt_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Olt)
        .where(Olt.id == olt_id)
        .options(selectinload(Olt.ports))
    )
    result = await db.execute(stmt)
    olt = result.scalar_one_or_none()
    if not olt:
        raise HTTPException(status_code=404, detail="OLT no encontrado")

    ports_read = [OltPortRead.model_validate(p) for p in olt.ports]
    return OltDetailRead(
        id=olt.id,
        olt_id=olt.olt_id,
        name=olt.name,
        hub_id=olt.hub_id,
        localidad=olt.localidad,
        ip_address=olt.ip_address,
        brand=olt.brand,
        model=olt.model,
        total_ports=olt.total_ports,
        status=olt.status,
        created_at=olt.created_at,
        port_count=len(olt.ports),
        ports=ports_read,
    )


# ---------------------------------------------------------------------------
# Actualizar OLT
# ---------------------------------------------------------------------------
@router.patch("/{olt_id}", response_model=OltRead)
async def update_olt(olt_id: str, payload: OltUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Olt).where(Olt.id == olt_id))
    olt = result.scalar_one_or_none()
    if not olt:
        raise HTTPException(status_code=404, detail="OLT no encontrado")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(olt, field, value)

    await db.flush()
    await db.refresh(olt)

    count_result = await db.execute(
        select(func.count(OltPort.id)).where(OltPort.olt_pk_id == olt.id)
    )
    return _to_read(olt, count_result.scalar_one())


# ---------------------------------------------------------------------------
# Eliminar OLT (cascade a puertos/N1/N2/etc. por FK en BD)
# ---------------------------------------------------------------------------
@router.delete("/{olt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_olt(olt_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Olt).where(Olt.id == olt_id))
    olt = result.scalar_one_or_none()
    if not olt:
        raise HTTPException(status_code=404, detail="OLT no encontrado")
    await db.delete(olt)


# ---------------------------------------------------------------------------
# Listar puertos de un OLT
# ---------------------------------------------------------------------------
@router.get("/{olt_id}/ports", response_model=List[OltPortRead])
async def list_olt_ports(olt_id: str, db: AsyncSession = Depends(get_db)):
    olt = (await db.execute(select(Olt).where(Olt.id == olt_id))).scalar_one_or_none()
    if not olt:
        raise HTTPException(status_code=404, detail="OLT no encontrado")

    result = await db.execute(select(OltPort).where(OltPort.olt_pk_id == olt_id))
    ports = result.scalars().all()
    return [OltPortRead.model_validate(p) for p in ports]


# ---------------------------------------------------------------------------
# Agregar puerto a un OLT existente
# ---------------------------------------------------------------------------
@router.post("/{olt_id}/ports", response_model=OltPortRead, status_code=status.HTTP_201_CREATED)
async def add_port_to_olt(
    olt_id: str,
    payload: OltPortForOltCreate,
    db: AsyncSession = Depends(get_db),
):
    olt = (await db.execute(select(Olt).where(Olt.id == olt_id))).scalar_one_or_none()
    if not olt:
        raise HTTPException(status_code=404, detail="OLT no encontrado")

    # Verificar duplicado (olt_id + port_id)
    existing = (
        await db.execute(
            select(OltPort).where(
                OltPort.olt_id == olt.olt_id,
                OltPort.port_id == payload.port_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        # Upsert: actualizar datos existentes
        existing.port_occupancy_percentage = payload.port_occupancy_percentage
        existing.connected_clients_count = payload.connected_clients_count
        existing.current_sfp_tx_power_dbm = payload.current_sfp_tx_power_dbm
        existing.olt_pk_id = olt.id
        port = existing
    else:
        port = OltPort(
            olt_pk_id=olt.id,
            olt_id=olt.olt_id,
            port_id=payload.port_id,
            hub_id=olt.hub_id,
            localidad=olt.localidad,
            port_occupancy_percentage=payload.port_occupancy_percentage,
            connected_clients_count=payload.connected_clients_count,
            current_sfp_tx_power_dbm=payload.current_sfp_tx_power_dbm,
        )
        db.add(port)

    await db.flush()
    await db.refresh(port)

    # Evaluación SFP automática si se enviaron potencias de clientes
    if payload.client_powers:
        await process_sfp_evaluation(db, port, payload.client_powers)
        await db.flush()
        await db.refresh(port)

    return OltPortRead.model_validate(port)
