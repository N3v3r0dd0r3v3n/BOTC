from botc.scripts import register_role
from botc.model import Team, RoleType, Game

@register_role
class Baron:
    id = "Baron"
    team = Team.EVIL
    type = RoleType.MINION
    owner = None

    def on_setup(self, g: Game):
        g.log.append("Baron in play (setup note: +2 Outsiders)")

    def on_night(self, g: Game): pass
    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
