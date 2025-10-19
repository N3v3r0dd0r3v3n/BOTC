import json
import tornado

from botc.model import rooms


class JoinRoomHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404); self.write({"error":"room_not_found"}); return
        body = json.loads(self.request.body or b"{}")
        player_name = body.get("name")
        if not player_name:
            self.set_status(400); self.write({"error":"missing_name"}); return
        seat = room.join_unseated(player_name)
        if not seat:
            self.set_status(409); self.write({"error":"room_not_open"}); return
        room.broadcast()
        self.write({"ok": True, "player": seat, "max_players": room.info.max_players})