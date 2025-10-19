import random
from botc.model import Team, RoleType, Game
from botc.scripts import register_role


@register_role
class Imp:
    id = "Imp"
    team = Team.EVIL
    type = RoleType.DEMON
    owner = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game):
        me = g.player(self.owner)
        if not me.alive:
            return
        candidates = g.alive_others(self.owner)
        if not candidates:
            return
        target = random.choice(candidates)
        g.demon_attack(target.id)

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass

