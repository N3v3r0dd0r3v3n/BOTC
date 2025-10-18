from botc.model import Team, RoleType, Game


class ScarletWoman:
    id = "Scarlet Woman"
    team = Team.EVIL
    type = RoleType.MINION
    owner = None

    # No night action. The promotion to Demon is handled by the engine
    # when a Demon dies and 5+ players are alive.
    def on_setup(self, g: Game): pass
    def on_night(self, g: Game): pass
    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass