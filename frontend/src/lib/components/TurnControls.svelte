<script lang="ts">
	import { game } from '$lib/stores/game.svelte'

	const phase = $derived(game.phase)
	const turnState = $derived(game.turnState)
	const isMyTurn = $derived(game.isMyTurn)

	function endPhase() {
		game.endPhase()
	}

	const phaseLabel = $derived(
		phase === 'action' ? 'Action Phase'
		: phase === 'buy' ? 'Buy Phase'
		: phase === 'cleanup' ? 'Cleanup'
		: 'Waiting...'
	)
</script>

<div class="turn-controls" class:active={isMyTurn}>
	<!-- Phase indicator -->
	<div class="phase-badge" data-phase={phase}>
		{phaseLabel}
	</div>

	<!-- Turn resources -->
	{#if turnState}
		<div class="resources">
			<span class="resource actions" title="Actions remaining">
				<span class="resource-icon">⚡</span>
				<span class="resource-value">{turnState.actions}</span>
			</span>
			<span class="resource buys" title="Buys remaining">
				<span class="resource-icon">🛒</span>
				<span class="resource-value">{turnState.buys}</span>
			</span>
			<span class="resource coins" title="Coins available">
				<span class="resource-icon">🪙</span>
				<span class="resource-value">{turnState.coins}</span>
			</span>
		</div>
	{/if}

	<!-- Action buttons -->
	<div class="controls-buttons">
		{#if isMyTurn && phase === 'action'}
			<button
				class="btn-secondary control-btn"
				onclick={endPhase}
			>
				End Actions
			</button>
		{:else if isMyTurn && phase === 'buy'}
			<button
				class="btn-primary control-btn"
				onclick={endPhase}
			>
				End Turn
			</button>
		{:else}
			<span class="waiting-label">
				{isMyTurn ? '' : "Opponent's turn"}
			</span>
		{/if}
	</div>
</div>

<style>
	.turn-controls {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		padding: var(--space-sm) var(--space-md);
		background: var(--bg-surface);
		border-top: 1px solid var(--border);
		flex-wrap: wrap;
	}

	.turn-controls.active {
		border-top-color: var(--accent-dim);
	}

	/* Phase badge */
	.phase-badge {
		font-family: var(--font-heading);
		font-size: 0.7rem;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		padding: 3px 8px;
		border-radius: 20px;
		border: 1px solid;
		white-space: nowrap;
	}

	.phase-badge[data-phase="action"] {
		color: var(--type-action);
		border-color: var(--type-action);
		background: rgba(184, 92, 56, 0.1);
	}

	.phase-badge[data-phase="buy"] {
		color: var(--accent);
		border-color: var(--accent-dim);
		background: rgba(201, 168, 76, 0.1);
	}

	.phase-badge[data-phase="cleanup"] {
		color: var(--text-muted);
		border-color: var(--border);
		background: transparent;
	}

	.phase-badge[data-phase="waiting"] {
		color: var(--text-muted);
		border-color: var(--border);
		background: transparent;
	}

	/* Resources */
	.resources {
		display: flex;
		gap: var(--space-sm);
		align-items: center;
	}

	.resource {
		display: flex;
		align-items: center;
		gap: 3px;
		font-size: 0.8rem;
		color: var(--text-muted);
		white-space: nowrap;
	}

	.resource.coins .resource-value {
		color: var(--accent);
		font-weight: 700;
	}

	.resource.actions .resource-value {
		color: var(--type-action);
		font-weight: 700;
	}

	.resource-icon {
		font-size: 0.75rem;
	}

	.resource-value {
		font-size: 0.85rem;
		font-weight: 600;
		min-width: 12px;
	}

	/* Buttons */
	.controls-buttons {
		margin-left: auto;
	}

	.control-btn {
		font-size: 0.8rem;
		padding: 6px 14px;
	}

	.waiting-label {
		font-size: 0.75rem;
		color: var(--text-muted);
		font-style: italic;
	}
</style>
