import json
import uuid
from dataclasses import asdict

from botc.cli import new_game
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms
from botc.rooms import GameRoom
from botc.scripts import trouble_brewing_script


class RoomsHandler(BaseHandler):
    def post(self):
        # create room: {name, script, max_players}
        body = json.loads(self.request.body or b"{}")
        room_name = body.get("name") or "Untitled Room"
        # For now default to trouble brewing
        script = trouble_brewing_script()
        max_players = int(body.get("max_players") or 8)

        initial_names = body.get("names") or []  # optional pre-fill seats

        gid = uuid.uuid4().hex[:8]
        # TODO Do I actually want to create a game right now?
        g = new_game(initial_names)  # can be []
        room = GameRoom(gid, g, room_name, script, max_players)

        rooms[gid] = room  # <-- write to the same registry

        self.write({
            "gid": gid,
            "room": asdict(room.info),
            "seats": [{"id": p.id, "name": p.name} for p in g.players],
        })