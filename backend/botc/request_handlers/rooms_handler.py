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
        # create room: {name, script, initial_seat_count}
        body = json.loads(self.request.body or b"{}")
        creator = body.get("creator")
        #print("Creator is " + asdict(creator))
        room_name = body.get("name") or "Untitled Room"
        print(room_name)
        # For now default to trouble brewing
        script = trouble_brewing_script()
        seat_count = int(body.get("seat_count") or 8)
        gid = uuid.uuid4().hex[:8]
        # TODO Do I actually want to create a game right now?
        #g = new_game(initial_names)  # can be []
        room = GameRoom(gid, room_name, script, creator, seat_count)

        rooms[gid] = room  # <-- write to the same registry

        print(rooms)

        self.write({
            "gid": gid,
            "room": asdict(room.info),
            "seats": room.seats,
            #"seats": [{"seat": s.seat, "occupant": s.occupant} for s in room.seats],
        })
