from botc.scripts import register_role
from botc.model import Team, RoleType, Game
from botc.view import role_view


@register_role
class Librarian:
    id = "Librarian"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None
    outsider = None
    wrong = None

    def on_setup(self, g: Game):
        me = g.player(self.owner)
        outsiders = [
            {"id": p.id,
             "name": p.name,
             "role": role_view(p.role)}
            for p in g.alive_players()
            if p.id != me.id and getattr(p.role, "type", None) == RoleType.OUTSIDER]
        if outsiders:
            g.request_setup_task(
                kind="select_outsider",
                role=self.id,
                owner_id=me.id,
                prompt="Pick an outsider for the Librarian",
                options=outsiders,
            )

    def apply_setup(self, kind: str, selection: dict, game: Game):
        if kind != "select_outsider" and kind != "select_wrong":
            return
        me = game.player(self.owner)
        if kind == "select_outsider":
            if selection['id'] in [p.id for p in game.alive_players()]:
                self.outsider = selection

            wrong_options = [
                {"id": player.id,
                 "name": player.name,
                 "role": role_view(player.role)}
                for player in game.alive_players()
                if player.id != me.id and player.id != selection['id']
            ]
            if wrong_options:
                game.request_setup_task(
                    kind="select_wrong",
                    role=self.id,
                    owner_id=me.id,
                    prompt="Pick wrong (bluff) for the Librarian",
                    options=wrong_options,
                )
        elif kind == "select_wrong":
            selected_wrong = selection.get("player_id")
            if selected_wrong in [p for p in game.alive_players()]:
                self.wrong = selected_wrong

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
