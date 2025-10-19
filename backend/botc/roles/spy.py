from botc.scripts import register_role
from botc.model import Team, RoleType, Game


@register_role
class Spy:
    id = "Spy"
    team = Team.EVIL
    type = RoleType.MINION
    owner = None

    def on_setup(self, g: Game): pass

    def on_night(self, g: Game):
        # First & other nights: Storyteller shows the grimoire.
        # For CLI we just log a placeholder so order proceeds.
        me = g.player(self.owner)
        if me.alive:
            g.log.append(f"{me.name} (Spy) observes the grimoire")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
