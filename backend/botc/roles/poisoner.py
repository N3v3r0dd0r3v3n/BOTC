from __future__ import annotations
from botc.model import Team, RoleType, Game
from botc.scripts import register_role


@register_role
class Poisoner:
    id = "Poisoner"
    team = Team.EVIL
    type = RoleType.MINION
    owner = None

    def __init__(self):
        self.poisoned_pid: int | None = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game):
        me = g.player(self.owner)
        if not me.alive:
            return
        candidates = [p.id for p in g.alive_players() if p.id != me.id]
        if not candidates:
            return
        pid = g.prompt.choose_one(self.owner, candidates, "Poison whom?")
        if pid is not None:
            self.poisoned_pid = pid
            g.log.append(f"{g.player(pid).name} is poisoned tonight")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
