<script lang="ts">
	import { onMount } from 'svelte'
	import { game } from '$lib/stores/game.svelte'
	import type { Card, SupplyPile } from '$lib/game/types'
	import Lobby from '$lib/components/Lobby.svelte'
	import Hand from '$lib/components/Hand.svelte'
	import Supply from '$lib/components/Supply.svelte'
	import PlayArea from '$lib/components/PlayArea.svelte'
	import TurnControls from '$lib/components/TurnControls.svelte'
	import GameLog from '$lib/components/GameLog.svelte'
	import ChoiceModal from '$lib/components/ChoiceModal.svelte'

	onMount(() => {
		game.connect()
	})

	const inGame = $derived(game.inGame)
	const gameOver = $derived(game.gameOver)
	const gameState = $derived(game.gameState)
	const pendingChoice = $derived(game.pendingChoice)

	const hand = $derived(game.hand)
	const supply = $derived(game.supply)
	const turnState = $derived(game.turnState)
	const phase = $derived(game.phase)
	const isMyTurn = $derived(game.isMyTurn)
	const log = $derived(game.log)

	const inPlay = $derived(gameState?.in_play ?? [])
	const opponents = $derived(gameState?.opponents ?? [])
	const deckCount = $derived(gameState?.deck_count ?? 0)
	const discardCount = $derived(gameState?.discard_count ?? 0)
	const discardTop = $derived(gameState?.discard_top ?? null)

	const canPlay = $derived(isMyTurn && (phase === 'action' || phase === 'buy'))
	const canBuy = $derived(isMyTurn && phase === 'buy')
	const coins = $derived(turnState?.coins ?? 0)

	// Log drawer
	let logOpen = $state(false)

	// Buy confirmation + gain animation
	let buyTarget = $state<{ card: Card; pile: SupplyPile } | null>(null)
	let lastGained = $state<Card | null>(null)

	function onSupplyClick(card: Card, pile: SupplyPile) {
		if (!canBuy || coins < card.cost || pile.count <= 0) return
		buyTarget = { card, pile }
	}

	function confirmBuy() {
		if (buyTarget) {
			lastGained = buyTarget.card
			game.buyCard(buyTarget.card.id)
			buyTarget = null
			// Clear after animation
			setTimeout(() => { lastGained = null }, 700)
		}
	}

	function cancelBuy() {
		buyTarget = null
	}

	function dismissGameOver() {
		window.location.reload()
	}
</script>

{#if !inGame}
	<Lobby />
{:else}
	<div class="game-board">
		<!-- Log tab + drawer -->
		<button class="log-tab" onclick={() => logOpen = !logOpen}>
			Log
		</button>
		<div class="log-drawer" class:open={logOpen}>
			<div class="log-drawer-header">
				<span>Game Log</span>
				<button class="log-close" onclick={() => logOpen = false}>&times;</button>
			</div>
			<GameLog entries={log} />
		</div>
		{#if logOpen}
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="log-backdrop" onclick={() => logOpen = false}></div>
		{/if}

		<!-- Opponents (top bar) -->
		<div class="board-opponents">
			{#each opponents as opp (opp.id)}
				<div class="opp-chip">
					<span class="opp-name">{opp.name}</span>
					<span class="opp-stat" title="Hand">{opp.hand_count}</span>
					<span class="opp-stat" title="Deck">{opp.deck_count}</span>
					<span class="opp-stat" title="Discard">{opp.discard_count}</span>
				</div>
			{/each}
		</div>

		<!-- Supply (main section) -->
		<div class="board-supply">
			<Supply {supply} canBuy={false} {coins} onCardClick={onSupplyClick} />
		</div>

		<!-- Play area (compact) -->
		<div class="board-play">
			<PlayArea {inPlay} opponents={[]} />
		</div>

		<!-- Controls + hand (bottom) -->
		<div class="board-bottom">
			<TurnControls />
			<Hand cards={hand} {canPlay} {deckCount} {discardCount} {discardTop} {lastGained} />
		</div>
	</div>

	<!-- Buy confirmation popup -->
	{#if buyTarget}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div class="buy-overlay" onclick={cancelBuy}>
			<!-- svelte-ignore a11y_click_events_have_key_events -->
			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div class="buy-popup" onclick={(e) => e.stopPropagation()}>
				<p class="buy-prompt">Buy <strong>{buyTarget.card.name}</strong> for {buyTarget.card.cost} coin{buyTarget.card.cost !== 1 ? 's' : ''}?</p>
				<div class="buy-actions">
					<button class="btn-secondary" onclick={cancelBuy}>Cancel</button>
					<button class="btn-primary" onclick={confirmBuy}>Buy</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- Choice modal -->
	{#if pendingChoice && isMyTurn}
		<ChoiceModal choice={pendingChoice} {hand} {supply} />
	{/if}

	<!-- Game over -->
	{#if gameOver}
		<div class="gameover-overlay">
			<div class="gameover-card">
				<h2>Game Over</h2>
				<div class="scores">
					{#each gameOver.sort((a, b) => b.score - a.score) as entry, i}
						<div class="score-row" class:winner={i === 0}>
							<span class="score-rank">{i + 1}.</span>
							<span class="score-name">{entry.player_name}</span>
							<span class="score-points">{entry.score} VP</span>
						</div>
					{/each}
				</div>
				<button class="btn-primary" onclick={dismissGameOver}>Play Again</button>
			</div>
		</div>
	{/if}
{/if}

<style>
	.game-board {
		display: flex;
		flex-direction: column;
		height: 100dvh;
		overflow: hidden;
	}

	/* === Log tab & drawer === */
	.log-tab {
		position: fixed;
		top: 12px;
		left: 0;
		z-index: 100;
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-left: none;
		border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
		padding: 6px 12px;
		font-size: 0.7rem;
		font-family: var(--font-heading);
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--text-muted);
		cursor: pointer;
		transition: color var(--transition-fast), background var(--transition-fast);
	}

	.log-tab:hover {
		color: var(--accent);
		background: rgba(201, 168, 76, 0.08);
	}

	.log-drawer {
		position: fixed;
		top: 0;
		left: -300px;
		width: 300px;
		height: 100dvh;
		z-index: 150;
		background: var(--bg-surface);
		border-right: 1px solid var(--border);
		display: flex;
		flex-direction: column;
		transition: left 200ms ease;
	}

	.log-drawer.open {
		left: 0;
	}

	.log-drawer-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--space-sm) var(--space-md);
		border-bottom: 1px solid var(--border);
		font-family: var(--font-heading);
		font-size: 0.8rem;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: var(--text-muted);
	}

	.log-close {
		background: none;
		border: none;
		color: var(--text-muted);
		font-size: 1.2rem;
		cursor: pointer;
		padding: 0 4px;
	}

	.log-backdrop {
		position: fixed;
		inset: 0;
		z-index: 140;
		background: rgba(0, 0, 0, 0.4);
	}

	/* === Opponents bar === */
	.board-opponents {
		display: flex;
		gap: var(--space-sm);
		padding: var(--space-sm) var(--space-md);
		padding-left: 60px; /* clear the log tab */
		background: var(--bg-surface);
		border-bottom: 1px solid var(--border);
		flex-shrink: 0;
		overflow-x: auto;
	}

	.opp-chip {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 4px 10px;
		border: 1px solid var(--border);
		border-radius: 20px;
		font-size: 0.75rem;
		white-space: nowrap;
		flex-shrink: 0;
	}

	.opp-name {
		font-family: var(--font-heading);
		color: var(--accent);
		font-weight: 600;
	}

	.opp-stat {
		color: var(--text-muted);
		font-size: 0.7rem;
	}

	/* === Supply (main) === */
	.board-supply {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
	}

	/* === Play area (compact) === */
	.board-play {
		flex-shrink: 0;
		border-top: 1px solid var(--border);
		max-height: 100px;
		overflow-x: auto;
	}

	/* === Bottom === */
	.board-bottom {
		flex-shrink: 0;
		border-top: 1px solid var(--border);
	}

	/* === Buy popup === */
	.buy-overlay {
		position: fixed;
		inset: 0;
		z-index: 200;
		background: rgba(0, 0, 0, 0.6);
		display: flex;
		align-items: center;
		justify-content: center;
		backdrop-filter: blur(2px);
	}

	.buy-popup {
		background: var(--bg-surface);
		border: 1px solid var(--border-strong);
		border-radius: var(--radius-md);
		padding: var(--space-lg) var(--space-xl);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-md);
		animation: popIn 150ms ease-out;
		min-width: 240px;
	}

	@keyframes popIn {
		from { opacity: 0; transform: scale(0.95); }
		to { opacity: 1; transform: scale(1); }
	}

	.buy-prompt {
		font-family: var(--font-heading);
		font-size: 1rem;
		text-align: center;
	}

	.buy-prompt strong {
		color: var(--accent);
	}

	.buy-actions {
		display: flex;
		gap: var(--space-sm);
	}

	.buy-actions button {
		min-width: 80px;
	}

	/* === Game over === */
	.gameover-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.8);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 200;
		padding: var(--space-md);
		backdrop-filter: blur(4px);
	}

	.gameover-card {
		background: var(--bg-surface);
		border: 1px solid var(--border-strong);
		border-radius: var(--radius-md);
		padding: var(--space-xl);
		max-width: 380px;
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-lg);
		text-align: center;
		animation: popIn 250ms ease-out;
	}

	.scores {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
		width: 100%;
	}

	.score-row {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		padding: var(--space-sm) var(--space-md);
		border-radius: var(--radius-sm);
		background: rgba(255, 255, 255, 0.04);
	}

	.score-row.winner {
		background: rgba(201, 168, 76, 0.12);
		border: 1px solid var(--accent-dim);
	}

	.score-rank { color: var(--text-muted); font-size: 0.8rem; width: 18px; }
	.score-row.winner .score-rank { color: var(--accent); }
	.score-name { flex: 1; text-align: left; font-family: var(--font-heading); }
	.score-row.winner .score-name { color: var(--accent); }
	.score-points { font-weight: 700; color: var(--accent); }
</style>
