import json
import tornado
from typing import Dict, Optional

from botc.rooms import GameRoom
from botc.view import view_for_room


class RoomViewerSocket(tornado.websocket.WebSocketHandler):
    """Anonymous room view: receives seat map & status updates, no actions."""
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
        room.add_room_viewer(self)
        # send initial state
        initial = view_for_room(room.game, room)
        self.send({"type": "state", "view": initial})

    def on_message(self, message):
        # Read-only; ignore
        pass

    def on_close(self):
        if self.room:
            self.room.remove_room_viewer(self)

    def send(self, obj):
        self.write_message(json.dumps(obj))