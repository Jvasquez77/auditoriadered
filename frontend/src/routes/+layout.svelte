<script lang="ts">
	import '../app.css';
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';

	interface Props { children: Snippet }
	let { children }: Props = $props();

	let expanded = $state(true);

	const isNetworkAudit = $derived($page.url.pathname.startsWith('/network-audit'));

	type NavItem = { href: string; label: string; exact: boolean; icon: string };

	const navItems: NavItem[] = [
		{
			href: '/network-audit',
			label: 'Dashboard',
			exact: true,
			icon: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>`
		},
		{
			href: '/network-audit/ingest',
			label: 'Ingesta',
			exact: false,
			icon: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" /></svg>`
		},
		{
			href: '/network-audit/field',
			label: 'Campo',
			exact: false,
			icon: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" /></svg>`
		},
		{
			href: '/network-audit/certification',
			label: 'Actas',
			exact: false,
			icon: `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>`
		}
	];

	function active(href: string, exact: boolean): boolean {
		const p = $page.url.pathname;
		return exact ? p === href : (p.startsWith(href) && href !== '/network-audit');
	}

	const moduleName = $derived.by(() => {
		const p = $page.url.pathname;
		if (p.includes('/ingest'))        return 'Ingesta de Datos';
		if (p.includes('/field'))         return 'Mediciones en Campo';
		if (p.includes('/certification')) return 'Actas de Entrega';
		return 'Dashboard ODN';
	});
</script>

{#if isNetworkAudit}
	<div class="flex min-h-screen bg-slate-50">

		<!-- ── Sidebar ── -->
		<aside
			class="fixed top-0 left-0 h-full z-30 bg-slate-800 flex flex-col transition-all duration-200 ease-in-out"
			class:w-16={!expanded}
			class:w-56={expanded}
		>
			<!-- Logo / brand -->
			<div class="h-16 flex items-center border-b border-slate-700 overflow-hidden px-4 shrink-0">
				{#if expanded}
					<div class="flex items-center gap-2.5">
						<div class="w-7 h-7 rounded-lg bg-violet-600 flex items-center justify-center shrink-0">
							<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
								<path stroke-linecap="round" stroke-linejoin="round" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
							</svg>
						</div>
						<span class="text-white font-bold text-sm leading-tight whitespace-nowrap">AuditoríaRed</span>
					</div>
				{:else}
					<div class="w-7 h-7 rounded-lg bg-violet-600 flex items-center justify-center mx-auto">
						<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
						</svg>
					</div>
				{/if}
			</div>

			<!-- Nav items -->
			<nav class="flex-1 py-4 px-2 space-y-0.5 overflow-hidden">
				{#each navItems as item}
					{@const isActive = active(item.href, item.exact) || ($page.url.pathname === '/network-audit' && item.exact)}
					<a
						href={item.href}
						title={!expanded ? item.label : undefined}
						class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors relative group"
						class:text-white={isActive}
						class:bg-slate-700={isActive}
					>
						{#if isActive}
							<span class="absolute left-0 top-1.5 bottom-1.5 w-0.5 bg-violet-500 rounded-r-full"></span>
						{/if}
						<span class="shrink-0 {isActive ? 'text-violet-400' : ''}">
							{@html item.icon}
						</span>
						{#if expanded}
							<span class="text-sm font-medium whitespace-nowrap">{item.label}</span>
						{/if}
					</a>
				{/each}
			</nav>

			<!-- Toggle button -->
			<div class="p-3 border-t border-slate-700 shrink-0">
				<button
					onclick={() => (expanded = !expanded)}
					class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
					title={expanded ? 'Colapsar menú' : 'Expandir menú'}
				>
					{#if expanded}
						<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
						</svg>
						<span class="text-xs font-medium whitespace-nowrap">Colapsar</span>
					{:else}
						<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
						</svg>
					{/if}
				</button>
			</div>
		</aside>

		<!-- ── Content area ── -->
		<div
			class="flex-1 flex flex-col min-w-0 transition-all duration-200 ease-in-out"
			class:ml-16={!expanded}
			class:ml-56={expanded}
		>
			<!-- Top navbar -->
			<header class="sticky top-0 z-20 h-16 bg-white border-b border-slate-200 flex items-center px-6 gap-4 shrink-0">
				<h1 class="text-sm font-semibold text-slate-700 whitespace-nowrap">{moduleName}</h1>

				<!-- Search -->
				<div class="flex-1 max-w-sm mx-auto hidden md:block">
					<div class="relative">
						<svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
						<input
							type="search"
							placeholder="Buscar tramos, cajas, puertos…"
							class="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent transition"
						/>
					</div>
				</div>

				<!-- Right: avatar -->
				<div class="ml-auto flex items-center gap-3">
					<button class="w-8 h-8 rounded-lg bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 transition-colors" title="Notificaciones">
						<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
						</svg>
					</button>
					<div class="h-6 w-px bg-slate-200"></div>
					<div class="flex items-center gap-2.5">
						<div class="w-8 h-8 rounded-full bg-violet-100 flex items-center justify-center shrink-0">
							<span class="text-violet-700 text-xs font-bold">JV</span>
						</div>
						<div class="hidden sm:block">
							<p class="text-xs font-semibold text-slate-800 leading-none">Julio Vásquez</p>
							<p class="text-xs text-slate-400 leading-none mt-0.5">Supervisor Técnico</p>
						</div>
					</div>
				</div>
			</header>

			<!-- Page content -->
			<main class="flex-1 p-6">
				{@render children()}
			</main>
		</div>
	</div>
{:else}
	<main>
		{@render children()}
	</main>
{/if}
