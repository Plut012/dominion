# Dominion — Architecture

## Stack

| Layer | Tech | Why |
|-------|------|-----|
| Frontend | SvelteKit + TypeScript | Smooth animations, reactive state, known tool |
| Backend | Python (FastAPI + WebSockets) | Simple, fast iteration, game logic isn't perf-critical |
| Transport | WebSocket | Real-time bidirectional state sync |
| Package mgmt | uv (Python), npm (JS) | Standard tooling |
| Dev | Vite (frontend), uvicorn (backend) | Hot reload on both sides |

No database. No persistence. Games live in server memory and die when they end.

## Core Principle: Server Is Truth

The client is a renderer with input. It never decides game state.

```
Client                          Server
  |                               |
  |-- "I play Smithy" ----------->|
  |                               |-- validate (is it your turn?
  |                               |    do you have Smithy? do you
  |                               |    have actions remaining?)
  |                               |-- resolve effect queue
  |                               |-- broadcast new state
  |<-- GameState update ----------|
  |                               |
  |-- render new state            |
```

## The Effect Queue

This is the heart of the engine. Every card decomposes into atomic effects.

### Atomic Effects

```
DrawCards(n)              — draw n cards from deck (shuffle discard if needed)
AddActions(n)             — +n actions this turn
AddBuys(n)                — +n buys this turn  
AddCoins(n)               — +n coins this turn
GainCard(card, to)        — gain a card from supply to discard/hand/deck
TrashCards(cards)          — remove cards from game
DiscardCards(cards)        — move cards to discard pile
ChooseCards(prompt, from, min, max, filter) — ask player to choose cards
ChooseEffect(prompt, options) — ask player to choose between effects
ForEachOpponent(effects)  — apply effects to each other player
MayPlay(type)             — optionally play a card of given type
RevealCards(n, from)      — reveal cards from deck
PutBack(cards, to)        — put cards on top of deck / back in hand
```

### How It Works

1. Player plays a card → card's effect list is pushed onto the queue
2. Engine pops the next effect from the queue
3. If the effect is self-resolving (DrawCards, AddActions, etc.) → execute immediately, pop next
4. If the effect needs player input (ChooseCards, ChooseEffect) → send prompt to client, wait
5. Client responds with choice → engine validates, continues popping
6. Queue empty → player regains control (can play another action or move to buy phase)

### Example: Throne Room

```
Throne Room's effects: [ChooseCard(from: hand, type: action)]

Player chooses Smithy →
  Queue becomes: [PlayCard(Smithy), PlayCard(Smithy)]

Resolving first PlayCard(Smithy):
  Queue becomes: [DrawCards(3), PlayCard(Smithy)]

Resolving DrawCards(3): draw 3 cards
  Queue becomes: [PlayCard(Smithy)]

Resolving second PlayCard(Smithy):
  Queue becomes: [DrawCards(3)]

Resolving DrawCards(3): draw 3 cards
  Queue empty → turn continues
```

No special Throne Room logic in the engine. Throne Room is just data.

### Reactions

Cards like Moat interrupt the normal flow. When an attack effect targets an opponent:

1. Before resolving, check if opponent has reaction cards in hand
2. If yes, push a MayReveal prompt to that player
3. If they reveal Moat, skip the attack effect for that player
4. Continue queue

Reactions are hooks, not special cases. The engine checks for them at defined points.

## Game State

```python
@dataclass
class GameState:
    supply: dict[str, int]          # card_id → count remaining
    trash: list[Card]
    players: list[PlayerState]
    current_player: int
    phase: Phase                    # action | buy | cleanup | waiting
    effect_queue: list[Effect]
    pending_choice: Choice | None   # what we're waiting for from a player
    turn_state: TurnState           # actions_remaining, buys_remaining, coins

@dataclass  
class PlayerState:
    hand: list[Card]
    deck: list[Card]
    discard: list[Card]
    in_play: list[Card]

@dataclass
class TurnState:
    actions: int    # starts at 1
    buys: int       # starts at 1
    coins: int      # starts at 0
```

## Card Definitions

Cards are data, not code. A card definition:

```python
Card(
    id="smithy",
    name="Smithy",
    cost=4,
    types=[CardType.ACTION],
    effects=[DrawCards(3)],
    art="smithy.webp",
    description="+3 Cards"
)

Card(
    id="village", 
    name="Village",
    cost=3,
    types=[CardType.ACTION],
    effects=[DrawCards(1), AddActions(2)],
    art="village.webp",
    description="+1 Card, +2 Actions"
)

Card(
    id="throne_room",
    name="Throne Room",
    cost=4,
    types=[CardType.ACTION],
    effects=[ChooseCard(from_zone="hand", card_type=CardType.ACTION, 
                        then=PlayCardTwice)],
    art="throne_room.webp",
    description="You may play an Action card from your hand twice."
)
```

Adding a new card = adding a Card() entry. No engine changes.

## Client State & Sync

The server sends each player a **view** of the game state — not the raw state. Players don't see other players' hands or decks.

```python
@dataclass
class PlayerView:
    hand: list[Card]                # your hand (full info)
    in_play: list[Card]             # cards you've played this turn
    deck_count: int                 # how many cards in your deck (no peeking)
    discard_top: Card | None        # top of your discard (visible)
    discard_count: int
    opponents: list[OpponentView]   # name, hand_count, deck_count, discard_count
    supply: dict[str, SupplyPile]   # card info + count remaining
    trash: list[Card]
    phase: Phase
    turn_state: TurnState
    pending_choice: Choice | None   # if it's your turn to decide something
    is_your_turn: bool
    log: list[str]                  # recent game log entries
```

## Directory Structure

```
dominion/
  backend/
    server.py              — FastAPI app, WebSocket handling, room management
    engine.py              — game loop, effect queue resolution
    models.py              — GameState, PlayerState, Card, Effect dataclasses
    cards/
      base.py              — base set card definitions
    views.py               — GameState → PlayerView projection
  frontend/
    src/
      lib/
        stores/            — Svelte stores (connection, game state, UI state)
        components/
          Card.svelte       — single card rendering
          Hand.svelte       — player's hand (fan layout)
          Supply.svelte     — kingdom card supply grid
          PlayArea.svelte   — cards in play
          TurnControls.svelte — action/buy/end turn buttons
          Lobby.svelte      — room creation and joining
          GameLog.svelte    — scrolling game log
        api/
          websocket.ts      — WebSocket client, message types
        game/
          types.ts          — TypeScript types mirroring server models
          animations.ts     — card movement, transitions
      routes/
        +page.svelte        — lobby
        game/
          [room]/
            +page.svelte    — game board
      app.css               — global styles, medieval theme
    static/
      cards/                — AI-generated card art (webp)
      fonts/                — medieval/serif fonts
  docs/
    overview.md
    architecture.md
```

## WebSocket Protocol

Messages are JSON with a `type` field:

```
Client → Server:
  { type: "create_room", player_name: "..." }
  { type: "join_room", room_code: "...", player_name: "..." }
  { type: "start_game", kingdom: [...] | "random" }
  { type: "play_card", card_index: int }
  { type: "buy_card", card_id: str }
  { type: "choose", choice: [...] }       — response to pending_choice
  { type: "end_phase" }                   — end action or buy phase

Server → Client:
  { type: "room_created", room_code: "...", players: [...] }
  { type: "player_joined", players: [...] }
  { type: "game_state", state: PlayerView }
  { type: "choice_required", choice: Choice }
  { type: "game_over", scores: [...] }
  { type: "error", message: "..." }
  { type: "log", entries: [...] }
```

## End Game

Game ends when any 3 supply piles are empty OR the Province pile is empty. Server detects this after every buy, calculates scores (sum of victory point values in each player's deck+hand+discard), and broadcasts game_over.
