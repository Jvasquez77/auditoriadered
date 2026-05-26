<script lang="ts">
	import {
		classifyPower,
		getPowerStatusColor,
		POWER_THRESHOLDS,
		type N2PortMeasurementCreate,
		type PowerStatus
	} from '$lib/types/network-audit';

	interface Props {
		n2BoxId: string;
		n2InfrastructureId: string;
		totalPorts?: 8 | 16;
		onSubmit?: (measurements: N2PortMeasurementCreate[]) => void | Promise<void>;
	}

	let { n2BoxId, n2InfrastructureId, totalPorts = 8, onSubmit }: Props = $props();

	interface PortEntry {
		port_number: number;
		measured_power_dbm: string;
		client_id: string;
		photo_file: File | null;
		photo_preview: string | null;
		status: PowerStatus | null;
	}

	const initialPorts = (): PortEntry[] =>
		Array.from({ length: totalPorts }, (_, i) => ({
			port_number: i + 1,
			measured_power_dbm: '',
			client_id: '',
			photo_file: null,
			photo_preview: null,
			status: null
		}));

	let ports = $state<PortEntry[]>(initialPorts());
	let submitting = $state(false);
	let geoLocation = $state<{ latitude: number; longitude: number } | null>(null);
	let geoLoading = $state(false);

	function updatePortStatus(index: number) {
		const val = parseFloat(ports[index].measured_power_dbm);
		if (!isNaN(val)) {
			ports[index].status = classifyPower(val);
		} else {
			ports[index].status = null;
		}
	}

	function handlePhotoChange(e: Event, index: number) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) {
			ports[index].photo_file = file;
			ports[index].photo_preview = URL.createObjectURL(file);
		}
	}

	async function requestGeolocation() {
		geoLoading = true;
		try {
			const pos = await new Promise<GeolocationPosition>((resolve, reject) =>
				navigator.geolocation.getCurrentPosition(resolve, reject)
			);
			geoLocation = {
				latitude: pos.coords.latitude,
				longitude: pos.coords.longitude
			};
		} catch {
			alert('No se pudo obtener la ubicación GPS');
		} finally {
			geoLoading = false;
		}
	}

	const completedPorts = $derived(
		ports.filter((p) => p.measured_power_dbm !== '' && !isNaN(parseFloat(p.measured_power_dbm)))
			.length
	);

	const criticalCount = $derived(
		ports.filter((p) => p.status === 'CRITICO' || p.status === 'SEVERO').length
	);

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (submitting) return;
		submitting = true;
		try {
			const measurements: N2PortMeasurementCreate[] = ports
				.filter((p) => p.measured_power_dbm !== '')
				.map((p) => ({
					n2_infrastructure_id: n2InfrastructureId,
					port_number: p.port_number,
					measured_power_dbm: parseFloat(p.measured_power_dbm),
					photo_port_url: p.photo_preview ?? '/placeholder.jpg',
					client_id: p.client_id || undefined,
					geo_coordinates: geoLocation ?? undefined
				}));
			await onSubmit?.(measurements);
		} finally {
			submitting = false;
		}
	}
</script>

<div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-5">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-3">
			<span class="text-2xl">📶</span>
			<div>
				<h2 class="text-lg font-bold text-gray-800">Medición de Potencias en Calle</h2>
				<p class="text-sm text-gray-500">Caja NAP: <strong>{n2BoxId}</strong> · {totalPorts} puertos</p>
			</div>
		</div>
		<div class="text-right">
			<p class="text-sm text-gray-500">{completedPorts}/{totalPorts} medidos</p>
			{#if criticalCount > 0}
				<p class="text-sm font-bold text-red-600">{criticalCount} fuera de rango</p>
			{/if}
		</div>
	</div>

	<!-- Geolocalización -->
	<div class="bg-gray-50 rounded-xl p-4 flex items-center justify-between">
		<div>
			<p class="text-sm font-medium text-gray-700">📍 Georreferenciación</p>
			{#if geoLocation}
				<p class="text-xs text-green-600">
					{geoLocation.latitude.toFixed(6)}, {geoLocation.longitude.toFixed(6)}
				</p>
			{:else}
				<p class="text-xs text-gray-400">Sin ubicación GPS capturada</p>
			{/if}
		</div>
		<button
			type="button"
			onclick={requestGeolocation}
			disabled={geoLoading}
			class="text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
		>
			{geoLoading ? 'Obteniendo...' : 'Capturar GPS'}
		</button>
	</div>

	<!-- Umbrales de referencia -->
	<div class="grid grid-cols-3 gap-3 text-xs">
		<div class="bg-green-50 rounded-lg p-3 text-center">
			<div class="font-bold text-green-700">NORMAL</div>
			<div class="text-green-600">&gt; {POWER_THRESHOLDS.CLIENT_CRITICAL_DBM} dBm</div>
		</div>
		<div class="bg-orange-50 rounded-lg p-3 text-center">
			<div class="font-bold text-orange-700">CRÍTICO</div>
			<div class="text-orange-600">
				{POWER_THRESHOLDS.CLIENT_SEVERE_DBM} a {POWER_THRESHOLDS.CLIENT_CRITICAL_DBM} dBm
			</div>
		</div>
		<div class="bg-red-50 rounded-lg p-3 text-center">
			<div class="font-bold text-red-700">SEVERO</div>
			<div class="text-red-600">&lt; {POWER_THRESHOLDS.CLIENT_SEVERE_DBM} dBm</div>
		</div>
	</div>

	<form onsubmit={handleSubmit} class="space-y-3">
		{#each ports as port, i}
			{@const statusColor = port.status ? getPowerStatusColor(port.status) : '#6b7280'}
			<div
				class="rounded-xl border-2 p-4 transition-colors"
				style="border-color: {port.status ? statusColor : '#e5e7eb'}"
			>
				<div class="flex items-center gap-3 mb-3">
					<span
						class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm text-white"
						style="background-color: {statusColor}"
					>
						{port.port_number}
					</span>
					<div class="flex-1 grid grid-cols-3 gap-3">
						<div>
							<label class="text-xs text-gray-500">Potencia (dBm)</label>
							<input
								type="number"
								step="0.01"
								bind:value={port.measured_power_dbm}
								oninput={() => updatePortStatus(i)}
								class="w-full border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
								placeholder="-XX.XX"
							/>
						</div>
						<div>
							<label class="text-xs text-gray-500">ID Cliente</label>
							<input
								bind:value={port.client_id}
								class="w-full border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
								placeholder="Opcional"
							/>
						</div>
						<div>
							<label class="text-xs text-gray-500">Foto puerto</label>
							<label class="flex items-center gap-2 cursor-pointer">
								<input
									type="file"
									accept="image/*"
									capture="environment"
									class="hidden"
									onchange={(e) => handlePhotoChange(e, i)}
								/>
								{#if port.photo_preview}
									<img
										src={port.photo_preview}
										alt="Puerto {port.port_number}"
										class="h-8 w-8 rounded object-cover"
									/>
								{:else}
									<div class="h-8 w-8 rounded bg-gray-100 border flex items-center justify-center text-gray-400 text-xs">
										📷
									</div>
								{/if}
							</label>
						</div>
					</div>
					{#if port.status}
						<span
							class="text-xs font-bold px-2 py-1 rounded-full text-white whitespace-nowrap"
							style="background-color: {statusColor}"
						>
							{port.status}
						</span>
					{/if}
				</div>
			</div>
		{/each}

		<button
			type="submit"
			disabled={submitting || completedPorts === 0}
			class="w-full bg-green-600 text-white font-semibold py-3 rounded-xl hover:bg-green-700
				disabled:opacity-50 disabled:cursor-not-allowed transition-colors mt-4"
		>
			{submitting ? 'Guardando...' : `Enviar ${completedPorts} medicion${completedPorts !== 1 ? 'es' : ''}`}
		</button>
	</form>
</div>
