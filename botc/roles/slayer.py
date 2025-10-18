from botc.model import Team, RoleType, Game

class Slayer:
    id = "Slayer"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def __init__(self):
        self.used = False

    def on_setup(self, g: Game): pass
    def on_night(self, g: Game): pass
    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass

    def slay(self, g: Game, target_pid: int) -> bool:
        if self.used or not g.player(self.owner).alive or g.phase.name != "DAY":
            return False
        self.used = True
        target = g.player(target_pid)
        if getattr(target.role, "type", None) == RoleType.DEMON:
            g.kill_now(target_pid)
        else:
            g.log.append("Slayer misses")
        return True

