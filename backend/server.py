"""FastAPI WebSocket server for the Dominion card game.

Single endpoint: ws:// /ws
First message must be create_room or join_room.
All subsequent messages are game actions.
"""

from __future__ import annotations

import json
import os
import random
import uuid
from dataclasses import dataclass, field

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models import (
    BuyCard,
    ChooseResponse,
    CreateRoom,
    EndPhase,
    GameOver,
    GameState,
    JoinRoom,
    Phase,
    PlayCard,
    PlayerScore,
    PlayerState,
    StartGame,
    TurnState,
)
from engine import GameEngine
from views import make_player_view, player_view_to_dict
from cards.base import BASE_CARDS, KINGDOM_CARDS, setup_supply

# ---------------------------------------------------------------------------
# Room management
# ---------------------------------------------------------------------------

ROOM_WORDS = [
    "CROWN", "SWORD", "CASTLE", "THRONE", "KNIGHT",
    "SHIELD", "BANNER", "DRAGON", "FORGE", "REALM",
]


def generate_room_code() -> str:
    word = random.choice(ROOM_WORDS)
    digits = random.randint(1000, 9999)
    return f"{word}-{digits}"


@dataclass
class Room:
    code: str
    players: dict[str, WebSocket] = field(default_factory=dict)   # player_id → ws
    player_names: dict[str, str] = field(default_factory=dict)    # player_id → name
    host_id: str = ""
    engine: GameEngine | None = None
    started: bool = False

    def ordered_player_names(self) -> list[str]:
        """Return player names in insertion order."""
        return [self.player_names[pid] for pid in self.players]


# Global room registry: room_code → Room
rooms: dict[str, Room] = {}

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Dominion Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the built SvelteKit frontend if available.
_FRONTEND_BUILD = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "build"
)
if os.path.isdir(_FRONTEND_BUILD):
    app.mount("/", StaticFiles(directory=_FRONTEND_BUILD, html=True), name="frontend")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def send_error(ws: WebSocket, message: str) -> None:
    await ws.send_json({"type": "error", "message": message})


async def broadcast_state(room: Room) -> None:
    """Send each connected player their own personalised PlayerView."""
    if room.engine is None:
        return
    state = room.engine.state
    for player_id, ws in list(room.players.items()):
        try:
            view = make_player_view(state, player_id)
            await ws.send_json(
                {"type": "game_state", "state": player_view_to_dict(view)}
            )
        except Exception:
            # If a send fails we continue broadcasting to others.
            pass


async def broadcast_player_list(room: Room) -> None:
    """Broadcast current player list to everyone in the room."""
    names = room.ordered_player_names()
    for ws in list(room.players.values()):
        try:
            await ws.send_json({"type": "player_joined", "players": names})
        except Exception:
            pass


async def check_game_over(room: Room) -> bool:
    """Check for end-of-game, broadcast scores if over. Returns True if over."""
    if room.engine is None:
        return False
    if not room.engine.is_game_over():
        return False

    scores = room.engine.calculate_scores()  # dict of player_id → score
    score_list = [
        PlayerScore(player_name=room.player_names.get(pid, pid), score=sc)
        for pid, sc in scores.items()
    ]
    payload = GameOver(scores=score_list).model_dump()
    for ws in list(room.players.values()):
        try:
            await ws.send_json(payload)
        except Exception:
            pass
    return True


# ---------------------------------------------------------------------------
# Message handlers
# ---------------------------------------------------------------------------


async def handle_create_room(ws: WebSocket, msg: CreateRoom) -> tuple[str, Room] | tuple[None, None]:
    """Create a new room. Returns (player_id, room) on success, (None, None) on error."""
    # Generate a unique room code (retry on the tiny chance of collision).
    for _ in range(10):
        code = generate_room_code()
        if code not in rooms:
            break
    else:
        await send_error(ws, "Could not generate a unique room code — try again.")
        return None, None

    player_id = str(uuid.uuid4())
    room = Room(code=code, host_id=player_id)
    room.players[player_id] = ws
    room.player_names[player_id] = msg.player_name
    rooms[code] = room

    await ws.send_json(
        {
            "type": "room_created",
            "room_code": code,
            "players": room.ordered_player_names(),
        }
    )
    return player_id, room


async def handle_join_room(ws: WebSocket, msg: JoinRoom) -> tuple[str | None, Room | None]:
    """Join an existing room. Returns (player_id, room) on success."""
    code = msg.room_code.upper()
    room = rooms.get(code)
    if room is None:
        await send_error(ws, f"Room '{code}' not found.")
        return None, None
    if room.started:
        await send_error(ws, "That game has already started.")
        return None, None
    if len(room.players) >= 4:
        await send_error(ws, "Room is full (max 4 players).")
        return None, None

    player_id = str(uuid.uuid4())
    room.players[player_id] = ws
    room.player_names[player_id] = msg.player_name

    await broadcast_player_list(room)
    return player_id, room


async def handle_start_game(
    ws: WebSocket, msg: StartGame, room: Room, player_id: str
) -> None:
    if player_id != room.host_id:
        await send_error(ws, "Only the host can start the game.")
        return
    if room.started:
        await send_error(ws, "Game has already started.")
        return
    if len(room.players) < 2:
        await send_error(ws, "Need at least 2 players to start.")
        return

    # Resolve kingdom cards.
    all_kingdom_ids = list(KINGDOM_CARDS)
    if msg.kingdom == "random":
        kingdom_ids = random.sample(all_kingdom_ids, min(10, len(all_kingdom_ids)))
    else:
        # Validate supplied IDs.
        valid = set(all_kingdom_ids)
        bad = [k for k in msg.kingdom if k not in valid]
        if bad:
            await send_error(ws, f"Unknown kingdom card(s): {', '.join(bad)}")
            return
        kingdom_ids = list(msg.kingdom)[:10]

    # Build supply and player list in connection order.
    player_ids = list(room.players.keys())
    supply = setup_supply(kingdom_ids, num_players=len(player_ids))

    # Create starting decks (7 Copper + 3 Estate), shuffle, draw 5.
    players = []
    for pid in player_ids:
        deck = [BASE_CARDS["copper"]] * 7 + [BASE_CARDS["estate"]] * 3
        random.shuffle(deck)
        hand = deck[:5]
        deck = deck[5:]
        players.append(PlayerState(
            id=pid,
            name=room.player_names[pid],
            hand=hand,
            deck=deck,
            discard=[],
            in_play=[],
        ))

    state = GameState(
        room_code=room.code,
        supply=supply,
        trash=[],
        players=players,
        current_player=0,
        phase=Phase.ACTION,
        effect_queue=[],
        pending_choice=None,
        turn_state=TurnState(),
    )
    room.engine = GameEngine(state)
    room.started = True

    await broadcast_state(room)


async def handle_play_card(
    ws: WebSocket, msg: PlayCard, room: Room, player_id: str
) -> None:
    if not room.started or room.engine is None:
        await send_error(ws, "Game has not started.")
        return
    try:
        room.engine.play_card(player_id, msg.card_index)
    except Exception as exc:
        await send_error(ws, str(exc))
        return
    await broadcast_state(room)


async def handle_buy_card(
    ws: WebSocket, msg: BuyCard, room: Room, player_id: str
) -> None:
    if not room.started or room.engine is None:
        await send_error(ws, "Game has not started.")
        return
    try:
        room.engine.buy_card(player_id, msg.card_id)
    except Exception as exc:
        await send_error(ws, str(exc))
        return
    if not await check_game_over(room):
        await broadcast_state(room)


async def handle_end_phase(
    ws: WebSocket, msg: EndPhase, room: Room, player_id: str
) -> None:
    if not room.started or room.engine is None:
        await send_error(ws, "Game has not started.")
        return
    try:
        room.engine.end_phase(player_id)
    except Exception as exc:
        await send_error(ws, str(exc))
        return
    await broadcast_state(room)


async def handle_choose(
    ws: WebSocket, msg: ChooseResponse, room: Room, player_id: str
) -> None:
    if not room.started or room.engine is None:
        await send_error(ws, "Game has not started.")
        return
    try:
        room.engine.handle_choice(player_id, msg.choice)
    except Exception as exc:
        await send_error(ws, str(exc))
        return
    if not await check_game_over(room):
        await broadcast_state(room)


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    player_id: str | None = None
    room: Room | None = None

    try:
        # --- Handshake: first message must be create_room or join_room ---
        raw = await websocket.receive_text()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await send_error(websocket, "Invalid JSON.")
            await websocket.close()
            return

        msg_type = data.get("type")

        if msg_type == "create_room":
            msg = CreateRoom(**{k: v for k, v in data.items() if k != "type"})
            player_id, room = await handle_create_room(websocket, msg)
            if player_id is None:
                await websocket.close()
                return

        elif msg_type == "join_room":
            msg = JoinRoom(**{k: v for k, v in data.items() if k != "type"})
            player_id, room = await handle_join_room(websocket, msg)
            if player_id is None:
                await websocket.close()
                return

        else:
            await send_error(websocket, "First message must be 'create_room' or 'join_room'.")
            await websocket.close()
            return

        # --- Main message loop ---
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await send_error(websocket, "Invalid JSON.")
                continue

            msg_type = data.get("type")

            if msg_type == "start_game":
                kingdom_raw = data.get("kingdom", "random")
                msg = StartGame(kingdom=kingdom_raw)
                await handle_start_game(websocket, msg, room, player_id)

            elif msg_type == "play_card":
                msg = PlayCard(card_index=int(data.get("card_index", 0)))
                await handle_play_card(websocket, msg, room, player_id)

            elif msg_type == "buy_card":
                msg = BuyCard(card_id=str(data.get("card_id", "")))
                await handle_buy_card(websocket, msg, room, player_id)

            elif msg_type == "end_phase":
                msg = EndPhase()
                await handle_end_phase(websocket, msg, room, player_id)

            elif msg_type == "choose":
                choices = data.get("choice", [])
                if not isinstance(choices, list):
                    choices = [choices]
                msg = ChooseResponse(choice=choices)
                await handle_choose(websocket, msg, room, player_id)

            else:
                await send_error(websocket, f"Unknown message type: '{msg_type}'.")

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await send_error(websocket, f"Server error: {exc}")
        except Exception:
            pass
    finally:
        # Clean up: remove the player from their room and notify others.
        if room is not None and player_id is not None:
            room.players.pop(player_id, None)
            room.player_names.pop(player_id, None)

            if not room.players:
                # Last player left — remove the room entirely.
                rooms.pop(room.code, None)
            elif not room.started:
                # Room still in lobby — notify remaining players.
                await broadcast_player_list(room)
            # If game was in progress we leave the room so others can finish
            # (or detect the disconnect from the missing player in state).


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7478)
