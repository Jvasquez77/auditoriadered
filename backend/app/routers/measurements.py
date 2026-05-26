"""Router: Mediciones de potencia N2 en calle (Ingesta G) — Interfaz de campo."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.network_audit import N2Infrastructure, N2PortMeasurement
from app.schemas.network_audit import N2PortMeasurementCreate, N2PortMeasurementRead
from app.services.power_audit_service import process_n2_measurement

router = APIRouter(prefix="/measurements", tags=["Field Measurements"])


def _to_read(m: N2PortMeasurement) -> N2PortMeasurementRead:
    return N2PortMeasurementRead.model_validate(m)


@router.get("/", response_model=List[N2PortMeasurementRead])
async def list_measurements(
    n2_infrastructure_id: str | None = None,
    critical_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(N2PortMeasurement)
    if n2_infrastructure_id:
        stmt = stmt.where(
            N2PortMeasurement.n2_infrastructure_id == n2_infrastructure_id
        )
    result = await db.execute(stmt)
    measurements = result.scalars().all()

    if critical_only:
        measurements = [m for m in measurements if m.is_critical]

    return [_to_read(m) for m in measurements]


@router.post("/", response_model=N2PortMeasurementRead, status_code=status.HTTP_201_CREATED)
async def create_measurement(
    payload: N2PortMeasurementCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verificar que la caja N2 padre existe
    n2_stmt = select(N2Infrastructure).where(
        N2Infrastructure.id == payload.n2_infrastructure_id
    )
    n2_result = await db.execute(n2_stmt)
    n2_box = n2_result.scalar_one_or_none()
    if not n2_box:
        raise HTTPException(status_code=404, detail="Caja N2 no encontrada")

    data = payload.model_dump()
    geo = data.pop("geo_coordinates", None)

    measurement = N2PortMeasurement(
        **{k: v for k, v in data.items()},
        geo_latitude=geo["latitude"] if geo else None,
        geo_longitude=geo["longitude"] if geo else None,
    )
    db.add(measurement)
    await db.flush()

    # Aplicar reglas de negocio: visita técnica si está fuera de rango
    await process_n2_measurement(db, measurement)
    await db.flush()
    await db.refresh(measurement)
    return _to_read(measurement)


@router.get("/{measurement_id}", response_model=N2PortMeasurementRead)
async def get_measurement(measurement_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(N2PortMeasurement).where(N2PortMeasurement.id == measurement_id)
    result = await db.execute(stmt)
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Medición no encontrada")
    return _to_read(m)
