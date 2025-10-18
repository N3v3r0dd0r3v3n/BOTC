from __future__ import annotations

import asyncio
import json
import uuid
from collections import defaultdict
from typing import Dict, Optional, Set

import tornado.ioloop
import tornado.web
import tornado.websocket

import botc.roles  # ensure ROLE_REGISTRY is populated
from botc.cli import new_game  # reuse your factory
from botc.ws.prompt_bus import PromptBus
from botc.ws.ws_prompt import WsPrompt

from dataclasses import dataclass, asdict
from typing import Any, List
from botc.view import view_for_seat, view_for_player, view_for_storyteller

# ───────────────────────── Rooms ─────────────────────────

@dataclass
class Seat:
    number: int
    player_id: int | None = None

@dataclass
class RoomInfo:
    gid: str
    name: str
    script_name: str
    max_players: int
    status: str = "open"  # open | started | finished

class SitHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = ROOMS.get(gid)
        if not room:
            self.set_status(404); self.write({"error":"room_not_found"}); return
        body = json.loads(self.request.body or b"{}")
        try:
            pid = int(body.get("player_id"))
            seat_no = int(body.get("seat"))
        except (TypeError, ValueError):
            self.set_status(400); self.write({"error":"invalid_payload"}); return
        ok, err = room.sit(pid, seat_no)
        if not ok:
            self.set_status(409); self.write({"error": err}); return
        room.broadcast()
        self.write({"ok": True})

class VacateHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = ROOMS.get(gid)
        if not room:
            self.set_status(404); self.write({"error":"room_not_found"}); return
        body = json.loads(self.request.body or b"{}")
        try:
            pid = int(body.get("player_id"))
        except (TypeError, ValueError):
            self.set_status(400); self.write({"error":"invalid_payload"}); return
        ok, err = room.vacate(pid)
        if not ok:
            self.set_status(409); self.write({"error": err}); return
        room.broadcast()
        self.write({"ok": True})


class RoomViewerSocket(tornado.websocket.WebSocketHandler):
    """Anonymous room view: receives seat map & status updates, no actions."""
    def initialize(self, rooms: Dict[str, GameRoom]):
        self.rooms = rooms
        self.room: Optional[GameRoom] = None

    def open(self, gid: str):
        room = self.rooms.get(gid)
        if not room:
            self.write_message(json.dumps({"type":"error","error":"room_not_found"}))
            self.close(); return
        self.room = room
        room.add_room_viewer(self)
        # send initial state
        from botc.view import view_for_storyteller  # reuse; or make a dedicated "room view"
        self.send({"type":"state","view": view_for_storyteller(room.game, room)})
        # (We’re using the ST view here because it includes seats & status; it’s fine pre-game.)

    def on_message(self, message):
        # Read-only; ignore
        pass

    def on_close(self):
        if self.room:
            self.room.remove_room_viewer(self)

    def send(self, obj):
        self.write_message(json.dumps(obj))



class GameRoom:
    def __init__(self, gid: str, game, name: str, script_name: str, max_players: int):
        self.gid = gid
        self.game = game
        self.info = RoomInfo(gid=gid, name=name, script_name=script_name, max_players=max_players)
        self.bus = PromptBus()
        self.storyteller = None
        self.players = {}
        # install WsPrompt
        self.game.prompt = WsPrompt(self._send_to_storyteller, self.bus)

        self.room_viewers: Set["RoomViewerSocket"] = set()  # 👈 NEW: anonymous viewers
        self.player_sockets = defaultdict(set)  # (from earlier patch)

    def add_room_viewer(self, sock):
        self.room_viewers.add(sock)

    def remove_room_viewer(self, sock):
        self.room_viewers.discard(sock)

    def update_max_players(self, new_max: int) -> tuple[bool, str | None]:
        if new_max < 1:
            return False, "min_seats_is_1"
        current = len(self.game.players)
        if new_max < current:
            # Can't reduce below occupied seats
            return False, "cannot_reduce_below_current_player_count"
        self.info.max_players = new_max
        return True, None

    def is_full(self) -> bool:
        return len(self.game.players) >= self.info.max_players

    def add_player(self, player_name: str) -> dict | None:
        if self.info.status != "open" or self.is_full():
            return None
        seat = len(self.game.players) + 1
        from botc.model import Player
        p = Player(id=seat, name=player_name, seat=seat)
        self.game.players.append(p)
        return {"id": p.id, "seat": p.seat, "name": p.name}

    def start_game(self, role_names: List[str] | None = None):
        import random
        from botc.scripts import ROLE_REGISTRY
        from botc.cli import assign_by_names, default_roles_for

        # must be seated and within capacity
        if any(p.seat is None for p in self.game.players):
            return False  # some players unseated
        if len(self.game.players) > self.info.max_players:
            return False
        # normalize players by seat order 1..N
        seated = sorted([p for p in self.game.players if p.seat is not None], key=lambda p: p.seat)
        # reassign ids 1..N for engine consistency (optional, but tidy)
        for i, p in enumerate(seated, start=1):
            p.id = i
        self.game.players = seated

        n = len(self.game.players)
        if n == 0:
            return False

        if role_names is None:
            allowed = [r for r in self.game.script.roles if r in ROLE_REGISTRY]
            if len(allowed) < n:
                allowed = default_roles_for(n)
            chosen = random.sample(allowed, n) if len(allowed) >= n else allowed[:n]
        else:
            chosen = role_names

        # clear and assign
        for p in self.game.players:
            p.role = None
            p.alive = True
            p.ghost_vote_available = False

        assign_by_names(self.game, chosen)

        for p in self.game.players:
            if p.role and hasattr(p.role, "on_setup"):
                p.role.on_setup(self.game)

        self.info.status = "started"
        return True

    # broadcast helpers
    def _send_to_storyteller(self, payload: dict):

        if self.storyteller:
            self.storyteller.send({"type": "state", "view": view_for_storyteller(self.game, self)})

    def broadcast(self):
        # Push to all connected player sockets (id-scoped)
        for pid, socks in list(self.player_sockets.items()):
            view = view_for_player(self.game, pid, self)
            msg = {"type": "state", "view": view}
            for sock in list(socks):
                sock.send(msg)

        # Push to storyteller
        if self.storyteller:
            self.storyteller.send({"type": "state", "view": view_for_storyteller(self.game, self)})

        # Push to anonymous room viewers (everyone sees the same “room view”)
        if self.room_viewers:
            room_view = {"type": "state", "view": view_for_storyteller(self.game, self)}
            for v in list(self.room_viewers):
                v.send(room_view)

    # called by sockets
    def respond(self, cid: int, answer):
        self.bus.fulfill(cid, answer)
        self.broadcast()

    # ----- capacity & seating -----
    def seats_used(self) -> int:
        return sum(1 for p in self.game.players if p.seat is not None)

    def seat_map(self) -> list[dict]:
        """Return seat list 1..max_players with occupant info (or None)."""
        seats = []
        for n in range(1, self.info.max_players + 1):
            occ = next((p for p in self.game.players if p.seat == n), None)
            seats.append({
                "seat": n,
                "occupant": None if not occ else {"id": occ.id, "name": occ.name}
            })
        return seats

    def player_by_id(self, pid: int):
        return next((p for p in self.game.players if p.id == pid), None)

    def join_unseated(self, player_name: str) -> dict | None:
        """Add a player record with no seat yet."""
        if self.info.status != "open":
            return None
        # Generate a new player id (unique, independent from seat numbers)
        new_id = (max([p.id for p in self.game.players] or [0]) + 1)
        from botc.model import Player
        p = Player(id=new_id, name=player_name, seat=None)
        self.game.players.append(p)
        return {"id": p.id, "name": p.name, "seat": p.seat}

    def sit(self, pid: int, seat_no: int) -> tuple[bool, str | None]:
        if self.info.status != "open":
            return False, "room_not_open"
        if not (1 <= seat_no <= self.info.max_players):
            return False, "invalid_seat"
        p = self.player_by_id(pid)
        if not p:
            return False, "player_not_found"
        # seat must be empty
        if any(x.seat == seat_no for x in self.game.players):
            return False, "seat_occupied"
        p.seat = seat_no
        return True, None

    def vacate(self, pid: int) -> tuple[bool, str | None]:
        if self.info.status != "open":
            return False, "room_not_open"
        p = self.player_by_id(pid)
        if not p:
            return False, "player_not_found"
        p.seat = None
        return True, None


ROOMS: Dict[str, GameRoom] = {}

# ─────────────────────── WebSocket handlers ───────────────────────

class StorytellerSocket(tornado.websocket.WebSocketHandler):
    def initialize(self, rooms: Dict[str, GameRoom]):
        self.rooms = rooms
        self.room: Optional[GameRoom] = None

    def open(self, gid: str):
        room = self.rooms.get(gid)
        if not room:
            self.write_message(json.dumps({"type":"error","error":"room_not_found"}))
            self.close()
            return
        self.room = room
        room.storyteller = self
        self.send({"type":"hello","gid":gid})
        room.broadcast()

    def on_message(self, message):
        msg = json.loads(message)
        if msg.get("type") == "respond":
            cid = int(msg["cid"])
            answer = msg.get("answer")
            self.room.respond(cid, answer)
        elif msg.get("type") == "action":
            # (optional) storyteller controls like step-phase, nominate, execute, etc.
            # For now, we just no-op and rebroadcast.
            pass
        self.room.broadcast()

    def on_close(self):
        if self.room and self.room.storyteller is self:
            self.room.storyteller = None

    def send(self, obj):
        self.write_message(json.dumps(obj))

class PlayerSocket(tornado.websocket.WebSocketHandler):
    def initialize(self, rooms: Dict[str, GameRoom]):
        self.rooms = rooms
        self.room: Optional[GameRoom] = None
        self.seat: Optional[int] = None

    def open(self, gid: str, seat: str):
        room = self.rooms.get(gid)
        if not room:
            self.write_message(json.dumps({"type":"error","error":"room_not_found"}))
            self.close()
            return
        self.room = room
        self.seat = int(seat)
        room.players[self.seat] = self
        self.send({"type":"hello","gid":gid,"seat":self.seat})
        room.broadcast()

    def on_message(self, message):
        # (optional) player-driven actions later
        pass

    def on_close(self):
        if self.room and self.seat in self.room.players and self.room.players[self.seat] is self:
            del self.room.players[self.seat]

    def send(self, obj):
        self.write_message(json.dumps(obj))

# ───────────────────────── HTTP helpers ─────────────────────────

class NewRoomHandler(tornado.web.RequestHandler):
    def post(self):
        # Create a new game/room
        body = json.loads(self.request.body or b"{}")
        names = body.get("names") or ["Eve","Sam","Kim","Luke","Anna","Ben"]
        gid = uuid.uuid4().hex[:8]
        g = new_game(names)  # AutoPrompt gets replaced by WsPrompt in GameRoom
        room = GameRoom(gid, g)
        ROOMS[gid] = room
        self.write({"gid": gid, "seats": [{"id": p.id, "name": p.name} for p in g.players]})

class StepHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = ROOMS.get(gid)
        if not room:
            self.set_status(404); self.write({"error":"room_not_found"}); return
        # Drive one engine step (useful while no UI exists)
        room.game.step()
        room.broadcast()
        self.write({"ok": True, "phase": room.game.phase.name, "night": room.game.night})

class LobbyHandler(tornado.web.RequestHandler):
    def get(self):
        # list rooms
        rooms = []
        for room in ROOMS.values():
            g = room.game
            rooms.append({
                **asdict(room.info),
                "players": [{"id": p.id, "name": p.name, "alive": p.alive} for p in g.players],
                "seats_used": len(g.players),
            })
        self.write({"rooms": rooms})

    def post(self):
        # create room: {name, script, max_players, names?}
        body = json.loads(self.request.body or b"{}")
        name = body.get("name") or "Untitled Room"
        script_name = body.get("script") or "Trouble Brewing"
        max_players = int(body.get("max_players") or 15)
        initial_names = body.get("names") or []  # optional pre-fill seats

        gid = uuid.uuid4().hex[:8]
        # create an empty game (no players yet); your new_game will accept names list
        g = new_game(initial_names)  # can be [] — players can join later
        room = GameRoom(gid, g, name, script_name, max_players)
        ROOMS[gid] = room

        self.write({
            "gid": gid,
            "room": asdict(room.info),
            "seats": [{"id": p.id, "name": p.name} for p in g.players],
        })


class LobbyRoomHandler(tornado.web.RequestHandler):
    def delete(self, gid: str):
        room = ROOMS.get(gid)
        if not room:
            self.set_status(404); self.write({"error":"room_not_found"}); return
        # cancel outstanding prompts
        room.bus.cancel_all()
        del ROOMS[gid]
        self.write({"ok": True})


class JoinRoomHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = ROOMS.get(gid)
        if not room:
            self.set_status(404); self.write({"error":"room_not_found"}); return
        body = json.loads(self.request.body or b"{}")
        player_name = body.get("name")
        if not player_name:
            self.set_status(400); self.write({"error":"missing_name"}); return
        seat = room.join_unseated(player_name)
        if not seat:
            self.set_status(409); self.write({"error":"room_not_open"}); return
        room.broadcast()
        self.write({"ok": True, "player": seat, "max_players": room.info.max_players})


class StartRoomHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = ROOMS.get(gid)
        if not room:
            self.set_status(404); self.write({"error":"room_not_found"}); return
        body = json.loads(self.request.body or b"{}")
        # optional explicit roles: ["Imp","Poisoner","Fortune Teller",...]
        role_names = body.get("roles")
        ok = room.start_game(role_names)
        if not ok:
            self.set_status(400); self.write({"error":"cannot_start"}); return
        room.broadcast()
        self.write({"ok": True, "assigned": role_names or "random"})

class SeatsHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        # For idempotency, use POST with {"max_players": N}; you could use PATCH too.
        room = ROOMS.get(gid)
        if not room:
            self.set_status(404); self.write({"error":"room_not_found"}); return
        body = json.loads(self.request.body or b"{}")
        try:
            new_max = int(body.get("max_players"))
        except (TypeError, ValueError):
            self.set_status(400); self.write({"error":"invalid_max_players"}); return

        ok, err = room.update_max_players(new_max)
        if not ok:
            self.set_status(409); self.write({"error": err, "current_players": len(room.game.players)}); return

        room.broadcast()
        self.write({"ok": True, "max_players": room.info.max_players, "seats_used": len(room.game.players)})



class PlayerSocket(tornado.websocket.WebSocketHandler):
    def initialize(self, rooms: Dict[str, GameRoom]):
        self.rooms = rooms
        self.room: Optional[GameRoom] = None
        self.player_id: Optional[int] = None

    def open(self, gid: str, pid: str):
        room = self.rooms.get(gid)
        if not room:
            self.write_message(json.dumps({"type":"error","error":"room_not_found"}))
            self.close(); return
        self.room = room
        self.player_id = int(pid)
        # basic presence check
        if not room.player_by_id(self.player_id):
            self.write_message(json.dumps({"type":"error","error":"player_not_found"}))
            self.close(); return

        self.send({"type":"hello","gid":gid,"player_id":self.player_id})
        self._broadcast_self()

    def on_message(self, message):
        msg = json.loads(message)
        t = msg.get("type")
        if t == "seat":
            action = msg.get("action")
            if action == "sit":
                seat_no = int(msg.get("seat", 0))
                ok, err = self.room.sit(self.player_id, seat_no)
                if not ok:
                    self.send({"type":"error","error":err})
                self._broadcast_all()
            elif action == "vacate":
                ok, err = self.room.vacate(self.player_id)
                if not ok:
                    self.send({"type":"error","error":err})
                self._broadcast_all()
        # (Later: allow players to nominate/vote messages too)
        else:
            self.send({"type":"error","error":"unknown_message"})

    def on_close(self):
        pass

    def _broadcast_self(self):
        self.send({"type":"state", "view": view_for_player(self.room.game, self.player_id, self.room)})
    def _broadcast_all(self):
        # update everyone (players + storyteller)
        for sock in list(self.room.players.values()):
            # NB: self.room.players currently keyed by seat in your previous code.
            # If you want to keep that for in-game, it's fine; we’re not using it pre-game.
            pass
        # broadcast to all player sockets we have (we don't store them yet; simplest: just send to self)
        self._broadcast_self()
        if self.room.storyteller:
            self.room.storyteller.send({"type":"state","view": view_for_storyteller(self.room.game, self.room)})

    def send(self, obj):
        self.write_message(json.dumps(obj))



def make_app():
    return tornado.web.Application([
        # Lobby
        (r"/api/lobby", LobbyHandler),
        (r"/api/lobby/(.+)", LobbyRoomHandler),
        (r"/api/room/(.+)/join", JoinRoomHandler),
        (r"/api/room/(.+)/start", StartRoomHandler),
        (r"/api/room/(.+)/seats", SeatsHandler),

        # Engine stepping (you had this)
        (r"/api/new", NewRoomHandler),  # (optional legacy)
        (r"/api/room/(.+)/step", StepHandler),
        (r"/api/room/(.+)/sit", SitHandler),
        (r"/api/room/(.+)/vacate", VacateHandler),

        # WebSockets
        (r"/ws/(.+)/st", StorytellerSocket, {"rooms": ROOMS}),
        (r"/ws/(.+)/player/(\d+)", PlayerSocket, {"rooms": ROOMS}),
        (r"/ws/(.+)/room", RoomViewerSocket, {"rooms": ROOMS}),

    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8765)
    print("Server on http://localhost:8765")
    tornado.ioloop.IOLoop.current().start()
