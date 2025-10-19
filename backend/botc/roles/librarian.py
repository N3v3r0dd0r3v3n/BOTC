from botc.scripts import register_role
from botc.model import Team, RoleType, Game

@register_role
class Librarian:
    id = "Librarian"
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
        outsiders = [p for p in g.players if getattr(p.role, "type", None) == RoleType.OUTSIDER]
        others = [p for p in g.players if p.id != me.id]
        if len(others) < 2:
            return
        if g.is_poisoned_like(self.owner) or not outsiders:
            a, b = others[0], others[1]
            g.log.append(f"{me.name} (Librarian) sees that {a.name} or {b.name} is an outsider")
        else:
            true = outsiders[0]
            bluff = next((p for p in others if p.id not in (me.id, true.id)), None)
            if not bluff:
                return
            g.log.append(f"{me.name} (Librarian) sees that {true.name} or {bluff.name} is an outsider")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
