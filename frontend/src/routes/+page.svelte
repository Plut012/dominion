<script lang="ts">
	import { onMount } from 'svelte'
	import { game } from '$lib/stores/game'
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

	// Derived state from the game store
	const inGame = $derived(game.inGame)
	const gameOver = $derived(game.gameOver)
	const gameState = $derived(game.gameState)
	const pendingChoice = $derived(game.pendingChoice)

	// Game board derived values
	const hand = $derived(game.hand)
	const supply = $derived(game.supply)
	const turnState = $derived(game.turnState)
	const phase = $derived(game.phase)
	const isMyTurn = $derived(game.isMyTurn)
	const log = $derived(game.log)

	const inPlay = $derived(gameState?.in_play ?? [])
	const opponents = $derived(gameState?.opponents ?? [])

	const canPlay = $derived(
		isMyTurn && (phase === 'action' || phase === 'buy')
	)

	const canBuy = $derived(
		isMyTurn && phase === 'buy'
	)

	const coins = $derived(turnState?.coins ?? 0)

	function dismissGameOver() {
		// Reset to lobby state — user will need to create/join a new room
		// For now just reload; a full reset would need a game.reset() method
		window.location.reload()
	}
</script>

{#if !inGame}
	<Lobby />
{:else}
	<div class="game-board">
		<!-- Play area + opponents (top) -->
		<div class="board-top">
			<PlayArea {inPlay} {opponents} />
		</div>

		<!-- Supply (middle, scrollable) -->
		<div class="board-middle">
			<Supply {supply} {canBuy} {coins} />
		</div>

		<!-- Bottom strip: hand + controls + log -->
		<div class="board-bottom">
			<TurnControls />
			<Hand cards={hand} {canPlay} />
			<div class="log-strip">
				<GameLog entries={log} />
			</div>
		</div>
	</div>

	<!-- Choice modal (above everything) -->
	{#if pendingChoice && isMyTurn}
		<ChoiceModal
			choice={pendingChoice}
			{hand}
			{supply}
		/>
	{/if}

	<!-- Game over overlay -->
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
				<button class="btn-primary" onclick={dismissGameOver}>
					Play Again
				</button>
			</div>
		</div>
	{/if}
{/if}

<style>
	/* ===== Game board layout ===== */
	.game-board {
		display: flex;
		flex-direction: column;
		height: 100dvh;
		overflow: hidden;
	}

	/* Top: play area, fixed height */
	.board-top {
		flex-shrink: 0;
		overflow-x: auto;
		border-bottom: 1px solid var(--border);
		min-height: 80px;
		max-height: 220px;
	}

	@media (min-width: 768px) {
		.board-top {
			max-height: 260px;
		}
	}

	/* Middle: supply, fills available space */
	.board-middle {
		flex: 1;
		overflow-y: auto;
		overflow-x: hidden;
		border-bottom: 1px solid var(--border);
	}

	/* Bottom: controls + hand + log, fixed */
	.board-bottom {
		flex-shrink: 0;
		display: flex;
		flex-direction: column;
	}

	.log-strip {
		padding: var(--space-xs) var(--space-sm) var(--space-sm);
		background: var(--bg);
	}

	/* ===== Game Over Overlay ===== */
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
		padding: var(--space-xl) var(--space-xl) var(--space-lg);
		max-width: 380px;
		width: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-lg);
		text-align: center;
		animation: modalIn 250ms ease-out;
	}

	@keyframes modalIn {
		from { opacity: 0; transform: scale(0.94) translateY(12px); }
		to { opacity: 1; transform: scale(1) translateY(0); }
	}

	.gameover-card h2 {
		font-size: 2rem;
		letter-spacing: 0.08em;
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
		font-size: 0.95rem;
	}

	.score-row.winner {
		background: rgba(201, 168, 76, 0.12);
		border: 1px solid var(--accent-dim);
	}

	.score-rank {
		color: var(--text-muted);
		font-size: 0.8rem;
		width: 18px;
		flex-shrink: 0;
	}

	.score-row.winner .score-rank {
		color: var(--accent);
	}

	.score-name {
		flex: 1;
		text-align: left;
		font-family: var(--font-heading);
	}

	.score-row.winner .score-name {
		color: var(--accent);
	}

	.score-points {
		font-weight: 700;
		color: var(--accent);
		font-family: var(--font-heading);
	}
</style>
