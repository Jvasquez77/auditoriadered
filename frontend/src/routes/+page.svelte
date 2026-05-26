<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	onMount(() => {
		goto('/network-audit');
	});
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
	<div class="text-center">
		<div class="text-5xl mb-4">🌐</div>
		<p class="text-gray-500">Redirigiendo al módulo de auditoría...</p>
	</div>
</div>
