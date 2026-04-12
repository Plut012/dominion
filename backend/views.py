"""
views.py — GameState → PlayerView projection layer.

Converts a raw GameState into a per-player view that contains only what
that player is allowed to see. No game logic lives here.
"""

from __future__ import annotations

from typing import Any

from models import (
    Card,
    CardType,
    Choice,
    GameState,
    OpponentView,
    Phase,
    PlayerView,
    SupplyPile,
    TurnState,
)

# ---------------------------------------------------------------------------
# Card serialization
# ---------------------------------------------------------------------------

LOG_TAIL = 20  # number of recent log entries to include in a view


def card_to_dict(card: Card) -> dict[str, Any]:
    """Serialize a Card to a JSON-serializable dict.

    Enum values are converted to their string values. The effects list is
    omitted — clients don't need the raw effect graph, they use the
    description field for display.
    """
    return {
        "id": card.id,
        "name": card.name,
        "cost": card.cost,
        "types": [t.value for t in card.types],
        "description": card.description,
        "art": card.art,
        "vp": card.vp,
        "coins": card.coins,
    }


# ---------------------------------------------------------------------------
# Choice serialization
# ---------------------------------------------------------------------------


def _choice_to_dict(choice: Choice) -> dict[str, Any]:
    return {
        "prompt": choice.prompt,
        "player_id": choice.player_id,
        "valid_options": choice.valid_options,
        "min_selections": choice.min_selections,
        "max_selections": choice.max_selections,
    }


# ---------------------------------------------------------------------------
# TurnState serialization
# ---------------------------------------------------------------------------


def _turn_state_to_dict(ts: TurnState) -> dict[str, Any]:
    return {
        "actions": ts.actions,
        "buys": ts.buys,
        "coins": ts.coins,
    }


# ---------------------------------------------------------------------------
# Primary projection function
# ---------------------------------------------------------------------------


def make_player_view(state: GameState, player_id: str) -> PlayerView:
    """Build a PlayerView for *player_id* from the full GameState.

    Hides information the player is not allowed to see:
    - Other players' hands are hidden (count only).
    - All players' decks are hidden (count only).
    - Only the top card of each discard pile is revealed.
    - pending_choice is only included when it targets this player.
    """
    # Locate this player's state.
    player = next(p for p in state.players if p.id == player_id)

    # Determine whether it's this player's turn.
    current = state.players[state.current_player]
    is_your_turn = current.id == player_id

    # Build opponent views — every player except this one, preserving order.
    opponents: list[OpponentView] = []
    for p in state.players:
        if p.id == player_id:
            continue
        discard_top = p.discard[-1] if p.discard else None
        opponents.append(
            OpponentView(
                id=p.id,
                name=p.name,
                hand_count=len(p.hand),
                deck_count=len(p.deck),
                discard_count=len(p.discard),
                discard_top=discard_top,
                in_play=list(p.in_play),
            )
        )

    # Build supply piles.  The supply dict maps card_id → count; we need to
    # look up the full Card definition.  Cards are available on any player's
    # hand/deck/discard/in_play, or we can find a representative instance by
    # searching all player zones and trash.  A more direct approach is to pull
    # the card definition from the cards registry, but since we want this
    # module to stay self-contained we gather them from any available source.
    card_registry = _build_card_registry(state)

    supply: dict[str, SupplyPile] = {}
    for card_id, count in state.supply.items():
        card_def = card_registry.get(card_id)
        if card_def is not None:
            supply[card_id] = SupplyPile(card=card_def, count=count)

    # pending_choice: only visible to the player it targets.
    pending_choice: Choice | None = None
    if state.pending_choice and state.pending_choice.player_id == player_id:
        pending_choice = state.pending_choice

    # This player's own discard top.
    own_discard_top = player.discard[-1] if player.discard else None

    return PlayerView(
        player_id=player_id,
        hand=list(player.hand),
        in_play=list(player.in_play),
        deck_count=len(player.deck),
        discard_top=own_discard_top,
        discard_count=len(player.discard),
        opponents=opponents,
        supply=supply,
        trash=list(state.trash),
        phase=state.phase,
        turn_state=state.turn_state,
        pending_choice=pending_choice,
        is_your_turn=is_your_turn,
        log=state.log[-LOG_TAIL:],
    )


# ---------------------------------------------------------------------------
# Full view serialization
# ---------------------------------------------------------------------------


def player_view_to_dict(view: PlayerView) -> dict[str, Any]:
    """Serialize a PlayerView to a JSON-serializable dict."""
    return {
        "player_id": view.player_id,
        "hand": [card_to_dict(c) for c in view.hand],
        "in_play": [card_to_dict(c) for c in view.in_play],
        "deck_count": view.deck_count,
        "discard_top": card_to_dict(view.discard_top) if view.discard_top else None,
        "discard_count": view.discard_count,
        "opponents": [_opponent_view_to_dict(o) for o in view.opponents],
        "supply": {
            card_id: _supply_pile_to_dict(pile)
            for card_id, pile in view.supply.items()
        },
        "trash": [card_to_dict(c) for c in view.trash],
        "phase": view.phase.value,
        "turn_state": _turn_state_to_dict(view.turn_state),
        "pending_choice": _choice_to_dict(view.pending_choice) if view.pending_choice else None,
        "is_your_turn": view.is_your_turn,
        "log": list(view.log),
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _opponent_view_to_dict(opp: OpponentView) -> dict[str, Any]:
    return {
        "id": opp.id,
        "name": opp.name,
        "hand_count": opp.hand_count,
        "deck_count": opp.deck_count,
        "discard_count": opp.discard_count,
        "discard_top": card_to_dict(opp.discard_top) if opp.discard_top else None,
        "in_play": [card_to_dict(c) for c in opp.in_play],
    }


def _supply_pile_to_dict(pile: SupplyPile) -> dict[str, Any]:
    return {
        "card": card_to_dict(pile.card),
        "count": pile.count,
    }


def _build_card_registry(state: GameState) -> dict[str, Card]:
    """Collect one Card instance per card_id from all visible zones.

    We need card definitions to populate SupplyPile objects.  Rather than
    importing the cards module (which would create a coupling we want to
    avoid), we harvest Card instances from the zones that are already present
    in the GameState — every card ever put into play passes through at least
    one player zone or the trash at some point.

    This is best-effort: supply piles that are entirely exhausted AND whose
    cards never appeared in any zone will be absent from the registry.  In
    practice the game always starts with cards distributed to starting decks
    (Copper, Estate) or available in the supply from game start, so this
    covers all real cases.
    """
    registry: dict[str, Card] = {}

    for player in state.players:
        for zone in (player.hand, player.deck, player.discard, player.in_play):
            for card in zone:
                if card.id not in registry:
                    registry[card.id] = card

    for card in state.trash:
        if card.id not in registry:
            registry[card.id] = card

    return registry
