"""
Servicio de Auditoría de Potencias N2 en Calle.

La lógica de clasificación vive en N2PortMeasurement (power_status, needs_technical_visit).
Este servicio sólo orquesta la creación de visitas técnicas y alertas de transformador.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.network_audit import N2Infrastructure, N2PortMeasurement, PendingTechnicalVisit


async def process_n2_measurement(
    db: AsyncSession,
    measurement: N2PortMeasurement,
) -> PendingTechnicalVisit | None:
    """
    Crea una visita técnica si la medición está fuera de rango.
    Delega la clasificación a measurement.power_status y needs_technical_visit().
    """
    if not measurement.needs_technical_visit():
        return None

    power_class = measurement.power_status
    priority = "URGENTE" if power_class == "SEVERO" else "NORMAL"
    failure_type = (
        "POTENCIA_SEVERA_N2" if power_class == "SEVERO" else "POTENCIA_CRITICA_N2"
    )
    client_id = measurement.client_id or f"PORT_{measurement.port_number}"

    if measurement.id:
        stmt = select(PendingTechnicalVisit).where(
            PendingTechnicalVisit.n2_port_measurement_id == measurement.id,
            PendingTechnicalVisit.status.in_(["PROGRAMADO", "EN_PROGRESO"]),
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            existing.measured_power_dbm = float(measurement.measured_power_dbm)
            existing.priority = priority
            return existing

    visit = PendingTechnicalVisit(
        n2_port_measurement_id=measurement.id,
        client_id=client_id,
        failure_type=failure_type,
        measured_power_dbm=float(measurement.measured_power_dbm),
        status="PROGRAMADO",
        priority=priority,
    )
    db.add(visit)
    return visit


async def process_transformer_alert(
    db: AsyncSession,
    n2_box: N2Infrastructure,
) -> PendingTechnicalVisit | None:
    """
    Crea alerta de seguridad industrial si la caja está bajo un transformador.
    Delega la decisión a n2_box.transformer_alert.
    """
    if not n2_box.transformer_alert:
        return None

    stmt = select(PendingTechnicalVisit).where(
        PendingTechnicalVisit.failure_type == "POSTE_CON_TRANSFORMADOR",
        PendingTechnicalVisit.client_id == n2_box.n2_box_id,
        PendingTechnicalVisit.status.in_(["PROGRAMADO", "EN_PROGRESO"]),
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    alert = PendingTechnicalVisit(
        n2_port_measurement_id=None,
        client_id=n2_box.n2_box_id,
        failure_type="POSTE_CON_TRANSFORMADOR",
        status="PROGRAMADO",
        priority="URGENTE",
    )
    db.add(alert)
    return alert
