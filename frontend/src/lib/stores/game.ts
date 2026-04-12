import type { PlayerView, Choice, ServerMessage } from '$lib/game/types'
import { GameSocket } from '$lib/api/websocket'

class GameStore {
  // Connection state
  connected = $state(false)

  // Lobby state
  roomCode = $state<string | null>(null)
  players = $state<string[]>([])
  playerName = $state('')
  isHost = $state(false)

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

  private socket: GameSocket

  constructor() {
    this.socket = new GameSocket(
      (msg) => this.handleMessage(msg),
      (connected) => { this.connected = connected }
    )
  }

  // Actions
  connect() { this.socket.connect() }

  createRoom(name: string) {
    this.playerName = name
    this.isHost = true
    this.socket.send({ type: 'create_room', player_name: name })
  }

  joinRoom(code: string, name: string) {
    this.playerName = name
    this.socket.send({ type: 'join_room', room_code: code, player_name: name })
  }

  startGame(kingdom: string[] | 'random' = 'random') {
    this.socket.send({ type: 'start_game', kingdom })
  }

  playCard(cardIndex: number) {
    this.socket.send({ type: 'play_card', card_index: cardIndex })
  }

  buyCard(cardId: string) {
    this.socket.send({ type: 'buy_card', card_id: cardId })
  }

  choose(choices: string[]) {
    this.socket.send({ type: 'choose', choice: choices })
  }

  endPhase() {
    this.socket.send({ type: 'end_phase' })
  }

  // Message handler
  private handleMessage(msg: ServerMessage) {
    switch (msg.type) {
      case 'room_created':
        this.roomCode = msg.room_code
        this.players = msg.players
        break
      case 'player_joined':
        this.players = msg.players
        break
      case 'game_state':
        this.gameState = msg.state
        this.error = null
        break
      case 'game_over':
        this.gameOver = msg.scores
        break
      case 'error':
        this.error = msg.message
        break
    }
  }
}

export const game = new GameStore()
