<script lang="ts">
	import type { Card, SupplyPile } from '$lib/game/types'
	import CardComponent from './Card.svelte'

	interface Props {
		supply: Record<string, SupplyPile>
		canBuy: boolean
		coins: number
		onCardClick?: (card: Card, pile: SupplyPile) => void
	}

	let { supply, canBuy, coins, onCardClick }: Props = $props()

	const TREASURE_IDS = ['copper', 'silver', 'gold']
	const VICTORY_IDS = ['estate', 'duchy', 'province']

	const treasurePiles = $derived(
		TREASURE_IDS.map(id => [id, supply[id]] as [string, SupplyPile]).filter(([, p]) => p)
	)

	const victoryPiles = $derived(
		VICTORY_IDS.map(id => [id, supply[id]] as [string, SupplyPile]).filter(([, p]) => p)
	)

	const HIDDEN_IDS = ['curse']

	const kingdomPiles = $derived(
		Object.entries(supply).filter(([id]) =>
			!TREASURE_IDS.includes(id) && !VICTORY_IDS.includes(id) && !HIDDEN_IDS.includes(id)
		)
	)

	function handleClick(pile: SupplyPile) {
		if (onCardClick) {
			onCardClick(pile.card, pile)
		}
	}

	// Hover preview
	let hoverCard = $state<Card | null>(null)
	let hoverPos = $state<{ x: number; y: number }>({ x: 0, y: 0 })

	function onPileEnter(card: Card, e: MouseEvent) {
		hoverCard = card
		hoverPos = { x: e.clientX, y: e.clientY }
	}

	function onPileMove(e: MouseEvent) {
		hoverPos = { x: e.clientX, y: e.clientY }
	}

	function onPileLeave() {
		hoverCard = null
	}

	// Keep preview on-screen
	const previewStyle = $derived(() => {
		const pw = 200, ph = 280
		let x = hoverPos.x + 16
		let y = hoverPos.y - ph / 2
		if (typeof window !== 'undefined') {
			if (x + pw > window.innerWidth) x = hoverPos.x - pw - 16
			if (y < 8) y = 8
			if (y + ph > window.innerHeight - 8) y = window.innerHeight - ph - 8
		}
		return `left:${x}px;top:${y}px`
	})
</script>

<div class="supply-layout">
	<!-- Left column: Treasures -->
	<div class="side-column">
		<h3 class="side-label">Treasury</h3>
		{#each treasurePiles as [id, pile] (id)}
			<div
				class="pile-wrapper"
				class:affordable={coins >= pile.card.cost && pile.count > 0}
				class:empty={pile.count === 0}
				onmouseenter={(e) => onPileEnter(pile.card, e)}
				onmousemove={onPileMove}
				onmouseleave={onPileLeave}
			>
				<CardComponent
					card={pile.card}
					showCount={pile.count}
					onclick={() => handleClick(pile)}
					playable={coins >= pile.card.cost && pile.count > 0}
				/>
			</div>
		{/each}
	</div>

	<!-- Center: Kingdom -->
	<div class="center-column">
		<h3 class="section-label">Kingdom</h3>
		<div class="supply-grid">
			{#each kingdomPiles.slice(0, 5) as [id, pile] (id)}
				<div
					class="pile-wrapper"
					class:affordable={coins >= pile.card.cost && pile.count > 0}
					class:empty={pile.count === 0}
					onmouseenter={(e) => onPileEnter(pile.card, e)}
					onmousemove={onPileMove}
					onmouseleave={onPileLeave}
				>
					<CardComponent
						card={pile.card}
						showCount={pile.count}
						onclick={() => handleClick(pile)}
						playable={coins >= pile.card.cost && pile.count > 0}
					/>
				</div>
			{/each}
		</div>
		<div class="supply-grid">
			{#each kingdomPiles.slice(5) as [id, pile] (id)}
				<div
					class="pile-wrapper"
					class:affordable={coins >= pile.card.cost && pile.count > 0}
					class:empty={pile.count === 0}
					onmouseenter={(e) => onPileEnter(pile.card, e)}
					onmousemove={onPileMove}
					onmouseleave={onPileLeave}
				>
					<CardComponent
						card={pile.card}
						showCount={pile.count}
						onclick={() => handleClick(pile)}
						playable={coins >= pile.card.cost && pile.count > 0}
					/>
				</div>
			{/each}
		</div>
	</div>

	<!-- Right column: Victory/Curse -->
	<div class="side-column">
		<h3 class="side-label">Victory</h3>
		{#each victoryPiles as [id, pile] (id)}
			<div
				class="pile-wrapper"
				class:affordable={coins >= pile.card.cost && pile.count > 0}
				class:empty={pile.count === 0}
				onmouseenter={(e) => onPileEnter(pile.card, e)}
				onmousemove={onPileMove}
				onmouseleave={onPileLeave}
			>
				<CardComponent
					card={pile.card}
					showCount={pile.count}
					onclick={() => handleClick(pile)}
					playable={coins >= pile.card.cost && pile.count > 0}
				/>
			</div>
		{/each}
	</div>
</div>

<!-- Hover preview -->
{#if hoverCard}
	<div class="hover-preview" style={previewStyle()}>
		<CardComponent card={hoverCard} />
	</div>
{/if}

<style>
	.supply-layout {
		display: flex;
		gap: var(--space-md);
		padding: var(--space-sm) var(--space-md);
		justify-content: center;
		align-items: flex-start;
		height: 100%;
	}

	/* Side columns (treasure / victory) */
	.side-column {
		display: flex;
		flex-direction: column;
		gap: var(--space-xs);
		align-items: center;
		flex-shrink: 0;
	}

	.side-label {
		font-family: var(--font-heading);
		font-size: 0.6rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--text-muted);
		font-weight: 400;
		margin-bottom: 2px;
	}

	/* Center kingdom */
	.center-column {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
		align-items: center;
		flex: 1;
		min-width: 0;
	}

	.section-label {
		font-family: var(--font-heading);
		font-size: 0.6rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--text-muted);
		font-weight: 400;
	}

	.supply-grid {
		display: grid;
		grid-template-columns: repeat(5, auto);
		gap: var(--space-xs);
		justify-content: center;
	}

	/* Cards are 1.5x larger via override */
	.pile-wrapper {
		position: relative;
		transition: opacity var(--transition-fast);
		border-radius: var(--radius-card);
		opacity: 0.6;
		overflow: visible;
	}

	.pile-wrapper :global(.card) {
		width: 150px;
		min-width: 150px;
	}

	.side-column .pile-wrapper :global(.card) {
		width: 140px;
		min-width: 140px;
	}

	@media (max-width: 1200px) {
		.pile-wrapper :global(.card) {
			width: 120px;
			min-width: 120px;
		}
		.side-column .pile-wrapper :global(.card) {
			width: 110px;
			min-width: 110px;
		}
	}

	@media (max-width: 900px) {
		.pile-wrapper :global(.card) {
			width: 90px;
			min-width: 90px;
		}
		.side-column .pile-wrapper :global(.card) {
			width: 85px;
			min-width: 85px;
		}
	}

	.pile-wrapper.affordable {
		opacity: 1;
	}

	.pile-wrapper.empty {
		opacity: 0.3;
		pointer-events: none;
	}

	/* Disable the default card hover scale in supply — we use the hover preview instead */
	.pile-wrapper :global(.card.clickable:hover),
	.pile-wrapper :global(.card.playable:hover) {
		transform: translateY(-3px);
		box-shadow:
			0 6px 16px rgba(0, 0, 0, 0.6),
			0 0 8px var(--accent-glow);
	}

	/* Hover preview (fixed, follows cursor) */
	.hover-preview {
		position: fixed;
		z-index: 300;
		pointer-events: none;
		filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.8));
	}

	.hover-preview :global(.card) {
		width: 200px;
		min-width: 200px;
	}
</style>
