from __future__ import annotations

import dataclasses
import random

from models import (
    AddActions,
    AddBuys,
    AddCoins,
    BanditAttack,
    Card,
    CardType,
    CellarDiscard,
    Choice,
    ChooseCards,
    DiscardCards,
    DiscardDownTo,
    DiscardPerEmptyPile,
    DrawCards,
    DrawToHandSize,
    Effect,
    ForEachOpponent,
    GainCard,
    GainCardCosting,
    GameState,
    InspectTopCards,
    LibraryContinue,
    LibrarySkipChoice,
    MayPlay,
    MayPlayFromDiscard,
    MoneylenderTrash,
    Phase,
    PlayerState,
    PlayCardTwice,
    PutBack,
    RegisterMerchantBonus,
    RevealCards,
    SentryDiscard,
    SentryReturn,
    SentryTrash,
    TrashAndGainUpgrade,
    TrashCards,
    VassalDiscard,
    Zone,
)


# ---------------------------------------------------------------------------
# Internal helper: targeted effect (used by ForEachOpponent)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class _TargetedEffect(Effect):
    """Wraps an inner effect with an explicit target player id.

    Used by ForEachOpponent to direct effects at specific opponents rather than
    always targeting the current player.
    """

    inner: Effect
    player_id: str


@dataclasses.dataclass
class _BanditChoose(Effect):
    """Internal effect: player selects which of the revealed cards to trash for Bandit.

    Used only when the opponent has multiple non-Copper Treasures revealed.
    """

    revealed: list  # list[Card], typed as list to avoid forward-ref issues


# ---------------------------------------------------------------------------
# Card registry — populated externally (e.g. by cards/base.py on import)
# ---------------------------------------------------------------------------

_CARD_REGISTRY: dict[str, Card] = {}


def register_card(card: Card) -> None:
    """Register a card definition so the engine can look it up by id."""
    _CARD_REGISTRY[card.id] = card


def get_card(card_id: str) -> Card:
    """Return the Card definition for *card_id*."""
    try:
        return _CARD_REGISTRY[card_id]
    except KeyError:
        raise KeyError(f"Unknown card id: {card_id!r}")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class InvalidAction(Exception):
    """Raised when a player attempts an illegal game action."""


# ---------------------------------------------------------------------------
# GameEngine
# ---------------------------------------------------------------------------


class GameEngine:
    """Drives turn flow and effect resolution for one game."""

    def __init__(self, state: GameState) -> None:
        self.state = state

    # ------------------------------------------------------------------
    # Public player actions (called by server on WS message receipt)
    # ------------------------------------------------------------------

    def play_card(self, player_id: str, card_index: int) -> None:
        """Play a card from the current player's hand.

        - Treasures can be played during action or buy phase; they add coins
          directly and do not cost an action.
        - Action cards can only be played during the action phase and cost one
          action each.
        """
        state = self.state
        player = self._current_player()

        if player.id != player_id:
            raise InvalidAction("It is not your turn.")

        if state.pending_choice is not None:
            raise InvalidAction("You must respond to the pending choice first.")

        if card_index < 0 or card_index >= len(player.hand):
            raise InvalidAction(f"Card index {card_index} is out of range.")

        card = player.hand[card_index]
        is_treasure = CardType.TREASURE in card.types
        is_action = CardType.ACTION in card.types

        if is_treasure:
            if state.phase not in (Phase.ACTION, Phase.BUY):
                raise InvalidAction(
                    "Treasures can only be played during the action or buy phase."
                )
            player.hand.pop(card_index)
            player.in_play.append(card)
            state.turn_state.coins += card.coins
            state.log.append(f"{player.name} plays {card.name}.")
            # Merchant bonus: first Silver played this turn awards +1 coin per
            # Merchant that was played this turn.
            if (
                card.id == "silver"
                and not state.turn_state.silver_played
                and state.turn_state.merchant_bonuses > 0
            ):
                state.turn_state.coins += state.turn_state.merchant_bonuses
                state.log.append(
                    f"{player.name} gets +{state.turn_state.merchant_bonuses} "
                    f"coin(s) from Merchant bonus."
                )
                state.turn_state.silver_played = True
            # Transition to buy phase when a treasure is played during action phase.
            if state.phase == Phase.ACTION:
                state.phase = Phase.BUY
            return

        if is_action:
            if state.phase != Phase.ACTION:
                raise InvalidAction(
                    "Action cards can only be played during the action phase."
                )
            if state.turn_state.actions < 1:
                raise InvalidAction("You have no actions remaining.")

            player.hand.pop(card_index)
            player.in_play.append(card)
            state.turn_state.actions -= 1
            state.log.append(f"{player.name} plays {card.name}.")
            # Push card's effects onto the front of the queue, then resolve.
            state.effect_queue = list(card.effects) + state.effect_queue
            self._resolve_queue()
            return

        raise InvalidAction(f"{card.name} is neither a treasure nor an action card.")

    def buy_card(self, player_id: str, card_id: str) -> None:
        """Buy a card from the supply during the buy phase."""
        state = self.state
        player = self._current_player()

        if player.id != player_id:
            raise InvalidAction("It is not your turn.")

        if state.phase != Phase.BUY:
            raise InvalidAction("You can only buy cards during the buy phase.")

        if state.pending_choice is not None:
            raise InvalidAction("You must respond to the pending choice first.")

        if state.turn_state.buys < 1:
            raise InvalidAction("You have no buys remaining.")

        if card_id not in state.supply:
            raise InvalidAction(f"Card {card_id!r} is not in the supply.")

        if state.supply[card_id] <= 0:
            raise InvalidAction(f"{card_id!r} pile is empty.")

        card = get_card(card_id)

        if state.turn_state.coins < card.cost:
            raise InvalidAction(
                f"Not enough coins: need {card.cost}, have {state.turn_state.coins}."
            )

        state.supply[card_id] -= 1
        state.turn_state.buys -= 1
        state.turn_state.coins -= card.cost
        player.discard.append(card)
        state.log.append(f"{player.name} buys {card.name}.")

        if self._check_game_over():
            state.phase = Phase.WAITING

    def end_phase(self, player_id: str) -> None:
        """Advance to the next phase (action → buy, buy → cleanup/next player)."""
        state = self.state
        player = self._current_player()

        if player.id != player_id:
            raise InvalidAction("It is not your turn.")

        if state.pending_choice is not None:
            raise InvalidAction("You must respond to the pending choice first.")

        if state.phase == Phase.ACTION:
            state.phase = Phase.BUY
        elif state.phase == Phase.BUY:
            self._cleanup()
        else:
            raise InvalidAction(
                f"Cannot end phase in phase {state.phase.value!r}."
            )

    def handle_choice(self, player_id: str, choice: list[str]) -> None:
        """Validate and apply a player's response to a pending choice."""
        state = self.state

        if state.pending_choice is None:
            raise InvalidAction("There is no pending choice.")

        pending = state.pending_choice
        if pending.player_id != player_id:
            raise InvalidAction("This choice is not for you.")

        n = len(choice)
        if n < pending.min_selections or n > pending.max_selections:
            raise InvalidAction(
                f"Must select between {pending.min_selections} and "
                f"{pending.max_selections} options (got {n})."
            )

        for item in choice:
            if item not in pending.valid_options:
                raise InvalidAction(f"{item!r} is not a valid option.")

        if len(choice) != len(set(choice)):
            raise InvalidAction("Duplicate selections are not allowed.")

        effect = pending.source_effect
        state.pending_choice = None

        if effect is not None:
            self._apply_choice(effect, player_id, choice)

        self._resolve_queue()

    # ------------------------------------------------------------------
    # Internal effect resolution
    # ------------------------------------------------------------------

    def _resolve_queue(self) -> None:
        """Pop and execute effects until empty or a player choice is required."""
        state = self.state
        while state.effect_queue and state.pending_choice is None:
            effect = state.effect_queue.pop(0)
            # Targeted effects carry their own player; others default to current player.
            if isinstance(effect, _TargetedEffect):
                target = self._player_by_id(effect.player_id)
                self._execute_effect(effect.inner, target)
            else:
                self._execute_effect(effect, self._current_player())

    def _execute_effect(self, effect: Effect, target_player: PlayerState) -> None:
        """Execute a single effect against target_player, updating state in place."""
        state = self.state

        # --- Self-resolving effects ---

        if isinstance(effect, DrawCards):
            drawn = self._draw_cards(target_player, effect.n)
            if drawn:
                state.log.append(
                    f"{target_player.name} draws {len(drawn)} card(s)."
                )

        elif isinstance(effect, AddActions):
            state.turn_state.actions += effect.n

        elif isinstance(effect, AddBuys):
            state.turn_state.buys += effect.n

        elif isinstance(effect, AddCoins):
            state.turn_state.coins += effect.n

        elif isinstance(effect, GainCard):
            if state.supply.get(effect.card_id, 0) <= 0:
                return  # Supply exhausted; gain silently fails.
            card = get_card(effect.card_id)
            state.supply[effect.card_id] -= 1
            self._send_to_zone(target_player, card, effect.to)
            state.log.append(f"{target_player.name} gains {card.name}.")

        elif isinstance(effect, ForEachOpponent):
            opponents = self._opponents(target_player)
            # Prepend targeted effects for each opponent in turn order.
            new_effects: list[Effect] = []
            for opp in opponents:
                for sub in effect.effects:
                    new_effects.append(_TargetedEffect(inner=sub, player_id=opp.id))
            state.effect_queue = new_effects + state.effect_queue

        elif isinstance(effect, PlayCardTwice):
            # Re-push the effects of the most recently played action card.
            if target_player.in_play:
                repeated = target_player.in_play[-1]
                state.effect_queue = list(repeated.effects) + state.effect_queue

        elif isinstance(effect, RevealCards):
            cards = self._peek_cards(target_player, effect.n)
            if cards:
                names = ", ".join(c.name for c in cards)
                state.log.append(f"{target_player.name} reveals: {names}.")

        elif isinstance(effect, PutBack):
            # PutBack is used in conjunction with RevealCards / ChooseCards.
            # Full implementation requires tracking "staged" cards; stub for now.
            pass

        elif isinstance(effect, DrawToHandSize):
            # Kick off Library loop.
            state.effect_queue.insert(
                0, LibraryContinue(set_aside=[], target=effect.target)
            )

        elif isinstance(effect, LibraryContinue):
            # Loop body: draw one card; if Action ask to skip; else keep; repeat.
            hand_size = len(target_player.hand)
            if hand_size >= effect.target:
                # Reached target — discard any set-aside cards.
                for card in effect.set_aside:
                    target_player.discard.append(card)
                    state.log.append(
                        f"{target_player.name} discards set-aside {card.name}."
                    )
                return
            # Attempt to draw one card.
            if not target_player.deck:
                self._shuffle_discard_into_deck(target_player)
            if not target_player.deck:
                # No cards to draw — discard set-aside and stop.
                for card in effect.set_aside:
                    target_player.discard.append(card)
                    state.log.append(
                        f"{target_player.name} discards set-aside {card.name}."
                    )
                return
            drawn = target_player.deck.pop(0)
            if CardType.ACTION in drawn.types:
                # Ask player whether to keep or set aside this Action.
                state.effect_queue.insert(
                    0,
                    LibrarySkipChoice(
                        candidate=drawn,
                        set_aside=effect.set_aside,
                        target=effect.target,
                    ),
                )
            else:
                # Non-Action: always keep.
                target_player.hand.append(drawn)
                state.log.append(f"{target_player.name} draws {drawn.name}.")
                # Continue loop.
                state.effect_queue.insert(
                    0,
                    LibraryContinue(set_aside=effect.set_aside, target=effect.target),
                )

        elif isinstance(effect, InspectTopCards):
            # Stage top n cards from deck (reshuffling if needed).
            staged: list[Card] = []
            for _ in range(effect.n):
                if not target_player.deck:
                    self._shuffle_discard_into_deck(target_player)
                if not target_player.deck:
                    break
                staged.append(target_player.deck.pop(0))
            if staged:
                names = ", ".join(c.name for c in staged)
                state.log.append(
                    f"{target_player.name} looks at: {names}."
                )
                # Queue three-step interaction: trash, then discard, then return.
                state.effect_queue = [
                    SentryTrash(staged=staged),
                    SentryDiscard(staged=staged),
                    SentryReturn(staged=staged),
                ] + state.effect_queue

        elif isinstance(effect, BanditAttack):
            # Reveal top 2 cards; trash a non-Copper Treasure; discard the rest.
            revealed: list[Card] = []
            for _ in range(2):
                if not target_player.deck:
                    self._shuffle_discard_into_deck(target_player)
                if not target_player.deck:
                    break
                revealed.append(target_player.deck.pop(0))
            if revealed:
                names = ", ".join(c.name for c in revealed)
                state.log.append(f"{target_player.name} reveals: {names}.")
            # Find non-Copper treasures.
            trashable = [
                c for c in revealed
                if CardType.TREASURE in c.types and c.id != "copper"
            ]
            if not trashable:
                # No trashable treasure — discard everything.
                for card in revealed:
                    target_player.discard.append(card)
                    state.log.append(f"{target_player.name} discards {card.name}.")
            elif len(trashable) == 1:
                # Exactly one — trash it automatically, discard the rest.
                state.trash.append(trashable[0])
                state.log.append(
                    f"{target_player.name} trashes {trashable[0].name}."
                )
                for card in revealed:
                    if card is not trashable[0]:
                        target_player.discard.append(card)
                        state.log.append(
                            f"{target_player.name} discards {card.name}."
                        )
            else:
                # Multiple non-Copper treasures — player must choose one to trash.
                # Encode revealed cards as indexed options among the revealed list.
                valid = [
                    str(i) for i, c in enumerate(revealed)
                    if CardType.TREASURE in c.types and c.id != "copper"
                ]
                # Stash revealed cards so _apply_choice can access them via
                # a temporary BanditChoose effect.
                bandit_choice_effect = _BanditChoose(
                    revealed=revealed,
                )
                state.pending_choice = Choice(
                    prompt=(
                        "Choose a Treasure to trash: "
                        + ", ".join(
                            f"{i}={revealed[int(i)].name}" for i in valid
                        )
                    ),
                    player_id=target_player.id,
                    valid_options=valid,
                    min_selections=1,
                    max_selections=1,
                    source_effect=bandit_choice_effect,
                )

        # --- Choice-requiring effects ---

        elif isinstance(effect, TrashCards):
            valid = [
                str(i)
                for i, c in enumerate(target_player.hand)
                if effect.filter_type is None or effect.filter_type in c.types
            ]
            avail = len(valid)
            state.pending_choice = Choice(
                prompt=(
                    f"Choose {effect.min}–{effect.max} card(s) to trash."
                    if effect.max > 1
                    else "Choose a card to trash."
                ),
                player_id=target_player.id,
                valid_options=valid,
                min_selections=min(effect.min, avail),
                max_selections=min(effect.max, avail),
                source_effect=effect,
            )

        elif isinstance(effect, DiscardCards):
            valid = [str(i) for i in range(len(target_player.hand))]
            avail = len(valid)
            state.pending_choice = Choice(
                prompt=f"Choose {effect.min}–{effect.max} card(s) to discard.",
                player_id=target_player.id,
                valid_options=valid,
                min_selections=min(effect.min, avail),
                max_selections=min(effect.max, avail),
                source_effect=effect,
            )

        elif isinstance(effect, DiscardDownTo):
            excess = len(target_player.hand) - effect.n
            if excess <= 0:
                return  # Player is already at or below the limit.
            valid = [str(i) for i in range(len(target_player.hand))]
            state.pending_choice = Choice(
                prompt=(
                    f"Discard down to {effect.n} cards. "
                    f"Choose {excess} card(s) to discard."
                ),
                player_id=target_player.id,
                valid_options=valid,
                min_selections=excess,
                max_selections=excess,
                source_effect=effect,
            )

        elif isinstance(effect, ChooseCards):
            zone_cards = self._zone_cards(target_player, effect.zone)
            valid = [
                str(i)
                for i, c in enumerate(zone_cards)
                if effect.filter_type is None or effect.filter_type in c.types
            ]
            avail = len(valid)
            state.pending_choice = Choice(
                prompt=effect.prompt,
                player_id=target_player.id,
                valid_options=valid,
                min_selections=min(effect.min, avail),
                max_selections=min(effect.max, avail),
                source_effect=effect,
            )

        elif isinstance(effect, GainCardCosting):
            valid = [
                cid
                for cid, count in state.supply.items()
                if count > 0
                and get_card(cid).cost <= effect.max_cost
                and (
                    effect.filter_type is None
                    or effect.filter_type in get_card(cid).types
                )
            ]
            type_clause = (
                f" ({effect.filter_type.value})" if effect.filter_type else ""
            )
            state.pending_choice = Choice(
                prompt=f"Gain a card{type_clause} costing up to {effect.max_cost} coins.",
                player_id=target_player.id,
                valid_options=valid,
                min_selections=0,
                max_selections=1,
                source_effect=effect,
            )

        elif isinstance(effect, TrashAndGainUpgrade):
            valid = [
                str(i)
                for i, c in enumerate(target_player.hand)
                if effect.filter_type is None or effect.filter_type in c.types
            ]
            avail = len(valid)
            type_clause = (
                f" {effect.filter_type.value}" if effect.filter_type else ""
            )
            state.pending_choice = Choice(
                prompt=f"Choose a{type_clause} card from your hand to trash.",
                player_id=target_player.id,
                valid_options=valid,
                min_selections=0,
                max_selections=min(1, avail),
                source_effect=effect,
            )

        elif isinstance(effect, MayPlay):
            valid = [
                str(i)
                for i, c in enumerate(target_player.hand)
                if effect.card_type in c.types
            ]
            state.pending_choice = Choice(
                prompt=f"You may play a {effect.card_type.value} card from your hand.",
                player_id=target_player.id,
                valid_options=valid,
                min_selections=0,
                max_selections=1,
                source_effect=effect,
            )

        # --- New card-specific effects ---

        elif isinstance(effect, CellarDiscard):
            valid = [str(i) for i in range(len(target_player.hand))]
            state.pending_choice = Choice(
                prompt="Discard any number of cards, then draw that many.",
                player_id=target_player.id,
                valid_options=valid,
                min_selections=0,
                max_selections=len(valid),
                source_effect=effect,
            )

        elif isinstance(effect, RegisterMerchantBonus):
            state.turn_state.merchant_bonuses += 1

        elif isinstance(effect, MoneylenderTrash):
            valid = [
                str(i)
                for i, c in enumerate(target_player.hand)
                if c.id == "copper"
            ]
            avail = len(valid)
            state.pending_choice = Choice(
                prompt="You may trash a Copper from your hand. If you do, +3 Coins.",
                player_id=target_player.id,
                valid_options=valid,
                min_selections=0,
                max_selections=min(1, avail),
                source_effect=effect,
            )

        elif isinstance(effect, DiscardPerEmptyPile):
            empty_piles = sum(
                1 for count in state.supply.values() if count == 0
            )
            if empty_piles == 0:
                return  # Nothing to discard.
            # Enqueue a DiscardCards effect with the exact count needed.
            discard_effect = DiscardCards(min=empty_piles, max=empty_piles)
            state.effect_queue.insert(0, discard_effect)

        elif isinstance(effect, VassalDiscard):
            # Pop the top card of the deck (reshuffling discard if needed),
            # discard it, then conditionally offer to play it if it's an Action.
            if not target_player.deck:
                self._shuffle_discard_into_deck(target_player)
            if not target_player.deck:
                return  # Empty deck and discard; nothing to reveal.
            card = target_player.deck.pop(0)
            target_player.discard.append(card)
            state.log.append(f"{target_player.name} discards {card.name} from deck.")
            if CardType.ACTION in card.types:
                state.effect_queue.insert(0, MayPlayFromDiscard())

        elif isinstance(effect, MayPlayFromDiscard):
            # Offer to play the top card of the discard pile (placed there by VassalDiscard).
            if not target_player.discard:
                return
            top = target_player.discard[-1]
            if CardType.ACTION not in top.types:
                return
            state.pending_choice = Choice(
                prompt=f"You may play {top.name} (Vassal).",
                player_id=target_player.id,
                valid_options=["yes", "no"],
                min_selections=1,
                max_selections=1,
                source_effect=effect,
            )

        elif isinstance(effect, SentryTrash):
            # Player chooses which staged cards to trash (may choose none).
            valid = [str(i) for i in range(len(effect.staged))]
            avail = len(valid)
            state.pending_choice = Choice(
                prompt=(
                    "Sentry: choose cards to trash: "
                    + ", ".join(f"{i}={effect.staged[int(i)].name}" for i in valid)
                ),
                player_id=target_player.id,
                valid_options=valid,
                min_selections=0,
                max_selections=avail,
                source_effect=effect,
            )

        elif isinstance(effect, SentryDiscard):
            # Player chooses which remaining staged cards to discard.
            valid = [str(i) for i in range(len(effect.staged))]
            avail = len(valid)
            state.pending_choice = Choice(
                prompt=(
                    "Sentry: choose cards to discard: "
                    + ", ".join(f"{i}={effect.staged[int(i)].name}" for i in valid)
                ),
                player_id=target_player.id,
                valid_options=valid,
                min_selections=0,
                max_selections=avail,
                source_effect=effect,
            )

        elif isinstance(effect, SentryReturn):
            # Player must specify the order to return remaining cards to deck-top.
            # They submit the indices in the order they want them placed (last
            # submitted index ends up on top since we insert at position 0).
            valid = [str(i) for i in range(len(effect.staged))]
            avail = len(valid)
            if avail == 0:
                return  # Nothing left to return.
            state.pending_choice = Choice(
                prompt=(
                    "Sentry: choose order to return cards to your deck (first = bottom, last = top): "
                    + ", ".join(f"{i}={effect.staged[int(i)].name}" for i in valid)
                ),
                player_id=target_player.id,
                valid_options=valid,
                min_selections=avail,
                max_selections=avail,
                source_effect=effect,
            )

        elif isinstance(effect, LibrarySkipChoice):
            state.pending_choice = Choice(
                prompt=(
                    f"Library: set aside {effect.candidate.name} (Action card)? "
                    "Choose 'yes' to set aside, 'no' to keep."
                ),
                player_id=target_player.id,
                valid_options=["yes", "no"],
                min_selections=1,
                max_selections=1,
                source_effect=effect,
            )

        else:
            state.log.append(f"[engine] Unhandled effect: {type(effect).__name__}")

    def _apply_choice(self, effect: Effect, player_id: str, choice: list[str]) -> None:
        """Apply the player's selected options for the given choice-requiring effect."""
        state = self.state
        player = self._player_by_id(player_id)

        if isinstance(effect, TrashCards):
            # Remove highest indices first so lower indices stay stable.
            for idx in sorted((int(i) for i in choice), reverse=True):
                card = player.hand.pop(idx)
                state.trash.append(card)
                state.log.append(f"{player.name} trashes {card.name}.")

        elif isinstance(effect, (DiscardCards, DiscardDownTo)):
            for idx in sorted((int(i) for i in choice), reverse=True):
                card = player.hand.pop(idx)
                player.discard.append(card)
                state.log.append(f"{player.name} discards {card.name}.")

        elif isinstance(effect, ChooseCards):
            zone_cards = self._zone_cards(player, effect.zone)
            chosen = [zone_cards[int(i)] for i in choice]
            if chosen:
                state.log.append(
                    f"{player.name} chooses: {', '.join(c.name for c in chosen)}."
                )
            if effect.move_to is not None and chosen:
                # Remove chosen cards from their source zone and send to destination.
                source = self._zone_cards(player, effect.zone)
                for card in chosen:
                    source.remove(card)
                    self._send_to_zone(player, card, effect.move_to)
                    state.log.append(
                        f"{player.name} moves {card.name} to {effect.move_to.value}."
                    )

        elif isinstance(effect, GainCardCosting):
            if not choice:
                return
            card_id = choice[0]
            card = get_card(card_id)
            if state.supply.get(card_id, 0) <= 0:
                return
            state.supply[card_id] -= 1
            self._send_to_zone(player, card, effect.to)
            state.log.append(f"{player.name} gains {card.name}.")

        elif isinstance(effect, TrashAndGainUpgrade):
            if not choice:
                return
            idx = int(choice[0])
            trashed = player.hand.pop(idx)
            state.trash.append(trashed)
            state.log.append(f"{player.name} trashes {trashed.name}.")
            # Queue a gain-costing effect for the upgrade.
            gain_effect = GainCardCosting(
                max_cost=trashed.cost + effect.cost_increase,
                to=effect.to,
                filter_type=effect.gain_filter_type,
            )
            state.effect_queue.insert(0, gain_effect)

        elif isinstance(effect, MayPlay):
            if not choice:
                return
            idx = int(choice[0])
            card = player.hand.pop(idx)
            player.in_play.append(card)
            state.log.append(f"{player.name} plays {card.name}.")
            state.effect_queue = list(card.effects) + state.effect_queue

        elif isinstance(effect, CellarDiscard):
            # Discard chosen cards, then draw that many.
            n_discarded = len(choice)
            for idx in sorted((int(i) for i in choice), reverse=True):
                card = player.hand.pop(idx)
                player.discard.append(card)
                state.log.append(f"{player.name} discards {card.name}.")
            if n_discarded > 0:
                state.effect_queue.insert(0, DrawCards(n_discarded))

        elif isinstance(effect, MoneylenderTrash):
            if not choice:
                return  # Player chose not to trash a Copper; no bonus.
            idx = int(choice[0])
            card = player.hand.pop(idx)
            state.trash.append(card)
            state.log.append(f"{player.name} trashes {card.name}.")
            if card.id == "copper":
                state.turn_state.coins += 3
                state.log.append(f"{player.name} gets +3 Coins from Moneylender.")

        elif isinstance(effect, MayPlayFromDiscard):
            # "yes" means play the top discard card; "no" means skip.
            if not choice or choice[0] == "no":
                return
            # choice[0] == "yes": move top of discard to in_play and queue effects.
            if not player.discard:
                return
            card = player.discard.pop()
            player.in_play.append(card)
            state.log.append(f"{player.name} plays {card.name} (Vassal).")
            state.effect_queue = list(card.effects) + state.effect_queue

        elif isinstance(effect, SentryTrash):
            # Trash chosen cards; update staged list for next Sentry step.
            trashed_indices = sorted((int(i) for i in choice), reverse=True)
            remaining = list(effect.staged)
            for idx in trashed_indices:
                card = remaining.pop(idx)
                state.trash.append(card)
                state.log.append(f"{player.name} trashes {card.name}.")
            # Update the downstream SentryDiscard and SentryReturn with remaining.
            self._update_sentry_staged(remaining)

        elif isinstance(effect, SentryDiscard):
            # Discard chosen cards; update staged list for SentryReturn.
            discarded_indices = sorted((int(i) for i in choice), reverse=True)
            remaining = list(effect.staged)
            for idx in discarded_indices:
                card = remaining.pop(idx)
                player.discard.append(card)
                state.log.append(f"{player.name} discards {card.name}.")
            self._update_sentry_staged(remaining)

        elif isinstance(effect, SentryReturn):
            # Put cards back on top of deck in the specified order.
            # The player supplies indices in bottom-to-top order; we insert
            # them one by one so the last index ends up on top.
            ordered = [effect.staged[int(i)] for i in choice]
            for card in ordered:
                player.deck.insert(0, card)
                state.log.append(f"{player.name} puts {card.name} back on their deck.")

        elif isinstance(effect, LibrarySkipChoice):
            if choice[0] == "yes":
                # Set aside the candidate.
                new_set_aside = effect.set_aside + [effect.candidate]
                state.log.append(
                    f"{player.name} sets aside {effect.candidate.name}."
                )
            else:
                # Keep the candidate.
                player.hand.append(effect.candidate)
                state.log.append(
                    f"{player.name} keeps {effect.candidate.name}."
                )
                new_set_aside = effect.set_aside
            # Continue the Library loop.
            state.effect_queue.insert(
                0,
                LibraryContinue(set_aside=new_set_aside, target=effect.target),
            )

        elif isinstance(effect, _BanditChoose):
            # Player chose which revealed card to trash; discard the rest.
            trash_idx = int(choice[0])
            for i, card in enumerate(effect.revealed):
                if i == trash_idx:
                    state.trash.append(card)
                    state.log.append(f"{player.name} trashes {card.name}.")
                else:
                    player.discard.append(card)
                    state.log.append(f"{player.name} discards {card.name}.")

        else:
            state.log.append(
                f"[engine] _apply_choice: unhandled effect {type(effect).__name__}"
            )

    # ------------------------------------------------------------------
    # Deck operations
    # ------------------------------------------------------------------

    def _draw_cards(self, player: PlayerState, n: int) -> list[Card]:
        """Draw up to n cards into hand, reshuffling discard if the deck runs dry."""
        drawn: list[Card] = []
        for _ in range(n):
            if not player.deck:
                self._shuffle_discard_into_deck(player)
            if not player.deck:
                break  # Both piles empty; draw what we could.
            drawn.append(player.deck.pop(0))
        player.hand.extend(drawn)
        return drawn

    def _shuffle_discard_into_deck(self, player: PlayerState) -> None:
        """Move all cards from discard to deck and shuffle."""
        player.deck = player.discard[:]
        player.discard = []
        random.shuffle(player.deck)

    def _peek_cards(self, player: PlayerState, n: int) -> list[Card]:
        """Return the top n cards from the deck (without moving them)."""
        if not player.deck:
            self._shuffle_discard_into_deck(player)
        return player.deck[:n]

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    def _start_turn(self) -> None:
        """Initialise the action phase for the current player."""
        state = self.state
        state.phase = Phase.ACTION
        state.turn_state.actions = 1
        state.turn_state.buys = 1
        state.turn_state.coins = 0
        state.turn_state.merchant_bonuses = 0
        state.turn_state.silver_played = False
        state.effect_queue = []
        state.pending_choice = None
        player = self._current_player()
        state.log.append(f"--- {player.name}'s turn ---")

    def _cleanup(self) -> None:
        """Move hand and in-play cards to discard, draw 5, advance to next player."""
        player = self._current_player()
        player.discard.extend(player.hand)
        player.discard.extend(player.in_play)
        player.hand = []
        player.in_play = []
        self._draw_cards(player, 5)
        self._next_player()

    def _next_player(self) -> None:
        """Rotate current_player and start the next turn."""
        state = self.state
        state.current_player = (state.current_player + 1) % len(state.players)
        self._start_turn()

    # ------------------------------------------------------------------
    # Game-over detection and scoring
    # ------------------------------------------------------------------

    def _check_game_over(self) -> bool:
        """Return True if the end-of-game condition is met."""
        state = self.state
        if state.supply.get("province", 0) == 0:
            return True
        empty_piles = sum(1 for count in state.supply.values() if count == 0)
        return empty_piles >= 3

    def is_game_over(self) -> bool:
        """Public wrapper — return True if the end-of-game condition is met."""
        return self._check_game_over()

    def _calculate_scores(self) -> dict[str, int]:
        """Return {player_id: total_vp} for all players.

        Gardens counts as 1 VP per 10 cards the player owns (rounded down).
        All other VP comes from the card's .vp field.
        """
        scores: dict[str, int] = {}
        for player in self.state.players:
            all_cards = (
                player.hand + player.deck + player.discard + player.in_play
            )
            total_count = len(all_cards)
            total = 0
            for card in all_cards:
                if card.id == "gardens":
                    total += total_count // 10
                else:
                    total += card.vp
            scores[player.id] = total
        return scores

    def calculate_scores(self) -> dict[str, int]:
        """Public wrapper — return {player_id: total_vp} for all players."""
        return self._calculate_scores()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _current_player(self) -> PlayerState:
        return self.state.players[self.state.current_player]

    def _opponents(self, player: PlayerState) -> list[PlayerState]:
        return [p for p in self.state.players if p.id != player.id]

    def _player_by_id(self, player_id: str) -> PlayerState:
        for p in self.state.players:
            if p.id == player_id:
                return p
        raise KeyError(f"No player with id {player_id!r}")

    def _update_sentry_staged(self, remaining: list[Card]) -> None:
        """Update SentryDiscard and SentryReturn in the effect queue with new staged list.

        Called after SentryTrash or SentryDiscard resolves to propagate the
        remaining cards to the next Sentry step.
        """
        for i, effect in enumerate(self.state.effect_queue):
            if isinstance(effect, (SentryDiscard, SentryReturn)):
                # Replace with updated staged list.
                if isinstance(effect, SentryDiscard):
                    self.state.effect_queue[i] = SentryDiscard(staged=remaining)
                else:
                    self.state.effect_queue[i] = SentryReturn(staged=remaining)

    def _zone_cards(self, player: PlayerState, zone: Zone) -> list[Card]:
        mapping = {
            Zone.HAND: player.hand,
            Zone.DECK: player.deck,
            Zone.DISCARD: player.discard,
            Zone.IN_PLAY: player.in_play,
        }
        if zone not in mapping:
            raise ValueError(f"Cannot access zone {zone!r} on a player.")
        return mapping[zone]

    def _send_to_zone(self, player: PlayerState, card: Card, zone: Zone) -> None:
        if zone == Zone.HAND:
            player.hand.append(card)
        elif zone == Zone.DISCARD:
            player.discard.append(card)
        elif zone == Zone.DECK:
            player.deck.insert(0, card)  # top of deck
        elif zone == Zone.IN_PLAY:
            player.in_play.append(card)
        elif zone == Zone.TRASH:
            self.state.trash.append(card)
        else:
            raise ValueError(f"Cannot send card to zone {zone!r}.")


# Alias for compatibility
Engine = GameEngine
