"""`even_better`: better plus a supplier belief and one purposeful move per message."""

import json

from arena_kit.agents.better_agent import BetterAgent
from arena_kit.agents.even_better_agent import EvenBetterAgent
from tests.test_better_agent import _case, _mine, _sup


def _price(d):
    return d["message"]["term_sheets"][0]["terms"]["unit_price"]


def test_reply_with_several_sheets_is_cut_to_one():
    case = _case(payment_days=[14, 30, 60])
    ev = [_sup(30.0, 0)]
    assert len(BetterAgent().decide(case, {"t": ev})["message"]["term_sheets"]) > 1
    assert len(EvenBetterAgent().decide(case, {"t": ev})["message"]["term_sheets"]) == 1


def test_repeated_price_keeps_our_price_and_changes_one_lever():
    case = _case(payment_days=[14, 30, 60])
    ev = [_sup(30.0, 0), _mine(24.0), _sup(28.0, 1), _mine(25.0), _sup(28.0, 2)]
    d = EvenBetterAgent().decide(case, {"t": ev})
    t = d["message"]["term_sheets"][0]["terms"]
    assert len(d["message"]["term_sheets"]) == 1 and t["unit_price"] == 25.0 and t["payment_days"] != 30
    assert "We can meet you on payment_days" in d["message"]["body"]


def test_last_two_moves_are_betters_own():
    case = _case(payment_days=[14, 30, 60])
    case["round_limit"] = 3
    ev = [_sup(30.0, 0), _mine(24.0), _sup(28.0, 1), _mine(25.0), _sup(28.0, 2)]
    a, b = EvenBetterAgent().decide(case, {"t": ev}), BetterAgent().decide(case, {"t": ev})
    assert a["message"] == b["message"]


def test_belief_is_logged_with_the_why():
    ev = [_sup(30.0, 0), _mine(24.0), _sup(28.0, 1), _mine(25.0), _sup(28.0, 2)]
    d = EvenBetterAgent().decide(_case(payment_days=[14, 30, 60]), {"t": ev})
    belief = json.loads(json.dumps(d["why"]["belief"]))
    assert belief.keys() == {"values", "refuses", "uncertain", "resistance"} and belief["resistance"] == 1
