/**
 * Funciones auxiliares del lado del servidor (SvelteKit load functions / actions).
 * Todas las llamadas al backend FastAPI se centralizan aquí.
 */

import type {
	AuditDashboardSummary,
	DeliveryActRead,
	N1InfrastructureRead,
	N2InfrastructureRead,
	OltPortRead,
	OtdrIncidenceRead,
	PendingTechnicalVisitRead,
	SfpReplacementRead
} from '$lib/types/network-audit';

const API_BASE = process.env.API_BASE_URL ?? 'http://localhost:8000/api/v1';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${API_BASE}${path}`, {
		headers: { 'Content-Type': 'application/json', ...init?.headers },
		...init
	});
	if (!res.ok) {
		const body = await res.text();
		throw new Error(`API ${path} → ${res.status}: ${body}`);
	}
	return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
export async function getDashboardSummary(): Promise<AuditDashboardSummary> {
	return apiFetch<AuditDashboardSummary>('/reports/dashboard');
}

// ---------------------------------------------------------------------------
// OLT Ports
// ---------------------------------------------------------------------------
export async function listOltPorts(localidad?: string): Promise<OltPortRead[]> {
	const q = localidad ? `?localidad=${encodeURIComponent(localidad)}` : '';
	return apiFetch<OltPortRead[]>(`/olt-ports/${q}`);
}

export async function getOltPort(id: string): Promise<OltPortRead> {
	return apiFetch<OltPortRead>(`/olt-ports/${id}`);
}

// ---------------------------------------------------------------------------
// N1 Infrastructure
// ---------------------------------------------------------------------------
export async function listN1(params?: { olt_port_id?: string; approved_only?: boolean }): Promise<N1InfrastructureRead[]> {
	const q = new URLSearchParams();
	if (params?.olt_port_id) q.set('olt_port_id', params.olt_port_id);
	if (params?.approved_only) q.set('approved_only', 'true');
	const qs = q.toString() ? `?${q}` : '';
	return apiFetch<N1InfrastructureRead[]>(`/n1/${qs}`);
}

export async function getN1(id: string): Promise<N1InfrastructureRead> {
	return apiFetch<N1InfrastructureRead>(`/n1/${id}`);
}

export async function getOtdrIncidences(n1Id: string): Promise<OtdrIncidenceRead[]> {
	return apiFetch<OtdrIncidenceRead[]>(`/n1/${n1Id}/otdr-incidences`);
}

// ---------------------------------------------------------------------------
// N2 Infrastructure
// ---------------------------------------------------------------------------
export async function listN2(parentN1Id?: string): Promise<N2InfrastructureRead[]> {
	const q = parentN1Id ? `?parent_n1_id=${encodeURIComponent(parentN1Id)}` : '';
	return apiFetch<N2InfrastructureRead[]>(`/n2/${q}`);
}

// ---------------------------------------------------------------------------
// Reports
// ---------------------------------------------------------------------------
export async function listSfpReplacements(status?: string): Promise<SfpReplacementRead[]> {
	const q = status ? `?status_filter=${encodeURIComponent(status)}` : '';
	return apiFetch<SfpReplacementRead[]>(`/reports/sfp-replacements${q}`);
}

export async function listPendingVisits(params?: {
	status?: string;
	priority?: string;
}): Promise<PendingTechnicalVisitRead[]> {
	const q = new URLSearchParams();
	if (params?.status) q.set('status_filter', params.status);
	if (params?.priority) q.set('priority', params.priority);
	const qs = q.toString() ? `?${q}` : '';
	return apiFetch<PendingTechnicalVisitRead[]>(`/reports/pending-visits${qs}`);
}

// ---------------------------------------------------------------------------
// Delivery Acts
// ---------------------------------------------------------------------------
export async function listActs(status?: string): Promise<DeliveryActRead[]> {
	const q = status ? `?status_filter=${encodeURIComponent(status)}` : '';
	return apiFetch<DeliveryActRead[]>(`/reports/acts${q}`);
}

export async function getAct(id: string): Promise<DeliveryActRead> {
	return apiFetch<DeliveryActRead>(`/reports/acts/${id}`);
}
