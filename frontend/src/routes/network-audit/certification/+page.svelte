<script lang="ts">
	import { onMount } from 'svelte';
	import type { DeliveryActRead } from '$lib/types/network-audit';

	let acts = $state<DeliveryActRead[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let filterStatus = $state<string>('');

	async function loadActs() {
		loading = true;
		error = null;
		try {
			const q = filterStatus ? `?status_filter=${encodeURIComponent(filterStatus)}` : '';
			const res = await fetch(`/api/v1/reports/acts${q}`);
			if (!res.ok) throw new Error('Error al cargar actas');
			acts = await res.json();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	onMount(loadActs);

	const statusBadge: Record<string, string> = {
		BORRADOR:           'bg-yellow-100 text-yellow-800',
		APROBADO:           'bg-green-100 text-green-800',
		EXCEPCION_ACEPTADA: 'bg-blue-100 text-blue-800',
		RECHAZADO:          'bg-red-100 text-red-800'
	};

	function formatDate(iso: string) {
		return new Intl.DateTimeFormat('es-VE', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(iso));
	}
</script>

<svelte:head>
	<title>Actas de Entrega — Auditoría ODN</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-5xl mx-auto space-y-5">

		<div class="flex items-center justify-between">
			<div class="flex items-center gap-4">
				<a href="/network-audit" class="text-blue-600 hover:text-blue-800 text-sm">← Dashboard</a>
				<div>
					<h1 class="text-xl font-bold text-gray-900">Actas de Entrega Técnica</h1>
					<p class="text-sm text-gray-500">Documentos finales del proceso de auditoría ODN</p>
				</div>
			</div>
			<div class="flex gap-3">
				<select
					bind:value={filterStatus}
					onchange={loadActs}
					class="border border-gray-200 rounded-xl px-3 py-2 text-sm bg-white"
				>
					<option value="">Todos los estados</option>
					<option value="BORRADOR">Borrador</option>
					<option value="APROBADO">Aprobado</option>
					<option value="EXCEPCION_ACEPTADA">Excepción Aceptada</option>
					<option value="RECHAZADO">Rechazado</option>
				</select>
				<button
					onclick={loadActs}
					class="bg-white border border-gray-200 px-4 py-2 rounded-xl text-sm hover:bg-gray-50"
				>
					🔄
				</button>
			</div>
		</div>

		{#if error}
			<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
				{error}
			</div>
		{/if}

		{#if loading}
			<div class="space-y-3">
				{#each [1, 2, 3] as _}
					<div class="h-20 bg-white rounded-2xl border border-gray-200 animate-pulse"></div>
				{/each}
			</div>
		{:else if acts.length === 0}
			<div class="bg-white rounded-2xl border border-gray-200 p-12 text-center">
				<p class="text-4xl mb-4">📋</p>
				<p class="text-gray-500">No hay actas generadas aún.</p>
				<p class="text-sm text-gray-400 mt-2">
					Las actas se generan desde la sección de
					<a href="/network-audit/ingest" class="text-blue-600 hover:underline">Ingesta de Datos</a>
					una vez que el tramo N1 está aprobado.
				</p>
			</div>
		{:else}
			<div class="space-y-3">
				{#each acts as act}
					<a
						href="/network-audit/certification/{act.id}"
						class="block bg-white rounded-2xl border border-gray-200 p-5 hover:shadow-md transition-shadow"
					>
						<div class="flex items-start justify-between">
							<div class="space-y-1">
								<div class="flex items-center gap-3">
									<h3 class="font-bold text-gray-800">{act.sucursal}</h3>
									<span class="text-xs px-2.5 py-1 rounded-full font-semibold {statusBadge[act.status]}">
										{act.status}
									</span>
									{#if act.critical_subscribers > 0}
										<span class="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-semibold">
											{act.critical_subscribers} críticos
										</span>
									{/if}
								</div>
								<p class="text-sm text-gray-500">
									Manga N1: <strong class="text-gray-700">{act.n1_manga_id ?? '—'}</strong>
									· Líder: <strong class="text-gray-700">{act.squad_leader}</strong>
								</p>
								<div class="flex items-center gap-4 text-xs text-gray-400">
									<span>{act.active_subscribers} abonados activos</span>
									<span>{act.in_range_subscribers} en rango</span>
									<span>{act.n2_boxes.length} cajas N2</span>
									<span>{formatDate(act.created_at)}</span>
								</div>
							</div>
							<div class="flex items-center gap-2 ml-4">
								{#if act.executor_signature}
									<span class="text-green-500 text-lg" title="Firmado por Ejecutor">✍️</span>
								{/if}
								{#if act.supervisor_signature}
									<span class="text-blue-500 text-lg" title="Firmado por Supervisor">🔏</span>
								{/if}
								<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
								</svg>
							</div>
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</div>
</div>
