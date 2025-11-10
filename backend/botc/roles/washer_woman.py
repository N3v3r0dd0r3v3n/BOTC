from botc.scripts import register_role
from botc.model import Team, RoleType, Game
from botc.view import role_view


@register_role
class WasherWoman:
    id = "Washer Woman"
    team = Team.GOOD
    type = RoleType.TOWNSFOLK
    owner = None
    townsfolk = None
    wrong = None

    def on_setup(self, g: Game):
        me = g.player(self.owner)
        townsfolk = [
            {"id": p.id,
             "name": p.name,
             "role": role_view(p.role)}
            for p in g.alive_players()
            if p.id != me.id and getattr(p.role, "type", None) == RoleType.TOWNSFOLK]
        if townsfolk:
            g.request_setup_task(
                kind="select_townsfolk",
                role=self.id,
                owner_id=me.id,
                prompt="Pick a townsfolk for the Washer Woman",
                options=townsfolk,
            )

    def apply_setup(self, kind: str, selection: dict, game: Game):
        if kind != "select_townsfolk" and kind != "select_wrong":
            return
        me = game.player(self.owner)
        if kind == "select_townsfolk":
            if selection['id'] in [p.id for p in game.alive_players()]:
                self.townsfolk = selection

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
                    prompt="Pick wrong (bluff) for the Washer Woman",
                    options=wrong_options,
                )
        elif kind == "select_wrong":
            selected_wrong = selection.get("player_id")
            if selected_wrong in [p for p in game.alive_players()]:
                self.wrong = selected_wrong

    def on_night(self, g: Game):
        # first night only
        if g.night != 1:
            return
        me = g.player(self.owner)
        if not me.alive:
            return
        # find a townsfolk (excluding me)
        townsfolk = [p for p in g.alive_players()
                     if p.id != me.id and getattr(p.role, "type", None) == RoleType.TOWNSFOLK]
        if not townsfolk:
            return
        t = townsfolk[0]
        # pick 1 correct, 1 random incorrect name (simple variant)
        others = [p for p in g.alive_players() if p.id not in {me.id, t.id}]
        if not others:
            return
        bluff = others[0]
        # POISON: invert truth (show two wrong names) – simple approach
        if g.is_poisoned(self.owner):
            g.log.append(f"{me.name} (Washerwoman) sees that {bluff.name} or {others[-1].name} is a townsfolk")
        else:
            g.log.append(f"{me.name} (Washerwoman) sees that {t.name} or {bluff.name} is a townsfolk")

    def on_day_start(self, g: Game): pass
    def on_death(self, g: Game): pass
    def on_execution(self, g: Game, executed_pid: int): pass
