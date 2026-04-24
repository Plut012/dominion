"""Base set Dominion card definitions.

Cards are pure data — no logic lives here. Each card is a Card dataclass
instance composed from Effect subclasses defined in models.py.

Where a card's full behaviour requires an effect type not yet in models.py,
a comment marks the gap.
"""

from __future__ import annotations

from models import (
    AddActions,
    AddBuys,
    AddCoins,
    BanditAttack,
    Card,
    CardType,
    ChooseCards,
    DiscardCards,
    DiscardDownTo,
    DrawCards,
    DrawToHandSize,
    ForEachOpponent,
    GainCard,
    GainCardCosting,
    InspectTopCards,
    MayPlay,
    PlayCardTwice,
    PutBack,
    RevealCards,
    TrashAndGainUpgrade,
    TrashCards,
    Zone,
)

# ---------------------------------------------------------------------------
# Treasure cards
# ---------------------------------------------------------------------------

COPPER = Card(
    id="copper",
    name="Copper",
    cost=0,
    types=[CardType.TREASURE],
    effects=[AddCoins(1)],
    description="1 coin.",
    art="copper.webp",
    coins=1,
)

SILVER = Card(
    id="silver",
    name="Silver",
    cost=3,
    types=[CardType.TREASURE],
    effects=[AddCoins(2)],
    description="2 coins.",
    art="silver.webp",
    coins=2,
)

GOLD = Card(
    id="gold",
    name="Gold",
    cost=6,
    types=[CardType.TREASURE],
    effects=[AddCoins(3)],
    description="3 coins.",
    art="gold.webp",
    coins=3,
)

# ---------------------------------------------------------------------------
# Victory cards
# ---------------------------------------------------------------------------

ESTATE = Card(
    id="estate",
    name="Estate",
    cost=2,
    types=[CardType.VICTORY],
    effects=[],
    description="1 VP.",
    art="estate.webp",
    vp=1,
)

DUCHY = Card(
    id="duchy",
    name="Duchy",
    cost=5,
    types=[CardType.VICTORY],
    effects=[],
    description="3 VP.",
    art="duchy.webp",
    vp=3,
)

PROVINCE = Card(
    id="province",
    name="Province",
    cost=8,
    types=[CardType.VICTORY],
    effects=[],
    description="6 VP.",
    art="province.webp",
    vp=6,
)

# ---------------------------------------------------------------------------
# Curse
# ---------------------------------------------------------------------------

CURSE = Card(
    id="curse",
    name="Curse",
    cost=0,
    types=[CardType.CURSE],
    effects=[],
    description="-1 VP.",
    art="curse.webp",
    vp=-1,
)

# ---------------------------------------------------------------------------
# Kingdom cards — cost 2
# ---------------------------------------------------------------------------

CELLAR = Card(
    id="cellar",
    name="Cellar",
    cost=2,
    types=[CardType.ACTION],
    effects=[
        AddActions(1),
        # Player chooses any number of cards to discard, then draws that many.
        # NOTE: DiscardCards uses a fixed max. A full implementation needs a
        # "discard N, draw N" effect where N is determined by the player's
        # choice (DrawCards equal to number discarded). Current models support
        # this as a two-step interaction: engine should count cards discarded
        # by this DiscardCards effect and enqueue DrawCards(n_discarded).
        DiscardCards(min=0, max=999),
        # TODO: engine must enqueue DrawCards(n) after resolving the discard
        # where n = number of cards actually discarded by this effect.
    ],
    description="+1 Action. Discard any number of cards, then draw that many.",
    art="cellar.webp",
)

CHAPEL = Card(
    id="chapel",
    name="Chapel",
    cost=2,
    types=[CardType.ACTION],
    effects=[
        TrashCards(min=0, max=4),
    ],
    description="Trash up to 4 cards from your hand.",
    art="chapel.webp",
)

MOAT = Card(
    id="moat",
    name="Moat",
    cost=2,
    types=[CardType.ACTION, CardType.REACTION],
    effects=[
        DrawCards(2),
    ],
    description=(
        "+2 Cards. "
        "When another player plays an Attack card, you may first reveal this "
        "from your hand. If you do, you are unaffected by that Attack."
    ),
    art="moat.webp",
    # NOTE: The reaction mechanic (block attack on reveal) is handled by the
    # engine's attack-resolution hook, not as an effect in this list. The
    # engine checks for REACTION cards in the target's hand before applying
    # ForEachOpponent effects.
)

# ---------------------------------------------------------------------------
# Kingdom cards — cost 3
# ---------------------------------------------------------------------------

HARBINGER = Card(
    id="harbinger",
    name="Harbinger",
    cost=3,
    types=[CardType.ACTION],
    effects=[
        DrawCards(1),
        AddActions(1),
        ChooseCards(
            prompt="You may put a card from your discard pile onto your deck.",
            zone=Zone.DISCARD,
            min=0,
            max=1,
            move_to=Zone.DECK,
        ),
    ],
    description="+1 Card, +1 Action. You may put a card from your discard onto your deck.",
    art="harbinger.webp",
)

MERCHANT = Card(
    id="merchant",
    name="Merchant",
    cost=3,
    types=[CardType.ACTION],
    effects=[
        DrawCards(1),
        AddActions(1),
        # NOTE: The "first Silver played this turn gives +1 coin" bonus is a
        # conditional deferred effect. models.py has no WhenPlaysTreasure or
        # ConditionalAddCoins effect. The engine must track Merchant plays and
        # hook into the treasure-play step to award +1 coin the first time a
        # Silver is played that turn.
    ],
    description="+1 Card, +1 Action. The first time you play a Silver this turn, +1 coin.",
    art="merchant.webp",
)

VASSAL = Card(
    id="vassal",
    name="Vassal",
    cost=3,
    types=[CardType.ACTION],
    effects=[
        AddCoins(2),
        # Discard top card of deck; if it is an Action, may play it.
        # NOTE: models.py has no "RevealAndMayPlayTopOfDeck" effect. The
        # engine needs to reveal the top card, and if it is an ACTION type,
        # prompt the player via MayPlay. Using RevealCards(1) + MayPlay as
        # the closest available combination; engine must handle the conditional
        # "discard if not played" cleanup.
        RevealCards(1),
        MayPlay(card_type=CardType.ACTION),
    ],
    description="+2 Coins. Discard the top card of your deck. If it's an Action card, you may play it.",
    art="vassal.webp",
)

VILLAGE = Card(
    id="village",
    name="Village",
    cost=3,
    types=[CardType.ACTION],
    effects=[
        DrawCards(1),
        AddActions(2),
    ],
    description="+1 Card, +2 Actions.",
    art="village.webp",
)

WORKSHOP = Card(
    id="workshop",
    name="Workshop",
    cost=3,
    types=[CardType.ACTION],
    effects=[
        GainCardCosting(max_cost=4, to=Zone.DISCARD),
    ],
    description="Gain a card costing up to 4.",
    art="workshop.webp",
)

# ---------------------------------------------------------------------------
# Kingdom cards — cost 4
# ---------------------------------------------------------------------------

BUREAUCRAT = Card(
    id="bureaucrat",
    name="Bureaucrat",
    cost=4,
    types=[CardType.ACTION, CardType.ATTACK],
    effects=[
        GainCard(card_id="silver", to=Zone.DECK),
        ForEachOpponent(effects=[
            # If opponent has a Victory card in hand they must put one on their deck.
            # min=0 handles the "no Victory cards" case gracefully.
            ChooseCards(
                prompt="Put a Victory card from your hand onto your deck (or reveal a hand with no Victory cards).",
                zone=Zone.HAND,
                min=0,
                max=1,
                filter_type=CardType.VICTORY,
                move_to=Zone.DECK,
            ),
        ]),
    ],
    description=(
        "Gain a Silver onto your deck. "
        "Each other player reveals a Victory card from their hand and puts it onto their deck "
        "(or reveals a hand with no Victory cards)."
    ),
    art="bureaucrat.webp",
)

GARDENS = Card(
    id="gardens",
    name="Gardens",
    cost=4,
    types=[CardType.VICTORY],
    effects=[],
    description="Worth 1 VP per 10 cards in your deck (rounded down).",
    art="gardens.webp",
    # NOTE: Gardens has a variable VP value (1 per 10 cards in full deck).
    # vp=0 here; the scoring engine must special-case Gardens (or any card
    # with a "variable_vp" flag) and compute its value at end-of-game.
    vp=0,
)

MILITIA = Card(
    id="militia",
    name="Militia",
    cost=4,
    types=[CardType.ACTION, CardType.ATTACK],
    effects=[
        AddCoins(2),
        ForEachOpponent(effects=[
            DiscardDownTo(n=3),
        ]),
    ],
    description="+2 Coins. Each other player discards down to 3 cards in hand.",
    art="militia.webp",
)

MONEYLENDER = Card(
    id="moneylender",
    name="Moneylender",
    cost=4,
    types=[CardType.ACTION],
    effects=[
        # Trash a Copper from hand; if you did, +3 coins.
        # NOTE: models.py has no "TrashForBonus" or conditional effect.
        # Closest: TrashCards(min=0, max=1, filter_type=TREASURE) then
        # AddCoins(3). The engine must award the +3 coins only when a Copper
        # was actually trashed (conditional on the player's choice resolving
        # with a Copper).
        TrashCards(min=0, max=1, filter_type=CardType.TREASURE),
        AddCoins(3),
        # TODO: AddCoins(3) should be conditional on a Copper being trashed.
    ],
    description="You may trash a Copper from your hand. If you do, +3 Coins.",
    art="moneylender.webp",
)

POACHER = Card(
    id="poacher",
    name="Poacher",
    cost=4,
    types=[CardType.ACTION],
    effects=[
        DrawCards(1),
        AddActions(1),
        AddCoins(1),
        # Discard a card per empty supply pile.
        # NOTE: models.py has no "DiscardPerEmptyPile" effect. The engine
        # must count empty supply piles at resolution time and enqueue
        # DiscardCards(min=n, max=n) where n = number of empty piles.
        # Represented here as a marker DiscardCards with min=0 to be replaced
        # by the engine at resolution.
        DiscardCards(min=0, max=0),
        # TODO: engine must substitute the correct min/max based on empty pile count.
    ],
    description="+1 Card, +1 Action, +1 Coin. Discard a card per empty Supply pile.",
    art="poacher.webp",
)

REMODEL = Card(
    id="remodel",
    name="Remodel",
    cost=4,
    types=[CardType.ACTION],
    effects=[
        TrashAndGainUpgrade(cost_increase=2),
    ],
    description="Trash a card from your hand. Gain a card costing up to 2 more than it.",
    art="remodel.webp",
)

SMITHY = Card(
    id="smithy",
    name="Smithy",
    cost=4,
    types=[CardType.ACTION],
    effects=[
        DrawCards(3),
    ],
    description="+3 Cards.",
    art="smithy.webp",
)

THRONE_ROOM = Card(
    id="throne_room",
    name="Throne Room",
    cost=4,
    types=[CardType.ACTION],
    effects=[
        ChooseCards(
            prompt="Choose an Action card from your hand to play twice.",
            zone=Zone.HAND,
            min=0,
            max=1,
            filter_type=CardType.ACTION,
        ),
        PlayCardTwice(),
    ],
    description="You may play an Action card from your hand twice.",
    art="throne_room.webp",
)

# ---------------------------------------------------------------------------
# Kingdom cards — cost 5
# ---------------------------------------------------------------------------

BANDIT = Card(
    id="bandit",
    name="Bandit",
    cost=5,
    types=[CardType.ACTION, CardType.ATTACK],
    effects=[
        GainCard(card_id="gold", to=Zone.DISCARD),
        ForEachOpponent(effects=[
            BanditAttack(),
        ]),
    ],
    description=(
        "Gain a Gold. "
        "Each other player reveals the top 2 cards of their deck, "
        "trashes a revealed Treasure other than Copper, and discards the rest."
    ),
    art="bandit.webp",
)

COUNCIL_ROOM = Card(
    id="council_room",
    name="Council Room",
    cost=5,
    types=[CardType.ACTION],
    effects=[
        DrawCards(4),
        AddBuys(1),
        ForEachOpponent(effects=[
            DrawCards(1),
        ]),
    ],
    description="+4 Cards, +1 Buy. Each other player draws a card.",
    art="council_room.webp",
)

FESTIVAL = Card(
    id="festival",
    name="Festival",
    cost=5,
    types=[CardType.ACTION],
    effects=[
        AddActions(2),
        AddBuys(1),
        AddCoins(2),
    ],
    description="+2 Actions, +1 Buy, +2 Coins.",
    art="festival.webp",
)

LABORATORY = Card(
    id="laboratory",
    name="Laboratory",
    cost=5,
    types=[CardType.ACTION],
    effects=[
        DrawCards(2),
        AddActions(1),
    ],
    description="+2 Cards, +1 Action.",
    art="laboratory.webp",
)

LIBRARY = Card(
    id="library",
    name="Library",
    cost=5,
    types=[CardType.ACTION],
    effects=[
        DrawToHandSize(target=7),
    ],
    description=(
        "Draw until you have 7 cards in hand, "
        "optionally setting aside Action cards as you draw them."
    ),
    art="library.webp",
)

MARKET = Card(
    id="market",
    name="Market",
    cost=5,
    types=[CardType.ACTION],
    effects=[
        DrawCards(1),
        AddActions(1),
        AddBuys(1),
        AddCoins(1),
    ],
    description="+1 Card, +1 Action, +1 Buy, +1 Coin.",
    art="market.webp",
)

MINE = Card(
    id="mine",
    name="Mine",
    cost=5,
    types=[CardType.ACTION],
    effects=[
        TrashAndGainUpgrade(
            cost_increase=3,
            filter_type=CardType.TREASURE,
            to=Zone.HAND,
            gain_filter_type=CardType.TREASURE,
        ),
    ],
    description="You may trash a Treasure from your hand. Gain a Treasure costing up to 3 more than it, putting it into your hand.",
    art="mine.webp",
)

SENTRY = Card(
    id="sentry",
    name="Sentry",
    cost=5,
    types=[CardType.ACTION],
    effects=[
        DrawCards(1),
        AddActions(1),
        InspectTopCards(n=2),
    ],
    description="+1 Card, +1 Action. Look at the top 2 cards of your deck. Trash and/or discard any number of them. Put the rest back in any order.",
    art="sentry.webp",
)

WITCH = Card(
    id="witch",
    name="Witch",
    cost=5,
    types=[CardType.ACTION, CardType.ATTACK],
    effects=[
        DrawCards(2),
        ForEachOpponent(effects=[
            GainCard(card_id="curse", to=Zone.DISCARD),
        ]),
    ],
    description="+2 Cards. Each other player gains a Curse.",
    art="witch.webp",
)

# ---------------------------------------------------------------------------
# Kingdom cards — cost 6
# ---------------------------------------------------------------------------

ARTISAN = Card(
    id="artisan",
    name="Artisan",
    cost=6,
    types=[CardType.ACTION],
    effects=[
        GainCardCosting(max_cost=5, to=Zone.HAND),
        ChooseCards(
            prompt="Put a card from your hand onto your deck.",
            zone=Zone.HAND,
            min=1,
            max=1,
            move_to=Zone.DECK,
        ),
    ],
    description="Gain a card costing up to 5 to your hand. Put a card from your hand onto your deck.",
    art="artisan.webp",
)

# ---------------------------------------------------------------------------
# Master collection
# ---------------------------------------------------------------------------

BASE_CARDS: dict[str, Card] = {
    card.id: card
    for card in [
        # Treasures
        COPPER,
        SILVER,
        GOLD,
        # Victories
        ESTATE,
        DUCHY,
        PROVINCE,
        # Curse
        CURSE,
        # Kingdom — cost 2
        CELLAR,
        CHAPEL,
        MOAT,
        # Kingdom — cost 3
        HARBINGER,
        MERCHANT,
        VASSAL,
        VILLAGE,
        WORKSHOP,
        # Kingdom — cost 4
        BUREAUCRAT,
        GARDENS,
        MILITIA,
        MONEYLENDER,
        POACHER,
        REMODEL,
        SMITHY,
        THRONE_ROOM,
        # Kingdom — cost 5
        BANDIT,
        COUNCIL_ROOM,
        FESTIVAL,
        LABORATORY,
        LIBRARY,
        MARKET,
        MINE,
        SENTRY,
        WITCH,
        # Kingdom — cost 6
        ARTISAN,
    ]
}

KINGDOM_CARDS: list[str] = [
    "cellar",
    "chapel",
    "moat",
    "harbinger",
    "merchant",
    "vassal",
    "village",
    "workshop",
    "bureaucrat",
    "gardens",
    "militia",
    "moneylender",
    "poacher",
    "remodel",
    "smithy",
    "throne_room",
    "bandit",
    "council_room",
    "festival",
    "laboratory",
    "library",
    "market",
    "mine",
    "sentry",
    "witch",
    "artisan",
]

assert len(KINGDOM_CARDS) == 26, f"Expected 26 kingdom cards, got {len(KINGDOM_CARDS)}"


# ---------------------------------------------------------------------------
# Supply setup
# ---------------------------------------------------------------------------

# Starting hand is 7 Coppers + 3 Estates; Coppers in the supply are reduced
# by the number given to players at game start.
_STARTING_COPPERS_PER_PLAYER = 7


def setup_supply(kingdom_card_ids: list[str], num_players: int) -> dict[str, int]:
    """Return initial supply counts for a game.

    Args:
        kingdom_card_ids: Exactly 10 kingdom card ids chosen for this game.
        num_players: Number of players (2–4).

    Returns:
        Mapping of card_id → initial count in supply.
    """
    if num_players < 2 or num_players > 4:
        raise ValueError(f"num_players must be 2–4, got {num_players}")
    if len(kingdom_card_ids) != 10:
        raise ValueError(f"Expected exactly 10 kingdom cards, got {len(kingdom_card_ids)}")

    victory_count = 8 if num_players == 2 else 12
    curse_count = 10 * (num_players - 1)
    starting_coppers = _STARTING_COPPERS_PER_PLAYER * num_players

    supply: dict[str, int] = {
        "copper": 60 - starting_coppers,
        "silver": 40,
        "gold": 30,
        "estate": victory_count,
        "duchy": victory_count,
        "province": victory_count,
        "curse": curse_count,
    }

    for card_id in kingdom_card_ids:
        supply[card_id] = 10

    return supply


# ---------------------------------------------------------------------------
# Register all cards with the engine's card registry on import
# ---------------------------------------------------------------------------

def _register_all() -> None:
    from engine import register_card
    for card in BASE_CARDS.values():
        register_card(card)

_register_all()
