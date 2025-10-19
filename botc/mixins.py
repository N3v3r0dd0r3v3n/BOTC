from __future__ import annotations

import json
import tornado.web
from .rooms import ROOMS, GameRoom


class JsonHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status=200):
        self.set_status(status)
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.finish(json.dumps(obj))

class RoomLookupMixin:
    room: GameRoom | None = None

    def get_room_or_404(self, gid: str) -> GameRoom:
        room = ROOMS.get(gid)
        if not room:
            raise tornado.web.HTTPError(404, reason="room_not_found")
        self.room = room
        return room
