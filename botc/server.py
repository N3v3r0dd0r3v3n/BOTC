import asyncio
import json
import uuid
from typing import Dict, Optional

import tornado.ioloop
import tornado.web
import tornado.websocket

import botc.roles  # ensure ROLE_REGISTRY is populated
from botc.cli import new_game  # reuse your factory
from botc.view import view_for_seat, view_for_storyteller
from botc.ws.prompt_bus import PromptBus
from botc.ws.ws_prompt import WsPrompt

# ───────────────────────── Rooms ─────────────────────────

class GameRoom:
    def __init__(self, gid: str, game):
        self.gid = gid
        self.game = game
        self.bus = PromptBus()
        self.storyteller: Optional["StorytellerSocket"] = None
        self.players: Dict[int, "PlayerSocket"] = {}

        # Install WsPrompt into the game (send to ST; await bus)
        self.game.prompt = WsPrompt(self._send_to_storyteller, self.bus)

    # broadcast helpers
    def _send_to_storyteller(self, payload: dict):
        if self.storyteller:
            self.storyteller.send(payload)

    def broadcast(self):
        # send player views
        for seat, sock in list(self.players.items()):
            try:
                sock.send({"type": "state", "view": view_for_seat(self.game, seat)})
            except Exception:
                pass
        # send storyteller view
        if self.storyteller:
            self.storyteller.send({"type": "state", "view": view_for_storyteller(self.game)})

    # called by sockets
    def respond(self, cid: int, answer):
        self.bus.fulfill(cid, answer)
        self.broadcast()

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

def make_app():
    return tornado.web.Application([
        (r"/api/new", NewRoomHandler),
        (r"/api/room/(.+)/step", StepHandler),
        (r"/ws/(.+)/st", StorytellerSocket, {"rooms": ROOMS}),
        (r"/ws/(.+)/(\d+)", PlayerSocket, {"rooms": ROOMS}),
    ], debug=True)

if __name__ == "__main__":
    app = make_app()
    app.listen(8765)
    print("Server on http://localhost:8765")
    tornado.ioloop.IOLoop.current().start()
