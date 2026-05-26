<script lang="ts">
	import FieldPowerForm from '$lib/components/network-audit/FieldPowerForm.svelte';
	import type { N2PortMeasurementCreate, N2InfrastructureRead } from '$lib/types/network-audit';

	// Svelte 5 runes
	let step = $state<'select' | 'measure' | 'done'>('select');
	let selectedBox = $state<N2InfrastructureRead | null>(null);

	let n2BoxIdInput = $state('');
	let n2InfraId = $state('');
	let searching = $state(false);
	let searchError = $state<string | null>(null);
	let submitSuccess = $state<{ total: number; critical: number } | null>(null);
	let submitError = $state<string | null>(null);

	async function searchN2Box() {
		if (!n2BoxIdInput.trim()) return;
		searching = true;
		searchError = null;
		try {
			const res = await fetch(`/api/v1/n2/?parent_n1_id=${encodeURIComponent(n2BoxIdInput)}`);
			if (!res.ok) {
				// Intentar buscar por box_id directo (el param puede ser el box_id)
				const res2 = await fetch(`/api/v1/n2/`);
				if (!res2.ok) throw new Error('No se pudo conectar al servidor');
				const all: N2InfrastructureRead[] = await res2.json();
				const found = all.find(b => b.n2_box_id === n2BoxIdInput);
				if (!found) throw new Error(`No se encontró la caja N2 con ID: ${n2BoxIdInput}`);
				selectedBox = found;
				n2InfraId = found.id;
			} else {
				const boxes: N2InfrastructureRead[] = await res.json();
				if (boxes.length === 0) throw new Error(`No se encontraron cajas N2 para el ID: ${n2BoxIdInput}`);
				selectedBox = boxes[0];
				n2InfraId = boxes[0].id;
			}
			step = 'measure';
		} catch (e) {
			searchError = e instanceof Error ? e.message : String(e);
		} finally {
			searching = false;
		}
	}

	async function handleMeasurements(measurements: N2PortMeasurementCreate[]) {
		submitError = null;
		submitSuccess = null;
		let criticalCount = 0;

		for (const m of measurements) {
			const res = await fetch('/api/v1/measurements/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(m)
			});
			if (res.ok) {
				const data = await res.json();
				if (data.power_status === 'CRITICO' || data.power_status === 'SEVERO') {
					criticalCount++;
				}
			} else {
				const err = await res.json();
				submitError = err.detail ?? 'Error al enviar mediciones';
				return;
			}
		}

		submitSuccess = { total: measurements.length, critical: criticalCount };
		step = 'done';
	}

	function startOver() {
		step = 'select';
		selectedBox = null;
		n2BoxIdInput = '';
		n2InfraId = '';
		submitSuccess = null;
		submitError = null;
		searchError = null;
	}
</script>

<svelte:head>
	<title>Mediciones en Calle — Auditoría ODN</title>
	<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
</svelte:head>

<!-- Diseño optimizado para móvil -->
<div class="min-h-screen bg-gray-100 p-4">
	<div class="max-w-2xl mx-auto space-y-4">

		<!-- Header móvil -->
		<div class="bg-white rounded-2xl p-4 flex items-center gap-3">
			<a href="/network-audit" class="text-blue-600">
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
				</svg>
			</a>
			<div>
				<h1 class="font-bold text-gray-900">Mediciones en Calle</h1>
				<p class="text-xs text-gray-500">Interfaz de campo — cuadrillas planta externa</p>
			</div>
			<!-- Indicador de paso -->
			<div class="ml-auto flex gap-1">
				{#each ['select', 'measure', 'done'] as s, i}
					<div
						class="w-2 h-2 rounded-full {step === s ? 'bg-blue-600' : 'bg-gray-300'}"
					></div>
				{/each}
			</div>
		</div>

		<!-- PASO 1: Seleccionar caja N2 -->
		{#if step === 'select'}
			<div class="bg-white rounded-2xl p-6 space-y-5">
				<div class="text-center">
					<div class="text-5xl mb-3">📦</div>
					<h2 class="text-lg font-bold text-gray-800">Identificar Caja NAP</h2>
					<p class="text-sm text-gray-500">Ingresa el ID de la caja N2 a medir</p>
				</div>

				{#if searchError}
					<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
						{searchError}
					</div>
				{/if}

				<div class="space-y-3">
					<input
						bind:value={n2BoxIdInput}
						placeholder="ID Caja N2 — ej: NAP-TIG-001"
						class="w-full border-2 border-gray-200 rounded-xl px-4 py-4 text-base focus:outline-none focus:border-blue-500"
						onkeydown={(e) => e.key === 'Enter' && searchN2Box()}
					/>
					<button
						onclick={searchN2Box}
						disabled={searching || !n2BoxIdInput.trim()}
						class="w-full bg-blue-600 text-white font-bold py-4 rounded-xl text-base
							hover:bg-blue-700 disabled:opacity-50 active:scale-95 transition-all"
					>
						{searching ? 'Buscando...' : 'Localizar Caja'}
					</button>
				</div>

				<div class="bg-blue-50 rounded-xl p-4 text-xs text-blue-700">
					<strong>¿Sin ID?</strong> Solicite el ID de la caja NAP al supervisor o escanee el
					código QR en la etiqueta de la caja.
				</div>
			</div>
		{/if}

		<!-- PASO 2: Mediciones -->
		{#if step === 'measure' && selectedBox}
			{#if selectedBox.transformer_alert}
				<div class="bg-red-50 border-2 border-red-400 rounded-2xl p-4">
					<div class="flex items-start gap-3">
						<span class="text-3xl">⚡</span>
						<div>
							<p class="font-bold text-red-800 text-base">ALERTA DE SEGURIDAD INDUSTRIAL</p>
							<p class="text-sm text-red-700 mt-1">
								Esta caja NAP está registrada bajo un transformador eléctrico.
								<strong>Proceda con máxima precaución.</strong> Se generará una orden de
								reubicación automáticamente.
							</p>
						</div>
					</div>
				</div>
			{/if}

			{#if submitError}
				<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-700">
					{submitError}
				</div>
			{/if}

			<FieldPowerForm
				n2BoxId={selectedBox.n2_box_id}
				n2InfrastructureId={selectedBox.id}
				totalPorts={selectedBox.total_ports}
				onSubmit={handleMeasurements}
			/>
		{/if}

		<!-- PASO 3: Completado -->
		{#if step === 'done'}
			<div class="bg-white rounded-2xl p-8 text-center space-y-5">
				<div class="text-6xl">
					{submitSuccess && submitSuccess.critical > 0 ? '⚠️' : '✅'}
				</div>
				<h2 class="text-xl font-bold text-gray-800">
					{submitSuccess && submitSuccess.critical > 0 ? 'Mediciones con Alertas' : 'Mediciones Guardadas'}
				</h2>
				{#if submitSuccess}
					<div class="space-y-2">
						<p class="text-gray-600">
							<strong>{submitSuccess.total}</strong> mediciones registradas correctamente.
						</p>
						{#if submitSuccess.critical > 0}
							<div class="bg-orange-50 border border-orange-200 rounded-xl p-4 text-sm text-orange-800">
								<strong>{submitSuccess.critical}</strong> puertos fuera de rango crítico.
								Se generaron visitas técnicas pendientes automáticamente.
							</div>
						{:else}
							<div class="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-800">
								Todos los puertos en rango aceptable.
							</div>
						{/if}
					</div>
				{/if}
				<div class="grid grid-cols-2 gap-3 pt-2">
					<button
						onclick={startOver}
						class="bg-blue-600 text-white font-bold py-4 rounded-xl hover:bg-blue-700 active:scale-95"
					>
						Nueva Caja
					</button>
					<a
						href="/network-audit"
						class="bg-gray-100 text-gray-800 font-bold py-4 rounded-xl hover:bg-gray-200 flex items-center justify-center"
					>
						Dashboard
					</a>
				</div>
			</div>
		{/if}
	</div>
</div>
