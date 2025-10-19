import json
import uuid
import tornado
from botc.cli import new_game
from botc.rooms import rooms
from botc.rooms import GameRoom


class RoomHandler(tornado.web.RequestHandler):
    def post(self):
        # Create a new game/room
        body = json.loads(self.request.body or b"{}")
        names = body.get("names") or ["Eve","Sam","Kim","Luke","Anna","Ben"]
        gid = uuid.uuid4().hex[:8]
        g = new_game(names)  # AutoPrompt gets replaced by WsPrompt in GameRoom
        room = GameRoom(gid, g)
        rooms[gid] = room
        self.write({"gid": gid, "seats": [{"id": p.id, "name": p.name} for p in g.players]})