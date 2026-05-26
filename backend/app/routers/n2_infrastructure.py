"""Router: Infraestructura N2 — Cajas NAP + OZmap (Ingestas E y F)."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.network_audit import N1Infrastructure, N2Infrastructure
from app.schemas.network_audit import N2InfrastructureCreate, N2InfrastructureRead
from app.services.power_audit_service import process_transformer_alert

router = APIRouter(prefix="/n2", tags=["N2 Infrastructure"])


def _to_read(b: N2Infrastructure) -> N2InfrastructureRead:
    return N2InfrastructureRead.model_validate(b)


@router.get("/", response_model=List[N2InfrastructureRead])
async def list_n2(
    parent_n1_id: str | None = None,
    transformer_alert: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(N2Infrastructure)
    if parent_n1_id:
        stmt = stmt.where(N2Infrastructure.parent_n1_id == parent_n1_id)
    if transformer_alert is not None:
        stmt = stmt.where(N2Infrastructure.under_transformer_shield.is_(transformer_alert))
    result = await db.execute(stmt)
    return [_to_read(b) for b in result.scalars().all()]


@router.post("/", response_model=N2InfrastructureRead, status_code=status.HTTP_201_CREATED)
async def create_n2(
    payload: N2InfrastructureCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verificar que el N1 padre existe y está aprobado (compuerta)
    n1_stmt = select(N1Infrastructure).where(
        N1Infrastructure.id == payload.parent_n1_id
    )
    n1_result = await db.execute(n1_stmt)
    n1 = n1_result.scalar_one_or_none()
    if not n1:
        raise HTTPException(status_code=404, detail="N1 padre no encontrado")
    if not n1.is_otdr_approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "BLOQUEADO: El tramo N1 tiene incidencias OTDR sin sanear. "
                "No se pueden registrar cajas N2 hasta que el tramo sea aprobado."
            ),
        )

    data = payload.model_dump()
    geo = data.pop("geo_coordinates")
    box = N2Infrastructure(
        **data,
        geo_latitude=geo["latitude"],
        geo_longitude=geo["longitude"],
    )
    db.add(box)
    await db.flush()

    # Evaluar alerta de transformador
    await process_transformer_alert(db, box)
    await db.flush()
    await db.refresh(box)
    return _to_read(box)


@router.get("/{box_id}", response_model=N2InfrastructureRead)
async def get_n2(box_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(N2Infrastructure).where(N2Infrastructure.id == box_id)
    result = await db.execute(stmt)
    box = result.scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=404, detail="Caja N2 no encontrada")
    return _to_read(box)


@router.post("/{box_id}/ozmap-sync", status_code=status.HTTP_200_OK)
async def sync_ozmap(
    box_id: str,
    ozmap_status: str,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza el estado de conciliación OZmap para una caja N2."""
    if ozmap_status not in ("CONCILIADO", "DISCREPANCIA", "PENDIENTE"):
        raise HTTPException(status_code=422, detail="Estado OZmap inválido")

    stmt = select(N2Infrastructure).where(N2Infrastructure.id == box_id)
    result = await db.execute(stmt)
    box = result.scalar_one_or_none()
    if not box:
        raise HTTPException(status_code=404, detail="Caja N2 no encontrada")

    box.ozmap_sync_status = ozmap_status
    await db.flush()
    return {"box_id": box_id, "ozmap_sync_status": ozmap_status}
