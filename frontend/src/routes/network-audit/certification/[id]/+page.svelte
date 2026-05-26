<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import DigitalActView from '$lib/components/network-audit/DigitalActView.svelte';
	import type { DeliveryActRead, DeliveryActSign } from '$lib/types/network-audit';

	// Svelte 5 runes
	let act = $state<DeliveryActRead | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let signError = $state<string | null>(null);
	let signSuccess = $state<string | null>(null);

	const actId = $derived($page.params.id);

	async function loadAct() {
		loading = true;
		error = null;
		try {
			const res = await fetch(`/api/v1/reports/acts/${actId}`);
			if (!res.ok) {
				const body = await res.json();
				throw new Error(body.detail ?? 'Error al cargar el acta');
			}
			act = await res.json();
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	async function handleSign(payload: DeliveryActSign) {
		signError = null;
		signSuccess = null;
		try {
			const res = await fetch(`/api/v1/reports/acts/${actId}/sign`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});
			if (!res.ok) {
				const body = await res.json();
				throw new Error(body.detail ?? 'Error al firmar el acta');
			}
			act = await res.json();
			const roleLabel = payload.role === 'EXECUTOR' ? 'Ejecutor' : 'Supervisor';
			signSuccess = `✅ Acta firmada correctamente por ${payload.signer_name} (${roleLabel})`;
		} catch (e) {
			signError = e instanceof Error ? e.message : String(e);
		}
	}

	onMount(loadAct);
</script>

<svelte:head>
	<title>Acta de Entrega — Auditoría ODN</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 p-6">
	<div class="max-w-4xl mx-auto space-y-5">

		<!-- Navegación -->
		<div class="flex items-center gap-4">
			<a href="/network-audit/certification" class="text-blue-600 hover:text-blue-800 text-sm">
				← Lista de Actas
			</a>
			<div class="flex-1">
				<h1 class="text-xl font-bold text-gray-900">Acta de Entrega Técnica ODN</h1>
				<p class="text-xs text-gray-500 font-mono">ID: {actId}</p>
			</div>
			<button
				onclick={loadAct}
				class="text-sm bg-white border border-gray-200 px-4 py-2 rounded-xl hover:bg-gray-50"
			>
				🔄 Recargar
			</button>
		</div>

		{#if signSuccess}
			<div class="bg-green-50 border border-green-300 rounded-xl p-4 text-green-800 text-sm">
				{signSuccess}
			</div>
		{/if}
		{#if signError}
			<div class="bg-red-50 border border-red-300 rounded-xl p-4 text-red-800 text-sm">
				<strong>Error al firmar:</strong> {signError}
			</div>
		{/if}

		{#if loading}
			<div class="bg-white rounded-2xl border border-gray-200 p-12 text-center">
				<div class="text-4xl mb-4 animate-spin">⏳</div>
				<p class="text-gray-500">Cargando acta...</p>
			</div>
		{:else if error}
			<div class="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
				<div class="text-4xl mb-4">❌</div>
				<p class="text-red-700 font-bold">{error}</p>
				<button
					onclick={loadAct}
					class="mt-4 bg-red-600 text-white px-6 py-2.5 rounded-xl hover:bg-red-700 text-sm font-semibold"
				>
					Reintentar
				</button>
			</div>
		{:else if act}
			<DigitalActView {act} onSign={handleSign} />
		{/if}
	</div>
</div>
