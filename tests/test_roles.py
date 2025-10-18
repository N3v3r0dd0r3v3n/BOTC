from botc.cli import new_game
from botc.roles.imp import Imp
from botc.roles.slayer import Slayer
from botc.roles.fortune_teller import FortuneTeller
from botc.roles.empath import Empath
from botc.model import Phase


def test_slayer_kills_imp_if_targeted_in_day():
    g = new_game(["Eve", "Sam", "Kim"])
    imp = next(p for p in g.players if isinstance(p.role, Imp))
    sl = next(p for p in g.players if isinstance(p.role, Slayer))
    g.phase = Phase.DAY
    ok = sl.role.slay(g, imp.id)
    assert ok is True
    assert imp.alive is False


def test_slayer_only_once():
    g = new_game(["Eve", "Sam", "Kim"])
    imp = next(p for p in g.players if isinstance(p.role, Imp))
    sl = next(p for p in g.players if isinstance(p.role, Slayer))
    g.phase = Phase.DAY
    assert sl.role.slay(g, imp.id)
    assert sl.role.slay(g, imp.id) is False


def test_fortune_teller_logs_result():
    g = new_game(["Eve", "Sam", "Kim"])
    ft = next(p for p in g.players if isinstance(p.role, FortuneTeller))
    g.phase = g.phase.NIGHT
    ft.role.on_night(g)
    # Should have written a log line about seeing YES/NO
    assert any("sees" in line for line in g.log)


def test_empath_reports_number():
    g = new_game(["Eve", "Sam", "Kim", "Luke"])
    em = next(p for p in g.players if isinstance(p.role, Empath))
    g.phase = g.phase.NIGHT
    em.role.on_night(g)
    assert any("Empath" in line for line in g.log)


def test_basic_nomination_executes_on_majority():
    g = new_game(["A", "B", "C", "D"])
    # Move to day
    g.phase = g.phase.DAY
    # Nominate B by A, votes from A,C,D are for, B abstains
    g.start_nomination(1, 2)
    g.cast_vote(1, True)
    g.cast_vote(2, False)
    g.cast_vote(3, True)
    g.cast_vote(4, True)
    assert g.close_nomination() is True
    g.execute(2)
    assert g.player(2).alive is False
