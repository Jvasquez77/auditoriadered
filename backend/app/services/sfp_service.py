"""
Servicio SFP — Orquestación de persistencia para evaluación de módulos ópticos.

La lógica de clasificación vive en OltPort (sfp_alert, needs_sfp_replacement).
Este servicio sólo se encarga de crear/actualizar registros en sfp_replacements.
"""

from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.network_audit import OltPort, SfpReplacement


async def process_sfp_evaluation(
    db: AsyncSession,
    olt_port: OltPort,
    client_powers: List[float],
) -> SfpReplacement | None:
    """
    Crea o actualiza el registro de reemplazo si el puerto necesita cambio de SFP.
    Delega la decisión a olt_port.needs_sfp_replacement().
    """
    if not olt_port.needs_sfp_replacement(client_powers):
        return None

    avg_power = OltPort.calculate_clients_average(client_powers)
    if avg_power is None:
        return None

    stmt = select(SfpReplacement).where(
        SfpReplacement.olt_port_id == olt_port.id,
        SfpReplacement.status == "PENDIENTE",
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        existing.sfp_tx_power_dbm = float(olt_port.current_sfp_tx_power_dbm)
        existing.calculated_clients_avg_dbm = avg_power
        return existing

    replacement = SfpReplacement(
        olt_port_id=olt_port.id,
        sfp_tx_power_dbm=float(olt_port.current_sfp_tx_power_dbm),
        calculated_clients_avg_dbm=avg_power,
        status="PENDIENTE",
    )
    db.add(replacement)
    return replacement
