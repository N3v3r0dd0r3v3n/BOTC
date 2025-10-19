import json
import tornado

from botc.rooms import rooms


class StartRoomHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error":"room_not_found"})
            return
        body = json.loads(self.request.body or b"{}")
        # optional explicit roles: ["Imp","Poisoner","Fortune Teller",...]
        role_names = body.get("roles")
        ok = room.start_game(role_names)
        if not ok:
            self.set_status(400)
            self.write({"error":"cannot_start"})
            return
        room.broadcast()
        self.write({"ok": True, "assigned": role_names or "random"})