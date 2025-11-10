from botc.model import Phase
from botc.request_handlers.base_handler import BaseHandler
from botc.rooms import rooms


class StepHandler(BaseHandler):
    def post(self, gid: str):
        room = rooms.get(gid)
        if not room:
            self.set_status(404)
            self.write({"error": "room_not_found"})
            return

        room.game.advance()

        # Don't broadcast until the game has begun
        # This might change later as we get more into the game
        if room.game.phase != Phase.SETUP:
            room.broadcast()
        self.write({"ok": True, "phase": room.game.phase.name, "night": room.game.night})