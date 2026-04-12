<script lang="ts">
	import type { SupplyPile } from '$lib/game/types'
	import { game } from '$lib/stores/game'
	import CardComponent from './Card.svelte'

	interface Props {
		supply: Record<string, SupplyPile>
		canBuy: boolean
		coins: number
	}

	let { supply, canBuy, coins }: Props = $props()

	// Separate piles into rows: base cards (copper/silver/gold/estate/duchy/province/curse), kingdom
	const BASE_IDS = new Set(['copper', 'silver', 'gold', 'estate', 'duchy', 'province', 'curse'])

	const basePiles = $derived(
		Object.entries(supply).filter(([id]) => BASE_IDS.has(id))
	)

	const kingdomPiles = $derived(
		Object.entries(supply).filter(([id]) => !BASE_IDS.has(id))
	)

	function canAfford(pile: SupplyPile): boolean {
		return coins >= pile.card.cost && pile.count > 0
	}

	function isHighlighted(pile: SupplyPile): boolean {
		return canBuy && canAfford(pile)
	}

	function isDimmed(pile: SupplyPile): boolean {
		return canBuy && !canAfford(pile)
	}

	function handleBuy(pile: SupplyPile) {
		if (!canBuy || !canAfford(pile)) return
		game.buyCard(pile.card.id)
	}
</script>

<div class="supply">
	{#if basePiles.length > 0}
		<div class="supply-section">
			<h3 class="section-label">Treasury &amp; Estates</h3>
			<div class="supply-row">
				{#each basePiles as [id, pile] (id)}
					<div
						class="pile-wrapper"
						class:highlighted={isHighlighted(pile)}
						class:dimmed={isDimmed(pile)}
						class:empty={pile.count === 0}
					>
						<CardComponent
							card={pile.card}
							showCount={pile.count}
							onclick={canBuy && canAfford(pile) ? () => handleBuy(pile) : undefined}
							playable={isHighlighted(pile)}
						/>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	{#if kingdomPiles.length > 0}
		<div class="supply-section">
			<h3 class="section-label">Kingdom</h3>
			<div class="supply-grid">
				{#each kingdomPiles as [id, pile] (id)}
					<div
						class="pile-wrapper"
						class:highlighted={isHighlighted(pile)}
						class:dimmed={isDimmed(pile)}
						class:empty={pile.count === 0}
					>
						<CardComponent
							card={pile.card}
							showCount={pile.count}
							onclick={canBuy && canAfford(pile) ? () => handleBuy(pile) : undefined}
							playable={isHighlighted(pile)}
						/>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.supply {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
		padding: var(--space-md) var(--space-sm);
		overflow-y: auto;
		flex: 1;
	}

	@media (min-width: 768px) {
		.supply {
			padding: var(--space-md);
		}
	}

	.supply-section {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
	}

	.section-label {
		font-family: var(--font-heading);
		font-size: 0.65rem;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: var(--text-muted);
		font-weight: 400;
		padding-bottom: 2px;
		border-bottom: 1px solid var(--border);
	}

	.supply-row {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-sm);
	}

	.supply-grid {
		display: grid;
		/* Fit as many ~80px cards as possible, min 80px */
		grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
		gap: var(--space-sm);
	}

	@media (min-width: 768px) {
		.supply-grid {
			grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
		}
	}

	@media (min-width: 1024px) {
		.supply-grid {
			grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
		}
	}

	/* Pile wrapper manages the dimming/glow without affecting Card internals */
	.pile-wrapper {
		position: relative;
		transition: opacity var(--transition-fast), filter var(--transition-fast);
		border-radius: var(--radius-card);
	}

	.pile-wrapper.dimmed {
		opacity: 0.5;
		filter: grayscale(0.3);
	}

	.pile-wrapper.empty {
		opacity: 0.35;
		pointer-events: none;
	}

	.pile-wrapper.highlighted {
		opacity: 1;
		filter: none;
	}

	/* Affordable glow ring around pile wrapper */
	.pile-wrapper.highlighted::after {
		content: '';
		position: absolute;
		inset: -3px;
		border-radius: calc(var(--radius-card) + 3px);
		border: 2px solid var(--accent);
		box-shadow: 0 0 8px var(--accent-glow);
		pointer-events: none;
		animation: affordablePulse 2s ease-in-out infinite;
	}

	@keyframes affordablePulse {
		0%, 100% { opacity: 0.7; }
		50% { opacity: 1; }
	}
</style>
