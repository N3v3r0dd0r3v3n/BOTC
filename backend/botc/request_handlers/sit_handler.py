import json

from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class SitHandler(BaseHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error": "room_not_found"})
            return

        body = json.loads(self.request.body or b"{}")
        try:
            # prefer spectator_id, fall back to player_id for legacy callers
            spectator_id = int(body.get("spectator_id") or body.get("player_id"))
            seat_no = int(body.get("seat"))
        except (TypeError, ValueError):
            self.set_status(400)
            self.write({"error": "invalid_payload"})
            return

        ok, err = room.sit(spectator_id, seat_no)
        if not ok:
            self.set_status(409)
            self.write({"error": err})
            return

        room.broadcast()
        # return the created player and seat info
        self.write({"ok": True})
