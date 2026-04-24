import type { PlayerView, ServerMessage } from '$lib/game/types'
import type { GameSocket } from '$lib/api/websocket'

const SESSION_KEY = 'dominion_session'

interface StoredSession {
  playerId: string
  playerName: string
  roomCode: string
}

function loadSession(): StoredSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY)
    if (!raw) return null
    return JSON.parse(raw) as StoredSession
  } catch {
    return null
  }
}

function saveSession(session: StoredSession): void {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  } catch {
    // localStorage unavailable — ignore
  }
}

function clearSession(): void {
  try {
    localStorage.removeItem(SESSION_KEY)
  } catch {
    // ignore
  }
}

class GameStore {
  // Connection state
  connected = $state(false)

  // Lobby state
  roomCode = $state<string | null>(null)
  players = $state<string[]>([])
  playerName = $state('')
  isHost = $state(false)
  playerId = $state<string | null>(null)

  // Reconnection state
  reconnecting = $state(false)

  // Game state
  gameState = $state<PlayerView | null>(null)
  gameOver = $state<{ player_name: string; score: number }[] | null>(null)
  error = $state<string | null>(null)

  // Derived
  get inGame() { return this.gameState !== null }
  get inLobby() { return this.roomCode !== null && !this.inGame }
  get phase() { return this.gameState?.phase ?? null }
  get isMyTurn() { return this.gameState?.is_your_turn ?? false }
  get hand() { return this.gameState?.hand ?? [] }
  get supply() { return this.gameState?.supply ?? {} }
  get turnState() { return this.gameState?.turn_state ?? null }
  get pendingChoice() { return this.gameState?.pending_choice ?? null }
  get log() { return this.gameState?.log ?? [] }

  private socket: GameSocket | null = null

  async connect() {
    const { GameSocket } = await import('$lib/api/websocket')
    this.socket = new GameSocket(
      (msg) => this.handleMessage(msg),
      (connected) => { this.connected = connected }
    )

    const session = loadSession()
    if (session) {
      this.reconnecting = true
      this.socket.connect(() => {
        this.socket?.send({
          type: 'rejoin',
          player_id: session.playerId,
          room_code: session.roomCode,
        })
      })
    } else {
      this.socket.connect()
    }
  }

  createRoom(name: string) {
    this.playerName = name
    this.isHost = true
    this.socket?.send({ type: 'create_room', player_name: name })
  }

  joinRoom(code: string, name: string) {
    this.playerName = name
    this.roomCode = code.toUpperCase()
    this.socket?.send({ type: 'join_room', room_code: code, player_name: name })
  }

  startGame(kingdom: string[] | 'random' = 'random') {
    this.socket?.send({ type: 'start_game', kingdom })
  }

  playCard(cardIndex: number) {
    this.socket?.send({ type: 'play_card', card_index: cardIndex })
  }

  buyCard(cardId: string) {
    this.socket?.send({ type: 'buy_card', card_id: cardId })
  }

  choose(choices: string[]) {
    this.socket?.send({ type: 'choose', choice: choices })
  }

  endPhase() {
    this.socket?.send({ type: 'end_phase' })
  }

  disconnect() {
    clearSession()
    this.socket?.disconnect()
    this.socket = null
    this.roomCode = null
    this.players = []
    this.playerName = ''
    this.isHost = false
    this.playerId = null
    this.gameState = null
    this.gameOver = null
    this.error = null
    this.reconnecting = false
  }

  private autoPlayTreasures() {
    const s = this.gameState
    if (!s || !s.is_your_turn || s.phase !== 'buy' || s.pending_choice) return
    // Find first treasure in hand and play it; the resulting state update
    // will re-trigger this until no treasures remain.
    const idx = s.hand.findIndex(c => c.types.includes('treasure'))
    if (idx !== -1) {
      setTimeout(() => this.playCard(idx), 80)
    }
  }

  private handleMessage(msg: ServerMessage) {
    switch (msg.type) {
      case 'room_created':
        this.playerId = msg.player_id
        this.roomCode = msg.room_code
        this.players = msg.players
        saveSession({
          playerId: msg.player_id,
          playerName: this.playerName,
          roomCode: msg.room_code,
        })
        break
      case 'player_joined':
        this.players = msg.players
        if (msg.player_id) {
          // This is the joining player receiving their own confirmation.
          this.playerId = msg.player_id
          saveSession({
            playerId: msg.player_id,
            playerName: this.playerName,
            roomCode: this.roomCode ?? '',
          })
        }
        break
      case 'game_state':
        this.gameState = msg.state
        this.error = null
        this.autoPlayTreasures()
        break
      case 'game_over':
        this.gameOver = msg.scores
        clearSession()
        break
      case 'rejoin_success': {
        this.reconnecting = false
        this.playerId = msg.player_id
        this.roomCode = msg.room_code
        if (msg.state) {
          // Game is in progress — restore game state.
          this.gameState = msg.state
          this.error = null
        } else if (msg.players) {
          // Still in lobby.
          this.players = msg.players
        }
        // Restore playerName from session before overwriting it.
        const existingSession = loadSession()
        if (!this.playerName && existingSession?.playerName) {
          this.playerName = existingSession.playerName
        }
        // Update session with confirmed data.
        saveSession({
          playerId: msg.player_id,
          playerName: this.playerName,
          roomCode: msg.room_code,
        })
        break
      }
      case 'rejoin_failed':
        this.reconnecting = false
        clearSession()
        this.error = null
        break
      case 'error':
        this.error = msg.message
        break
    }
  }
}

export const game = new GameStore()
