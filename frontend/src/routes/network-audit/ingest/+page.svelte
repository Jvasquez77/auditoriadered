<script lang="ts">
	import { onMount } from 'svelte';
	import OtdrDropzone from '$lib/components/network-audit/OtdrDropzone.svelte';
	import type { OtdrFormData } from '$lib/components/network-audit/OtdrDropzone.svelte';
	import type {
		OltCreate,
		OltPortForOltCreate,
		OltPortSyncRequest,
		OltRead
	} from '$lib/types/network-audit';

	let activeTab = $state<'olt' | 'otdr' | 'n2' | 'ozmap'>('olt');
	let successMsg = $state<string | null>(null);
	let errorMsg = $state<string | null>(null);

	// ── OLT wizard ───────────────────────────────────────────────────────────
	// Step 1: seleccionar o crear OLT
	// Step 2: agregar puerto al OLT seleccionado
	let oltStep = $state<1 | 2>(1);
	let olts = $state<OltRead[]>([]);
	let selectedOlt = $state<OltRead | null>(null);
	let loadingOlts = $state(false);

	// Formulario de nuevo OLT
	let newOltForm = $state<OltCreate>({
		olt_id: '',
		name: '',
		hub_id: '',
		localidad: '',
		ip_address: '',
		brand: '',
		model: '',
		total_ports: 16,
		status: 'ACTIVO'
	});
	let creatingOlt = $state(false);
	let showOltForm = $state(false);

	// Formulario de puerto (anidado bajo el OLT seleccionado)
	let portForm = $state<OltPortForOltCreate>({
		port_id: '',
		port_occupancy_percentage: 0,
		connected_clients_count: 0,
		current_sfp_tx_power_dbm: 0,
		client_powers: []
	});
	let portClientPowersRaw = $state('');
	let submittingPort = $state(false);

	async function loadOlts() {
		loadingOlts = true;
		try {
			const res = await fetch('/api/v1/olts/');
			if (res.ok) olts = await res.json();
		} catch {
			// ignore — usuario verá lista vacía
		} finally {
			loadingOlts = false;
		}
	}

	onMount(loadOlts);

	async function createOlt(e: SubmitEvent) {
		e.preventDefault();
		creatingOlt = true;
		errorMsg = null;
		try {
			const body: OltCreate = {
				olt_id:      newOltForm.olt_id,
				name:        newOltForm.name,
				hub_id:      newOltForm.hub_id,
				localidad:   newOltForm.localidad,
				total_ports: newOltForm.total_ports,
				status:      newOltForm.status,
				...(newOltForm.ip_address && { ip_address: newOltForm.ip_address }),
				...(newOltForm.brand      && { brand: newOltForm.brand }),
				...(newOltForm.model      && { model: newOltForm.model }),
			};
			const res = await fetch('/api/v1/olts/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(body)
			});
			if (!res.ok) throw new Error(await res.text());
			const olt: OltRead = await res.json();
			olts = [olt, ...olts];
			selectedOlt = olt;
			showOltForm = false;
			oltStep = 2;
			successMsg = `OLT "${olt.name}" (${olt.olt_id}) creado. Ahora agrega un puerto.`;
		} catch (e) {
			errorMsg = `Error al crear OLT: ${e instanceof Error ? e.message : String(e)}`;
		} finally {
			creatingOlt = false;
		}
	}

	function selectOlt(olt: OltRead) {
		selectedOlt = olt;
		oltStep = 2;
		successMsg = null;
		errorMsg = null;
	}

	async function submitPort(e: SubmitEvent) {
		e.preventDefault();
		if (!selectedOlt) return;
		submittingPort = true;
		errorMsg = null;
		successMsg = null;

		try {
			// Parsear potencias de clientes
			const powers = portClientPowersRaw
				.split(',')
				.map((p) => parseFloat(p.trim()))
				.filter((p) => !isNaN(p));

			const payload: OltPortForOltCreate = {
				port_id:                    portForm.port_id,
				port_occupancy_percentage:  portForm.port_occupancy_percentage,
				connected_clients_count:    portForm.connected_clients_count,
				current_sfp_tx_power_dbm:   portForm.current_sfp_tx_power_dbm,
				client_powers:              powers
			};

			const res = await fetch(`/api/v1/olts/${selectedOlt.id}/ports`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});
			if (!res.ok) throw new Error(await res.text());
			const port = await res.json();

			if (port.sfp_alert) {
				successMsg = `Puerto ${port.port_id} registrado. ⚠️ Alerta SFP — potencia TX por debajo del umbral mínimo.`;
			} else {
				successMsg = `Puerto ${port.port_id} registrado en ${selectedOlt.name}. SFP en rango óptimo.`;
			}

			// Resetear formulario de puerto para agregar otro
			portForm = { port_id: '', port_occupancy_percentage: 0, connected_clients_count: 0, current_sfp_tx_power_dbm: 0, client_powers: [] };
			portClientPowersRaw = '';

			// Actualizar conteo del OLT seleccionado
			await loadOlts();
			const updated = olts.find(o => o.id === selectedOlt!.id);
			if (updated) selectedOlt = updated;

		} catch (e) {
			errorMsg = `Error: ${e instanceof Error ? e.message : String(e)}`;
		} finally {
			submittingPort = false;
		}
	}

	async function submitOtdr(data: OtdrFormData) {
		errorMsg = null;
		successMsg = null;
		try {
			const photoUrl = data.photo_file
				? `${window.location.origin}/media/n1_${data.n1_manga_id}_${Date.now()}.jpg`
				: '/placeholder.jpg';

			const res = await fetch('/api/v1/n1/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					olt_port_id:              data.olt_port_id,
					n1_manga_id:              data.n1_manga_id,
					odf_port_id:              data.odf_port_id,
					otdr_total_distance_m:    data.otdr_total_distance_m,
					otdr_total_loss_db:       data.otdr_total_loss_db,
					otdr_max_fusion_loss_db:  data.otdr_max_fusion_loss_db,
					photo_url:                photoUrl,
					window_1310_loss_db:      data.window_1310_loss_db,
					window_1550_loss_db:      data.window_1550_loss_db
				})
			});
			const n1 = await res.json();
			if (!res.ok) throw new Error(n1.detail ?? JSON.stringify(n1));

			if (n1.otdr_status === 'BLOQUEADO') {
				errorMsg = '⛔ TRAMO BLOQUEADO: La pérdida de fusión supera 0.1 dB. Se creó la incidencia.';
			} else {
				successMsg = `✅ OTDR registrado y aprobado para el tramo ${n1.n1_manga_id}.`;
			}
		} catch (e) {
			errorMsg = `Error al registrar OTDR: ${e instanceof Error ? e.message : String(e)}`;
		}
	}

	const tabs = [
		{ id: 'olt',   label: 'OLT + SFP',   desc: 'Ingestas A y B' },
		{ id: 'otdr',  label: 'OTDR',          desc: 'Ingesta C y D' },
		{ id: 'n2',    label: 'Cajas NAP',     desc: 'Ingesta E' },
		{ id: 'ozmap', label: 'OZmap',          desc: 'Ingesta F' }
	] as const;

	const sfpAlertClass = $derived(
		portForm.current_sfp_tx_power_dbm !== 0 && portForm.current_sfp_tx_power_dbm < 6
			? 'border-red-400 bg-red-50 focus:ring-red-400'
			: 'border-slate-200 focus:ring-violet-500'
	);
</script>

<svelte:head>
	<title>Ingesta de Datos — Auditoría ODN</title>
</svelte:head>

<div class="space-y-5 max-w-4xl mx-auto">

	<!-- Page header -->
	<div>
		<h2 class="text-xl font-bold text-slate-900">Ingesta de Información</h2>
		<p class="text-sm text-slate-500 mt-0.5">Registro de las fuentes de datos del módulo ODN</p>
	</div>

	<!-- Alerts -->
	{#if successMsg}
		<div class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-sm text-emerald-800 flex items-start gap-2">
			<svg class="w-4 h-4 shrink-0 mt-0.5 text-emerald-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
			</svg>
			{successMsg}
		</div>
	{/if}
	{#if errorMsg}
		<div class="bg-red-50 border border-red-200 rounded-xl p-4 text-sm text-red-800 flex items-start gap-2">
			<svg class="w-4 h-4 shrink-0 mt-0.5 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
			</svg>
			{errorMsg}
		</div>
	{/if}

	<!-- Tab bar -->
	<div class="flex gap-1.5 bg-slate-100 rounded-xl p-1">
		{#each tabs as tab}
			<button
				onclick={() => { activeTab = tab.id; successMsg = null; errorMsg = null; }}
				class="flex-1 flex flex-col items-center py-2.5 px-3 rounded-lg text-sm transition-all"
				class:bg-white={activeTab === tab.id}
				class:shadow-sm={activeTab === tab.id}
				class:text-violet-700={activeTab === tab.id}
				class:font-semibold={activeTab === tab.id}
				class:text-slate-500={activeTab !== tab.id}
				class:hover:text-slate-700={activeTab !== tab.id}
			>
				<span class="font-medium">{tab.label}</span>
				<span class="text-xs opacity-60">{tab.desc}</span>
			</button>
		{/each}
	</div>

	<!-- ── Tab: OLT + SFP ────────────────────────────────────────────────── -->
	{#if activeTab === 'olt'}
		<div class="card overflow-hidden">

			<!-- Wizard step indicators -->
			<div class="flex border-b border-slate-100">
				<button
					onclick={() => { oltStep = 1; }}
					class="flex-1 flex items-center gap-2.5 px-5 py-4 text-sm border-b-2 transition-colors"
					class:border-violet-600={oltStep === 1}
					class:text-violet-700={oltStep === 1}
					class:font-semibold={oltStep === 1}
					class:border-transparent={oltStep !== 1}
					class:text-slate-500={oltStep !== 1}
				>
					<span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
						class:bg-violet-600={oltStep === 1}
						class:text-white={oltStep === 1}
						class:bg-slate-200={oltStep !== 1}
						class:text-slate-500={oltStep !== 1}
					>1</span>
					Seleccionar OLT
				</button>
				<button
					onclick={() => { if (selectedOlt) oltStep = 2; }}
					class="flex-1 flex items-center gap-2.5 px-5 py-4 text-sm border-b-2 transition-colors"
					class:border-violet-600={oltStep === 2}
					class:text-violet-700={oltStep === 2}
					class:font-semibold={oltStep === 2}
					class:border-transparent={oltStep !== 2}
					class:text-slate-500={oltStep !== 2}
					disabled={!selectedOlt}
				>
					<span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0"
						class:bg-violet-600={oltStep === 2}
						class:text-white={oltStep === 2}
						class:bg-slate-200={oltStep !== 2}
						class:text-slate-500={oltStep !== 2}
					>2</span>
					Agregar Puerto
					{#if selectedOlt}
						<span class="ml-auto text-xs text-violet-600 font-medium truncate max-w-28">{selectedOlt.name}</span>
					{/if}
				</button>
			</div>

			<!-- Step 1: Seleccionar / crear OLT -->
			{#if oltStep === 1}
				<div class="p-5 space-y-4">

					<div class="flex items-center justify-between">
						<p class="text-sm text-slate-600">Selecciona un OLT existente o crea uno nuevo.</p>
						<button
							onclick={() => (showOltForm = !showOltForm)}
							class="inline-flex items-center gap-1.5 text-sm font-semibold text-violet-600 hover:text-violet-700 transition-colors"
						>
							<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
							</svg>
							{showOltForm ? 'Cancelar' : 'Nuevo OLT'}
						</button>
					</div>

					<!-- Formulario nuevo OLT (colapsable) -->
					{#if showOltForm}
						<form onsubmit={createOlt} class="bg-slate-50 rounded-xl p-4 space-y-3 border border-slate-200">
							<p class="text-sm font-semibold text-slate-700">Registrar nuevo dispositivo OLT</p>
							<div class="grid grid-cols-2 gap-3">
								<div>
									<label class="block text-xs font-medium text-slate-600 mb-1">ID OLT *</label>
									<input bind:value={newOltForm.olt_id} required placeholder="OLT-TIG-01"
										class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none bg-white" />
								</div>
								<div>
									<label class="block text-xs font-medium text-slate-600 mb-1">Nombre descriptivo *</label>
									<input bind:value={newOltForm.name} required placeholder="OLT Tigre Centro"
										class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none bg-white" />
								</div>
								<div>
									<label class="block text-xs font-medium text-slate-600 mb-1">ID HUB *</label>
									<input bind:value={newOltForm.hub_id} required placeholder="HUB-TIG-001"
										class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none bg-white" />
								</div>
								<div>
									<label class="block text-xs font-medium text-slate-600 mb-1">Localidad *</label>
									<input bind:value={newOltForm.localidad} required placeholder="El Tigre"
										class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none bg-white" />
								</div>
								<div>
									<label class="block text-xs font-medium text-slate-600 mb-1">Marca</label>
									<input bind:value={newOltForm.brand} placeholder="Huawei"
										class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none bg-white" />
								</div>
								<div>
									<label class="block text-xs font-medium text-slate-600 mb-1">Modelo</label>
									<input bind:value={newOltForm.model} placeholder="MA5800-X7"
										class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none bg-white" />
								</div>
								<div>
									<label class="block text-xs font-medium text-slate-600 mb-1">IP de gestión</label>
									<input bind:value={newOltForm.ip_address} placeholder="192.168.1.100"
										class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none bg-white" />
								</div>
								<div>
									<label class="block text-xs font-medium text-slate-600 mb-1">Total puertos</label>
									<select bind:value={newOltForm.total_ports}
										class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none bg-white">
										<option value={8}>8</option>
										<option value={16}>16</option>
										<option value={32}>32</option>
										<option value={64}>64</option>
									</select>
								</div>
							</div>
							<button type="submit" disabled={creatingOlt}
								class="w-full bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors">
								{creatingOlt ? 'Creando...' : 'Crear OLT y continuar →'}
							</button>
						</form>
					{/if}

					<!-- Lista de OLTs existentes -->
					{#if loadingOlts}
						<div class="space-y-2">
							{#each [1, 2, 3] as _}
								<div class="skeleton h-16 w-full rounded-xl"></div>
							{/each}
						</div>
					{:else if olts.length === 0 && !showOltForm}
						<div class="flex flex-col items-center py-12 text-center">
							<div class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center mb-3">
								<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
									<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
								</svg>
							</div>
							<p class="text-sm font-medium text-slate-600">No hay OLTs registrados</p>
							<p class="text-xs text-slate-400 mt-1">Crea el primero usando el botón "Nuevo OLT"</p>
						</div>
					{:else}
						<div class="space-y-2">
							{#each olts as olt}
								<button
									onclick={() => selectOlt(olt)}
									class="w-full flex items-center justify-between p-4 rounded-xl border text-left transition-all"
									class:border-violet-300={selectedOlt?.id === olt.id}
									class:bg-violet-50={selectedOlt?.id === olt.id}
									class:border-slate-200={selectedOlt?.id !== olt.id}
									class:hover:border-slate-300={selectedOlt?.id !== olt.id}
									class:hover:bg-slate-50={selectedOlt?.id !== olt.id}
								>
									<div class="flex items-center gap-3">
										<div class="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
											<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
												<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
											</svg>
										</div>
										<div>
											<p class="text-sm font-semibold text-slate-800">{olt.name}</p>
											<p class="text-xs text-slate-400">{olt.olt_id} · {olt.localidad} · {olt.hub_id}</p>
										</div>
									</div>
									<div class="flex items-center gap-3 shrink-0">
										<div class="text-right">
											<p class="text-xs font-semibold text-slate-600">{olt.port_count}/{olt.total_ports}</p>
											<p class="text-xs text-slate-400">puertos</p>
										</div>
										<span class="badge"
											class:badge-aprobado={olt.status === 'ACTIVO'}
											class:badge-pendiente={olt.status === 'MANTENIMIENTO'}
											class:badge-bloqueado={olt.status === 'INACTIVO'}
										>{olt.status}</span>
									</div>
								</button>
							{/each}
						</div>
					{/if}

					{#if selectedOlt}
						<button
							onclick={() => (oltStep = 2)}
							class="w-full bg-violet-600 hover:bg-violet-700 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors"
						>
							Agregar puerto a {selectedOlt.name} →
						</button>
					{/if}
				</div>
			{/if}

			<!-- Step 2: Agregar puerto al OLT seleccionado -->
			{#if oltStep === 2 && selectedOlt}
				<div class="p-5 space-y-4">
					<!-- OLT context banner -->
					<div class="flex items-center gap-3 bg-violet-50 border border-violet-100 rounded-xl p-3">
						<div class="w-8 h-8 rounded-lg bg-violet-100 flex items-center justify-center shrink-0">
							<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
							</svg>
						</div>
						<div class="min-w-0">
							<p class="text-sm font-semibold text-violet-800">{selectedOlt.name}</p>
							<p class="text-xs text-violet-600">{selectedOlt.olt_id} · {selectedOlt.localidad} · {selectedOlt.port_count}/{selectedOlt.total_ports} puertos</p>
						</div>
						<button onclick={() => (oltStep = 1)} class="ml-auto text-xs text-violet-500 hover:text-violet-700 font-medium shrink-0">
							Cambiar
						</button>
					</div>

					<form onsubmit={submitPort} class="space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div class="col-span-2">
								<label class="block text-xs font-medium text-slate-600 mb-1">ID Puerto *</label>
								<input
									bind:value={portForm.port_id}
									required
									placeholder="GPON-0/0/1"
									class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none"
								/>
							</div>
							<div>
								<label class="block text-xs font-medium text-slate-600 mb-1">% Ocupación *</label>
								<input
									type="number" step="0.01" min="0" max="100"
									bind:value={portForm.port_occupancy_percentage}
									required
									class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none"
								/>
							</div>
							<div>
								<label class="block text-xs font-medium text-slate-600 mb-1">Clientes conectados *</label>
								<input
									type="number" min="0"
									bind:value={portForm.connected_clients_count}
									required
									class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none"
								/>
							</div>
							<div class="col-span-2">
								<label class="block text-xs font-medium text-slate-600 mb-1">
									Potencia TX SFP (dBm) * — umbral mínimo: +6 dBm
								</label>
								<input
									type="number" step="0.01"
									bind:value={portForm.current_sfp_tx_power_dbm}
									required
									class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:outline-none {sfpAlertClass}"
								/>
								{#if portForm.current_sfp_tx_power_dbm < 6 && portForm.current_sfp_tx_power_dbm !== 0}
									<p class="text-xs text-red-600 mt-1">⚠️ Por debajo del umbral mínimo — se activará evaluación SFP</p>
								{/if}
							</div>
							<div class="col-span-2">
								<label class="block text-xs font-medium text-slate-600 mb-1">
									Potencias ONTs del puerto (CSV, dBm) — para evaluación SFP
								</label>
								<input
									bind:value={portClientPowersRaw}
									placeholder="-22.5, -23.1, -24.8, -27.2, ..."
									class="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500 focus:outline-none"
								/>
								<p class="text-xs text-slate-400 mt-1">Separar con coma. Si el promedio &lt; -26.5 dBm, se genera reporte de SFP.</p>
							</div>
						</div>

						<div class="flex gap-3">
							<button
								type="button"
								onclick={() => (oltStep = 1)}
								class="flex-1 border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium py-2.5 rounded-lg text-sm transition-colors"
							>
								← Cambiar OLT
							</button>
							<button
								type="submit"
								disabled={submittingPort}
								class="flex-2 flex-1 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors"
							>
								{submittingPort ? 'Registrando...' : 'Registrar Puerto'}
							</button>
						</div>
					</form>
				</div>
			{/if}
		</div>
	{/if}

	<!-- ── Tab: OTDR ──────────────────────────────────────────────────────── -->
	{#if activeTab === 'otdr'}
		<OtdrDropzone onSubmit={submitOtdr} />
	{/if}

	<!-- ── Tab: Cajas NAP N2 ─────────────────────────────────────────────── -->
	{#if activeTab === 'n2'}
		<div class="card p-6 space-y-4">
			<div>
				<h3 class="text-base font-bold text-slate-800">Registro de Caja NAP N2</h3>
				<p class="text-sm text-slate-500 mt-0.5">Ingesta E — Foto + OZmap + Georreferenciación</p>
			</div>
			<div class="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
				<strong>Compuerta activa:</strong> Solo se pueden crear cajas N2 si el tramo N1 padre tiene OTDR aprobado. El backend rechazará si el tramo está bloqueado.
			</div>
			<p class="text-sm text-slate-400 text-center">
				Usa la sección
				<a href="/network-audit/field" class="text-violet-600 hover:underline font-medium">Mediciones en Calle</a>
				para una experiencia optimizada para móvil.
			</p>
		</div>
	{/if}

	<!-- ── Tab: OZmap ────────────────────────────────────────────────────── -->
	{#if activeTab === 'ozmap'}
		<div class="card p-6 space-y-4">
			<div>
				<h3 class="text-base font-bold text-slate-800">Conciliación OZmap</h3>
				<p class="text-sm text-slate-500 mt-0.5">Ingesta F — Sincronización cartográfica vs inventario físico</p>
			</div>
			<div class="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-800">
				La conciliación OZmap se realiza actualizando el campo <code class="font-mono bg-blue-100 px-1 rounded">ozmap_sync_status</code>
				de cada caja N2 vía la API <code class="font-mono bg-blue-100 px-1 rounded">POST /api/v1/n2/{"{id}"}/ozmap-sync</code>.
				Los estados posibles son: <strong>CONCILIADO</strong>, <strong>DISCREPANCIA</strong> o <strong>PENDIENTE</strong>.
			</div>
		</div>
	{/if}

</div>
