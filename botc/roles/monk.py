from botc.scripts import register_role
from botc.model import Team, RoleType, Game


@register_role
class Monk:
    id = "Monk"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game):
        me = g.player(self.owner)
        if not me.alive:
            return
        # If poisoned-like, their protection is ineffective (we'll still log)
        cands = [p.id for p in g.alive_players() if p.id != me.id]
        if not cands:
            return
        pid = g.prompt.choose_one(self.owner, cands, "Protect a player")
        if pid is None:
            return
        if g.is_poisoned_like(self.owner):
            g.log.append(f"{me.name} (Monk) attempts to protect {g.player(pid).name}, but is poisoned")
            return
        g.protect(pid)
        g.log.append(f"{me.name} (Monk) protects {g.player(pid).name}")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
