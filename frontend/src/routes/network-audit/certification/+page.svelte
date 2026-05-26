<script lang="ts">
	import { onMount } from 'svelte';
	import type { DeliveryActRead } from '$lib/types/network-audit';

	let acts = $state<DeliveryActRead[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let filterStatus = $state<string>('');
	let openMenuId = $state<string | null>(null);
	let selectedIds = $state<Set<string>>(new Set());

	async function loadActs() {
		loading = true;
		error = null;
		openMenuId = null;
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

	type BadgeKey = 'BORRADOR' | 'APROBADO' | 'EXCEPCION_ACEPTADA' | 'RECHAZADO';
	const statusBadge: Record<BadgeKey, string> = {
		BORRADOR:           'badge-borrador',
		APROBADO:           'badge-aprobado',
		EXCEPCION_ACEPTADA: 'badge-excepcion',
		RECHAZADO:          'badge-rechazado'
	};

	const statusLabel: Record<BadgeKey, string> = {
		BORRADOR:           'Borrador',
		APROBADO:           'Aprobado',
		EXCEPCION_ACEPTADA: 'Excepción',
		RECHAZADO:          'Rechazado'
	};

	function formatDate(iso: string) {
		return new Intl.DateTimeFormat('es-VE', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(iso));
	}

	function toggleSelect(id: string) {
		const s = new Set(selectedIds);
		if (s.has(id)) s.delete(id); else s.add(id);
		selectedIds = s;
	}

	const allSelected = $derived(acts.length > 0 && selectedIds.size === acts.length);

	function toggleAll() {
		if (allSelected) {
			selectedIds = new Set();
		} else {
			selectedIds = new Set(acts.map(a => a.id));
		}
	}
</script>

<svelte:head>
	<title>Actas de Entrega — Auditoría ODN</title>
</svelte:head>

<!-- Click-away to close ⋮ menu -->
<svelte:window onclick={() => { openMenuId = null; }} />

<div class="space-y-5 max-w-6xl mx-auto">

	<!-- Page header -->
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-xl font-bold text-slate-900">Actas de Entrega Técnica</h2>
			<p class="text-sm text-slate-500 mt-0.5">Documentos finales del proceso de auditoría ODN</p>
		</div>
		<div class="flex items-center gap-2">
			<!-- Status filter -->
			<select
				bind:value={filterStatus}
				onchange={loadActs}
				class="bg-white border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-violet-500 shadow-sm"
			>
				<option value="">Todos los estados</option>
				<option value="BORRADOR">Borrador</option>
				<option value="APROBADO">Aprobado</option>
				<option value="EXCEPCION_ACEPTADA">Excepción Aceptada</option>
				<option value="RECHAZADO">Rechazado</option>
			</select>

			<button
				onclick={loadActs}
				class="inline-flex items-center gap-1.5 bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 px-3 py-2 rounded-lg text-sm font-medium transition-colors shadow-sm"
				disabled={loading}
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" class:animate-spin={loading} fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
				</svg>
				Actualizar
			</button>
		</div>
	</div>

	<!-- Error -->
	{#if error}
		<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700 flex items-center gap-2">
			<svg class="w-4 h-4 shrink-0" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			{error}
		</div>
	{/if}

	<!-- Table card -->
	<div class="card overflow-hidden">

		<!-- Bulk action bar (when items are selected) -->
		{#if selectedIds.size > 0}
			<div class="flex items-center gap-3 px-5 py-3 bg-violet-50 border-b border-violet-100">
				<span class="text-sm font-semibold text-violet-700">{selectedIds.size} seleccionado(s)</span>
				<button class="text-sm text-slate-600 hover:text-red-600 transition-colors">Exportar</button>
				<button onclick={() => { selectedIds = new Set(); }} class="ml-auto text-sm text-slate-500 hover:text-slate-700">Limpiar selección</button>
			</div>
		{/if}

		<!-- Table -->
		<div class="overflow-x-auto">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b border-slate-100 bg-slate-50">
						<th class="w-10 px-4 py-3">
							<input
								type="checkbox"
								checked={allSelected}
								onchange={toggleAll}
								class="rounded border-slate-300 text-violet-600 focus:ring-violet-500"
							/>
						</th>
						<th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Sucursal / Manga</th>
						<th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Líder</th>
						<th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Abonados</th>
						<th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Firmas</th>
						<th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Estado</th>
						<th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Creado</th>
						<th class="w-10 px-4 py-3"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					{#if loading}
						{#each [1, 2, 3, 4, 5] as _}
							<tr>
								<td class="px-4 py-4"><div class="skeleton h-4 w-4 rounded"></div></td>
								<td class="px-4 py-4">
									<div class="skeleton h-4 w-32 mb-1.5"></div>
									<div class="skeleton h-3 w-20"></div>
								</td>
								<td class="px-4 py-4"><div class="skeleton h-4 w-24"></div></td>
								<td class="px-4 py-4"><div class="skeleton h-4 w-16"></div></td>
								<td class="px-4 py-4"><div class="skeleton h-5 w-10 rounded-full"></div></td>
								<td class="px-4 py-4"><div class="skeleton h-5 w-20 rounded-full"></div></td>
								<td class="px-4 py-4"><div class="skeleton h-4 w-20"></div></td>
								<td class="px-4 py-4"><div class="skeleton h-4 w-4 rounded"></div></td>
							</tr>
						{/each}
					{:else if acts.length === 0}
						<tr>
							<td colspan="8" class="px-4 py-16 text-center">
								<div class="flex flex-col items-center gap-3">
									<div class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center">
										<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
											<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
										</svg>
									</div>
									<p class="text-sm font-medium text-slate-500">No hay actas generadas</p>
									<p class="text-xs text-slate-400">
										Las actas se crean desde
										<a href="/network-audit/ingest" class="text-violet-600 hover:underline">Ingesta de Datos</a>
										cuando el tramo N1 está aprobado
									</p>
								</div>
							</td>
						</tr>
					{:else}
						{#each acts as act}
							<tr class="hover:bg-slate-50 transition-colors" class:bg-violet-50={selectedIds.has(act.id)}>
								<!-- Checkbox -->
								<td class="px-4 py-4">
									<input
										type="checkbox"
										checked={selectedIds.has(act.id)}
										onchange={() => toggleSelect(act.id)}
										onclick={(e) => e.stopPropagation()}
										class="rounded border-slate-300 text-violet-600 focus:ring-violet-500"
									/>
								</td>

								<!-- Sucursal / Manga -->
								<td class="px-4 py-4">
									<a href="/network-audit/certification/{act.id}" class="block group">
										<p class="font-semibold text-slate-900 group-hover:text-violet-600 transition-colors">{act.sucursal}</p>
										<p class="text-xs text-slate-400 mt-0.5">Manga: {act.n1_manga_id ?? '—'}</p>
									</a>
								</td>

								<!-- Líder -->
								<td class="px-4 py-4">
									<p class="text-slate-700">{act.squad_leader}</p>
								</td>

								<!-- Abonados (composite) -->
								<td class="px-4 py-4">
									<div class="flex flex-col gap-0.5">
										<span class="text-slate-700">{act.active_subscribers} activos</span>
										<span class="text-xs text-slate-400">{act.in_range_subscribers} en rango</span>
										{#if act.critical_subscribers > 0}
											<span class="badge badge-bloqueado mt-0.5 w-fit">{act.critical_subscribers} críticos</span>
										{/if}
									</div>
								</td>

								<!-- Firmas -->
								<td class="px-4 py-4">
									<div class="flex items-center gap-1.5">
										<span
											class="w-6 h-6 rounded-full flex items-center justify-center text-xs"
											class:bg-emerald-100={act.executor_signature}
											class:text-emerald-700={act.executor_signature}
											class:bg-slate-100={!act.executor_signature}
											class:text-slate-400={!act.executor_signature}
											title="Ejecutor"
										>E</span>
										<span
											class="w-6 h-6 rounded-full flex items-center justify-center text-xs"
											class:bg-violet-100={act.supervisor_signature}
											class:text-violet-700={act.supervisor_signature}
											class:bg-slate-100={!act.supervisor_signature}
											class:text-slate-400={!act.supervisor_signature}
											title="Supervisor"
										>S</span>
									</div>
								</td>

								<!-- Status badge pill -->
								<td class="px-4 py-4">
									<span class="badge {statusBadge[act.status as BadgeKey] ?? 'badge-borrador'}">
										{statusLabel[act.status as BadgeKey] ?? act.status}
									</span>
								</td>

								<!-- Date -->
								<td class="px-4 py-4 text-xs text-slate-400 whitespace-nowrap">
									{formatDate(act.created_at)}
								</td>

								<!-- ⋮ Action menu -->
								<td class="px-4 py-4 relative">
									<button
										onclick={(e) => { e.stopPropagation(); openMenuId = openMenuId === act.id ? null : act.id; }}
										class="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
									>
										<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
											<circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/>
										</svg>
									</button>

									{#if openMenuId === act.id}
										<div
											class="absolute right-10 top-2 z-50 bg-white border border-slate-200 rounded-xl shadow-lg py-1 min-w-[160px]"
											onclick={(e) => e.stopPropagation()}
										>
											<a
												href="/network-audit/certification/{act.id}"
												class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
											>
												<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
												</svg>
												Ver detalle
											</a>
											<a
												href="/network-audit/certification/{act.id}"
												class="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50 transition-colors"
											>
												<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
												</svg>
												Firmar acta
											</a>
											<div class="border-t border-slate-100 my-1"></div>
											<button
												class="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-400 cursor-not-allowed"
												disabled
											>
												<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
													<path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
												</svg>
												Exportar PDF
											</button>
										</div>
									{/if}
								</td>
							</tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>

		<!-- Table footer -->
		{#if !loading && acts.length > 0}
			<div class="px-5 py-3 border-t border-slate-100 flex items-center justify-between bg-slate-50">
				<p class="text-xs text-slate-500">{acts.length} acta(s) encontrada(s)</p>
				<p class="text-xs text-slate-400">{selectedIds.size > 0 ? `${selectedIds.size} seleccionada(s)` : ''}</p>
			</div>
		{/if}
	</div>
</div>
