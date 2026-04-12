# Dominion — Overview

A web-based implementation of the Dominion deck-building card game. Play with friends over a shared link — no accounts, no installs. A medieval world rendered through grimdark fantasy meets art nouveau (Mucha) aesthetics, with AI-generated card art.

## The Feeling

Heavy parchment. Gilt edges catching torchlight. Cards that feel like artifacts pulled from a crumbling cathedral. The UI should feel like you're playing at a stone table in a candlelit hall — minimal chrome, maximal atmosphere. Money isn't a card — it's a coin. The kingdom supply isn't a row of cards — it's a market stall.

Every interaction should feel deliberate and smooth. Cards slide, fan, and settle with weight. No snapping, no teleporting. The game should flow like a conversation between players, not a spreadsheet of clicks.

## What Makes This Implementation Different

- **Art direction**: Grimdark fantasy x art nouveau. Every card is an AI-generated piece mixing Mucha's ornamental elegance with dark, weighty fantasy.
- **Tactile UI**: Coins clink. Cards have weight. The hand fans naturally. Playing a card feels like placing it on stone.
- **Simplicity of engine**: The game logic is a queue of atomic effects. Cards are pure data — no card-specific code in the engine. Adding a card means adding a data definition, not writing game logic.
- **Friends-first multiplayer**: Generate a room code, share a link, play. Nothing else.

## Scope

**MVP: Base Set**
- 7 treasure cards, 3 victory cards, 1 curse, 25 kingdom cards
- 2-4 players
- Full turn flow: Action → Buy → Clean-up
- Lobby with room codes

**Future: Extensible by Design**
- Architecture supports adding any expansion as a card data file
- Potential for custom card creation
- But none of this is built until the base set is rock-solid
