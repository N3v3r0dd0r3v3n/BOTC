import json

import tornado
from typing import Dict, Optional

from botc.rooms import GameRoom


class PlayerSocket(tornado.websocket.WebSocketHandler):
    def initialize(self, rooms: Dict[str, GameRoom]):
        self.rooms = rooms
        self.room: Optional[GameRoom] = None
        self.player_id: Optional[int] = None

    def check_origin(self, origin):
        return True  # dev only

    def open(self, gid: str, pid: str):
        room = self.rooms.get(gid)
        if not room:
            self.write_message(json.dumps({"type": "error", "error": "room_not_found"}))
            self.close(); return

        self.room = room
        self.player_id = int(pid)

        if not room.player_by_id(self.player_id):
            self.write_message(json.dumps({"type": "error", "error": "player_not_found"}))
            self.close(); return

        # track this socket
        room.player_sockets[self.player_id].add(self)

        self.send({"type": "hello", "gid": gid, "player_id": self.player_id})
        room.broadcast()

    def on_message(self, message):
        msg = json.loads(message)
        t = msg.get("type")
        if t == "seat":
            action = msg.get("action")
            if action == "sit":
                seat_no = int(msg.get("seat", 0))
                ok, err = self.room.sit(self.player_id, seat_no)
                if not ok:
                    self.send({"type": "error", "error": err})
                self.room.broadcast()
            elif action == "vacate":
                ok, err = self.room.vacate(self.player_id)
                if not ok:
                    self.send({"type": "error", "error": err})
                self.room.broadcast()
            else:
                self.send({"type": "error", "error": "unknown_seat_action"})
        else:
            self.send({"type": "error", "error": "unknown_message"})

    def on_close(self):
        if self.room and self.player_id is not None:
            self.room.player_sockets[self.player_id].discard(self)
            if not self.room.player_sockets[self.player_id]:
                del self.room.player_sockets[self.player_id]

    def send(self, obj):
        self.write_message(json.dumps(obj))
