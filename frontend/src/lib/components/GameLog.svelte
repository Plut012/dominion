<script lang="ts">
	import { tick } from 'svelte'

	interface Props {
		entries: string[]
	}

	let { entries }: Props = $props()

	let scrollEl = $state<HTMLElement | null>(null)

	// Auto-scroll to bottom whenever entries change
	$effect(() => {
		// Access entries to create a dependency
		void entries.length
		tick().then(() => {
			if (scrollEl) {
				scrollEl.scrollTop = scrollEl.scrollHeight
			}
		})
	})
</script>

<div class="game-log">
	<div class="log-header">Log</div>
	<div class="log-scroll" bind:this={scrollEl}>
		{#if entries.length === 0}
			<p class="log-empty">Game events will appear here…</p>
		{:else}
			{#each entries as entry, i (i)}
				<p class="log-entry">{entry}</p>
			{/each}
		{/if}
	</div>
</div>

<style>
	.game-log {
		display: flex;
		flex-direction: column;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid var(--border);
		border-radius: var(--radius-sm);
		overflow: hidden;
		max-height: 160px;
	}

	@media (min-width: 768px) {
		.game-log {
			max-height: 200px;
		}
	}

	.log-header {
		font-size: 0.6rem;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: var(--text-muted);
		padding: 4px var(--space-sm);
		border-bottom: 1px solid var(--border);
		background: rgba(0, 0, 0, 0.3);
		flex-shrink: 0;
	}

	.log-scroll {
		overflow-y: auto;
		flex: 1;
		padding: var(--space-xs) var(--space-sm);
		scrollbar-width: thin;
		scrollbar-color: var(--accent-dim) transparent;
	}

	.log-empty {
		color: var(--text-muted);
		font-size: 0.72rem;
		font-style: italic;
		padding: 4px 0;
	}

	.log-entry {
		font-size: 0.72rem;
		color: var(--text);
		line-height: 1.5;
		padding: 1px 0;
		border-bottom: 1px solid rgba(255, 255, 255, 0.04);
	}

	.log-entry:last-child {
		border-bottom: none;
		color: var(--accent);
	}
</style>
