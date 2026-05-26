<script lang="ts">
	import type { DeliveryActRead, DeliveryActSign } from '$lib/types/network-audit';

	interface Props {
		act: DeliveryActRead;
		onSign?: (payload: DeliveryActSign) => void | Promise<void>;
	}

	let { act, onSign }: Props = $props();

	let signingRole = $state<'EXECUTOR' | 'SUPERVISOR' | null>(null);
	let signerName = $state('');
	let signingInProgress = $state(false);

	const canSign = $derived(act.status === 'BORRADOR' || act.status === 'APROBADO');
	const isFullySigned = $derived(!!act.executor_signature && !!act.supervisor_signature);

	const passedChecks = $derived(act.checklist.filter((c) => c.passed).length);
	const totalChecks = $derived(act.checklist.length);
	const allChecksPassed = $derived(passedChecks === totalChecks);

	const statusConfig: Record<string, { color: string; label: string; icon: string }> = {
		BORRADOR:          { color: 'text-yellow-700 bg-yellow-100', label: 'Borrador',          icon: '📝' },
		APROBADO:          { color: 'text-green-700 bg-green-100',   label: 'Aprobado',          icon: '✅' },
		EXCEPCION_ACEPTADA:{ color: 'text-blue-700 bg-blue-100',     label: 'Excepción Aceptada',icon: '⚠️' },
		RECHAZADO:         { color: 'text-red-700 bg-red-100',       label: 'Rechazado',         icon: '❌' }
	};

	async function handleSign(role: 'EXECUTOR' | 'SUPERVISOR') {
		if (!signerName.trim()) {
			alert('Por favor ingrese el nombre del firmante');
			return;
		}
		signingInProgress = true;
		try {
			const payload: DeliveryActSign = {
				role,
				signature_data: `FIRMA_DIGITAL_${role}_${signerName}_${Date.now()}`,
				signer_name: signerName
			};
			await onSign?.(payload);
			signingRole = null;
			signerName = '';
		} finally {
			signingInProgress = false;
		}
	}

	function formatDate(iso: string | null) {
		if (!iso) return '—';
		return new Intl.DateTimeFormat('es-VE', {
			dateStyle: 'medium',
			timeStyle: 'short'
		}).format(new Date(iso));
	}
</script>

<div class="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
	<!-- Encabezado del acta -->
	<div class="bg-gradient-to-r from-blue-700 to-blue-900 text-white p-6">
		<div class="flex items-start justify-between">
			<div>
				<p class="text-blue-200 text-sm uppercase tracking-wide">Acta de Entrega Técnica</p>
				<h1 class="text-2xl font-bold mt-1">Red FTTX — ODN</h1>
				<p class="text-blue-200 mt-1">Sucursal: <strong class="text-white">{act.sucursal}</strong></p>
			</div>
			<span class="px-3 py-1.5 rounded-full text-sm font-bold {statusConfig[act.status]?.color ?? ''}">
				{statusConfig[act.status]?.icon} {statusConfig[act.status]?.label}
			</span>
		</div>
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5 text-sm">
			<div>
				<p class="text-blue-300">Manga N1</p>
				<p class="font-semibold">{act.n1_manga_id ?? '—'}</p>
			</div>
			<div>
				<p class="text-blue-300">Líder de Cuadrilla</p>
				<p class="font-semibold">{act.squad_leader}</p>
			</div>
			<div>
				<p class="text-blue-300">Fecha de Creación</p>
				<p class="font-semibold">{formatDate(act.created_at)}</p>
			</div>
			<div>
				<p class="text-blue-300">Aprobación</p>
				<p class="font-semibold">{formatDate(act.approved_at)}</p>
			</div>
		</div>
	</div>

	<div class="p-6 space-y-6">
		<!-- Resumen de abonados -->
		<div>
			<h3 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-3">
				Resumen de Abonados
			</h3>
			<div class="grid grid-cols-3 gap-4">
				<div class="bg-blue-50 rounded-xl p-4 text-center">
					<p class="text-3xl font-bold text-blue-700">{act.active_subscribers}</p>
					<p class="text-sm text-blue-600 mt-1">Activos</p>
				</div>
				<div class="bg-green-50 rounded-xl p-4 text-center">
					<p class="text-3xl font-bold text-green-700">{act.in_range_subscribers}</p>
					<p class="text-sm text-green-600 mt-1">En Rango Óptimo</p>
				</div>
				<div class="rounded-xl p-4 text-center {act.critical_subscribers > 0 ? 'bg-red-50' : 'bg-gray-50'}">
					<p class="text-3xl font-bold {act.critical_subscribers > 0 ? 'text-red-700' : 'text-gray-400'}">
						{act.critical_subscribers}
					</p>
					<p class="text-sm {act.critical_subscribers > 0 ? 'text-red-600' : 'text-gray-400'} mt-1">
						Críticos
					</p>
				</div>
			</div>
			{#if act.critical_subscribers > 0}
				<div class="mt-3 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
					⚠️ Existen <strong>{act.critical_subscribers}</strong> abonados en estado crítico.
					Deben estar en <strong>0</strong> o con plan de choque previo para aprobar el acta.
				</div>
			{/if}
		</div>

		<!-- Checklist de validación -->
		<div>
			<div class="flex items-center justify-between mb-3">
				<h3 class="text-sm font-bold text-gray-500 uppercase tracking-wide">
					Matriz de Validación
				</h3>
				<span class="text-sm font-bold {allChecksPassed ? 'text-green-600' : 'text-orange-600'}">
					{passedChecks}/{totalChecks} condiciones
				</span>
			</div>
			<div class="space-y-2">
				{#each act.checklist as item}
					<div
						class="flex items-start gap-3 p-3 rounded-lg {item.passed ? 'bg-green-50 border border-green-100' : 'bg-red-50 border border-red-100'}"
					>
						<span class="text-lg mt-0.5">{item.passed ? '✅' : '❌'}</span>
						<div class="flex-1">
							<p class="text-sm font-medium {item.passed ? 'text-green-800' : 'text-red-800'}">
								{item.label}
							</p>
							{#if item.notes}
								<p class="text-xs {item.passed ? 'text-green-600' : 'text-red-600'} mt-0.5">
									{item.notes}
								</p>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Cajas NAP N2 con fotos (hipervínculos) -->
		{#if act.n2_boxes.length > 0}
			<div>
				<h3 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-3">
					Cajas NAP Secundarias ({act.n2_boxes.length})
				</h3>
				<div class="grid grid-cols-2 md:grid-cols-3 gap-3">
					{#each act.n2_boxes as box}
						<div
							class="rounded-xl border p-4 {box.transformer_alert ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-gray-50'}"
						>
							<div class="flex items-center justify-between mb-2">
								<p class="text-sm font-bold text-gray-800">{box.n2_box_id}</p>
								{#if box.transformer_alert}
									<span class="text-red-600 text-lg" title="Bajo transformador eléctrico">⚡</span>
								{/if}
							</div>
							<a
								href={box.photo_url}
								target="_blank"
								rel="noopener noreferrer"
								class="block text-xs text-blue-600 hover:text-blue-800 hover:underline mb-2"
							>
								📸 Ver foto en alta resolución ↗
							</a>
							<div class="flex items-center gap-2">
								<span
									class="text-xs px-2 py-0.5 rounded-full font-medium
										{box.ozmap_sync_status === 'CONCILIADO' ? 'bg-green-100 text-green-700' :
										box.ozmap_sync_status === 'DISCREPANCIA' ? 'bg-red-100 text-red-700' :
										'bg-yellow-100 text-yellow-700'}"
								>
									OZmap: {box.ozmap_sync_status}
								</span>
								<span class="text-xs text-gray-500">{box.total_ports} puertos</span>
							</div>
							{#if box.transformer_alert}
								<p class="text-xs text-red-600 font-bold mt-2">
									⚠️ REUBICACIÓN REQUERIDA — Bajo transformador
								</p>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/if}

		<!-- Bloque de firmas -->
		<div class="border-t pt-6">
			<h3 class="text-sm font-bold text-gray-500 uppercase tracking-wide mb-4">
				Firmas de Conformidad
			</h3>
			<div class="grid grid-cols-2 gap-6">
				<!-- Ejecutor (1CLICK) -->
				<div class="rounded-xl border-2 {act.executor_signature ? 'border-green-300 bg-green-50' : 'border-gray-200'} p-5">
					<p class="text-sm font-bold text-gray-700 mb-1">Ejecutor (1CLICK)</p>
					{#if act.executor_signature}
						<div class="text-center py-3">
							<span class="text-3xl">✅</span>
							<p class="text-sm text-green-700 font-semibold mt-1">Firmado</p>
							<p class="text-xs text-gray-500">{formatDate(act.executor_signed_at)}</p>
						</div>
					{:else if canSign}
						{#if signingRole === 'EXECUTOR'}
							<div class="space-y-2">
								<input
									bind:value={signerName}
									placeholder="Nombre del ejecutor"
									class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
								<button
									onclick={() => handleSign('EXECUTOR')}
									disabled={signingInProgress}
									class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-semibold
										hover:bg-blue-700 disabled:opacity-50"
								>
									{signingInProgress ? 'Firmando...' : 'Confirmar Firma'}
								</button>
								<button
									onclick={() => { signingRole = null; signerName = ''; }}
									class="w-full text-gray-500 py-1 text-sm hover:text-gray-700"
								>
									Cancelar
								</button>
							</div>
						{:else}
							<button
								onclick={() => { signingRole = 'EXECUTOR'; }}
								class="w-full border-2 border-dashed border-blue-400 text-blue-600 py-6 rounded-xl
									hover:bg-blue-50 text-sm font-semibold transition-colors"
							>
								🖊️ Firmar como Ejecutor
							</button>
						{/if}
					{:else}
						<div class="text-center py-6 text-gray-300">
							<p class="text-4xl">—</p>
							<p class="text-sm text-gray-400 mt-1">Pendiente de firma</p>
						</div>
					{/if}
				</div>

				<!-- Supervisor (VNET) -->
				<div class="rounded-xl border-2 {act.supervisor_signature ? 'border-green-300 bg-green-50' : 'border-gray-200'} p-5">
					<p class="text-sm font-bold text-gray-700 mb-1">Supervisor (VNET)</p>
					{#if act.supervisor_signature}
						<div class="text-center py-3">
							<span class="text-3xl">✅</span>
							<p class="text-sm text-green-700 font-semibold mt-1">Firmado</p>
							<p class="text-xs text-gray-500">{formatDate(act.supervisor_signed_at)}</p>
						</div>
					{:else if canSign}
						{#if signingRole === 'SUPERVISOR'}
							<div class="space-y-2">
								<input
									bind:value={signerName}
									placeholder="Nombre del supervisor"
									class="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
								/>
								<button
									onclick={() => handleSign('SUPERVISOR')}
									disabled={signingInProgress}
									class="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-semibold
										hover:bg-blue-700 disabled:opacity-50"
								>
									{signingInProgress ? 'Firmando...' : 'Confirmar Firma'}
								</button>
								<button
									onclick={() => { signingRole = null; signerName = ''; }}
									class="w-full text-gray-500 py-1 text-sm hover:text-gray-700"
								>
									Cancelar
								</button>
							</div>
						{:else}
							<button
								onclick={() => { signingRole = 'SUPERVISOR'; }}
								class="w-full border-2 border-dashed border-blue-400 text-blue-600 py-6 rounded-xl
									hover:bg-blue-50 text-sm font-semibold transition-colors"
							>
								🖊️ Firmar como Supervisor
							</button>
						{/if}
					{:else}
						<div class="text-center py-6 text-gray-300">
							<p class="text-4xl">—</p>
							<p class="text-sm text-gray-400 mt-1">Pendiente de firma</p>
						</div>
					{/if}
				</div>
			</div>

			{#if isFullySigned}
				<div class="mt-4 bg-green-100 border border-green-300 rounded-xl p-4 text-center">
					<p class="text-green-800 font-bold text-lg">✅ Acta completamente firmada y aprobada</p>
					<p class="text-green-600 text-sm mt-1">Aprobada el {formatDate(act.approved_at)}</p>
				</div>
			{/if}
		</div>
	</div>
</div>
