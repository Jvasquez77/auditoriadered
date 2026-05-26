<script lang="ts">
	import { POWER_THRESHOLDS } from '$lib/types/network-audit';

	interface Props {
		n1MangaId?: string;
		odfPortId?: string;
		onSubmit?: (data: OtdrFormData) => void | Promise<void>;
	}

	export interface OtdrFormData {
		olt_port_id: string;
		n1_manga_id: string;
		odf_port_id: string;
		otdr_total_distance_m: number;
		otdr_total_loss_db: number;
		otdr_max_fusion_loss_db: number;
		window_1310_loss_db?: number;
		window_1550_loss_db?: number;
		photo_file: File | null;
	}

	let { n1MangaId = '', odfPortId = '', onSubmit }: Props = $props();

	// Svelte 5 runes
	let form = $state<OtdrFormData>({
		olt_port_id: '',
		n1_manga_id: n1MangaId,
		odf_port_id: odfPortId,
		otdr_total_distance_m: 0,
		otdr_total_loss_db: 0,
		otdr_max_fusion_loss_db: 0,
		window_1310_loss_db: undefined,
		window_1550_loss_db: undefined,
		photo_file: null
	});

	let submitting = $state(false);
	let dragOver = $state(false);
	let photoPreview = $state<string | null>(null);

	const fusionAlert = $derived(
		form.otdr_max_fusion_loss_db > POWER_THRESHOLDS.OTDR_MAX_FUSION_LOSS_DB
	);

	function handleFileDrop(e: DragEvent) {
		e.preventDefault();
		dragOver = false;
		const file = e.dataTransfer?.files[0];
		if (file && file.type.startsWith('image/')) {
			form.photo_file = file;
			photoPreview = URL.createObjectURL(file);
		}
	}

	function handleFileInput(e: Event) {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) {
			form.photo_file = file;
			photoPreview = URL.createObjectURL(file);
		}
	}

	async function handleSubmit(e: SubmitEvent) {
		e.preventDefault();
		if (submitting) return;
		submitting = true;
		try {
			await onSubmit?.(form);
		} finally {
			submitting = false;
		}
	}
</script>

<div class="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 space-y-6">
	<div class="flex items-center gap-3">
		<span class="text-2xl">📊</span>
		<div>
			<h2 class="text-lg font-bold text-gray-800">Carga de Reflectometría OTDR</h2>
			<p class="text-sm text-gray-500">Ingesta C — ODF Nodo → Manga Primaria N1</p>
		</div>
	</div>

	{#if fusionAlert}
		<div class="bg-red-50 border border-red-300 rounded-lg p-4 flex items-start gap-3">
			<span class="text-red-600 text-xl">⛔</span>
			<div>
				<p class="font-bold text-red-700">COMPUERTA BLOQUEADA</p>
				<p class="text-sm text-red-600">
					Pérdida por fusión <strong>{form.otdr_max_fusion_loss_db} dB</strong> supera el umbral
					de <strong>{POWER_THRESHOLDS.OTDR_MAX_FUSION_LOSS_DB} dB</strong>.
					No se podrán crear órdenes de trabajo para este tramo hasta que sea saneado.
				</p>
			</div>
		</div>
	{/if}

	<form onsubmit={handleSubmit} class="space-y-5">
		<div class="grid grid-cols-2 gap-4">
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">ID Puerto OLT *</label>
				<input
					bind:value={form.olt_port_id}
					required
					class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
					placeholder="UUID del puerto"
				/>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">ID Manga N1 *</label>
				<input
					bind:value={form.n1_manga_id}
					required
					class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
					placeholder="ej: N1-TIG-001"
				/>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Puerto ODF *</label>
				<input
					bind:value={form.odf_port_id}
					required
					class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
					placeholder="ej: ODF-A-01"
				/>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Distancia total (m) *</label>
				<input
					type="number"
					step="0.01"
					bind:value={form.otdr_total_distance_m}
					required
					min="0"
					class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
				/>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Pérdida total (dB) *</label>
				<input
					type="number"
					step="0.01"
					bind:value={form.otdr_total_loss_db}
					required
					class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
				/>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">
					Pérdida máx. por fusión (dB) *
				</label>
				<input
					type="number"
					step="0.001"
					bind:value={form.otdr_max_fusion_loss_db}
					required
					class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:outline-none
						{fusionAlert ? 'border-red-500 focus:ring-red-500 bg-red-50' : 'border-gray-300 focus:ring-blue-500'}"
				/>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Pérdida 1310 nm (dB)</label>
				<input
					type="number"
					step="0.01"
					bind:value={form.window_1310_loss_db}
					class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
				/>
			</div>
			<div>
				<label class="block text-sm font-medium text-gray-700 mb-1">Pérdida 1550 nm (dB)</label>
				<input
					type="number"
					step="0.01"
					bind:value={form.window_1550_loss_db}
					class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
				/>
			</div>
		</div>

		<!-- Dropzone de foto N1 -->
		<div>
			<label class="block text-sm font-medium text-gray-700 mb-2">Fotografía Manga N1 *</label>
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
				role="button"
				tabindex="0"
				class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors
					{dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'}"
				ondragover={(e) => { e.preventDefault(); dragOver = true; }}
				ondragleave={() => { dragOver = false; }}
				ondrop={handleFileDrop}
				onkeydown={(e) => e.key === 'Enter' && document.getElementById('photo-input')?.click()}
				onclick={() => document.getElementById('photo-input')?.click()}
			>
				{#if photoPreview}
					<img src={photoPreview} alt="Vista previa manga N1" class="h-32 mx-auto rounded-lg object-cover" />
					<p class="text-sm text-gray-500 mt-2">{form.photo_file?.name}</p>
				{:else}
					<div class="text-4xl mb-2">📸</div>
					<p class="text-sm text-gray-500">Arrastrar foto o hacer clic para seleccionar</p>
					<p class="text-xs text-gray-400">PNG, JPG — máx. 10 MB</p>
				{/if}
			</div>
			<input
				id="photo-input"
				type="file"
				accept="image/*"
				class="hidden"
				onchange={handleFileInput}
			/>
		</div>

		<button
			type="submit"
			disabled={submitting || !form.photo_file}
			class="w-full bg-blue-600 text-white font-semibold py-3 rounded-xl hover:bg-blue-700
				disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
		>
			{submitting ? 'Enviando...' : 'Registrar Datos OTDR'}
		</button>
	</form>
</div>
