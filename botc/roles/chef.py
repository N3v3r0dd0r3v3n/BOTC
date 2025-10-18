from botc.scripts import register_role
from botc.model import Team, RoleType, Game

@register_role
class Chef:
    id = "Chef"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game):
        if g.night != 1:
            return
        me = g.player(self.owner)
        if not me.alive:
            return
        players = g.players
        pairs = 0
        for i in range(len(players)):
            a, b = players[i], players[(i+1) % len(players)]
            a_evil = (getattr(a.role, "team", None) == Team.EVIL)
            b_evil = (getattr(b.role, "team", None) == Team.EVIL)
            # Recluse nuance ignored for now; keep it simple
            if a_evil and b_evil:
                pairs += 1
        if g.is_poisoned_like(self.owner):
            pairs = (pairs + 1) % 3  # small skew
        g.log.append(f"{me.name} (Chef) learns there are {pairs} pairs of evil neighbors")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
