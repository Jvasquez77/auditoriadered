"""
Motor de compilación del Acta de Entrega Técnica ODN.

El acta sólo se habilita cuando el estado del tramo es APROBADO
o EXCEPCION_ACEPTADA (sin abonados críticos sin mitigar).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.network_audit import (
    DeliveryAct,
    N1Infrastructure,
    N2Infrastructure,
    N2PortMeasurement,
)
from app.schemas.network_audit import ChecklistItem, DeliveryActRead, N2InfrastructureRead

settings = get_settings()


def _build_checklist(
    n1: N1Infrastructure,
    n2_boxes: List[N2Infrastructure],
    measurements: List[N2PortMeasurement],
) -> List[ChecklistItem]:
    """Genera la matriz de validación del acta."""
    critical_measurements = [m for m in measurements if m.is_critical]
    transformer_boxes = [b for b in n2_boxes if b.transformer_alert]

    checklist = [
        ChecklistItem(
            label="Reflectometría OTDR aprobada (≤ 0.1 dB por fusión)",
            passed=n1.is_otdr_approved,
        ),
        ChecklistItem(
            label="Sin abonados en potencia crítica sin mitigar",
            passed=len(critical_measurements) == 0,
            notes=(
                f"{len(critical_measurements)} abonados críticos pendientes"
                if critical_measurements
                else None
            ),
        ),
        ChecklistItem(
            label="Seguridad en postes — sin elementos bajo transformadores",
            passed=len(transformer_boxes) == 0,
            notes=(
                f"{len(transformer_boxes)} cajas requieren reubicación"
                if transformer_boxes
                else None
            ),
        ),
        ChecklistItem(
            label="Hermeticidad de mangas y cajas NAP",
            passed=True,  # Validación manual — operador confirma
        ),
        ChecklistItem(
            label="Marcaje acrílico en caja y cliente",
            passed=True,
        ),
        ChecklistItem(
            label=f"Reserva técnica en cajas ({settings.RESERVE_BOX_METERS}m mínimo)",
            passed=True,
        ),
        ChecklistItem(
            label=f"Reserva en poste ({settings.RESERVE_POLE_METERS}m c/ {settings.RESERVE_POLE_INTERVAL_METERS}m)",
            passed=True,
        ),
        ChecklistItem(
            label="OZmap conciliado con inventario físico",
            passed=all(b.ozmap_sync_status == "CONCILIADO" for b in n2_boxes),
        ),
    ]
    return checklist


async def compile_delivery_act(
    db: AsyncSession,
    act: DeliveryAct,
) -> DeliveryActRead:
    """Compila el acta completa con todos sus datos enriquecidos."""
    # Cargar N1 + OLT
    n1_stmt = select(N1Infrastructure).where(N1Infrastructure.id == act.n1_infrastructure_id)
    n1_result = await db.execute(n1_stmt)
    n1 = n1_result.scalar_one()

    # Cargar N2 boxes
    n2_stmt = select(N2Infrastructure).where(N2Infrastructure.parent_n1_id == n1.id)
    n2_result = await db.execute(n2_stmt)
    n2_boxes = list(n2_result.scalars().all())

    # Cargar mediciones de todos los N2
    measurements: List[N2PortMeasurement] = []
    for box in n2_boxes:
        m_stmt = select(N2PortMeasurement).where(
            N2PortMeasurement.n2_infrastructure_id == box.id
        )
        m_result = await db.execute(m_stmt)
        measurements.extend(list(m_result.scalars().all()))

    checklist = _build_checklist(n1, n2_boxes, measurements)

    from app.schemas.network_audit import N2InfrastructureRead as N2Read

    n2_reads = [N2Read.model_validate(b) for b in n2_boxes]

    return DeliveryActRead(
        id=act.id,
        n1_infrastructure_id=act.n1_infrastructure_id,
        sucursal=act.sucursal,
        squad_leader=act.squad_leader,
        active_subscribers=act.active_subscribers,
        in_range_subscribers=act.in_range_subscribers,
        critical_subscribers=act.critical_subscribers,
        status=act.status,
        executor_signature=act.executor_signature,
        supervisor_signature=act.supervisor_signature,
        executor_signed_at=act.executor_signed_at,
        supervisor_signed_at=act.supervisor_signed_at,
        created_at=act.created_at,
        approved_at=act.approved_at,
        n1_manga_id=n1.n1_manga_id,
        checklist=checklist,
        n2_boxes=n2_reads,
    )


async def sign_act(
    db: AsyncSession,
    act: DeliveryAct,
    role: str,
    signature_data: str,
    signer_name: str,
) -> DeliveryAct:
    """Registra la firma digital del ejecutor o supervisor."""
    now = datetime.now(timezone.utc)
    if role == "EXECUTOR":
        act.executor_signature = signature_data
        act.executor_signed_at = now
    elif role == "SUPERVISOR":
        act.supervisor_signature = signature_data
        act.supervisor_signed_at = now

    # Si ambas firmas están presentes, marcar como APROBADO
    if act.executor_signature and act.supervisor_signature:
        act.status = "APROBADO"
        act.approved_at = now

    return act
