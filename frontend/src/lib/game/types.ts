// Enums
export type Phase = 'action' | 'buy' | 'cleanup' | 'waiting'
export type CardType = 'action' | 'treasure' | 'victory' | 'curse' | 'attack' | 'reaction'

// Data
export interface Card {
  id: string
  name: string
  cost: number
  types: CardType[]
  description: string
  art: string
  vp?: number
  coins?: number
}

export interface OpponentView {
  id: string
  name: string
  hand_count: number
  deck_count: number
  discard_count: number
  in_play: Card[]
  discard_top: Card | null
}

export interface SupplyPile {
  card: Card
  count: number
}

export interface TurnState {
  actions: number
  buys: number
  coins: number
}

export interface Choice {
  prompt: string
  player_id: string
  valid_options: string[]
  min_selections: number
  max_selections: number
}

export interface PlayerView {
  player_id: string
  hand: Card[]
  in_play: Card[]
  deck_count: number
  discard_top: Card | null
  discard_count: number
  opponents: OpponentView[]
  supply: Record<string, SupplyPile>
  trash: Card[]
  phase: Phase
  turn_state: TurnState
  pending_choice: Choice | null
  is_your_turn: boolean
  log: string[]
}

// Messages client → server
export interface CreateRoomMsg { type: 'create_room'; player_name: string }
export interface JoinRoomMsg { type: 'join_room'; room_code: string; player_name: string }
export interface StartGameMsg { type: 'start_game'; kingdom: string[] | 'random' }
export interface PlayCardMsg { type: 'play_card'; card_index: number }
export interface BuyCardMsg { type: 'buy_card'; card_id: string }
export interface ChooseMsg { type: 'choose'; choice: string[] }
export interface EndPhaseMsg { type: 'end_phase' }

export type ClientMessage =
  | CreateRoomMsg
  | JoinRoomMsg
  | StartGameMsg
  | PlayCardMsg
  | BuyCardMsg
  | ChooseMsg
  | EndPhaseMsg

// Messages server → client
export interface RoomCreatedMsg { type: 'room_created'; room_code: string; players: string[] }
export interface PlayerJoinedMsg { type: 'player_joined'; players: string[] }
export interface GameStateMsg { type: 'game_state'; state: PlayerView }
export interface ChoiceRequiredMsg { type: 'choice_required'; choice: Choice }
export interface GameOverMsg { type: 'game_over'; scores: { player_name: string; score: number }[] }
export interface ErrorMsg { type: 'error'; message: string }
export interface LogMsg { type: 'log'; entries: string[] }

export type ServerMessage =
  | RoomCreatedMsg
  | PlayerJoinedMsg
  | GameStateMsg
  | ChoiceRequiredMsg
  | GameOverMsg
  | ErrorMsg
  | LogMsg
