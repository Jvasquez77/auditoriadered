<script lang="ts">
	import type { AuditDashboardSummary } from '$lib/types/network-audit';

	interface Props {
		summary: AuditDashboardSummary;
		loading?: boolean;
	}

	let { summary, loading = false }: Props = $props();

	type Card = {
		label: string;
		value: number;
		sub: string | null;
		iconHtml: string;
		iconBg: string;
		iconColor: string;
		accentColor: string;
	};

	const cards = $derived<Card[]>([
		{
			label: 'Puertos OLT Auditados',
			value: summary.total_ports_audited,
			sub: 'Puertos evaluados',
			iconBg: 'bg-violet-100',
			iconColor: 'text-violet-600',
			accentColor: 'text-slate-900',
			iconHtml: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" /></svg>`
		},
		{
			label: 'Tramos OTDR Bloqueados',
			value: summary.blocked_otdr_tramos,
			sub: summary.blocked_otdr_tramos > 0 ? 'Requieren saneamiento' : 'Sin bloqueos activos',
			iconBg: summary.blocked_otdr_tramos > 0 ? 'bg-red-100' : 'bg-emerald-100',
			iconColor: summary.blocked_otdr_tramos > 0 ? 'text-red-600' : 'text-emerald-600',
			accentColor: summary.blocked_otdr_tramos > 0 ? 'text-red-600' : 'text-slate-900',
			iconHtml: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" /></svg>`
		},
		{
			label: 'SFPs por Cambiar',
			value: summary.ports_with_sfp_alert,
			sub: 'Pendientes de reemplazo',
			iconBg: summary.ports_with_sfp_alert > 0 ? 'bg-orange-100' : 'bg-emerald-100',
			iconColor: summary.ports_with_sfp_alert > 0 ? 'text-orange-600' : 'text-emerald-600',
			accentColor: summary.ports_with_sfp_alert > 0 ? 'text-orange-600' : 'text-slate-900',
			iconHtml: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>`
		},
		{
			label: 'Visitas Técnicas Pendientes',
			value: summary.pending_technical_visits,
			sub: 'Programadas / en progreso',
			iconBg: summary.pending_technical_visits > 0 ? 'bg-amber-100' : 'bg-emerald-100',
			iconColor: summary.pending_technical_visits > 0 ? 'text-amber-600' : 'text-emerald-600',
			accentColor: summary.pending_technical_visits > 0 ? 'text-amber-700' : 'text-slate-900',
			iconHtml: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>`
		},
		{
			label: 'Alertas Transformadores',
			value: summary.transformer_alerts,
			sub: 'Seguridad industrial',
			iconBg: summary.transformer_alerts > 0 ? 'bg-red-100' : 'bg-emerald-100',
			iconColor: summary.transformer_alerts > 0 ? 'text-red-600' : 'text-emerald-600',
			accentColor: summary.transformer_alerts > 0 ? 'text-red-600' : 'text-slate-900',
			iconHtml: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>`
		},
		{
			label: 'Actas Aprobadas',
			value: summary.acts_approved,
			sub: `${summary.acts_pending} pendientes de firma`,
			iconBg: 'bg-emerald-100',
			iconColor: 'text-emerald-600',
			accentColor: 'text-emerald-700',
			iconHtml: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>`
		}
	]);
</script>

<div class="grid grid-cols-2 md:grid-cols-3 gap-4">
	{#each cards as card}
		<div class="card p-5 flex items-center justify-between gap-4">
			<!-- Left: label + number + sub -->
			<div class="min-w-0">
				<p class="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none">{card.label}</p>
				{#if loading}
					<div class="skeleton h-8 w-16 mt-2"></div>
					<div class="skeleton h-3 w-24 mt-2"></div>
				{:else}
					<p class="text-3xl font-bold mt-1.5 leading-none {card.accentColor}">{card.value}</p>
					{#if card.sub}
						<p class="text-xs text-slate-400 mt-1.5 leading-none">{card.sub}</p>
					{/if}
				{/if}
			</div>

			<!-- Right: circular icon -->
			{#if loading}
				<div class="w-12 h-12 rounded-full skeleton shrink-0"></div>
			{:else}
				<div class="w-12 h-12 rounded-full {card.iconBg} {card.iconColor} flex items-center justify-center shrink-0">
					{@html card.iconHtml}
				</div>
			{/if}
		</div>
	{/each}
</div>
