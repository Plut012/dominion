<script lang="ts">
	import type { Card, OpponentView } from '$lib/game/types'
	import CardComponent from './Card.svelte'

	interface Props {
		inPlay: Card[]
		opponents?: OpponentView[]
	}

	let { inPlay, opponents = [] }: Props = $props()
</script>

<div class="play-area">
	{#if inPlay.length > 0}
		<div class="in-play-cards">
			{#each inPlay as card, i (i)}
				<div class="played-card">
					<CardComponent {card} />
				</div>
			{/each}
		</div>
	{:else}
		<p class="empty-label">No cards in play</p>
	{/if}
</div>

<style>
	.play-area {
		display: flex;
		align-items: center;
		padding: var(--space-xs) var(--space-md);
		min-height: 50px;
		background: rgba(0, 0, 0, 0.1);
	}

	.in-play-cards {
		display: flex;
		gap: 4px;
		overflow-x: auto;
	}

	.played-card {
		animation: slideIn 150ms ease-out;
		transform: scale(0.7);
		transform-origin: center;
	}

	@keyframes slideIn {
		from { opacity: 0; transform: scale(0.5) translateY(-8px); }
		to { opacity: 1; transform: scale(0.7) translateY(0); }
	}

	.empty-label {
		color: var(--text-muted);
		font-size: 0.7rem;
		font-style: italic;
		width: 100%;
		text-align: center;
	}
</style>
