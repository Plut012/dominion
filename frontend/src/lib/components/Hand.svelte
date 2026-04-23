<script lang="ts">
	import type { Card } from '$lib/game/types'
	import { game } from '$lib/stores/game.svelte'
	import CardComponent from './Card.svelte'

	interface Props {
		cards: Card[]
		canPlay: boolean
		deckCount: number
		discardCount: number
		discardTop: Card | null
		lastGained: Card | null
	}

	let { cards, canPlay, deckCount, discardCount, discardTop, lastGained }: Props = $props()

	let selectedIndex = $state<number | null>(null)
	let gainAnimCard = $state<Card | null>(null)

	// Split hand into playable cards and victory/curse cards (flat on table)
	const playableCards = $derived(
		cards.map((c, i) => ({ card: c, origIndex: i }))
			.filter(({ card }) => !isVictoryOnly(card))
	)
	const tableCards = $derived(
		cards.map((c, i) => ({ card: c, origIndex: i }))
			.filter(({ card }) => isVictoryOnly(card))
	)

	function isVictoryOnly(card: Card): boolean {
		// Pure victory or curse cards go on the table
		// Action-Victory (like Gardens) stays in hand since it's playable
		const types = card.types
		if (types.includes('curse')) return true
		if (types.includes('victory') && !types.includes('action')) return true
		return false
	}

	$effect(() => {
		if (lastGained) {
			gainAnimCard = lastGained
			setTimeout(() => { gainAnimCard = null }, 600)
		}
	})

	function handleCardClick(card: Card, origIndex: number) {
		if (!canPlay) return

		if (
			game.phase === 'action' &&
			card.types.includes('action') &&
			game.turnState !== null &&
			game.turnState.actions > 0
		) {
			selectedIndex = null
			game.playCard(origIndex)
			return
		}

		if (game.phase === 'buy' && card.types.includes('treasure')) {
			selectedIndex = null
			game.playCard(origIndex)
			return
		}

		selectedIndex = selectedIndex === origIndex ? null : origIndex
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

<div class="hand-row">
	<!-- Deck (left, face down) -->
	<div class="pile deck-pile">
		<div class="pile-stack">
			{#if deckCount > 0}
				<div class="card-back"></div>
			{:else}
				<div class="pile-empty"></div>
			{/if}
		</div>
		<span class="pile-label">{deckCount}</span>
	</div>

	<!-- Hand (center) -->
	<div class="hand-center">
		<!-- Victory/curse cards flat on the table -->
		{#if tableCards.length > 0}
			<div class="table-cards">
				{#each tableCards as { card, origIndex } (origIndex)}
					<div class="table-card">
						<CardComponent {card} />
					</div>
				{/each}
			</div>
		{/if}

		<!-- Playable cards in hand -->
		<div class="hand-area">
			{#if playableCards.length === 0 && tableCards.length === 0}
				<p class="empty-hand">No cards in hand</p>
			{:else if playableCards.length > 0}
				<div class="hand-scroll">
					<div class="hand-cards">
						{#each playableCards as { card, origIndex }, i (origIndex)}
							<div class="hand-card-wrapper" style="--i: {i}">
								<CardComponent
									{card}
									playable={isPlayable(card)}
									selected={selectedIndex === origIndex}
									onclick={() => handleCardClick(card, origIndex)}
								/>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Discard (right, face up) -->
	<div class="pile discard-pile">
		<div class="pile-stack">
			{#if discardTop}
				<div class="discard-top">
					<CardComponent card={discardTop} />
				</div>
			{:else}
				<div class="pile-empty"></div>
			{/if}
			{#if gainAnimCard}
				<div class="gain-anim">
					<CardComponent card={gainAnimCard} />
				</div>
			{/if}
		</div>
		<span class="pile-label">{discardCount}</span>
	</div>
</div>

<style>
	.hand-row {
		display: flex;
		align-items: flex-end;
		padding: var(--space-sm);
		background: rgba(0, 0, 0, 0.3);
		border-top: 1px solid var(--border);
		gap: var(--space-sm);
		min-height: 120px;
	}

	@media (min-width: 768px) {
		.hand-row {
			min-height: 160px;
			padding: var(--space-md);
		}
	}

	/* === Deck & Discard piles === */
	.pile {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		flex-shrink: 0;
		width: 60px;
	}

	@media (min-width: 768px) {
		.pile { width: 80px; }
	}

	.pile-stack {
		position: relative;
		width: 100%;
		aspect-ratio: 5 / 7;
	}

	.pile-label {
		font-size: 0.65rem;
		color: var(--text-muted);
		font-family: var(--font-heading);
		letter-spacing: 0.05em;
	}

	.card-back {
		width: 100%;
		height: 100%;
		border-radius: var(--radius-card);
		background: linear-gradient(135deg, #2a1f3d 0%, #1a1428 40%, #2a1f3d 100%);
		border: 1px solid rgba(201, 168, 76, 0.3);
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
		position: relative;
		overflow: hidden;
	}

	.card-back::after {
		content: '';
		position: absolute;
		inset: 6px;
		border: 1px solid rgba(201, 168, 76, 0.15);
		border-radius: calc(var(--radius-card) - 4px);
	}

	.pile-empty {
		width: 100%;
		height: 100%;
		border-radius: var(--radius-card);
		border: 1px dashed var(--border);
		opacity: 0.3;
	}

	.discard-top {
		position: absolute;
		inset: 0;
		transform: scale(0.95);
		transform-origin: center;
	}

	.discard-top :global(.card) {
		width: 100% !important;
		min-width: unset !important;
	}

	/* === Gain animation === */
	.gain-anim {
		position: absolute;
		inset: 0;
		transform: scale(0.95);
		transform-origin: center;
		animation: gainDrop 500ms ease-out forwards;
		z-index: 10;
	}

	.gain-anim :global(.card) {
		width: 100% !important;
		min-width: unset !important;
	}

	@keyframes gainDrop {
		0% {
			opacity: 0;
			transform: scale(0.6) translateY(-60px);
		}
		60% {
			opacity: 1;
			transform: scale(1) translateY(4px);
		}
		100% {
			opacity: 1;
			transform: scale(0.95) translateY(0);
		}
	}

	/* === Center column === */
	.hand-center {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		min-width: 0;
		gap: 4px;
	}

	/* === Table cards (victory/curse, flat) === */
	.table-cards {
		display: flex;
		gap: 2px;
		justify-content: center;
	}

	.table-card {
		transform: scale(0.45) perspective(200px) rotateX(30deg);
		transform-origin: bottom center;
		opacity: 0.55;
		transition: opacity var(--transition-fast);
		margin: 0 -16px;
	}

	.table-card:hover {
		opacity: 0.8;
	}

	/* === Hand === */
	.hand-area {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		width: 100%;
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
		padding-bottom: 10px;
		scrollbar-width: thin;
		scrollbar-color: var(--accent-dim) transparent;
	}

	.hand-cards {
		display: flex;
		align-items: flex-end;
		justify-content: center;
		min-width: min-content;
		margin: 0 auto;
		padding: 0 var(--space-sm);
	}

	.hand-card-wrapper {
		margin-right: -22px;
		transition: transform var(--transition-base);
		z-index: var(--i);
		position: relative;
	}

	.hand-card-wrapper:last-child {
		margin-right: 0;
	}

	@media (min-width: 480px) {
		.hand-card-wrapper { margin-right: -18px; }
	}

	@media (min-width: 768px) {
		.hand-card-wrapper { margin-right: -20px; }
	}

	.hand-card-wrapper:hover {
		z-index: 50;
		transform: translateY(-8px);
	}
</style>
