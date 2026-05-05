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
	let playConfirm = $state<{ card: Card; origIndex: number } | null>(null)

	const playableCards = $derived(
		cards.map((c, i) => ({ card: c, origIndex: i }))
	)

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
			playConfirm = { card, origIndex }
			return
		}

		if (game.phase === 'buy' && card.types.includes('treasure')) {
			selectedIndex = null
			game.playCard(origIndex)
			return
		}

		selectedIndex = selectedIndex === origIndex ? null : origIndex
	}

	function confirmPlay() {
		if (playConfirm) {
			game.playCard(playConfirm.origIndex)
			playConfirm = null
		}
	}

	function cancelPlay() {
		playConfirm = null
	}

	function isPlayConfirmVisible() {
		return playConfirm !== null
	}

	export { confirmPlay, cancelPlay, isPlayConfirmVisible }

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
		<div class="hand-area">
			{#if playableCards.length === 0}
				<p class="empty-hand">No cards in hand</p>
			{:else}
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

{#if playConfirm}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="play-overlay" onclick={cancelPlay}>
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="play-confirm" onclick={(e) => e.stopPropagation()}>
			<div class="play-card-preview">
				<CardComponent card={playConfirm.card} />
			</div>
			<p class="play-prompt">Play <strong>{playConfirm.card.name}</strong>?</p>
			<div class="play-actions">
				<button class="btn-secondary" onclick={cancelPlay}>Cancel</button>
				<button class="btn-primary" onclick={confirmPlay}>Play</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.hand-row {
		display: flex;
		align-items: flex-end;
		padding: 2px var(--space-sm);
		padding-left: 160px;
		padding-right: 160px;
		background: rgba(0, 0, 0, 0.3);
		border-top: 1px solid var(--border);
		gap: var(--space-sm);
		min-height: 56px;
		overflow: visible;
	}

	@media (min-width: 768px) {
		.hand-row {
			min-height: 64px;
			padding: 2px var(--space-md);
			padding-left: 160px;
			padding-right: 160px;
		}
	}

	/* === Deck & Discard piles === */
	.pile {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2px;
		flex-shrink: 0;
		width: 44px;
	}

	@media (min-width: 768px) {
		.pile { width: 56px; }
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
		overflow: visible;
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
		overflow: visible;
		padding-bottom: 10px;
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
		margin-right: -20px;
		transition: transform 200ms ease;
		z-index: var(--i);
		position: relative;
	}

	.hand-card-wrapper:last-child {
		margin-right: 0;
	}

	@media (min-width: 480px) {
		.hand-card-wrapper { margin-right: -16px; }
	}

	@media (min-width: 768px) {
		.hand-card-wrapper { margin-right: -18px; }
	}

	.hand-card-wrapper :global(.card) {
		width: 100px;
		min-width: 100px;
	}

	@media (min-width: 768px) {
		.hand-card-wrapper :global(.card) {
			width: 120px;
			min-width: 120px;
		}
	}

	.hand-card-wrapper:hover {
		z-index: 50;
		transform: translateY(-30px) scale(1.5);
	}

	/* === Play confirmation overlay === */
	.play-overlay {
		position: fixed;
		inset: 0;
		z-index: 200;
		background: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		backdrop-filter: blur(3px);
	}

	.play-confirm {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-md);
		animation: playConfirmIn 180ms ease-out;
	}

	@keyframes playConfirmIn {
		from { opacity: 0; transform: scale(0.9) translateY(12px); }
		to { opacity: 1; transform: scale(1) translateY(0); }
	}

	.play-card-preview {
		transform: scale(2.4);
		transform-origin: center;
		margin-bottom: 80px;
		margin-top: 60px;
	}

	.play-card-preview :global(.card:hover) {
		transform: none !important;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5) !important;
	}

	.play-prompt {
		font-family: var(--font-heading);
		font-size: 1.1rem;
		color: var(--text);
		text-align: center;
	}

	.play-prompt strong {
		color: var(--accent);
	}

	.play-actions {
		display: flex;
		gap: var(--space-sm);
	}

	.play-actions button {
		min-width: 80px;
	}
</style>
