<script lang="ts">
	import OtdrDropzone from '$lib/components/network-audit/OtdrDropzone.svelte';
	import type { OtdrFormData } from '$lib/components/network-audit/OtdrDropzone.svelte';
	import type { OltPortCreate, OltPortSyncRequest } from '$lib/types/network-audit';

	// Svelte 5 runes
	let activeTab = $state<'olt' | 'otdr' | 'n2' | 'ozmap'>('olt');
	let successMsg = $state<string | null>(null);
	let errorMsg = $state<string | null>(null);

	// OLT Form state
	let oltForm = $state<OltPortCreate>({
		olt_id: '',
		port_id: '',
		hub_id: '',
		localidad: '',
		port_occupancy_percentage: 0,
		connected_clients_count: 0,
		current_sfp_tx_power_dbm: 0
	});
	let oltClientPowers = $state('');
	let oltSubmitting = $state(false);

	async function submitOltPort(e: SubmitEvent) {
		e.preventDefault();
		oltSubmitting = true;
		errorMsg = null;
		successMsg = null;
		try {
			// 1. Crear/upsert el puerto
			const res = await fetch('/api/v1/olt-ports/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(oltForm)
			});
			if (!res.ok) throw new Error(await res.text());
			const port = await res.json();

			// 2. Si hay potencias de clientes, sincronizar evaluación SFP
			if (oltClientPowers.trim()) {
				const powers = oltClientPowers
					.split(',')
					.map((p) => parseFloat(p.trim()))
					.filter((p) => !isNaN(p));

				if (powers.length > 0) {
					const syncReq: OltPortSyncRequest = {
						olt_id: oltForm.olt_id,
						port_id: oltForm.port_id,
						client_powers: powers
					};
					const syncRes = await fetch(`/api/v1/olt-ports/${port.id}/sync-sfp`, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify(syncReq)
					});
					const syncData = await syncRes.json();
					if (syncData.sfp_alert) {
						successMsg = `Puerto registrado. ⚠️ Alerta SFP activada — promedio ONTs fuera de rango${syncData.replacement_created ? '. Agregado al reporte de SFPs.' : ''}.`;
					} else {
						successMsg = `Puerto OLT registrado correctamente. SFP en rango óptimo.`;
					}
					return;
				}
			}
			successMsg = `Puerto OLT ${port.olt_id}/${port.port_id} registrado correctamente.`;
		} catch (e) {
			errorMsg = `Error: ${e instanceof Error ? e.message : String(e)}`;
		} finally {
			oltSubmitting = false;
		}
	}

	async function submitOtdr(data: OtdrFormData) {
		errorMsg = null;
		successMsg = null;
		try {
			// En producción, subiría la foto a Object Storage primero
			// Aquí simulamos la URL
			const photoUrl = data.photo_file
				? `${window.location.origin}/media/n1_${data.n1_manga_id}_${Date.now()}.jpg`
				: '/placeholder.jpg';

			const payload = {
				olt_port_id: data.olt_port_id,
				n1_manga_id: data.n1_manga_id,
				odf_port_id: data.odf_port_id,
				otdr_total_distance_m: data.otdr_total_distance_m,
				otdr_total_loss_db: data.otdr_total_loss_db,
				otdr_max_fusion_loss_db: data.otdr_max_fusion_loss_db,
				photo_url: photoUrl,
				window_1310_loss_db: data.window_1310_loss_db,
				window_1550_loss_db: data.window_1550_loss_db
			};

			const res = await fetch('/api/v1/n1/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});

			const n1 = await res.json();
			if (!res.ok) throw new Error(n1.detail ?? JSON.stringify(n1));

			if (n1.otdr_status === 'BLOQUEADO') {
				errorMsg =
					'⛔ TRAMO BLOQUEADO: La pérdida de fusión supera 0.1 dB. ' +
					'Se creó la incidencia. No se podrán crear órdenes de trabajo hasta sanear el tramo.';
			} else {
				successMsg = `✅ OTDR registrado y aprobado para el tramo ${n1.n1_manga_id}.`;
			}
		} catch (e) {
			errorMsg = `Error al registrar OTDR: ${e instanceof Error ? e.message : String(e)}`;
		}
	}

	const tabs = [
		{ id: 'olt', label: 'OLT + SFP', icon: '📡', desc: 'Ingestas A y B' },
		{ id: 'otdr', label: 'OTDR', icon: '📊', desc: 'Ingesta C y D' },
		{ id: 'n2', label: 'Cajas NAP', icon: '📦', desc: 'Ingesta E' },
		{ id: 'ozmap', label: 'OZmap', icon: '🗺️', desc: 'Ingesta F' }
	] as const;
</script>

<svelte:head>
	<title>Ingesta de Datos — Auditoría ODN</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-4xl mx-auto space-y-6">

		<div class="flex items-center gap-4">
			<a href="/network-audit" class="text-blue-600 hover:text-blue-800 text-sm">← Dashboard</a>
			<div>
				<h1 class="text-xl font-bold text-gray-900">Ingesta de Información</h1>
				<p class="text-sm text-gray-500">Registro de las 7 fuentes de datos del módulo ODN</p>
			</div>
		</div>

		{#if successMsg}
			<div class="bg-green-50 border border-green-300 rounded-xl p-4 text-green-800 text-sm">
				{successMsg}
			</div>
		{/if}
		{#if errorMsg}
			<div class="bg-red-50 border border-red-300 rounded-xl p-4 text-red-800 text-sm">
				{errorMsg}
			</div>
		{/if}

		<!-- Tabs -->
		<div class="flex gap-2 bg-white rounded-2xl border border-gray-200 p-2">
			{#each tabs as tab}
				<button
					onclick={() => { activeTab = tab.id; successMsg = null; errorMsg = null; }}
					class="flex-1 flex flex-col items-center py-3 rounded-xl text-sm transition-colors
						{activeTab === tab.id ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'}"
				>
					<span class="text-xl mb-1">{tab.icon}</span>
					<span class="font-semibold">{tab.label}</span>
					<span class="text-xs opacity-70">{tab.desc}</span>
				</button>
			{/each}
		</div>

		<!-- OLT + SFP -->
		{#if activeTab === 'olt'}
			<div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-5">
				<div class="flex items-center gap-3">
					<span class="text-2xl">📡</span>
					<div>
						<h2 class="text-lg font-bold text-gray-800">Puerto OLT + Módulo SFP</h2>
						<p class="text-sm text-gray-500">Ingestas A (Smart OLT API) y B (Potencia TX)</p>
					</div>
				</div>
				<form onsubmit={submitOltPort} class="space-y-4">
					<div class="grid grid-cols-2 gap-4">
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">ID OLT *</label>
							<input
								bind:value={oltForm.olt_id}
								required
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
								placeholder="ej: OLT-TIG-01"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">ID Puerto *</label>
							<input
								bind:value={oltForm.port_id}
								required
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
								placeholder="ej: GPON-0/0/1"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">ID HUB *</label>
							<input
								bind:value={oltForm.hub_id}
								required
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
								placeholder="ej: HUB-TIG-001"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Localidad *</label>
							<input
								bind:value={oltForm.localidad}
								required
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
								placeholder="ej: El Tigre"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">% Ocupación *</label>
							<input
								type="number"
								step="0.01"
								min="0"
								max="100"
								bind:value={oltForm.port_occupancy_percentage}
								required
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
							/>
						</div>
						<div>
							<label class="block text-sm font-medium text-gray-700 mb-1">Clientes conectados *</label>
							<input
								type="number"
								min="0"
								bind:value={oltForm.connected_clients_count}
								required
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
							/>
						</div>
						<div class="col-span-2">
							<label class="block text-sm font-medium text-gray-700 mb-1">
								Potencia TX SFP (dBm) * — umbral mínimo: +6 dBm
							</label>
							<input
								type="number"
								step="0.01"
								bind:value={oltForm.current_sfp_tx_power_dbm}
								required
								class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:outline-none
									{oltForm.current_sfp_tx_power_dbm < 6 ? 'border-red-500 bg-red-50 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'}"
							/>
							{#if oltForm.current_sfp_tx_power_dbm < 6 && oltForm.current_sfp_tx_power_dbm !== 0}
								<p class="text-xs text-red-600 mt-1">⚠️ Por debajo del umbral mínimo +6 dBm — se activará evaluación SFP</p>
							{/if}
						</div>
						<div class="col-span-2">
							<label class="block text-sm font-medium text-gray-700 mb-1">
								Potencias ONTs del puerto (CSV, dBm) — para evaluación SFP
							</label>
							<input
								bind:value={oltClientPowers}
								class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
								placeholder="-22.5, -23.1, -24.8, -27.2, ..."
							/>
							<p class="text-xs text-gray-400 mt-1">Separar valores con coma. Si el promedio es &lt; -26.5 dBm, se agrega al reporte de SFPs.</p>
						</div>
					</div>
					<button
						type="submit"
						disabled={oltSubmitting}
						class="w-full bg-blue-600 text-white font-semibold py-3 rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
					>
						{oltSubmitting ? 'Registrando...' : 'Registrar Puerto OLT'}
					</button>
				</form>
			</div>
		{/if}

		<!-- OTDR -->
		{#if activeTab === 'otdr'}
			<OtdrDropzone onSubmit={submitOtdr} />
		{/if}

		<!-- Cajas NAP N2 -->
		{#if activeTab === 'n2'}
			<div class="bg-white rounded-2xl border border-gray-200 p-6">
				<div class="flex items-center gap-3 mb-5">
					<span class="text-2xl">📦</span>
					<div>
						<h2 class="text-lg font-bold text-gray-800">Registro de Caja NAP N2</h2>
						<p class="text-sm text-gray-500">Ingesta E — Foto + OZmap + Georreferenciación</p>
					</div>
				</div>
				<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800">
					⚠️ <strong>Compuerta activa:</strong> Solo se pueden crear cajas N2 si el tramo N1 padre
					tiene OTDR aprobado. El backend rechazará la solicitud si el tramo está bloqueado.
				</div>
				<p class="text-sm text-gray-400 mt-4 text-center">
					Formulario disponible desde la interfaz de campo — usa la sección
					<a href="/network-audit/field" class="text-blue-600 hover:underline">Mediciones en Calle</a>
					para una experiencia optimizada para móvil.
				</p>
			</div>
		{/if}

		<!-- OZmap -->
		{#if activeTab === 'ozmap'}
			<div class="bg-white rounded-2xl border border-gray-200 p-6">
				<div class="flex items-center gap-3 mb-5">
					<span class="text-2xl">🗺️</span>
					<div>
						<h2 class="text-lg font-bold text-gray-800">Conciliación OZmap</h2>
						<p class="text-sm text-gray-500">Ingesta F — Sincronización cartográfica vs inventario físico</p>
					</div>
				</div>
				<div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
					La conciliación OZmap se realiza actualizando el campo <code>ozmap_sync_status</code>
					de cada caja N2 vía la API <code>POST /api/v1/n2/{"{id}"}/ozmap-sync</code>.
					Los estados posibles son: <strong>CONCILIADO</strong>, <strong>DISCREPANCIA</strong> o <strong>PENDIENTE</strong>.
				</div>
			</div>
		{/if}
	</div>
</div>
