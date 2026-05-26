<script lang="ts">
	import type { AuditDashboardSummary } from '$lib/types/network-audit';

	interface Props {
		summary: AuditDashboardSummary;
		loading?: boolean;
	}

	let { summary, loading = false }: Props = $props();

	const cards = $derived([
		{
			label: 'Puertos OLT Auditados',
			value: summary.total_ports_audited,
			icon: '📡',
			color: 'blue',
			sub: null
		},
		{
			label: 'Tramos OTDR Bloqueados',
			value: summary.blocked_otdr_tramos,
			icon: '🚫',
			color: summary.blocked_otdr_tramos > 0 ? 'red' : 'green',
			sub: summary.blocked_otdr_tramos > 0 ? 'Requieren saneamiento' : 'Sin bloqueos'
		},
		{
			label: 'SFPs por Cambiar',
			value: summary.ports_with_sfp_alert,
			icon: '🔴',
			color: summary.ports_with_sfp_alert > 0 ? 'orange' : 'green',
			sub: 'Pendientes de reemplazo'
		},
		{
			label: 'Visitas Técnicas Pendientes',
			value: summary.pending_technical_visits,
			icon: '🛠️',
			color: summary.pending_technical_visits > 0 ? 'orange' : 'green',
			sub: 'Programadas / En progreso'
		},
		{
			label: 'Alertas Transformadores',
			value: summary.transformer_alerts,
			icon: '⚡',
			color: summary.transformer_alerts > 0 ? 'red' : 'green',
			sub: 'Seguridad industrial'
		},
		{
			label: 'Actas Aprobadas',
			value: summary.acts_approved,
			icon: '✅',
			color: 'green',
			sub: `${summary.acts_pending} pendientes de firma`
		}
	]);

	const colorMap: Record<string, string> = {
		blue:   'bg-blue-50 border-blue-200 text-blue-700',
		red:    'bg-red-50 border-red-200 text-red-700',
		orange: 'bg-orange-50 border-orange-200 text-orange-700',
		green:  'bg-green-50 border-green-200 text-green-700'
	};
</script>

<div class="grid grid-cols-2 md:grid-cols-3 gap-4">
	{#each cards as card}
		<div
			class="rounded-xl border p-5 transition-shadow hover:shadow-md {colorMap[card.color]}"
			class:animate-pulse={loading}
		>
			<div class="flex items-center justify-between mb-2">
				<span class="text-2xl">{card.icon}</span>
				{#if loading}
					<div class="h-8 w-12 bg-current opacity-20 rounded"></div>
				{:else}
					<span class="text-3xl font-bold">{card.value}</span>
				{/if}
			</div>
			<p class="text-sm font-semibold">{card.label}</p>
			{#if card.sub}
				<p class="text-xs opacity-70 mt-1">{card.sub}</p>
			{/if}
		</div>
	{/each}
</div>
