import json
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class SeatsHandler(BaseHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error": "room_not_found"})
            return
        body = json.loads(self.request.body or b"{}")
        try:
            new_seat_count = int(body.get("seat_count"))
        except (TypeError, ValueError):
            self.set_status(400)
            self.write({"error": "invalid_seat_count"})
            return

        ok, err = room.update_max_seats(new_seat_count)
        if not ok:
            self.set_status(409)
            self.write({"error": err, "seats": len(room.seats)})
            return

        room.broadcast()
        self.write({
            "ok": True
        })
