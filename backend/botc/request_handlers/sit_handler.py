import json
import tornado

from botc.rooms import rooms


class SitHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error":"room_not_found"})
            return
        body = json.loads(self.request.body or b"{}")
        try:
            pid = int(body.get("player_id"))
            seat_no = int(body.get("seat"))
        except (TypeError, ValueError):
            self.set_status(400)
            self.write({"error":"invalid_payload"})
            return
        ok, err = room.sit(pid, seat_no)
        if not ok:
            self.set_status(409)
            self.write({"error": err})
            return
        room.broadcast()
        self.write({"ok": True})
