<script lang="ts">
	import type { Card } from '$lib/game/types'

	interface Props {
		card: Card
		playable?: boolean
		selected?: boolean
		onclick?: (card: Card) => void
		showCount?: number | null
	}

	let { card, playable = false, selected = false, onclick, showCount = null }: Props = $props()

	function primaryType(card: Card): string {
		if (card.types.includes('curse')) return 'curse'
		if (card.types.includes('victory')) return 'victory'
		if (card.types.includes('treasure')) return 'treasure'
		if (card.types.includes('action')) return 'action'
		return 'action'
	}

	function typeLabel(card: Card): string {
		return card.types.map(t => t.charAt(0).toUpperCase() + t.slice(1)).join(' – ')
	}

	const type = $derived(primaryType(card))

	function handleClick() {
		if (onclick) onclick(card)
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
	class="card"
	class:playable
	class:selected
	class:clickable={!!onclick}
	data-type={type}
	onclick={handleClick}
	role={onclick ? 'button' : undefined}
	tabindex={onclick ? 0 : undefined}
	onkeydown={onclick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleClick() } } : undefined}
>
	<div class="card-inner">
		<!-- Top row: cost + name -->
		<div class="card-top">
			<span class="card-cost">{card.cost}</span>
			<span class="card-name">{card.name}</span>
		</div>

		<!-- Art area -->
		<div class="card-art">
			{#if card.art}
				<img src="/cards/{card.art}" alt={card.name} loading="lazy" />
			{:else}
				<div class="art-placeholder"></div>
			{/if}
		</div>

		<!-- Type stripe -->
		<div class="card-type-stripe">
			<span class="type-label">{typeLabel(card)}</span>
		</div>

		<!-- Description -->
		<div class="card-desc">
			<p>{card.description}</p>
			{#if card.vp != null && card.vp !== 0}
				<p class="card-vp">{card.vp > 0 ? '+' : ''}{card.vp} VP</p>
			{/if}
		</div>
	</div>

	<!-- Pile count badge (for supply cards) -->
	{#if showCount !== null}
		<div class="pile-count" class:empty={showCount === 0}>
			{showCount}
		</div>
	{/if}
</div>

<style>
	.card {
		position: relative;
		width: 80px;
		min-width: 80px;
		aspect-ratio: 5 / 7;
		border-radius: var(--radius-card);
		background: var(--card-bg);
		border: 1px solid rgba(0, 0, 0, 0.25);
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
		overflow: hidden;
		transition:
			transform var(--transition-base),
			box-shadow var(--transition-base),
			border-color var(--transition-fast);
		user-select: none;
		flex-shrink: 0;
	}

	@media (min-width: 768px) {
		.card {
			width: 110px;
			min-width: 110px;
		}
	}

	@media (min-width: 1024px) {
		.card {
			width: 120px;
			min-width: 120px;
		}
	}

	.card.clickable {
		cursor: pointer;
	}

	.card.playable:hover {
		transform: translateY(-6px) scale(1.04);
		box-shadow:
			0 8px 20px rgba(0, 0, 0, 0.6),
			0 0 12px var(--accent-glow);
	}

	.card.selected {
		border: 2px solid var(--accent);
		box-shadow:
			0 0 0 1px var(--accent),
			0 4px 14px rgba(0, 0, 0, 0.6),
			0 0 16px var(--accent-glow);
		transform: translateY(-4px);
	}

	/* Type-based left border */
	.card::before {
		content: '';
		position: absolute;
		inset: 0 auto 0 0;
		width: 4px;
		z-index: 2;
	}

	.card[data-type="action"]::before  { background: var(--type-action); }
	.card[data-type="treasure"]::before { background: var(--type-treasure); }
	.card[data-type="victory"]::before  { background: var(--type-victory); }
	.card[data-type="curse"]::before    { background: var(--type-curse); }

	.card-inner {
		display: flex;
		flex-direction: column;
		height: 100%;
		padding-left: 4px; /* offset for type stripe */
	}

	/* Top row */
	.card-top {
		display: flex;
		align-items: center;
		gap: 4px;
		padding: 3px 4px 2px 4px;
		background: rgba(0, 0, 0, 0.06);
	}

	.card-cost {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 16px;
		height: 16px;
		min-width: 16px;
		border-radius: 50%;
		background: var(--accent);
		color: var(--bg);
		font-size: 9px;
		font-weight: 700;
		font-family: var(--font-heading);
		line-height: 1;
	}

	@media (min-width: 768px) {
		.card-cost {
			width: 18px;
			height: 18px;
			min-width: 18px;
			font-size: 10px;
		}
	}

	.card-name {
		font-family: var(--font-heading);
		font-size: 7px;
		color: var(--text-dark);
		font-weight: 700;
		line-height: 1.1;
		overflow: hidden;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
	}

	@media (min-width: 768px) {
		.card-name { font-size: 9px; }
	}

	@media (min-width: 1024px) {
		.card-name { font-size: 10px; }
	}

	/* Art */
	.card-art {
		flex: 1;
		overflow: hidden;
		background: rgba(0, 0, 0, 0.08);
	}

	.card-art img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}

	.art-placeholder {
		width: 100%;
		height: 100%;
		background: linear-gradient(135deg, #d4c5a9 0%, #bfaf93 100%);
	}

	/* Type stripe */
	.card-type-stripe {
		padding: 1px 4px;
		text-align: center;
	}

	.card[data-type="action"]  .card-type-stripe { background: var(--type-action); }
	.card[data-type="treasure"] .card-type-stripe { background: var(--type-treasure); }
	.card[data-type="victory"]  .card-type-stripe { background: var(--type-victory); }
	.card[data-type="curse"]    .card-type-stripe { background: var(--type-curse); }

	.type-label {
		font-size: 6px;
		font-family: var(--font-heading);
		color: #fff;
		text-shadow: 0 1px 2px rgba(0,0,0,0.5);
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	@media (min-width: 768px) {
		.type-label { font-size: 7px; }
	}

	/* Description */
	.card-desc {
		padding: 2px 4px 3px;
		background: rgba(255,255,255,0.3);
	}

	.card-desc p {
		font-size: 6px;
		color: var(--text-dark);
		line-height: 1.3;
		text-align: center;
	}

	@media (min-width: 768px) {
		.card-desc p { font-size: 7px; }
	}

	.card-vp {
		font-weight: 700;
		color: var(--type-victory) !important;
	}

	/* Pile count badge */
	.pile-count {
		position: absolute;
		bottom: 4px;
		right: 4px;
		background: var(--bg);
		color: var(--text);
		font-size: 9px;
		font-weight: 700;
		min-width: 16px;
		height: 16px;
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 0 3px;
		border: 1px solid var(--border);
		line-height: 1;
	}

	.pile-count.empty {
		color: var(--text-muted);
		background: #111;
	}
</style>
