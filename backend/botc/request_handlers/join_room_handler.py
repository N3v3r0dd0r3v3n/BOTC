import json
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class JoinRoomHandler(BaseHandler):
    def post(self, gid: str):
        print("Joining room " + gid)
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error": "room_not_found"})
            return
        body = json.loads(self.request.body or b"{}")

        spectator_id = body.get("id")
        spectator_name = body.get("name")
        if not spectator_name:
            self.set_status(400)
            self.write({"error": "missing_name"})
            return

        #If I am the story teller then don't add me.
        spectator = room.join_unseated(spectator_id, spectator_name)
        if not spectator:
            self.set_status(409)
            self.write({"error": "room_not_open"})
            return
        room.broadcast()
        self.write({"ok": True, "spectator": spectator, "total_spectators": len(room.spectators)})
