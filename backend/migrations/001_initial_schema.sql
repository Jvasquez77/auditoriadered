-- =============================================================================
-- Módulo de Auditoría de Red ODN — Esquema inicial
-- Bounded Context: network_audit
-- Estrategia: Índices B-tree para búsquedas de alta concurrencia
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS network_audit;

-- ---------------------------------------------------------------------------
-- Tabla de configuración paramétrica (umbrales — NUNCA hardcodeados)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.thresholds_config (
    key         VARCHAR(100) PRIMARY KEY,
    value       NUMERIC(10, 4) NOT NULL,
    description TEXT,
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO network_audit.thresholds_config (key, value, description)
VALUES
    ('OTDR_MAX_FUSION_LOSS_DB',         0.1000, 'Pérdida máxima permitida por fusión en OTDR (dB). Compuerta de bloqueo.'),
    ('SFP_MIN_TX_POWER_DBM',            6.0000, 'Potencia mínima de transmisión SFP OLT (dBm). Por debajo: revisión.'),
    ('CLIENT_AVG_MIN_POWER_DBM',       -26.5000,'Promedio mínimo de potencia ONT por puerto (dBm). Agrega al reporte SFP.'),
    ('CLIENT_CRITICAL_POWER_DBM',      -25.4000,'Umbral crítico de potencia en calle N2 (dBm). Genera visita técnica.'),
    ('CLIENT_CRITICAL_SEVERE_POWER_DBM',-27.0100,'Umbral crítico severo N2 (dBm). Genera visita técnica urgente.'),
    ('RESERVE_BOX_METERS',             15.0000, 'Reserva técnica mínima en caja (metros).'),
    ('RESERVE_POLE_METERS',            40.0000, 'Reserva técnica mínima en poste (metros).'),
    ('RESERVE_POLE_INTERVAL_METERS',  400.0000, 'Intervalo entre reservas en poste (metros).')
ON CONFLICT (key) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 1. Puertos OLT (telemetría Smart OLT)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.olt_ports (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    olt_id                      VARCHAR(100) NOT NULL,
    port_id                     VARCHAR(50)  NOT NULL,
    hub_id                      VARCHAR(100) NOT NULL,
    localidad                   VARCHAR(100) NOT NULL,
    port_occupancy_percentage   NUMERIC(5, 2) NOT NULL,
    connected_clients_count     INT          NOT NULL,
    current_sfp_tx_power_dbm    NUMERIC(4, 2) NOT NULL,
    last_sync_at                TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_olt_port UNIQUE (olt_id, port_id)
);

CREATE INDEX IF NOT EXISTS idx_olt_ports_search   ON network_audit.olt_ports (olt_id, port_id);
CREATE INDEX IF NOT EXISTS idx_olt_ports_localidad ON network_audit.olt_ports (localidad);

-- ---------------------------------------------------------------------------
-- 2. Infraestructura N1 — Manga primaria + OTDR
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.n1_infrastructure (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    olt_port_id             UUID NOT NULL REFERENCES network_audit.olt_ports(id) ON DELETE CASCADE,
    n1_manga_id             VARCHAR(100) NOT NULL UNIQUE,
    odf_port_id             VARCHAR(100) NOT NULL,
    otdr_total_distance_m   NUMERIC(8, 2) NOT NULL,
    otdr_total_loss_db      NUMERIC(5, 2) NOT NULL,
    otdr_max_fusion_loss_db NUMERIC(4, 2) NOT NULL,  -- Regla de 0.1 dB
    photo_url               TEXT NOT NULL,
    is_otdr_approved        BOOLEAN NOT NULL DEFAULT FALSE,  -- Compuerta de bloqueo
    window_1310_loss_db     NUMERIC(5, 2),
    window_1550_loss_db     NUMERIC(5, 2),
    audited_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_n1_manga_search ON network_audit.n1_infrastructure (n1_manga_id);
CREATE INDEX IF NOT EXISTS idx_n1_port_fk      ON network_audit.n1_infrastructure (olt_port_id);

-- ---------------------------------------------------------------------------
-- 3. Infraestructura N2 — Cajas NAP + OZmap
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.n2_infrastructure (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_n1_id            UUID NOT NULL REFERENCES network_audit.n1_infrastructure(id) ON DELETE CASCADE,
    n2_box_id               VARCHAR(100) NOT NULL UNIQUE,
    under_transformer_shield BOOLEAN NOT NULL DEFAULT FALSE,
    photo_url               TEXT NOT NULL,
    ozmap_sync_status       VARCHAR(50) NOT NULL CHECK (ozmap_sync_status IN ('CONCILIADO','DISCREPANCIA','PENDIENTE')),
    geo_latitude            NUMERIC(10, 7) NOT NULL,
    geo_longitude           NUMERIC(10, 7) NOT NULL,
    total_ports             INT NOT NULL DEFAULT 8 CHECK (total_ports IN (8, 16)),
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_n2_box_search ON network_audit.n2_infrastructure (n2_box_id);
CREATE INDEX IF NOT EXISTS idx_n2_parent_fk  ON network_audit.n2_infrastructure (parent_n1_id);

-- ---------------------------------------------------------------------------
-- 4. Mediciones de potencia en calle (puertos N2)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.n2_port_measurements (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    n2_infrastructure_id UUID NOT NULL REFERENCES network_audit.n2_infrastructure(id) ON DELETE CASCADE,
    port_number          INT NOT NULL,
    measured_power_dbm   NUMERIC(5, 2) NOT NULL,
    photo_port_url       TEXT NOT NULL,
    client_id            VARCHAR(100),
    geo_latitude         NUMERIC(10, 7),
    geo_longitude        NUMERIC(10, 7),
    measured_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_n2_port_measurement UNIQUE (n2_infrastructure_id, port_number),
    CONSTRAINT chk_port_number CHECK (port_number BETWEEN 1 AND 16)
);

CREATE INDEX IF NOT EXISTS idx_n2_measurements_fk ON network_audit.n2_port_measurements (n2_infrastructure_id);

-- ---------------------------------------------------------------------------
-- 5. Incidencias OTDR — Bloqueos de reflectometría
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.otdr_incidences (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    n1_infrastructure_id UUID NOT NULL REFERENCES network_audit.n1_infrastructure(id) ON DELETE CASCADE,
    detected_loss_db     NUMERIC(4, 2) NOT NULL,
    status               VARCHAR(50) NOT NULL DEFAULT 'BLOQUEADO'
                             CHECK (status IN ('BLOQUEADO','SANEADO')),
    resolved_at          TIMESTAMP WITH TIME ZONE,
    created_at           TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_otdr_incidences_status ON network_audit.otdr_incidences (status);
CREATE INDEX IF NOT EXISTS idx_otdr_incidences_n1_fk  ON network_audit.otdr_incidences (n1_infrastructure_id);

-- ---------------------------------------------------------------------------
-- 6. Reporte acumulado SFPs por cambiar
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.sfp_replacements (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    olt_port_id              UUID NOT NULL REFERENCES network_audit.olt_ports(id) ON DELETE CASCADE,
    sfp_tx_power_dbm         NUMERIC(4, 2) NOT NULL,
    calculated_clients_avg_dbm NUMERIC(5, 2) NOT NULL,
    status                   VARCHAR(50) NOT NULL DEFAULT 'PENDIENTE'
                                 CHECK (status IN ('PENDIENTE','REEMPLAZADO')),
    updated_at               TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sfp_replacements_status ON network_audit.sfp_replacements (status);

-- ---------------------------------------------------------------------------
-- 7. Reporte acumulado de visitas técnicas pendientes
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.pending_technical_visits (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    n2_port_measurement_id UUID REFERENCES network_audit.n2_port_measurements(id) ON DELETE SET NULL,
    client_id              VARCHAR(100) NOT NULL,
    failure_type           VARCHAR(100) NOT NULL
                               CHECK (failure_type IN ('POTENCIA_CRITICA_N2','POTENCIA_SEVERA_N2','POSTE_CON_TRANSFORMADOR')),
    measured_power_dbm     NUMERIC(5, 2),
    status                 VARCHAR(50) NOT NULL DEFAULT 'PROGRAMADO'
                               CHECK (status IN ('PROGRAMADO','EN_PROGRESO','RESUELTO')),
    assigned_quad_id       VARCHAR(100),
    priority               VARCHAR(20) NOT NULL DEFAULT 'NORMAL'
                               CHECK (priority IN ('NORMAL','URGENTE')),
    created_at             TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pending_visits_status   ON network_audit.pending_technical_visits (status);
CREATE INDEX IF NOT EXISTS idx_pending_visits_priority ON network_audit.pending_technical_visits (priority);

-- ---------------------------------------------------------------------------
-- 8. Actas de entrega ODN (documento final)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS network_audit.delivery_acts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    n1_infrastructure_id UUID NOT NULL REFERENCES network_audit.n1_infrastructure(id) ON DELETE CASCADE,
    sucursal            VARCHAR(100) NOT NULL,
    squad_leader        VARCHAR(100) NOT NULL,
    active_subscribers  INT NOT NULL DEFAULT 0,
    in_range_subscribers INT NOT NULL DEFAULT 0,
    critical_subscribers INT NOT NULL DEFAULT 0,
    status              VARCHAR(50) NOT NULL DEFAULT 'BORRADOR'
                            CHECK (status IN ('BORRADOR','APROBADO','EXCEPCION_ACEPTADA','RECHAZADO')),
    executor_signature  TEXT,
    supervisor_signature TEXT,
    executor_signed_at  TIMESTAMP WITH TIME ZONE,
    supervisor_signed_at TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_at         TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_delivery_acts_status ON network_audit.delivery_acts (status);
CREATE INDEX IF NOT EXISTS idx_delivery_acts_n1_fk  ON network_audit.delivery_acts (n1_infrastructure_id);
