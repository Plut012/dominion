<script lang="ts">
	import type { Card } from '$lib/game/types'
	import { game } from '$lib/stores/game'
	import CardComponent from './Card.svelte'

	interface Props {
		cards: Card[]
		canPlay: boolean
	}

	let { cards, canPlay }: Props = $props()

	let selectedIndex = $state<number | null>(null)

	function handleCardClick(card: Card) {
		if (!canPlay) return
		const index = cards.indexOf(card)
		if (index === -1) return

		// Action cards: play on click when in action phase
		if (
			game.phase === 'action' &&
			card.types.includes('action') &&
			game.turnState !== null &&
			game.turnState.actions > 0
		) {
			selectedIndex = null
			game.playCard(index)
			return
		}

		// Treasure cards: can be played in buy phase
		if (game.phase === 'buy' && card.types.includes('treasure')) {
			selectedIndex = null
			game.playCard(index)
			return
		}

		// Otherwise just select for visual feedback
		selectedIndex = selectedIndex === index ? null : index
	}

	function isPlayable(card: Card): boolean {
		if (!canPlay) return false
		if (game.phase === 'action' && card.types.includes('action')) {
			return (game.turnState?.actions ?? 0) > 0
		}
		if (game.phase === 'buy' && card.types.includes('treasure')) {
			return true
		}
		return false
	}
</script>

<div class="hand-area">
	{#if cards.length === 0}
		<p class="empty-hand">No cards in hand</p>
	{:else}
		<div class="hand-scroll">
			<div class="hand-cards" style="--card-count: {cards.length}">
				{#each cards as card, i (i)}
					<div class="hand-card-wrapper" style="--i: {i}">
						<CardComponent
							{card}
							playable={isPlayable(card)}
							selected={selectedIndex === i}
							onclick={handleCardClick}
						/>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.hand-area {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		padding: var(--space-sm) var(--space-sm) var(--space-sm);
		background: rgba(0, 0, 0, 0.3);
		border-top: 1px solid var(--border);
		min-height: 120px;
	}

	@media (min-width: 768px) {
		.hand-area {
			min-height: 160px;
			padding: var(--space-md);
		}
	}

	.empty-hand {
		color: var(--text-muted);
		font-size: 0.875rem;
		font-style: italic;
	}

	.hand-scroll {
		width: 100%;
		overflow-x: auto;
		overflow-y: visible;
		/* Extra bottom padding so lifted cards don't clip */
		padding-bottom: 10px;
		/* Hide scrollbar on desktop, keep usable on mobile */
		scrollbar-width: thin;
		scrollbar-color: var(--accent-dim) transparent;
	}

	.hand-cards {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		/* Negative margin creates overlap */
		gap: 0;
		/* Ensure at least a minimum width so centering works */
		min-width: min-content;
		/* Center within scroll container */
		margin: 0 auto;
		padding: 0 var(--space-sm);
	}

	.hand-card-wrapper {
		/* Each card overlaps the previous by ~28px on mobile */
		margin-right: -22px;
		transition: transform var(--transition-base);
		/* Later cards on top */
		z-index: var(--i);
		position: relative;
	}

	.hand-card-wrapper:last-child {
		margin-right: 0;
	}

	/* Spread cards slightly when few */
	@media (min-width: 480px) {
		.hand-card-wrapper {
			margin-right: -18px;
		}
	}

	@media (min-width: 768px) {
		.hand-card-wrapper {
			margin-right: -20px;
		}
	}

	/* Subtle fan: alternate slight rotation for multi-card hands */
	.hand-card-wrapper:hover {
		z-index: 50;
		transform: translateY(-8px);
	}
</style>
