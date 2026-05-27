from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _uuid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Mixin de configuración — evita importar get_settings en cada método
# ---------------------------------------------------------------------------
def _settings():
    from app.config import get_settings  # importación diferida para evitar circulares
    return get_settings()


# ---------------------------------------------------------------------------
# Configuración de umbrales parametrizados
# ---------------------------------------------------------------------------
class ThresholdsConfig(Base):
    __tablename__ = "thresholds_config"
    __table_args__ = {"schema": "network_audit"}

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ---------------------------------------------------------------------------
# 1. Dispositivo OLT (entidad padre de puertos)
# ---------------------------------------------------------------------------
class Olt(Base):
    __tablename__ = "olts"
    __table_args__ = {"schema": "network_audit"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    olt_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    hub_id: Mapped[str] = mapped_column(String(100), nullable=False)
    localidad: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    brand: Mapped[Optional[str]] = mapped_column(String(100))
    model: Mapped[Optional[str]] = mapped_column(String(100))
    total_ports: Mapped[int] = mapped_column(Integer, nullable=False, default=16)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVO")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    ports: Mapped[List["OltPort"]] = relationship(
        back_populates="olt",
        cascade="all, delete-orphan",
        foreign_keys="OltPort.olt_pk_id",
    )

    # ------------------------------------------------------------------
    # Lógica de negocio
    # ------------------------------------------------------------------
    @property
    def has_sfp_alerts(self) -> bool:
        return any(p.sfp_alert for p in self.ports)

    @property
    def has_blocked_tramos(self) -> bool:
        return any(
            n1.otdr_status == "BLOQUEADO"
            for p in self.ports
            for n1 in p.n1_infrastructure
        )


# ---------------------------------------------------------------------------
# 2. Puerto OLT
# ---------------------------------------------------------------------------
class OltPort(Base):
    __tablename__ = "olt_ports"
    __table_args__ = (
        UniqueConstraint("olt_id", "port_id", name="unique_olt_port"),
        {"schema": "network_audit"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    # FK opcional al dispositivo OLT padre (nullable para datos pre-migración)
    olt_pk_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("network_audit.olts.id", ondelete="SET NULL"),
        nullable=True,
    )
    olt_id: Mapped[str] = mapped_column(String(100), nullable=False)
    port_id: Mapped[str] = mapped_column(String(50), nullable=False)
    hub_id: Mapped[str] = mapped_column(String(100), nullable=False)
    localidad: Mapped[str] = mapped_column(String(100), nullable=False)
    port_occupancy_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    connected_clients_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_sfp_tx_power_dbm: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    last_sync_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relaciones
    olt: Mapped[Optional["Olt"]] = relationship(
        back_populates="ports",
        foreign_keys=[olt_pk_id],
    )
    n1_infrastructure: Mapped[List["N1Infrastructure"]] = relationship(
        back_populates="olt_port", cascade="all, delete-orphan"
    )
    sfp_replacements: Mapped[List["SfpReplacement"]] = relationship(
        back_populates="olt_port", cascade="all, delete-orphan"
    )

    # ------------------------------------------------------------------
    # Lógica de negocio
    # ------------------------------------------------------------------
    @property
    def sfp_alert(self) -> bool:
        """True si la potencia TX del SFP está por debajo del umbral mínimo."""
        return float(self.current_sfp_tx_power_dbm) < _settings().SFP_MIN_TX_POWER_DBM

    @staticmethod
    def calculate_clients_average(client_powers: List[float]) -> Optional[float]:
        """Promedio de potencias de las ONTs del puerto; None si no hay datos válidos."""
        valid = [p for p in client_powers if p is not None]
        return sum(valid) / len(valid) if valid else None

    def needs_sfp_replacement(self, client_powers: List[float]) -> bool:
        """True si el SFP y el promedio de ONTs superan ambos umbrales de reemplazo."""
        if not self.sfp_alert:
            return False
        avg = self.calculate_clients_average(client_powers)
        return avg is not None and avg < _settings().CLIENT_AVG_MIN_POWER_DBM


# ---------------------------------------------------------------------------
# 2. Infraestructura N1 (manga primaria + OTDR)
# ---------------------------------------------------------------------------
class N1Infrastructure(Base):
    __tablename__ = "n1_infrastructure"
    __table_args__ = {"schema": "network_audit"}

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    olt_port_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("network_audit.olt_ports.id", ondelete="CASCADE"),
        nullable=False,
    )
    n1_manga_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    odf_port_id: Mapped[str] = mapped_column(String(100), nullable=False)
    otdr_total_distance_m: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    otdr_total_loss_db: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    otdr_max_fusion_loss_db: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    photo_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_otdr_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    window_1310_loss_db: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    window_1550_loss_db: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    audited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    olt_port: Mapped["OltPort"] = relationship(back_populates="n1_infrastructure")
    n2_infrastructure: Mapped[List["N2Infrastructure"]] = relationship(
        back_populates="parent_n1", cascade="all, delete-orphan"
    )
    otdr_incidences: Mapped[List["OtdrIncidence"]] = relationship(
        back_populates="n1_infrastructure", cascade="all, delete-orphan"
    )
    delivery_acts: Mapped[List["DeliveryAct"]] = relationship(
        back_populates="n1_infrastructure", cascade="all, delete-orphan"
    )

    # ------------------------------------------------------------------
    # Lógica de negocio
    # ------------------------------------------------------------------
    @property
    def otdr_status(self) -> str:
        """Estado calculado del tramo: APROBADO | BLOQUEADO | PENDIENTE."""
        if self.is_otdr_approved:
            return "APROBADO"
        if float(self.otdr_max_fusion_loss_db) > _settings().OTDR_MAX_FUSION_LOSS_DB:
            return "BLOQUEADO"
        return "PENDIENTE"

    def passes_otdr_gate(self) -> bool:
        """True si la pérdida máxima por fusión está dentro del umbral permitido."""
        return float(self.otdr_max_fusion_loss_db) <= _settings().OTDR_MAX_FUSION_LOSS_DB


# ---------------------------------------------------------------------------
# 3. Infraestructura N2 (caja NAP + OZmap)
# ---------------------------------------------------------------------------
class N2Infrastructure(Base):
    __tablename__ = "n2_infrastructure"
    __table_args__ = (
        CheckConstraint("ozmap_sync_status IN ('CONCILIADO','DISCREPANCIA','PENDIENTE')"),
        {"schema": "network_audit"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    parent_n1_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("network_audit.n1_infrastructure.id", ondelete="CASCADE"),
        nullable=False,
    )
    n2_box_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    under_transformer_shield: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    photo_url: Mapped[str] = mapped_column(Text, nullable=False)
    ozmap_sync_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    geo_latitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    geo_longitude: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    total_ports: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    parent_n1: Mapped["N1Infrastructure"] = relationship(back_populates="n2_infrastructure")
    port_measurements: Mapped[List["N2PortMeasurement"]] = relationship(
        back_populates="n2_infrastructure", cascade="all, delete-orphan"
    )

    # ------------------------------------------------------------------
    # Lógica de negocio
    # ------------------------------------------------------------------
    @property
    def transformer_alert(self) -> bool:
        """True si la caja NAP está bajo un transformador eléctrico (riesgo industrial)."""
        return self.under_transformer_shield


# ---------------------------------------------------------------------------
# 4. Mediciones de potencia en calle (puertos N2)
# ---------------------------------------------------------------------------
class N2PortMeasurement(Base):
    __tablename__ = "n2_port_measurements"
    __table_args__ = (
        UniqueConstraint("n2_infrastructure_id", "port_number", name="unique_n2_port_measurement"),
        CheckConstraint("port_number BETWEEN 1 AND 16"),
        {"schema": "network_audit"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    n2_infrastructure_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("network_audit.n2_infrastructure.id", ondelete="CASCADE"),
        nullable=False,
    )
    port_number: Mapped[int] = mapped_column(Integer, nullable=False)
    measured_power_dbm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    photo_port_url: Mapped[str] = mapped_column(Text, nullable=False)
    client_id: Mapped[Optional[str]] = mapped_column(String(100))
    geo_latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    geo_longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    n2_infrastructure: Mapped["N2Infrastructure"] = relationship(
        back_populates="port_measurements"
    )
    pending_visits: Mapped[List["PendingTechnicalVisit"]] = relationship(
        back_populates="n2_port_measurement"
    )

    # ------------------------------------------------------------------
    # Lógica de negocio
    # ------------------------------------------------------------------
    @property
    def power_status(self) -> str:
        """Clasifica la potencia medida: NORMAL | CRITICO | SEVERO."""
        s = _settings()
        power = float(self.measured_power_dbm)
        if power < s.CLIENT_CRITICAL_SEVERE_POWER_DBM:
            return "SEVERO"
        if power < s.CLIENT_CRITICAL_POWER_DBM:
            return "CRITICO"
        return "NORMAL"

    @property
    def is_critical(self) -> bool:
        """True si la potencia está por debajo del umbral crítico."""
        return float(self.measured_power_dbm) < _settings().CLIENT_CRITICAL_POWER_DBM

    def needs_technical_visit(self) -> bool:
        """True si la medición requiere visita técnica (fuera de rango normal)."""
        return self.power_status != "NORMAL"


# ---------------------------------------------------------------------------
# 5. Incidencias OTDR (bloqueos de reflectometría)
# ---------------------------------------------------------------------------
class OtdrIncidence(Base):
    __tablename__ = "otdr_incidences"
    __table_args__ = (
        CheckConstraint("status IN ('BLOQUEADO','SANEADO')"),
        {"schema": "network_audit"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    n1_infrastructure_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("network_audit.n1_infrastructure.id", ondelete="CASCADE"),
        nullable=False,
    )
    detected_loss_db: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="BLOQUEADO")
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    n1_infrastructure: Mapped["N1Infrastructure"] = relationship(
        back_populates="otdr_incidences"
    )


# ---------------------------------------------------------------------------
# 6. Reporte acumulado SFPs por cambiar
# ---------------------------------------------------------------------------
class SfpReplacement(Base):
    __tablename__ = "sfp_replacements"
    __table_args__ = (
        CheckConstraint("status IN ('PENDIENTE','REEMPLAZADO')"),
        {"schema": "network_audit"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    olt_port_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("network_audit.olt_ports.id", ondelete="CASCADE"),
        nullable=False,
    )
    sfp_tx_power_dbm: Mapped[float] = mapped_column(Numeric(4, 2), nullable=False)
    calculated_clients_avg_dbm: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    olt_port: Mapped["OltPort"] = relationship(back_populates="sfp_replacements")


# ---------------------------------------------------------------------------
# 7. Visitas técnicas pendientes
# ---------------------------------------------------------------------------
class PendingTechnicalVisit(Base):
    __tablename__ = "pending_technical_visits"
    __table_args__ = (
        CheckConstraint(
            "failure_type IN ('POTENCIA_CRITICA_N2','POTENCIA_SEVERA_N2','POSTE_CON_TRANSFORMADOR')"
        ),
        CheckConstraint("status IN ('PROGRAMADO','EN_PROGRESO','RESUELTO')"),
        CheckConstraint("priority IN ('NORMAL','URGENTE')"),
        {"schema": "network_audit"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    n2_port_measurement_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("network_audit.n2_port_measurements.id", ondelete="SET NULL"),
    )
    client_id: Mapped[str] = mapped_column(String(100), nullable=False)
    failure_type: Mapped[str] = mapped_column(String(100), nullable=False)
    measured_power_dbm: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PROGRAMADO")
    assigned_quad_id: Mapped[Optional[str]] = mapped_column(String(100))
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="NORMAL")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    n2_port_measurement: Mapped[Optional["N2PortMeasurement"]] = relationship(
        back_populates="pending_visits"
    )


# ---------------------------------------------------------------------------
# 8. Actas de entrega ODN
# ---------------------------------------------------------------------------
class DeliveryAct(Base):
    __tablename__ = "delivery_acts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('BORRADOR','APROBADO','EXCEPCION_ACEPTADA','RECHAZADO')"
        ),
        {"schema": "network_audit"},
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    n1_infrastructure_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("network_audit.n1_infrastructure.id", ondelete="CASCADE"),
        nullable=False,
    )
    sucursal: Mapped[str] = mapped_column(String(100), nullable=False)
    squad_leader: Mapped[str] = mapped_column(String(100), nullable=False)
    active_subscribers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    in_range_subscribers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    critical_subscribers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="BORRADOR")
    executor_signature: Mapped[Optional[str]] = mapped_column(Text)
    supervisor_signature: Mapped[Optional[str]] = mapped_column(Text)
    executor_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    supervisor_signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    n1_infrastructure: Mapped["N1Infrastructure"] = relationship(
        back_populates="delivery_acts"
    )
