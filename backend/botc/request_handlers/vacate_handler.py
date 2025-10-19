import json
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class VacateHandler(BaseHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error": "room_not_found"})
            return
        body = json.loads(self.request.body or b"{}")
        try:
            player_id = int(body.get("player_id"))
            seat = int(body.get("seat"))
        except (TypeError, ValueError):
            self.set_status(400)
            self.write({"error": "invalid_payload"})
            return
        ok, err = room.vacate(player_id, seat)
        if not ok:
            self.set_status(409)
            self.write({"error": err})
            return
        room.broadcast()
        self.write({"ok": True})
