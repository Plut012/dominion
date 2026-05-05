# Dominion — Overview

A web-based implementation of the Dominion deck-building card game. Play with friends over a shared link — no accounts, no installs. A world rendered in **Cosmic Nouveau** — art nouveau elegance fused with Moebius's surreal, vast linework. AI-generated card art.

## The Feeling

Dusty parchment. Soft light from somewhere you can't name. Cards that feel like fragments of a half-remembered vision — familiar subjects stretched into the cosmic and strange. The UI should feel like playing at a stone table in a hall whose ceiling opens to an impossible sky — minimal chrome, maximal atmosphere. Money isn't a card — it's a coin. The kingdom supply isn't a row of cards — it's a market stall.

Every interaction should feel deliberate and smooth. Cards slide, fan, and settle with weight. No snapping, no teleporting. The game should flow like a conversation between players, not a spreadsheet of clicks.

## What Makes This Implementation Different

- **Art direction**: Cosmic Nouveau — Mucha's ornamental elegance fused with Moebius's surreal vastness. See [docs/art-direction.md](art-direction.md).
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
