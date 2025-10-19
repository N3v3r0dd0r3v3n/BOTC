import json
import uuid

import tornado

from botc.cli import new_game

from dataclasses import asdict

from botc.rooms import GameRoom, rooms


class LobbyHandler(tornado.web.RequestHandler):
    def get(self):
        # list rooms
        payload = []
        for room in rooms.values():  # <-- iterate the registry
            g = room.game
            payload.append({
                **asdict(room.info),
                "players": [{"id": p.id, "name": p.name, "alive": p.alive} for p in g.players],
                "seats_used": len(g.players),
            })
        self.write({"rooms": payload})

    def post(self):
        # create room: {name, script, max_players, names?}
        body = json.loads(self.request.body or b"{}")
        name = body.get("name") or "Untitled Room"
        script_name = body.get("script") or "Trouble Brewing"
        max_players = int(body.get("max_players") or 15)
        initial_names = body.get("names") or []  # optional pre-fill seats

        gid = uuid.uuid4().hex[:8]
        g = new_game(initial_names)  # can be []
        room = GameRoom(gid, g, name, script_name, max_players)

        rooms[gid] = room  # <-- write to the same registry

        self.write({
            "gid": gid,
            "room": asdict(room.info),
            "seats": [{"id": p.id, "name": p.name} for p in g.players],
        })