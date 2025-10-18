from botc.model import Game, Player, Phase
from botc.rules import Rules
from botc.roles.imp import Imp
from botc.roles.slayer import Slayer
from botc.roles.fortune_teller import FortuneTeller


def new_game(names):
    players = [Player(id=i + 1, name=n, seat=i + 1) for i, n in enumerate(names)]
    g = Game(players=players, rules=Rules())
    g.assign_role(players[0].id, Imp())
    g.assign_role(players[1].id, Slayer())
    g.assign_role(players[2].id, FortuneTeller())
    g.night_order = ["Fortune Teller", "Imp"]

    for p in g.players:
        r = p.role
        if r and hasattr(r, "on_setup"): r.on_setup(g)
    return g


def run():
    g = new_game(["Eve", "Sam", "Kim", "Luke", "Anna"])
    while True:
        if g.phase == Phase.SETUP:
            g.step()
        elif g.phase == Phase.NIGHT:
            for role_name in g.night_order:
                for p in g.alive_players():
                    r = p.role
                    if r and getattr(r, "id", None) == role_name:
                        r.on_night(g)
            g.step()

        elif g.phase == Phase.DAY:
            slayer = next((p for p in g.alive_players() if isinstance(p.role, Slayer)), None)
            if slayer:
                target = next((p for p in g.alive_players() if p.id != slayer.id), None)
                if target:
                    slayer.role.slay(g, target.id)
            g.step()
        elif g.phase == Phase.FINAL_CHECK:
            if g.rules.check_end(g):
                print("\n".join(g.log))
                break
            g.step()
        else:
            g.step()


if __name__ == "__main__":
    run()
