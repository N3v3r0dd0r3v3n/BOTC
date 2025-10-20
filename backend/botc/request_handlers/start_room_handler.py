import json

from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class StartRoomHandler(BaseHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error":"room_not_found"})
            return
        body = json.loads(self.request.body or b"{}")

        ok = room.setup_game()
        #ok = room.start_game(role_names)
        if not ok:
            self.set_status(400)
            self.write({"error":"cannot_start"})
            return
        room.broadcast()
        self.write({"ok": True, "assigned": "random"}) #role_names or "random"})