import json
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class RoomHandler(BaseHandler):
    def get(self, gid: str):
        print("Getting room details " + gid)
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error": "room_not_found"})
            return

        payload = {
            "ok": True,
            "storyteller_id": room.info.storyteller_id,
            "total_spectators": len(room.spectators),
            "total_players": len(room.players)
        }

        self.write(payload)
        return
