<script lang="ts">
	import type { Snippet } from 'svelte';
	import { page } from '$app/stores';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	const isNetworkAudit = $derived($page.url.pathname.startsWith('/network-audit'));
</script>

{#if isNetworkAudit}
	<!-- Sidebar de navegación para el módulo de auditoría -->
	<div class="flex min-h-screen">
		<aside class="w-16 bg-slate-900 flex flex-col items-center py-6 gap-4 fixed h-full z-10">
			<a href="/network-audit" title="Dashboard" class="text-2xl hover:scale-110 transition-transform">
				🏠
			</a>
			<div class="w-8 border-t border-slate-700"></div>
			<a href="/network-audit/ingest" title="Ingesta" class="text-2xl hover:scale-110 transition-transform">
				📥
			</a>
			<a href="/network-audit/field" title="Campo" class="text-2xl hover:scale-110 transition-transform">
				📶
			</a>
			<a href="/network-audit/certification" title="Actas" class="text-2xl hover:scale-110 transition-transform">
				📋
			</a>
		</aside>
		<main class="flex-1 ml-16">
			{@render children()}
		</main>
	</div>
{:else}
	<main>
		{@render children()}
	</main>
{/if}
