"""
Contratos de datos Pydantic v2 — Módulo de Auditoría de Red ODN.

Estos esquemas son la fuente de verdad del contrato Frontend ↔ Backend.
Cada cambio aquí debe reflejarse en /frontend/src/lib/types/network-audit.ts.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Base model con serialización de UUID y datetime
# ---------------------------------------------------------------------------
class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Configuración de umbrales
# ---------------------------------------------------------------------------
class ThresholdRead(_Base):
    key: str
    value: float
    description: Optional[str] = None
    updated_at: datetime


class ThresholdUpdate(BaseModel):
    value: float = Field(..., description="Nuevo valor del umbral")


# ---------------------------------------------------------------------------
# Dispositivo OLT
# ---------------------------------------------------------------------------
class OltCreate(BaseModel):
    olt_id: str
    name: str
    hub_id: str
    localidad: str
    ip_address: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    total_ports: int = Field(default=16, ge=1, le=64)
    status: str = Field(default="ACTIVO")


class OltUpdate(BaseModel):
    name: Optional[str] = None
    hub_id: Optional[str] = None
    localidad: Optional[str] = None
    ip_address: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    total_ports: Optional[int] = Field(None, ge=1, le=64)
    status: Optional[str] = None


class OltRead(_Base):
    id: str
    olt_id: str
    name: str
    hub_id: str
    localidad: str
    ip_address: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    total_ports: int
    status: str
    created_at: datetime
    port_count: int = 0


# ---------------------------------------------------------------------------
# Puerto OLT
# ---------------------------------------------------------------------------
class OltPortCreate(BaseModel):
    olt_id: str
    port_id: str
    hub_id: str
    localidad: str
    port_occupancy_percentage: float = Field(..., ge=0, le=100)
    connected_clients_count: int = Field(..., ge=0)
    current_sfp_tx_power_dbm: float
    olt_pk_id: Optional[str] = None  # FK al dispositivo OLT padre


class OltPortForOltCreate(BaseModel):
    """Creación de puerto anidada bajo /olts/{id}/ports — no requiere olt_id/hub/localidad."""
    port_id: str
    port_occupancy_percentage: float = Field(..., ge=0, le=100)
    connected_clients_count: int = Field(..., ge=0)
    current_sfp_tx_power_dbm: float
    client_powers: List[float] = Field(default_factory=list)


class OltPortUpdate(BaseModel):
    port_occupancy_percentage: Optional[float] = Field(None, ge=0, le=100)
    connected_clients_count: Optional[int] = None
    current_sfp_tx_power_dbm: Optional[float] = None


class OltPortRead(_Base):
    id: str
    olt_pk_id: Optional[str] = None
    olt_id: str
    port_id: str
    hub_id: str
    localidad: str
    port_occupancy_percentage: float
    connected_clients_count: int
    current_sfp_tx_power_dbm: float
    last_sync_at: datetime
    sfp_alert: bool = False


class OltDetailRead(OltRead):
    """OLT con todos sus puertos y el conteo real de hijos."""
    ports: List[OltPortRead] = Field(default_factory=list)


class OltPortSyncRequest(BaseModel):
    """Payload para sincronización con Smart OLT (o mock)."""
    olt_id: str
    port_id: str
    client_powers: List[float] = Field(
        default_factory=list,
        description="Vector de potencias de ONTs en el puerto (dBm)",
    )


# ---------------------------------------------------------------------------
# N1 — Manga primaria + OTDR
# ---------------------------------------------------------------------------
class N1InfrastructureCreate(BaseModel):
    olt_port_id: str
    n1_manga_id: str
    odf_port_id: str
    otdr_total_distance_m: float = Field(..., gt=0)
    otdr_total_loss_db: float
    otdr_max_fusion_loss_db: float
    photo_url: str
    window_1310_loss_db: Optional[float] = None
    window_1550_loss_db: Optional[float] = None


class N1InfrastructureUpdate(BaseModel):
    is_otdr_approved: Optional[bool] = None
    photo_url: Optional[str] = None
    otdr_max_fusion_loss_db: Optional[float] = None
    otdr_total_loss_db: Optional[float] = None
    window_1310_loss_db: Optional[float] = None
    window_1550_loss_db: Optional[float] = None


class N1InfrastructureRead(_Base):
    id: str
    olt_port_id: str
    n1_manga_id: str
    odf_port_id: str
    otdr_total_distance_m: float
    otdr_total_loss_db: float
    otdr_max_fusion_loss_db: float
    photo_url: str
    is_otdr_approved: bool
    window_1310_loss_db: Optional[float] = None
    window_1550_loss_db: Optional[float] = None
    audited_at: datetime
    # Estado calculado
    otdr_status: str = "PENDIENTE"  # APROBADO | BLOQUEADO | PENDIENTE


# ---------------------------------------------------------------------------
# N2 — Caja NAP + OZmap
# ---------------------------------------------------------------------------
class GeoCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class N2InfrastructureCreate(BaseModel):
    parent_n1_id: str
    n2_box_id: str
    under_transformer_shield: bool = False
    photo_url: str
    ozmap_sync_status: str = "PENDIENTE"
    geo_coordinates: GeoCoordinates
    total_ports: int = Field(default=8)

    @field_validator("total_ports")
    @classmethod
    def validate_ports(cls, v: int) -> int:
        if v not in (8, 16):
            raise ValueError("total_ports debe ser 8 o 16")
        return v


class N2InfrastructureRead(_Base):
    id: str
    parent_n1_id: str
    n2_box_id: str
    under_transformer_shield: bool
    photo_url: str
    ozmap_sync_status: str
    geo_latitude: float
    geo_longitude: float
    total_ports: int
    created_at: datetime
    # Alerta de seguridad calculada
    transformer_alert: bool = False


# ---------------------------------------------------------------------------
# Mediciones de potencia N2 en calle
# ---------------------------------------------------------------------------
class N2PortMeasurementCreate(BaseModel):
    n2_infrastructure_id: str
    port_number: int = Field(..., ge=1, le=16)
    measured_power_dbm: float
    photo_port_url: str
    client_id: Optional[str] = None
    geo_coordinates: Optional[GeoCoordinates] = None


class N2PortMeasurementRead(_Base):
    id: str
    n2_infrastructure_id: str
    port_number: int
    measured_power_dbm: float
    photo_port_url: str
    client_id: Optional[str] = None
    geo_latitude: Optional[float] = None
    geo_longitude: Optional[float] = None
    measured_at: datetime
    # Clasificación calculada por servicio
    power_status: str = "NORMAL"  # NORMAL | CRITICO | SEVERO


# ---------------------------------------------------------------------------
# Incidencias OTDR
# ---------------------------------------------------------------------------
class OtdrIncidenceRead(_Base):
    id: str
    n1_infrastructure_id: str
    detected_loss_db: float
    status: str
    resolved_at: Optional[datetime] = None
    created_at: datetime


class OtdrIncidenceResolve(BaseModel):
    resolved_by: str = Field(..., description="ID del técnico que sanea el tramo")


# ---------------------------------------------------------------------------
# Reporte acumulado: SFPs por cambiar
# ---------------------------------------------------------------------------
class SfpReplacementRead(_Base):
    id: str
    olt_port_id: str
    sfp_tx_power_dbm: float
    calculated_clients_avg_dbm: float
    status: str
    updated_at: datetime
    # Datos del puerto enriquecidos
    olt_id: Optional[str] = None
    port_id: Optional[str] = None
    localidad: Optional[str] = None


# ---------------------------------------------------------------------------
# Reporte acumulado: Visitas técnicas pendientes
# ---------------------------------------------------------------------------
class PendingTechnicalVisitRead(_Base):
    id: str
    n2_port_measurement_id: Optional[str] = None
    client_id: str
    failure_type: str
    measured_power_dbm: Optional[float] = None
    status: str
    assigned_quad_id: Optional[str] = None
    priority: str
    created_at: datetime


class PendingTechnicalVisitUpdate(BaseModel):
    status: Optional[str] = None
    assigned_quad_id: Optional[str] = None
    priority: Optional[str] = None


# ---------------------------------------------------------------------------
# Acta de entrega ODN
# ---------------------------------------------------------------------------
class ChecklistItem(BaseModel):
    label: str
    passed: bool
    notes: Optional[str] = None


class DeliveryActCreate(BaseModel):
    n1_infrastructure_id: str
    sucursal: str
    squad_leader: str
    active_subscribers: int = Field(..., ge=0)
    in_range_subscribers: int = Field(..., ge=0)
    critical_subscribers: int = Field(..., ge=0)


class DeliveryActRead(_Base):
    id: str
    n1_infrastructure_id: str
    sucursal: str
    squad_leader: str
    active_subscribers: int
    in_range_subscribers: int
    critical_subscribers: int
    status: str
    executor_signature: Optional[str] = None
    supervisor_signature: Optional[str] = None
    executor_signed_at: Optional[datetime] = None
    supervisor_signed_at: Optional[datetime] = None
    created_at: datetime
    approved_at: Optional[datetime] = None
    # Campos enriquecidos desde N1
    n1_manga_id: Optional[str] = None
    olt_port_info: Optional[OltPortRead] = None
    checklist: List[ChecklistItem] = Field(default_factory=list)
    n2_boxes: List[N2InfrastructureRead] = Field(default_factory=list)


class DeliveryActSign(BaseModel):
    role: str = Field(..., pattern="^(EXECUTOR|SUPERVISOR)$")
    signature_data: str = Field(..., description="Firma digital en base64 o texto")
    signer_name: str


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------
class AuditDashboardSummary(BaseModel):
    total_ports_audited: int = 0
    ports_with_sfp_alert: int = 0
    blocked_otdr_tramos: int = 0
    pending_technical_visits: int = 0
    transformer_alerts: int = 0
    acts_approved: int = 0
    acts_pending: int = 0
