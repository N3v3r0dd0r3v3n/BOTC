import json
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class SeatsHandler(BaseHandler):
    def post(self, gid: str):
        # For idempotency, use POST with {"max_players": N}; you could use PATCH too.
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error":"room_not_found"})
            return
        body = json.loads(self.request.body or b"{}")
        try:
            new_max = int(body.get("max_players"))
        except (TypeError, ValueError):
            self.set_status(400)
            self.write({"error":"invalid_max_players"})
            return

        ok, err = room.update_max_players(new_max)
        if not ok:
            self.set_status(409)
            self.write({"error": err, "current_players": len(room.game.players)})
            return

        room.broadcast()
        self.write({
            "ok": True,
            "max_players": room.info.max_players,
            "counts": room.counts(),
            "seat_map": room.seat_map(),  # optional but useful for clients
        })
