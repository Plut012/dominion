<script lang="ts">
	import type { Card, OpponentView } from '$lib/game/types'
	import CardComponent from './Card.svelte'

	interface Props {
		inPlay: Card[]
		opponents: OpponentView[]
	}

	let { inPlay, opponents }: Props = $props()
</script>

<div class="play-area">
	<!-- Opponents row -->
	{#if opponents.length > 0}
		<div class="opponents">
			{#each opponents as opp (opp.id)}
				<div class="opponent">
					<div class="opp-name">{opp.name}</div>
					<div class="opp-counts">
						<span title="Cards in hand">✋ {opp.hand_count}</span>
						<span title="Cards in deck">🂠 {opp.deck_count}</span>
						<span title="Cards in discard">♻ {opp.discard_count}</span>
					</div>
					{#if opp.in_play.length > 0}
						<div class="opp-in-play">
							{#each opp.in_play as card, i (i)}
								<div class="opp-card-mini">
									<CardComponent card={card} />
								</div>
							{/each}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}

	<!-- Cards in play this turn -->
	<div class="in-play-area">
		{#if inPlay.length > 0}
			<div class="in-play-cards">
				{#each inPlay as card, i (i)}
					<div class="played-card">
						<CardComponent card={card} />
					</div>
				{/each}
			</div>
		{:else}
			<p class="no-cards">Play area</p>
		{/if}
	</div>
</div>

<style>
	.play-area {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
		padding: var(--space-sm);
	}

	/* ===== Opponents ===== */
	.opponents {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-sm);
	}

	.opponent {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: var(--space-sm) var(--space-md);
		display: flex;
		flex-direction: column;
		gap: 4px;
		flex: 1;
		min-width: 140px;
		max-width: 260px;
	}

	.opp-name {
		font-family: var(--font-heading);
		font-size: 0.8rem;
		color: var(--accent);
		font-weight: 700;
	}

	.opp-counts {
		display: flex;
		gap: var(--space-sm);
		font-size: 0.75rem;
		color: var(--text-muted);
	}

	.opp-counts span {
		white-space: nowrap;
	}

	.opp-in-play {
		display: flex;
		gap: 4px;
		flex-wrap: wrap;
		margin-top: 2px;
	}

	.opp-card-mini {
		/* Scale down opponent cards */
		transform: scale(0.65);
		transform-origin: top left;
		/* Compensate so cards don't take up full space */
		width: calc(80px * 0.65);
		height: calc(80px * 0.65 * 7 / 5);
		overflow: hidden;
		flex-shrink: 0;
	}

	/* ===== In-play area ===== */
	.in-play-area {
		min-height: 60px;
		display: flex;
		align-items: center;
		border: 1px dashed var(--border);
		border-radius: var(--radius-md);
		padding: var(--space-sm);
		background: rgba(0, 0, 0, 0.15);
	}

	@media (min-width: 768px) {
		.in-play-area {
			min-height: 90px;
		}
	}

	.no-cards {
		color: var(--text-muted);
		font-size: 0.75rem;
		font-style: italic;
		width: 100%;
		text-align: center;
	}

	.in-play-cards {
		display: flex;
		flex-wrap: wrap;
		gap: var(--space-sm);
		width: 100%;
	}

	.played-card {
		animation: cardPlayed 200ms ease-out;
	}

	@keyframes cardPlayed {
		from {
			opacity: 0;
			transform: translateY(-12px) scale(0.95);
		}
		to {
			opacity: 1;
			transform: translateY(0) scale(1);
		}
	}
</style>
