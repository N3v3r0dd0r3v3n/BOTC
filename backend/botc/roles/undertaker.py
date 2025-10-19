from botc.scripts import register_role
from botc.model import Team, RoleType, Game


@register_role
class Undertaker:
    id = "Undertaker"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game):
        # Other nights only (after day executions)
        if g.night < 2:
            return
        me = g.player(self.owner)
        if not me.alive:
            return
        if g.last_executed_pid is None:
            return

        seen = g.player(g.last_executed_pid)
        true_role = getattr(seen.role, "id", "Unknown")

        # Poison: wrong role (simple fake)
        if g.is_poisoned(self.owner):
            g.log.append(f"{me.name} (Undertaker) learns {seen.name} was the ???")
        else:
            g.log.append(f"{me.name} (Undertaker) learns {seen.name} was the {true_role}")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
