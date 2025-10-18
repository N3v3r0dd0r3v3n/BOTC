from __future__ import annotations

from botc.scripts import register_role
from botc.model import Team, RoleType, Game


@register_role
class Butler:
    id = "Butler"
    team = Team.GOOD
    type = RoleType.OUTSIDER
    owner = None

    def __init__(self):
        self.master_pid: int | None = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game):
        # Pick a master (alive other). First & other nights.
        me = g.player(self.owner)
        if not me.alive:
            return
        cands = [p.id for p in g.alive_players() if p.id != me.id]
        if not cands:
            return
        pick = g.prompt.choose_one(self.owner, cands, "Choose your master")
        if pick is not None:
            self.master_pid = pick
            g.log.append(f"{me.name} (Butler) chooses {g.player(pick).name} as master")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
