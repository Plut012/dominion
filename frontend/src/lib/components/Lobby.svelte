<script lang="ts">
	import { game } from '$lib/stores/game.svelte'

	let mode = $state<'pick' | 'create' | 'join'>('pick')
	let nameInput = $state('')
	let codeInput = $state('')
	let nameError = $state('')
	let codeError = $state('')

	const roomCode = $derived(game.roomCode)
	const players = $derived(game.players)
	const isHost = $derived(game.isHost)
	const connected = $derived(game.connected)
	const error = $derived(game.error)
	const inLobby = $derived(game.inLobby)
	const reconnecting = $derived(game.reconnecting)

	function validateName(): boolean {
		const trimmed = nameInput.trim()
		if (!trimmed) {
			nameError = 'Enter your name'
			return false
		}
		if (trimmed.length > 24) {
			nameError = 'Name too long (max 24 chars)'
			return false
		}
		nameError = ''
		return true
	}

	function handleCreate() {
		if (!validateName()) return
		game.createRoom(nameInput.trim())
	}

	function handleJoin() {
		if (!validateName()) return
		const code = codeInput.trim().toUpperCase()
		if (!code) {
			codeError = 'Enter a room code'
			return
		}
		codeError = ''
		game.joinRoom(code, nameInput.trim())
	}

	function handleStart() {
		game.startGame('random')
	}

	function copyCode() {
		if (roomCode) {
			navigator.clipboard.writeText(roomCode).catch(() => {})
		}
	}
</script>

<div class="lobby">
	<header class="lobby-header">
		<h1>Dominion</h1>
		<p class="subtitle">A deck-building game for the ages</p>
	</header>

	{#if reconnecting}
		<div class="status-msg">
			<span class="dot reconnecting"></span>
			Reconnecting…
		</div>
	{:else if !connected}
		<div class="status-msg">
			<span class="dot disconnected"></span>
			Connecting to server…
		</div>
	{/if}

	{#if error}
		<div class="error-banner">{error}</div>
	{/if}

	{#if !inLobby}
		<!-- Mode selection / forms -->
		{#if mode === 'pick'}
			<div class="mode-pick">
				<button class="btn-primary mode-btn" onclick={() => { mode = 'create' }}>
					Create Room
				</button>
				<button class="btn-secondary mode-btn" onclick={() => { mode = 'join' }}>
					Join Room
				</button>
			</div>
		{:else if mode === 'create'}
			<div class="form-card">
				<h2>Create a Room</h2>
				<div class="field">
					<label for="create-name">Your name</label>
					<input
						id="create-name"
						type="text"
						bind:value={nameInput}
						placeholder="e.g. Aldric"
						maxlength="24"
						onkeydown={(e) => e.key === 'Enter' && handleCreate()}
					/>
					{#if nameError}<span class="field-error">{nameError}</span>{/if}
				</div>
				<div class="form-actions">
					<button class="btn-secondary" onclick={() => { mode = 'pick'; nameError = '' }}>
						Back
					</button>
					<button class="btn-primary" onclick={handleCreate} disabled={!connected}>
						Create
					</button>
				</div>
			</div>
		{:else if mode === 'join'}
			<div class="form-card">
				<h2>Join a Room</h2>
				<div class="field">
					<label for="join-name">Your name</label>
					<input
						id="join-name"
						type="text"
						bind:value={nameInput}
						placeholder="e.g. Isolde"
						maxlength="24"
					/>
					{#if nameError}<span class="field-error">{nameError}</span>{/if}
				</div>
				<div class="field">
					<label for="join-code">Room code</label>
					<input
						id="join-code"
						type="text"
						bind:value={codeInput}
						placeholder="e.g. KXMR"
						maxlength="12"
						style="text-transform: uppercase; letter-spacing: 0.15em;"
						onkeydown={(e) => e.key === 'Enter' && handleJoin()}
					/>
					{#if codeError}<span class="field-error">{codeError}</span>{/if}
				</div>
				<div class="form-actions">
					<button class="btn-secondary" onclick={() => { mode = 'pick'; nameError = ''; codeError = '' }}>
						Back
					</button>
					<button class="btn-primary" onclick={handleJoin} disabled={!connected}>
						Join
					</button>
				</div>
			</div>
		{/if}
	{:else}
		<!-- In lobby: show room info and player list -->
		<div class="room-card">
			<div class="room-code-block">
				<p class="room-code-label">Room Code</p>
				<button class="room-code" onclick={copyCode} title="Click to copy">
					{roomCode}
				</button>
				<p class="room-code-hint">Share this code with friends</p>
			</div>

			<div class="player-list">
				<h3>Players ({players.length})</h3>
				<ul>
					{#each players as player}
						<li class="player-item">
							<span class="player-dot"></span>
							{player}
							{#if player === game.playerName && isHost}
								<span class="host-badge">host</span>
							{/if}
						</li>
					{/each}
				</ul>
			</div>

			{#if isHost}
				<div class="start-section">
					{#if players.length < 2}
						<p class="waiting-msg">Waiting for at least 2 players…</p>
					{/if}
					<button
						class="btn-primary start-btn"
						onclick={handleStart}
						disabled={players.length < 2}
					>
						Start Game
					</button>
				</div>
			{:else}
				<p class="waiting-msg">Waiting for host to start…</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.lobby {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 100dvh;
		padding: var(--space-xl) var(--space-md);
		gap: var(--space-lg);
	}

	/* Header */
	.lobby-header {
		text-align: center;
	}

	.lobby-header h1 {
		font-size: clamp(2rem, 8vw, 4rem);
		letter-spacing: 0.06em;
		text-shadow: 0 2px 20px rgba(201, 168, 76, 0.3);
	}

	.subtitle {
		color: var(--text-muted);
		font-style: italic;
		font-family: var(--font-heading);
		font-size: 0.95rem;
		margin-top: 4px;
	}

	/* Connection status */
	.status-msg {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		font-size: 0.8rem;
		color: var(--text-muted);
	}

	.dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.dot.disconnected {
		background: #c0392b;
		animation: blink 1.2s ease-in-out infinite;
	}

	.dot.reconnecting {
		background: var(--accent);
		animation: blink 1.2s ease-in-out infinite;
	}

	@keyframes blink {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.3; }
	}

	/* Error banner */
	.error-banner {
		background: rgba(139, 46, 46, 0.3);
		border: 1px solid rgba(139, 46, 46, 0.6);
		border-radius: var(--radius-sm);
		color: #e07070;
		font-size: 0.875rem;
		padding: var(--space-sm) var(--space-md);
		max-width: 380px;
		width: 100%;
		text-align: center;
	}

	/* Mode pick */
	.mode-pick {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
		width: 100%;
		max-width: 280px;
	}

	.mode-btn {
		width: 100%;
		padding: var(--space-md);
		font-size: 1rem;
	}

	/* Form card */
	.form-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: var(--space-lg);
		width: 100%;
		max-width: 360px;
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.form-card h2 {
		font-size: 1.2rem;
		text-align: center;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.field label {
		font-size: 0.8rem;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}

	.field-error {
		font-size: 0.75rem;
		color: #e07070;
	}

	.form-actions {
		display: flex;
		gap: var(--space-sm);
		justify-content: flex-end;
	}

	/* Room card */
	.room-card {
		background: var(--bg-surface);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: var(--space-lg);
		width: 100%;
		max-width: 400px;
		display: flex;
		flex-direction: column;
		gap: var(--space-lg);
	}

	.room-code-block {
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 6px;
	}

	.room-code-label {
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.12em;
		color: var(--text-muted);
	}

	.room-code {
		font-family: var(--font-mono);
		font-size: clamp(1.8rem, 8vw, 2.8rem);
		font-weight: 700;
		letter-spacing: 0.25em;
		color: var(--accent);
		background: transparent;
		border: 2px solid var(--border-strong);
		border-radius: var(--radius-sm);
		padding: var(--space-sm) var(--space-lg);
		cursor: pointer;
		transition: background var(--transition-fast);
	}

	.room-code:hover {
		background: rgba(201, 168, 76, 0.08);
	}

	.room-code-hint {
		font-size: 0.72rem;
		color: var(--text-muted);
	}

	/* Player list */
	.player-list h3 {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--text-muted);
		font-weight: 400;
		margin-bottom: var(--space-sm);
	}

	.player-list ul {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.player-item {
		display: flex;
		align-items: center;
		gap: var(--space-sm);
		font-size: 0.95rem;
	}

	.player-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background: var(--type-victory);
		flex-shrink: 0;
	}

	.host-badge {
		margin-left: auto;
		font-size: 0.65rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--accent);
		border: 1px solid var(--accent-dim);
		border-radius: 20px;
		padding: 1px 6px;
	}

	/* Start section */
	.start-section {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--space-sm);
	}

	.start-btn {
		width: 100%;
		padding: var(--space-md);
		font-size: 1rem;
	}

	.waiting-msg {
		font-size: 0.8rem;
		color: var(--text-muted);
		font-style: italic;
		text-align: center;
	}
</style>
