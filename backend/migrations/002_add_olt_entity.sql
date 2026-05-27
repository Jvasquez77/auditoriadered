-- Migración 002: Entidad OLT como raíz de la jerarquía de red ODN
-- Aplica sobre el schema network_audit creado en 001_initial_schema.sql

SET search_path TO network_audit, public;

-- 1. Tabla de dispositivos OLT
CREATE TABLE IF NOT EXISTS network_audit.olts (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    olt_id       VARCHAR(100) NOT NULL UNIQUE,
    name         VARCHAR(200) NOT NULL,
    hub_id       VARCHAR(100) NOT NULL,
    localidad    VARCHAR(100) NOT NULL,
    ip_address   VARCHAR(50),
    brand        VARCHAR(100),
    model        VARCHAR(100),
    total_ports  INTEGER      NOT NULL DEFAULT 16,
    status       VARCHAR(50)  NOT NULL DEFAULT 'ACTIVO'
                              CHECK (status IN ('ACTIVO', 'INACTIVO', 'MANTENIMIENTO')),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 2. FK opcional en olt_ports → olts (SET NULL para no romper puertos pre-migración)
ALTER TABLE network_audit.olt_ports
    ADD COLUMN IF NOT EXISTS olt_pk_id UUID
        REFERENCES network_audit.olts(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_olt_ports_olt_pk_id
    ON network_audit.olt_ports(olt_pk_id);
