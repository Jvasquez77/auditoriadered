/**
 * Contratos TypeScript — Módulo de Auditoría de Red ODN
 *
 * FUENTE DE VERDAD: Mirrors exactos de app/schemas/network_audit.py
 * Cualquier cambio en los schemas Pydantic debe reflejarse aquí.
 */

// ---------------------------------------------------------------------------
// Dispositivo OLT
// ---------------------------------------------------------------------------
export type OltStatus = 'ACTIVO' | 'INACTIVO' | 'MANTENIMIENTO';

export interface OltRead {
	id: string;
	olt_id: string;
	name: string;
	hub_id: string;
	localidad: string;
	ip_address: string | null;
	brand: string | null;
	model: string | null;
	total_ports: number;
	status: OltStatus;
	created_at: string;
	port_count: number;
}

export interface OltDetailRead extends OltRead {
	ports: OltPortRead[];
}

export interface OltCreate {
	olt_id: string;
	name: string;
	hub_id: string;
	localidad: string;
	ip_address?: string;
	brand?: string;
	model?: string;
	total_ports?: number;
	status?: OltStatus;
}

export interface OltPortForOltCreate {
	port_id: string;
	port_occupancy_percentage: number;
	connected_clients_count: number;
	current_sfp_tx_power_dbm: number;
	client_powers?: number[];
}

// ---------------------------------------------------------------------------
// Configuración de umbrales
// ---------------------------------------------------------------------------
export interface ThresholdRead {
	key: string;
	value: number;
	description: string | null;
	updated_at: string;
}

// ---------------------------------------------------------------------------
// Puerto OLT
// ---------------------------------------------------------------------------
export interface OltPortRead {
	id: string;
	olt_pk_id: string | null;
	olt_id: string;
	port_id: string;
	hub_id: string;
	localidad: string;
	port_occupancy_percentage: number;
	connected_clients_count: number;
	current_sfp_tx_power_dbm: number;
	last_sync_at: string;
	sfp_alert: boolean;
}

export interface OltPortCreate {
	olt_id: string;
	port_id: string;
	hub_id: string;
	localidad: string;
	port_occupancy_percentage: number;
	connected_clients_count: number;
	current_sfp_tx_power_dbm: number;
}

export interface OltPortSyncRequest {
	olt_id: string;
	port_id: string;
	client_powers: number[];
}

// ---------------------------------------------------------------------------
// N1 — Manga primaria + OTDR
// ---------------------------------------------------------------------------
export type OtdrStatus = 'APROBADO' | 'BLOQUEADO' | 'PENDIENTE';

export interface N1InfrastructureRead {
	id: string;
	olt_port_id: string;
	n1_manga_id: string;
	odf_port_id: string;
	otdr_total_distance_m: number;
	otdr_total_loss_db: number;
	otdr_max_fusion_loss_db: number;
	photo_url: string;
	is_otdr_approved: boolean;
	window_1310_loss_db: number | null;
	window_1550_loss_db: number | null;
	audited_at: string;
	otdr_status: OtdrStatus;
}

export interface N1InfrastructureCreate {
	olt_port_id: string;
	n1_manga_id: string;
	odf_port_id: string;
	otdr_total_distance_m: number;
	otdr_total_loss_db: number;
	otdr_max_fusion_loss_db: number;
	photo_url: string;
	window_1310_loss_db?: number;
	window_1550_loss_db?: number;
}

// ---------------------------------------------------------------------------
// N2 — Caja NAP + OZmap
// ---------------------------------------------------------------------------
export type OzmapSyncStatus = 'CONCILIADO' | 'DISCREPANCIA' | 'PENDIENTE';

export interface GeoCoordinates {
	latitude: number;
	longitude: number;
}

export interface N2InfrastructureRead {
	id: string;
	parent_n1_id: string;
	n2_box_id: string;
	under_transformer_shield: boolean;
	photo_url: string;
	ozmap_sync_status: OzmapSyncStatus;
	geo_latitude: number;
	geo_longitude: number;
	total_ports: 8 | 16;
	created_at: string;
	transformer_alert: boolean;
}

export interface N2InfrastructureCreate {
	parent_n1_id: string;
	n2_box_id: string;
	under_transformer_shield: boolean;
	photo_url: string;
	ozmap_sync_status: OzmapSyncStatus;
	geo_coordinates: GeoCoordinates;
	total_ports: 8 | 16;
}

// ---------------------------------------------------------------------------
// Mediciones de potencia en calle
// ---------------------------------------------------------------------------
export type PowerStatus = 'NORMAL' | 'CRITICO' | 'SEVERO';

export interface N2PortMeasurementRead {
	id: string;
	n2_infrastructure_id: string;
	port_number: number;
	measured_power_dbm: number;
	photo_port_url: string;
	client_id: string | null;
	geo_latitude: number | null;
	geo_longitude: number | null;
	measured_at: string;
	power_status: PowerStatus;
}

export interface N2PortMeasurementCreate {
	n2_infrastructure_id: string;
	port_number: number;
	measured_power_dbm: number;
	photo_port_url: string;
	client_id?: string;
	geo_coordinates?: GeoCoordinates;
}

// ---------------------------------------------------------------------------
// Incidencias OTDR
// ---------------------------------------------------------------------------
export type OtdrIncidenceStatus = 'BLOQUEADO' | 'SANEADO';

export interface OtdrIncidenceRead {
	id: string;
	n1_infrastructure_id: string;
	detected_loss_db: number;
	status: OtdrIncidenceStatus;
	resolved_at: string | null;
	created_at: string;
}

// ---------------------------------------------------------------------------
// Reportes acumulados
// ---------------------------------------------------------------------------
export type SfpStatus = 'PENDIENTE' | 'REEMPLAZADO';

export interface SfpReplacementRead {
	id: string;
	olt_port_id: string;
	sfp_tx_power_dbm: number;
	calculated_clients_avg_dbm: number;
	status: SfpStatus;
	updated_at: string;
	olt_id: string | null;
	port_id: string | null;
	localidad: string | null;
}

export type VisitStatus = 'PROGRAMADO' | 'EN_PROGRESO' | 'RESUELTO';
export type VisitPriority = 'NORMAL' | 'URGENTE';
export type FailureType =
	| 'POTENCIA_CRITICA_N2'
	| 'POTENCIA_SEVERA_N2'
	| 'POSTE_CON_TRANSFORMADOR';

export interface PendingTechnicalVisitRead {
	id: string;
	n2_port_measurement_id: string | null;
	client_id: string;
	failure_type: FailureType;
	measured_power_dbm: number | null;
	status: VisitStatus;
	assigned_quad_id: string | null;
	priority: VisitPriority;
	created_at: string;
}

// ---------------------------------------------------------------------------
// Acta de entrega ODN
// ---------------------------------------------------------------------------
export type ActStatus = 'BORRADOR' | 'APROBADO' | 'EXCEPCION_ACEPTADA' | 'RECHAZADO';

export interface ChecklistItem {
	label: string;
	passed: boolean;
	notes: string | null;
}

export interface DeliveryActRead {
	id: string;
	n1_infrastructure_id: string;
	sucursal: string;
	squad_leader: string;
	active_subscribers: number;
	in_range_subscribers: number;
	critical_subscribers: number;
	status: ActStatus;
	executor_signature: string | null;
	supervisor_signature: string | null;
	executor_signed_at: string | null;
	supervisor_signed_at: string | null;
	created_at: string;
	approved_at: string | null;
	n1_manga_id: string | null;
	checklist: ChecklistItem[];
	n2_boxes: N2InfrastructureRead[];
}

export interface DeliveryActCreate {
	n1_infrastructure_id: string;
	sucursal: string;
	squad_leader: string;
	active_subscribers: number;
	in_range_subscribers: number;
	critical_subscribers: number;
}

export interface DeliveryActSign {
	role: 'EXECUTOR' | 'SUPERVISOR';
	signature_data: string;
	signer_name: string;
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
export interface AuditDashboardSummary {
	total_ports_audited: number;
	ports_with_sfp_alert: number;
	blocked_otdr_tramos: number;
	pending_technical_visits: number;
	transformer_alerts: number;
	acts_approved: number;
	acts_pending: number;
}

// ---------------------------------------------------------------------------
// Constantes de umbrales (usados en lógica de UI)
// ---------------------------------------------------------------------------
export const POWER_THRESHOLDS = {
	SFP_MIN_TX_DBM: 6.0,
	CLIENT_AVG_MIN_DBM: -26.5,
	CLIENT_CRITICAL_DBM: -25.4,
	CLIENT_SEVERE_DBM: -27.01,
	OTDR_MAX_FUSION_LOSS_DB: 0.1
} as const;

// ---------------------------------------------------------------------------
// Helpers de clasificación (espejo de servicios Python)
// ---------------------------------------------------------------------------
export function classifyPower(dbm: number): PowerStatus {
	if (dbm < POWER_THRESHOLDS.CLIENT_SEVERE_DBM) return 'SEVERO';
	if (dbm < POWER_THRESHOLDS.CLIENT_CRITICAL_DBM) return 'CRITICO';
	return 'NORMAL';
}

export function getPowerStatusColor(status: PowerStatus): string {
	switch (status) {
		case 'SEVERO': return '#dc2626';   // red-600
		case 'CRITICO': return '#ea580c'; // orange-600
		case 'NORMAL': return '#16a34a';  // green-600
	}
}

export function getOtdrStatusColor(status: OtdrStatus): string {
	switch (status) {
		case 'BLOQUEADO': return '#dc2626';
		case 'APROBADO': return '#16a34a';
		case 'PENDIENTE': return '#ca8a04';
	}
}
