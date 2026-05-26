"""Router: Reportes acumulados, actas de entrega y dashboard."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.network_audit import (
    DeliveryAct,
    N1Infrastructure,
    N2Infrastructure,
    OltPort,
    OtdrIncidence,
    PendingTechnicalVisit,
    SfpReplacement,
)
from app.schemas.network_audit import (
    AuditDashboardSummary,
    DeliveryActCreate,
    DeliveryActRead,
    DeliveryActSign,
    PendingTechnicalVisitRead,
    PendingTechnicalVisitUpdate,
    SfpReplacementRead,
)
from app.services.act_service import compile_delivery_act, sign_act

router = APIRouter(prefix="/reports", tags=["Reports & Acts"])


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------
@router.get("/dashboard", response_model=AuditDashboardSummary)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    total_ports = (await db.execute(select(func.count(OltPort.id)))).scalar_one()
    sfp_alerts = (
        await db.execute(
            select(func.count(SfpReplacement.id)).where(SfpReplacement.status == "PENDIENTE")
        )
    ).scalar_one()
    blocked_otdr = (
        await db.execute(
            select(func.count(OtdrIncidence.id)).where(OtdrIncidence.status == "BLOQUEADO")
        )
    ).scalar_one()
    pending_visits = (
        await db.execute(
            select(func.count(PendingTechnicalVisit.id)).where(
                PendingTechnicalVisit.status.in_(["PROGRAMADO", "EN_PROGRESO"])
            )
        )
    ).scalar_one()
    transformer_alerts = (
        await db.execute(
            select(func.count(N2Infrastructure.id)).where(
                N2Infrastructure.under_transformer_shield.is_(True)
            )
        )
    ).scalar_one()
    acts_approved = (
        await db.execute(
            select(func.count(DeliveryAct.id)).where(
                DeliveryAct.status.in_(["APROBADO", "EXCEPCION_ACEPTADA"])
            )
        )
    ).scalar_one()
    acts_pending = (
        await db.execute(
            select(func.count(DeliveryAct.id)).where(DeliveryAct.status == "BORRADOR")
        )
    ).scalar_one()

    return AuditDashboardSummary(
        total_ports_audited=total_ports,
        ports_with_sfp_alert=sfp_alerts,
        blocked_otdr_tramos=blocked_otdr,
        pending_technical_visits=pending_visits,
        transformer_alerts=transformer_alerts,
        acts_approved=acts_approved,
        acts_pending=acts_pending,
    )


# ---------------------------------------------------------------------------
# Reporte SFP
# ---------------------------------------------------------------------------
@router.get("/sfp-replacements", response_model=List[SfpReplacementRead])
async def list_sfp_replacements(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(SfpReplacement, OltPort).join(
        OltPort, SfpReplacement.olt_port_id == OltPort.id
    )
    if status_filter:
        stmt = stmt.where(SfpReplacement.status == status_filter)
    result = await db.execute(stmt)
    rows = result.all()
    return [
        SfpReplacementRead(
            id=rep.id,
            olt_port_id=rep.olt_port_id,
            sfp_tx_power_dbm=float(rep.sfp_tx_power_dbm),
            calculated_clients_avg_dbm=float(rep.calculated_clients_avg_dbm),
            status=rep.status,
            updated_at=rep.updated_at,
            olt_id=port.olt_id,
            port_id=port.port_id,
            localidad=port.localidad,
        )
        for rep, port in rows
    ]


@router.patch("/sfp-replacements/{rep_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_sfp_replacement(rep_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(SfpReplacement).where(SfpReplacement.id == rep_id)
    result = await db.execute(stmt)
    rep = result.scalar_one_or_none()
    if not rep:
        raise HTTPException(status_code=404, detail="Registro SFP no encontrado")
    rep.status = "REEMPLAZADO"
    await db.flush()
    return {"id": rep_id, "status": "REEMPLAZADO"}


# ---------------------------------------------------------------------------
# Reporte visitas técnicas
# ---------------------------------------------------------------------------
@router.get("/pending-visits", response_model=List[PendingTechnicalVisitRead])
async def list_pending_visits(
    status_filter: str | None = None,
    priority: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PendingTechnicalVisit)
    if status_filter:
        stmt = stmt.where(PendingTechnicalVisit.status == status_filter)
    if priority:
        stmt = stmt.where(PendingTechnicalVisit.priority == priority)
    result = await db.execute(stmt)
    visits = result.scalars().all()
    return [
        PendingTechnicalVisitRead(
            id=v.id,
            n2_port_measurement_id=v.n2_port_measurement_id,
            client_id=v.client_id,
            failure_type=v.failure_type,
            measured_power_dbm=float(v.measured_power_dbm) if v.measured_power_dbm else None,
            status=v.status,
            assigned_quad_id=v.assigned_quad_id,
            priority=v.priority,
            created_at=v.created_at,
        )
        for v in visits
    ]


@router.patch("/pending-visits/{visit_id}", response_model=PendingTechnicalVisitRead)
async def update_pending_visit(
    visit_id: str,
    payload: PendingTechnicalVisitUpdate,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PendingTechnicalVisit).where(PendingTechnicalVisit.id == visit_id)
    result = await db.execute(stmt)
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="Visita técnica no encontrada")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(visit, field, value)
    await db.flush()
    await db.refresh(visit)
    return PendingTechnicalVisitRead(
        id=visit.id,
        n2_port_measurement_id=visit.n2_port_measurement_id,
        client_id=visit.client_id,
        failure_type=visit.failure_type,
        measured_power_dbm=float(visit.measured_power_dbm) if visit.measured_power_dbm else None,
        status=visit.status,
        assigned_quad_id=visit.assigned_quad_id,
        priority=visit.priority,
        created_at=visit.created_at,
    )


# ---------------------------------------------------------------------------
# Actas de entrega
# ---------------------------------------------------------------------------
@router.get("/acts", response_model=List[DeliveryActRead])
async def list_acts(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DeliveryAct)
    if status_filter:
        stmt = stmt.where(DeliveryAct.status == status_filter)
    result = await db.execute(stmt)
    acts = result.scalars().all()
    compiled = []
    for act in acts:
        try:
            compiled.append(await compile_delivery_act(db, act))
        except Exception:
            pass
    return compiled


@router.post("/acts", response_model=DeliveryActRead, status_code=status.HTTP_201_CREATED)
async def create_act(
    payload: DeliveryActCreate,
    db: AsyncSession = Depends(get_db),
):
    # Verificar que N1 existe y está aprobado
    n1_stmt = select(N1Infrastructure).where(
        N1Infrastructure.id == payload.n1_infrastructure_id
    )
    n1_result = await db.execute(n1_stmt)
    n1 = n1_result.scalar_one_or_none()
    if not n1:
        raise HTTPException(status_code=404, detail="N1 no encontrado")
    if not n1.is_otdr_approved:
        raise HTTPException(
            status_code=409,
            detail="No se puede generar el acta: el tramo N1 tiene OTDR bloqueado.",
        )

    act = DeliveryAct(**payload.model_dump())
    db.add(act)
    await db.flush()
    await db.refresh(act)
    return await compile_delivery_act(db, act)


@router.get("/acts/{act_id}", response_model=DeliveryActRead)
async def get_act(act_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(DeliveryAct).where(DeliveryAct.id == act_id)
    result = await db.execute(stmt)
    act = result.scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    return await compile_delivery_act(db, act)


@router.post("/acts/{act_id}/sign", response_model=DeliveryActRead)
async def sign_delivery_act(
    act_id: str,
    payload: DeliveryActSign,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DeliveryAct).where(DeliveryAct.id == act_id)
    result = await db.execute(stmt)
    act = result.scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Acta no encontrada")
    if act.status not in ("BORRADOR", "APROBADO"):
        raise HTTPException(status_code=409, detail=f"Acta en estado {act.status}, no se puede firmar")

    await sign_act(db, act, payload.role, payload.signature_data, payload.signer_name)
    await db.flush()
    await db.refresh(act)
    return await compile_delivery_act(db, act)
