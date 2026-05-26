<script lang="ts">
	import { onMount } from 'svelte';
	import DashboardStats from '$lib/components/network-audit/DashboardStats.svelte';
	import type { AuditDashboardSummary, OtdrIncidenceRead, SfpReplacementRead, PendingTechnicalVisitRead } from '$lib/types/network-audit';

	let summary = $state<AuditDashboardSummary>({
		total_ports_audited: 0,
		ports_with_sfp_alert: 0,
		blocked_otdr_tramos: 0,
		pending_technical_visits: 0,
		transformer_alerts: 0,
		acts_approved: 0,
		acts_pending: 0
	});

	let sfpReport = $state<SfpReplacementRead[]>([]);
	let urgentVisits = $state<PendingTechnicalVisitRead[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	async function fetchDashboard() {
		loading = true;
		error = null;
		try {
			const [summaryRes, sfpRes, visitsRes] = await Promise.all([
				fetch('/api/v1/reports/dashboard'),
				fetch('/api/v1/reports/sfp-replacements?status_filter=PENDIENTE'),
				fetch('/api/v1/reports/pending-visits?priority=URGENTE&status_filter=PROGRAMADO')
			]);
			if (summaryRes.ok) summary = await summaryRes.json();
			if (sfpRes.ok)     sfpReport = await sfpRes.json();
			if (visitsRes.ok)  urgentVisits = await visitsRes.json();
		} catch (e) {
			error = `Error de conexión: ${e instanceof Error ? e.message : String(e)}`;
		} finally {
			loading = false;
		}
	}

	onMount(fetchDashboard);
</script>

<svelte:head>
	<title>Dashboard — Auditoría ODN</title>
</svelte:head>

<div class="space-y-6 max-w-7xl mx-auto">

	<!-- Page header -->
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-xl font-bold text-slate-900">Panel de Control</h2>
			<p class="text-sm text-slate-500 mt-0.5">Auditorías de planta externa ODN</p>
		</div>
		<div class="flex items-center gap-2">
			<a
				href="/network-audit/ingest"
				class="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
				</svg>
				Nueva Ingesta
			</a>
			<button
				onclick={fetchDashboard}
				class="inline-flex items-center gap-2 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 px-3 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm"
				disabled={loading}
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" class:animate-spin={loading} fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
				Actualizar
			</button>
		</div>
	</div>

	<!-- Error state -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
			<svg class="w-5 h-5 text-red-500 shrink-0 mt-0.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			<div>
				<p class="text-sm font-semibold text-red-800">{error}</p>
				<p class="text-xs text-red-500 mt-0.5">Verifica que el backend FastAPI esté activo en <code class="font-mono">localhost:8000</code></p>
			</div>
		</div>
	{/if}

	<!-- KPI cards -->
	<DashboardStats {summary} {loading} />

	<!-- Critical alerts banner -->
	{#if !loading && (summary.blocked_otdr_tramos > 0 || summary.transformer_alerts > 0)}
		<div class="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
			<span class="w-2 h-2 rounded-full bg-red-500 mt-1.5 shrink-0 animate-pulse"></span>
			<div class="space-y-1.5">
				<p class="text-sm font-bold text-red-800">Alertas críticas activas</p>
				{#if summary.blocked_otdr_tramos > 0}
					<p class="text-sm text-red-700">
						<strong>{summary.blocked_otdr_tramos}</strong> tramo(s) OTDR bloqueado(s) — órdenes de calle suspendidas
					</p>
				{/if}
				{#if summary.transformer_alerts > 0}
					<p class="text-sm text-red-700">
						<strong>{summary.transformer_alerts}</strong> caja(s) bajo transformador eléctrico — reubicación requerida
					</p>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Report cards (2 cols) -->
	<div class="grid grid-cols-1 md:grid-cols-2 gap-5">

		<!-- SFPs por Cambiar -->
		<div class="card p-5">
			<div class="flex items-center justify-between mb-4">
				<div class="flex items-center gap-2">
					<div class="w-7 h-7 rounded-lg bg-orange-100 flex items-center justify-center">
						<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-orange-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
						</svg>
					</div>
					<h3 class="text-sm font-semibold text-slate-800">SFPs por Cambiar</h3>
				</div>
				<span class="badge {sfpReport.length > 0 ? 'badge-pendiente' : 'badge-aprobado'}">
					{sfpReport.length} pendientes
				</span>
			</div>

			{#if loading}
				<div class="space-y-2.5">
					{#each [1, 2, 3] as _}
						<div class="skeleton h-14 w-full"></div>
					{/each}
				</div>
			{:else if sfpReport.length === 0}
				<div class="flex flex-col items-center justify-center py-10 text-center">
					<div class="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center mb-3">
						<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
						</svg>
					</div>
					<p class="text-sm text-slate-500 font-medium">Sin SFPs degradados</p>
				</div>
			{:else}
				<div class="space-y-2 max-h-60 overflow-y-auto">
					{#each sfpReport as item}
						<div class="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-100">
							<div>
								<p class="text-sm font-semibold text-slate-800">{item.olt_id} / {item.port_id}</p>
								<p class="text-xs text-slate-500">{item.localidad}</p>
							</div>
							<div class="text-right">
								<p class="text-sm font-bold text-orange-700">{item.sfp_tx_power_dbm} dBm</p>
								<p class="text-xs text-slate-400">Avg ONT: {item.calculated_clients_avg_dbm} dBm</p>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Visitas Técnicas Urgentes -->
		<div class="card p-5">
			<div class="flex items-center justify-between mb-4">
				<div class="flex items-center gap-2">
					<div class="w-7 h-7 rounded-lg bg-red-100 flex items-center justify-center">
						<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
						</svg>
					</div>
					<h3 class="text-sm font-semibold text-slate-800">Visitas Técnicas Urgentes</h3>
				</div>
				<span class="badge {urgentVisits.length > 0 ? 'badge-bloqueado' : 'badge-aprobado'}">
					{urgentVisits.length} urgentes
				</span>
			</div>

			{#if loading}
				<div class="space-y-2.5">
					{#each [1, 2, 3] as _}
						<div class="skeleton h-14 w-full"></div>
					{/each}
				</div>
			{:else if urgentVisits.length === 0}
				<div class="flex flex-col items-center justify-center py-10 text-center">
					<div class="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center mb-3">
						<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
						</svg>
					</div>
					<p class="text-sm text-slate-500 font-medium">Sin visitas urgentes pendientes</p>
				</div>
			{:else}
				<div class="space-y-2 max-h-60 overflow-y-auto">
					{#each urgentVisits as visit}
						<div class="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-100">
							<div>
								<p class="text-sm font-semibold text-slate-800">{visit.client_id}</p>
								<p class="text-xs text-red-600 font-medium">{visit.failure_type}</p>
							</div>
							<div class="flex items-center gap-2">
								{#if visit.measured_power_dbm !== null}
									<p class="text-sm font-bold text-red-700">{visit.measured_power_dbm} dBm</p>
								{/if}
								<span class="badge badge-bloqueado">{visit.priority}</span>
							</div>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<!-- Quick links -->
	<div class="grid grid-cols-3 gap-4">
		{#each [
			{ href: '/network-audit/ingest', label: 'Ingesta de Datos', sub: 'OLT · SFP · OTDR · OZmap', iconBg: 'bg-violet-100', iconColor: 'text-violet-600', icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />' },
			{ href: '/network-audit/field',  label: 'Mediciones en Calle', sub: 'Interfaz móvil de cuadrillas', iconBg: 'bg-blue-100', iconColor: 'text-blue-600', icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />' },
			{ href: '/network-audit/certification', label: 'Actas de Entrega', sub: 'Generación y firma digital', iconBg: 'bg-emerald-100', iconColor: 'text-emerald-600', icon: '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />' }
		] as link}
			<a
				href={link.href}
				class="card-hover p-5 flex items-center gap-4 group cursor-pointer"
			>
				<div class="w-10 h-10 rounded-xl {link.iconBg} {link.iconColor} flex items-center justify-center shrink-0">
					<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						{@html link.icon}
					</svg>
				</div>
				<div class="min-w-0">
					<p class="text-sm font-semibold text-slate-800 group-hover:text-violet-600 transition-colors">{link.label}</p>
					<p class="text-xs text-slate-400 mt-0.5">{link.sub}</p>
				</div>
				<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-slate-300 ml-auto shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
				</svg>
			</a>
		{/each}
	</div>

</div>
