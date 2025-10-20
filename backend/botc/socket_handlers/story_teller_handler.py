import json
from typing import Dict, Optional
import tornado

from botc.rooms import GameRoom


class StorytellerSocket(tornado.websocket.WebSocketHandler):
    def initialize(self, rooms: Dict[str, GameRoom]):
        self.rooms = rooms
        self.room: Optional[GameRoom] = None

    def check_origin(self, origin):
        return True

    def open(self, gid: str):
        room = self.rooms.get(gid)
        if not room:
            self.write_message(json.dumps({"type": "error", "error": "room_not_found"}))
            self.close()
            return
        self.room = room
        room.storyteller = self
        self.send({"type": "hello", "gid": gid})
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