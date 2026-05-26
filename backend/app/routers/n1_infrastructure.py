"""Router: Infraestructura N1 — Manga primaria + OTDR (Ingestas C y D)."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.network_audit import N1Infrastructure, OtdrIncidence
from app.schemas.network_audit import (
    N1InfrastructureCreate,
    N1InfrastructureRead,
    N1InfrastructureUpdate,
    OtdrIncidenceRead,
    OtdrIncidenceResolve,
)
from app.services.otdr_service import evaluate_otdr_gate, resolve_otdr_incidence

router = APIRouter(prefix="/n1", tags=["N1 Infrastructure"])


def _to_read(n1: N1Infrastructure) -> N1InfrastructureRead:
    return N1InfrastructureRead.model_validate(n1)


@router.get("/", response_model=List[N1InfrastructureRead])
async def list_n1(
    olt_port_id: str | None = None,
    approved_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(N1Infrastructure)
    if olt_port_id:
        stmt = stmt.where(N1Infrastructure.olt_port_id == olt_port_id)
    if approved_only:
        stmt = stmt.where(N1Infrastructure.is_otdr_approved.is_(True))
    result = await db.execute(stmt)
    return [_to_read(n) for n in result.scalars().all()]


@router.post("/", response_model=N1InfrastructureRead, status_code=status.HTTP_201_CREATED)
async def create_n1(
    payload: N1InfrastructureCreate,
    db: AsyncSession = Depends(get_db),
):
    n1 = N1Infrastructure(**payload.model_dump())
    db.add(n1)
    await db.flush()

    # Evaluar compuerta OTDR inmediatamente
    await evaluate_otdr_gate(db, n1)
    await db.flush()
    await db.refresh(n1)
    return _to_read(n1)


@router.get("/{n1_id}", response_model=N1InfrastructureRead)
async def get_n1(n1_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(N1Infrastructure).where(N1Infrastructure.id == n1_id)
    result = await db.execute(stmt)
    n1 = result.scalar_one_or_none()
    if not n1:
        raise HTTPException(status_code=404, detail="Infraestructura N1 no encontrada")
    return _to_read(n1)


@router.patch("/{n1_id}", response_model=N1InfrastructureRead)
async def update_n1(
    n1_id: str,
    payload: N1InfrastructureUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(N1Infrastructure).where(N1Infrastructure.id == n1_id)
    result = await db.execute(stmt)
    n1 = result.scalar_one_or_none()
    if not n1:
        raise HTTPException(status_code=404, detail="Infraestructura N1 no encontrada")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(n1, field, value)

    # Re-evaluar compuerta si cambió la pérdida de fusión
    if payload.otdr_max_fusion_loss_db is not None:
        await evaluate_otdr_gate(db, n1)

    await db.flush()
    await db.refresh(n1)
    return _to_read(n1)


@router.get("/{n1_id}/otdr-incidences", response_model=List[OtdrIncidenceRead])
async def list_otdr_incidences(n1_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(OtdrIncidence).where(OtdrIncidence.n1_infrastructure_id == n1_id)
    result = await db.execute(stmt)
    return [
        OtdrIncidenceRead(
            id=i.id,
            n1_infrastructure_id=i.n1_infrastructure_id,
            detected_loss_db=float(i.detected_loss_db),
            status=i.status,
            resolved_at=i.resolved_at,
            created_at=i.created_at,
        )
        for i in result.scalars().all()
    ]


@router.post(
    "/incidences/{incidence_id}/resolve",
    response_model=OtdrIncidenceRead,
)
async def resolve_incidence(
    incidence_id: str,
    payload: OtdrIncidenceResolve,
    db: AsyncSession = Depends(get_db),
):
    try:
        incidence = await resolve_otdr_incidence(db, incidence_id, payload.resolved_by)
        await db.flush()
        return OtdrIncidenceRead(
            id=incidence.id,
            n1_infrastructure_id=incidence.n1_infrastructure_id,
            detected_loss_db=float(incidence.detected_loss_db),
            status=incidence.status,
            resolved_at=incidence.resolved_at,
            created_at=incidence.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
