import tornado

from botc.rooms import rooms


class StepHandler(tornado.web.RequestHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error":"room_not_found"})
            return
        # Drive one engine step (useful while no UI exists)
        room.game.step()
        room.broadcast()
        self.write({"ok": True, "phase": room.game.phase.name, "night": room.game.night})