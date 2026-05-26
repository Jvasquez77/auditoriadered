<script lang="ts">
	import { onMount } from 'svelte';
	import DashboardStats from '$lib/components/network-audit/DashboardStats.svelte';
	import type { AuditDashboardSummary, OtdrIncidenceRead, SfpReplacementRead, PendingTechnicalVisitRead } from '$lib/types/network-audit';

	// Svelte 5 runes
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
	let otdrBlocks = $state<OtdrIncidenceRead[]>([]);
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
			if (sfpRes.ok) sfpReport = await sfpRes.json();
			if (visitsRes.ok) urgentVisits = await visitsRes.json();
		} catch (e) {
			error = `Error de conexión con el backend: ${e instanceof Error ? e.message : String(e)}`;
		} finally {
			loading = false;
		}
	}

	onMount(fetchDashboard);

	const urgentCount = $derived(urgentVisits.filter(v => v.priority === 'URGENTE').length);
</script>

<svelte:head>
	<title>Dashboard — Auditoría ODN</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-7xl mx-auto space-y-6">

		<!-- Header -->
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-gray-900">Módulo de Auditoría de Red ODN</h1>
				<p class="text-gray-500 text-sm mt-1">Panel de control de auditorías de planta externa</p>
			</div>
			<div class="flex gap-3">
				<a
					href="/network-audit/ingest"
					class="bg-blue-600 text-white px-5 py-2.5 rounded-xl font-semibold text-sm hover:bg-blue-700 transition-colors"
				>
					+ Nueva Ingesta
				</a>
				<button
					onclick={fetchDashboard}
					class="bg-white border border-gray-200 text-gray-700 px-4 py-2.5 rounded-xl text-sm hover:bg-gray-50"
				>
					🔄 Actualizar
				</button>
			</div>
		</div>

		{#if error}
			<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700">
				<strong>Error:</strong> {error}
				<p class="text-sm mt-1 text-red-500">
					Asegúrate de que el backend FastAPI esté corriendo en <code>http://localhost:8000</code>
				</p>
			</div>
		{/if}

		<!-- KPIs -->
		<DashboardStats {summary} {loading} />

		<!-- Alertas urgentes -->
		{#if summary.blocked_otdr_tramos > 0 || summary.transformer_alerts > 0}
			<div class="bg-red-50 border-l-4 border-red-500 rounded-xl p-5">
				<h2 class="text-red-800 font-bold text-base mb-3">🚨 Alertas Críticas Activas</h2>
				<div class="space-y-2">
					{#if summary.blocked_otdr_tramos > 0}
						<div class="flex items-center gap-2 text-sm text-red-700">
							<span class="w-2 h-2 rounded-full bg-red-500"></span>
							<strong>{summary.blocked_otdr_tramos}</strong> tramo(s) OTDR bloqueado(s) — órdenes de calle suspendidas
						</div>
					{/if}
					{#if summary.transformer_alerts > 0}
						<div class="flex items-center gap-2 text-sm text-red-700">
							<span class="w-2 h-2 rounded-full bg-red-500"></span>
							<strong>{summary.transformer_alerts}</strong> caja(s) bajo transformador eléctrico — reubicación requerida
						</div>
					{/if}
				</div>
			</div>
		{/if}

		<!-- Grilla de reportes -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">

			<!-- SFPs por Cambiar -->
			<div class="bg-white rounded-2xl border border-gray-200 p-5">
				<div class="flex items-center justify-between mb-4">
					<h2 class="font-bold text-gray-800">🔴 SFPs por Cambiar</h2>
					<span class="text-sm text-gray-500">{sfpReport.length} pendientes</span>
				</div>
				{#if loading}
					<div class="space-y-3">
						{#each [1, 2, 3] as _}
							<div class="h-12 bg-gray-100 rounded-lg animate-pulse"></div>
						{/each}
					</div>
				{:else if sfpReport.length === 0}
					<p class="text-center text-gray-400 py-8">✅ Sin SFPs degradados</p>
				{:else}
					<div class="space-y-2 max-h-64 overflow-y-auto">
						{#each sfpReport as item}
							<div class="flex items-center justify-between text-sm bg-orange-50 rounded-lg p-3">
								<div>
									<p class="font-medium text-gray-800">{item.olt_id} / {item.port_id}</p>
									<p class="text-xs text-gray-500">{item.localidad}</p>
								</div>
								<div class="text-right">
									<p class="font-bold text-orange-700">{item.sfp_tx_power_dbm} dBm TX</p>
									<p class="text-xs text-gray-500">Avg ONT: {item.calculated_clients_avg_dbm} dBm</p>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Visitas Técnicas Urgentes -->
			<div class="bg-white rounded-2xl border border-gray-200 p-5">
				<div class="flex items-center justify-between mb-4">
					<h2 class="font-bold text-gray-800">🛠️ Visitas Técnicas Urgentes</h2>
					<span class="text-sm text-gray-500">{urgentVisits.length} urgentes</span>
				</div>
				{#if loading}
					<div class="space-y-3">
						{#each [1, 2, 3] as _}
							<div class="h-12 bg-gray-100 rounded-lg animate-pulse"></div>
						{/each}
					</div>
				{:else if urgentVisits.length === 0}
					<p class="text-center text-gray-400 py-8">✅ Sin visitas urgentes pendientes</p>
				{:else}
					<div class="space-y-2 max-h-64 overflow-y-auto">
						{#each urgentVisits as visit}
							<div class="flex items-center justify-between text-sm bg-red-50 rounded-lg p-3">
								<div>
									<p class="font-medium text-gray-800">{visit.client_id}</p>
									<p class="text-xs text-red-600 font-semibold">{visit.failure_type}</p>
								</div>
								<div class="text-right">
									{#if visit.measured_power_dbm !== null}
										<p class="font-bold text-red-700">{visit.measured_power_dbm} dBm</p>
									{/if}
									<span class="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded-full font-bold">
										{visit.priority}
									</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Accesos rápidos -->
		<div class="grid grid-cols-3 gap-4">
			<a
				href="/network-audit/ingest"
				class="bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-md transition-shadow text-center group"
			>
				<div class="text-4xl mb-3">📥</div>
				<p class="font-bold text-gray-800 group-hover:text-blue-600">Ingesta de Datos</p>
				<p class="text-xs text-gray-500 mt-1">OLT · SFP · OTDR · OZmap</p>
			</a>
			<a
				href="/network-audit/field"
				class="bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-md transition-shadow text-center group"
			>
				<div class="text-4xl mb-3">📶</div>
				<p class="font-bold text-gray-800 group-hover:text-blue-600">Mediciones en Calle</p>
				<p class="text-xs text-gray-500 mt-1">Interfaz móvil de cuadrillas</p>
			</a>
			<a
				href="/network-audit/certification"
				class="bg-white border border-gray-200 rounded-2xl p-6 hover:shadow-md transition-shadow text-center group"
			>
				<div class="text-4xl mb-3">📋</div>
				<p class="font-bold text-gray-800 group-hover:text-blue-600">Actas de Entrega</p>
				<p class="text-xs text-gray-500 mt-1">Generación y firma digital</p>
			</a>
		</div>
	</div>
</div>
