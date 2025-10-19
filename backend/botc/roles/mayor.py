from botc.scripts import register_role
from botc.model import Team, RoleType, Game

@register_role
class Mayor:
    id = "Mayor"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None
    def on_setup(self, g: Game): pass
    def on_night(self, g: Game): pass
    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
