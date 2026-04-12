# Dominion — Development Rules

## What This Is
A web-based Dominion card game. Python backend (FastAPI + WebSockets) serves game logic. SvelteKit frontend renders state and collects player input. Server is truth — clients are renderers.

## Stack
- **Backend:** Python 3.12+, FastAPI, WebSockets, uvicorn
- **Frontend:** SvelteKit + TypeScript, Vite
- **Package mgmt:** uv (backend), npm (frontend)
- **No database.** Games live in memory.

## Key Docs
- [docs/overview.md](docs/overview.md) — Vision, feeling, art direction
- [docs/architecture.md](docs/architecture.md) — Full technical design

## Core Rules

- **Simple, robust, clever — in that order.** Always.
- **Server is truth.** Client never decides game state. Client sends intentions, server validates and resolves, server broadcasts the new state.
- **Cards are data, not code.** A card is a dataclass with an effect list. No card-specific logic in the engine. Adding a card = adding a data entry.
- **Effect queue drives everything.** Card effects decompose into atomic instructions. The engine pops and resolves them one at a time. Player choices pause the queue until answered.
- **PlayerView, not GameState.** Never send raw game state to clients. Project it into what that player is allowed to see.
- **Animations follow state.** The client animates transitions between states. It doesn't animate actions — it receives "before" and "after" and interpolates.
- **Mobile-first layout.** Cards must be playable on a phone screen. Tap to play, tap to select. Fan hand layout that works at any width.

## What NOT to Build
- No accounts, auth, or persistence
- No AI opponents
- No expansion cards until base set is complete and solid
- No drag-and-drop (tap/click to play)
- No chat system
- No spectator mode
- No card editor UI

## Code Style
- Python: dataclasses over dicts, type hints everywhere, no classes where functions suffice
- TypeScript: strict mode, types mirroring server models
- Svelte: one component per file, props over context, scoped CSS
- WebSocket messages: JSON with `type` field, validated on receive

## Directory Reference
```
backend/
  server.py        — FastAPI app, WebSocket handling, rooms
  engine.py        — game loop, effect queue
  models.py        — dataclasses (GameState, Card, Effect, etc.)
  cards/base.py    — base set card definitions
  views.py         — GameState → PlayerView projection
frontend/
  src/lib/
    components/    — Svelte UI components
    stores/        — reactive state (connection, game, UI)
    api/           — WebSocket client
    game/          — types, animation helpers
docs/              — overview, architecture
```
