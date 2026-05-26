"""
Servicio OTDR — Compuerta de Bloqueo.

La lógica de clasificación vive en N1Infrastructure (otdr_status, passes_otdr_gate).
Este servicio sólo orquesta la creación/actualización de incidencias en la BD.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.network_audit import N1Infrastructure, OtdrIncidence


async def evaluate_otdr_gate(
    db: AsyncSession,
    n1: N1Infrastructure,
) -> tuple[bool, OtdrIncidence | None]:
    """
    Evalúa la compuerta OTDR para un tramo N1.

    Retorna (is_approved, incidence_or_None).
    Delega la decisión de umbral a n1.passes_otdr_gate().
    """
    passes = n1.passes_otdr_gate()

    stmt = select(OtdrIncidence).where(
        OtdrIncidence.n1_infrastructure_id == n1.id,
        OtdrIncidence.status == "BLOQUEADO",
    )
    result = await db.execute(stmt)
    existing_incidence = result.scalar_one_or_none()

    if passes:
        if existing_incidence:
            existing_incidence.status = "SANEADO"
            existing_incidence.resolved_at = datetime.now(timezone.utc)
        await db.execute(
            update(N1Infrastructure)
            .where(N1Infrastructure.id == n1.id)
            .values(is_otdr_approved=True)
        )
        return True, None
    else:
        if not existing_incidence:
            incidence = OtdrIncidence(
                n1_infrastructure_id=n1.id,
                detected_loss_db=float(n1.otdr_max_fusion_loss_db),
                status="BLOQUEADO",
            )
            db.add(incidence)
        else:
            existing_incidence.detected_loss_db = float(n1.otdr_max_fusion_loss_db)
            incidence = existing_incidence
        await db.execute(
            update(N1Infrastructure)
            .where(N1Infrastructure.id == n1.id)
            .values(is_otdr_approved=False)
        )
        return False, incidence


async def resolve_otdr_incidence(
    db: AsyncSession,
    incidence_id: str,
    resolved_by: str,
) -> OtdrIncidence:
    """Sanea manualmente una incidencia OTDR (tras reparación física)."""
    stmt = select(OtdrIncidence).where(OtdrIncidence.id == incidence_id)
    result = await db.execute(stmt)
    incidence = result.scalar_one_or_none()

    if not incidence:
        raise ValueError(f"Incidencia {incidence_id} no encontrada")
    if incidence.status == "SANEADO":
        raise ValueError("La incidencia ya fue saneada")

    incidence.status = "SANEADO"
    incidence.resolved_at = datetime.now(timezone.utc)

    n1_stmt = select(N1Infrastructure).where(
        N1Infrastructure.id == incidence.n1_infrastructure_id
    )
    n1_result = await db.execute(n1_stmt)
    n1 = n1_result.scalar_one_or_none()
    if n1:
        await db.execute(
            update(N1Infrastructure)
            .where(N1Infrastructure.id == n1.id)
            .values(is_otdr_approved=True)
        )

    return incidence
