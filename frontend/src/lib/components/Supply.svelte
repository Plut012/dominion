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

	const BASE_IDS = new Set(['copper', 'silver', 'gold', 'estate', 'duchy', 'province', 'curse'])

	const basePiles = $derived(
		Object.entries(supply).filter(([id]) => BASE_IDS.has(id) && id !== 'curse')
	)

	const kingdomPiles = $derived(
		Object.entries(supply).filter(([id]) => !BASE_IDS.has(id))
	)

	function handleClick(pile: SupplyPile) {
		if (onCardClick) {
			onCardClick(pile.card, pile)
		}
	}
</script>

<div class="supply">
	{#if basePiles.length > 0}
		<div class="supply-section">
			<h3 class="section-label">Treasury & Estates</h3>
			<div class="supply-row">
				{#each basePiles as [id, pile] (id)}
					<div
						class="pile-wrapper"
						class:affordable={coins >= pile.card.cost && pile.count > 0}
						class:empty={pile.count === 0}
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
	{/if}

	{#if kingdomPiles.length > 0}
		<div class="supply-section">
			<h3 class="section-label">Kingdom</h3>
			<div class="supply-grid">
				{#each kingdomPiles as [id, pile] (id)}
					<div
						class="pile-wrapper"
						class:affordable={coins >= pile.card.cost && pile.count > 0}
						class:empty={pile.count === 0}
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
	{/if}
</div>

<style>
	.supply {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
		padding: var(--space-md);
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

	.pile-wrapper {
		position: relative;
		transition: opacity var(--transition-fast);
		border-radius: var(--radius-card);
		opacity: 0.6;
	}

	.pile-wrapper.affordable {
		opacity: 1;
	}

	.pile-wrapper.empty {
		opacity: 0.3;
		pointer-events: none;
	}
</style>
