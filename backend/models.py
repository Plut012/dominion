from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Phase(str, Enum):
    ACTION = "action"
    BUY = "buy"
    CLEANUP = "cleanup"
    WAITING = "waiting"


class CardType(str, Enum):
    ACTION = "action"
    TREASURE = "treasure"
    VICTORY = "victory"
    CURSE = "curse"
    ATTACK = "attack"
    REACTION = "reaction"


class Zone(str, Enum):
    HAND = "hand"
    DECK = "deck"
    DISCARD = "discard"
    IN_PLAY = "in_play"
    SUPPLY = "supply"
    TRASH = "trash"


# ---------------------------------------------------------------------------
# Effects
# ---------------------------------------------------------------------------


@dataclass
class Effect:
    """Base class for all card effects."""

    @property
    def requires_choice(self) -> bool:
        """True when this effect must pause the queue for player input."""
        return False


@dataclass
class DrawCards(Effect):
    n: int


@dataclass
class AddActions(Effect):
    n: int


@dataclass
class AddBuys(Effect):
    n: int


@dataclass
class AddCoins(Effect):
    n: int


@dataclass
class GainCard(Effect):
    card_id: str
    to: Zone = Zone.DISCARD


@dataclass
class TrashCards(Effect):
    """Player must choose cards from their hand to trash."""

    min: int
    max: int
    filter_type: CardType | None = None

    @property
    def requires_choice(self) -> bool:
        return True


@dataclass
class DiscardCards(Effect):
    """Player must choose cards from their hand to discard."""

    min: int
    max: int

    @property
    def requires_choice(self) -> bool:
        return True


@dataclass
class ChooseCards(Effect):
    """Generic player-choice effect: select cards from a zone."""

    prompt: str
    zone: Zone
    min: int
    max: int
    filter_type: CardType | None = None

    @property
    def requires_choice(self) -> bool:
        return True


@dataclass
class PlayCardTwice(Effect):
    """Play the previously chosen action card a second time (Throne Room)."""


@dataclass
class ForEachOpponent(Effect):
    """Apply a list of effects to every opponent in turn order."""

    effects: list[Effect]


@dataclass
class MayPlay(Effect):
    """Optionally play a card of the given type from hand."""

    card_type: CardType

    @property
    def requires_choice(self) -> bool:
        return True


@dataclass
class RevealCards(Effect):
    """Reveal n cards from the top of the player's deck."""

    n: int


@dataclass
class PutBack(Effect):
    """Put revealed/chosen cards back to the specified zone."""

    to: Zone


@dataclass
class DiscardDownTo(Effect):
    """Opponent discards until they have n cards in hand (Militia)."""

    n: int

    @property
    def requires_choice(self) -> bool:
        return True


@dataclass
class GainCardCosting(Effect):
    """Gain a card from the supply costing up to max_cost (Workshop/Remodel)."""

    max_cost: int
    to: Zone = Zone.DISCARD

    @property
    def requires_choice(self) -> bool:
        return True


@dataclass
class TrashAndGainUpgrade(Effect):
    """Trash a card, gain one costing up to cost_increase more (Remodel)."""

    cost_increase: int

    @property
    def requires_choice(self) -> bool:
        return True


# ---------------------------------------------------------------------------
# Card
# ---------------------------------------------------------------------------


@dataclass
class Card:
    id: str
    name: str
    cost: int
    types: list[CardType]
    effects: list[Effect]
    description: str
    art: str
    # Victory cards
    vp: int = 0
    # Treasure cards — resolved as AddCoins(coins) when played
    coins: int = 0


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------


@dataclass
class TurnState:
    actions: int = 1
    buys: int = 1
    coins: int = 0


@dataclass
class PlayerState:
    id: str
    name: str
    hand: list[Card] = field(default_factory=list)
    deck: list[Card] = field(default_factory=list)
    discard: list[Card] = field(default_factory=list)
    in_play: list[Card] = field(default_factory=list)


@dataclass
class Choice:
    """Describes what the engine is waiting for from a player."""

    prompt: str
    player_id: str
    # Each option is a card id, zone label, or arbitrary string depending on context
    valid_options: list[str]
    min_selections: int = 1
    max_selections: int = 1
    # The effect that triggered this choice — used to resume the queue
    source_effect: Effect | None = None


@dataclass
class GameState:
    room_code: str
    supply: dict[str, int]          # card_id → count remaining
    trash: list[Card]
    players: list[PlayerState]
    current_player: int             # index into players
    phase: Phase
    effect_queue: list[Effect]
    pending_choice: Choice | None
    turn_state: TurnState
    log: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Client projection (views)
# ---------------------------------------------------------------------------


@dataclass
class OpponentView:
    id: str
    name: str
    hand_count: int
    deck_count: int
    discard_count: int
    discard_top: Card | None        # top card of discard is visible
    in_play: list[Card]


@dataclass
class SupplyPile:
    card: Card
    count: int


@dataclass
class PlayerView:
    """What a single player is allowed to see — sent over the wire as game_state."""

    player_id: str
    hand: list[Card]
    in_play: list[Card]
    deck_count: int
    discard_top: Card | None
    discard_count: int
    opponents: list[OpponentView]
    supply: dict[str, SupplyPile]   # card_id → pile info
    trash: list[Card]
    phase: Phase
    turn_state: TurnState
    pending_choice: Choice | None
    is_your_turn: bool
    log: list[str]


# ---------------------------------------------------------------------------
# WebSocket message types (Pydantic for automatic validation/serialisation)
# ---------------------------------------------------------------------------


# --- Client → Server ---


class CreateRoom(BaseModel):
    type: str = "create_room"
    player_name: str


class JoinRoom(BaseModel):
    type: str = "join_room"
    room_code: str
    player_name: str


class StartGame(BaseModel):
    type: str = "start_game"
    # List of card ids for a custom kingdom, or the string "random"
    kingdom: list[str] | str = "random"


class PlayCard(BaseModel):
    type: str = "play_card"
    card_index: int


class BuyCard(BaseModel):
    type: str = "buy_card"
    card_id: str


class ChooseResponse(BaseModel):
    type: str = "choose"
    # Selected card ids, zone names, or other option strings
    choice: list[str]


class EndPhase(BaseModel):
    type: str = "end_phase"


# Union of all inbound message types (used by server.py for dispatch)
ClientMessage = CreateRoom | JoinRoom | StartGame | PlayCard | BuyCard | ChooseResponse | EndPhase


# --- Server → Client ---


class RoomCreated(BaseModel):
    type: str = "room_created"
    room_code: str
    players: list[str]              # player names in join order


class PlayerJoined(BaseModel):
    type: str = "player_joined"
    players: list[str]


class GameStateMsg(BaseModel):
    type: str = "game_state"
    state: dict[str, Any]           # serialised PlayerView; Any avoids circular Pydantic/dataclass tension


class ChoiceRequired(BaseModel):
    type: str = "choice_required"
    choice: dict[str, Any]          # serialised Choice


class PlayerScore(BaseModel):
    player_name: str
    score: int


class GameOver(BaseModel):
    type: str = "game_over"
    scores: list[PlayerScore]


class Error(BaseModel):
    type: str = "error"
    message: str


class Log(BaseModel):
    type: str = "log"
    entries: list[str]


# Union of all outbound message types
ServerMessage = RoomCreated | PlayerJoined | GameStateMsg | ChoiceRequired | GameOver | Error | Log
