from arena_kit.agents import ExplorerAgent
from arena_kit.cli import agent_factory
from arena_kit.cost import total_cost

from test_kit import CASE
from test_rational import _alt, _threads


def _terms(msg):
    return [s["terms"] for s in msg["term_sheets"]]


def test_sends_equivalent_packages_below_supplier_cost():
    msg = ExplorerAgent().decide(CASE, _threads([44.0]))["message"]
    sheets = _terms(msg)
    costs = [total_cost(CASE, t) for t in sheets]
    assert 2 <= len(sheets) <= 3 and len({t["payment_days"] for t in sheets}) == len(sheets)
    assert max(costs) - min(costs) <= 0.01 * min(costs)
    assert max(costs) < total_cost(CASE, {"unit_price": 44.0, "payment_days": 30})
    assert min(t["unit_price"] for t in sheets) < 44.0 * 0.95 + 0.01


def test_first_message_asks_question_without_leaking():
    msg = ExplorerAgent().decide(_alt(40.0), _threads([44.0]))["message"]
    assert "?" in msg["body"] and "alternative" not in msg["body"].lower()


def test_never_accepts_worse_than_reservation():
    case = _alt(36.0)
    msg = ExplorerAgent().decide(case, _threads([44.0, 40.0], "final_offer", [38.0]))["message"]
    assert msg["action"] == {"type": "walk_away"}


def test_accepts_agreed_better_offer():
    msg = ExplorerAgent().decide(_alt(44.0), _threads([44.0, 40.0], "agreed", [38.0]))["message"]
    assert msg["action"] == {"type": "accept", "term_sheet_id": "o1"}


def test_no_live_threads_does_not_crash():
    threads = {"sup:A": [{"from": "sup:A", "status": "walked_away", "term_sheets": []}]}
    assert ExplorerAgent().decide(CASE, threads)["message"]["action"] == {"type": "walk_away"}


def test_crash_falls_back_safely(monkeypatch):
    monkeypatch.setattr(ExplorerAgent, "_decide", lambda *a: 1 / 0)
    assert ExplorerAgent().decide(_alt(36.0), _threads([44.0, 40.0]))["message"]["action"] == {"type": "walk_away"}


def test_final_offer_counter_at_their_price():
    case = {**CASE, "buyer": {k: v for k, v in CASE["buyer"].items() if k != "alternative"}}
    msg = ExplorerAgent().decide(case, _threads([44.0, 45.0], "final_offer", [38.0]))["message"]
    best = _terms(msg)[0]
    assert "action" not in msg and best["unit_price"] == 45.0
    assert total_cost(case, best) < total_cost(case, {"unit_price": 45.0, "payment_days": 30})


def test_no_moves_left_worse_offer_walks_away():
    case = {**_alt(36.0), "round_limit": 1}
    msg = ExplorerAgent().decide(case, _threads([44.0, 40.0], "open", [38.0]))["message"]
    assert msg["action"] == {"type": "walk_away"}


def test_holds_packages_when_supplier_did_not_move():
    a, th = ExplorerAgent(), _threads([44.0])
    first = _terms(a.decide(CASE, th)["message"])
    th["sup:A"] += [{"from": "buyer"}, {"from": "sup:A", "status": "open", "term_sheets": [{"term_sheet_id": "o1", "terms": {"unit_price": 44.0, "payment_days": 30}}]}]
    assert _terms(a.decide(CASE, th)["message"]) == first


def _round(a, th, price):
    th["sup:A"] += [{"from": "buyer"}, {"from": "sup:A", "status": "open", "term_sheets": [{"term_sheet_id": "o1", "terms": {"unit_price": price, "payment_days": 30}}]}]
    return a.decide(CASE, th)["message"]


def _first_price(a, case=CASE):
    return min(t["unit_price"] for t in _terms(a.decide(case, _threads([44.0]))["message"]))


def test_patience_concession_at_left_2_and_3():
    for left in (2, 3):
        case = {**CASE, "round_limit": left + 1}  # one buyer message sent in the thread below
        a, th = ExplorerAgent(), _threads([44.0])
        first = _terms(a.decide(case, th)["message"])
        th["sup:A"] += [{"from": "buyer"}, {"from": "sup:A", "status": "open", "term_sheets": [{"term_sheet_id": "o1", "terms": {"unit_price": 44.0, "payment_days": 30}}]}]
        msg = a.decide(case, th)["message"]
        assert _terms(msg)[0]["unit_price"] > first[0]["unit_price"]
        assert "adjusting" in msg["body"] and "moved our price" not in msg["body"]


def test_reciprocity_concession_when_supplier_improves():
    a, th = ExplorerAgent(), _threads([44.0])
    first = _terms(a.decide(CASE, th)["message"])
    msg = _round(a, th, 43.0)
    assert _terms(msg)[0]["unit_price"] > first[0]["unit_price"] and "moved our price" in msg["body"]


def test_no_alternative_accepts_at_the_end():
    case = {**CASE, "buyer": {k: v for k, v in CASE["buyer"].items() if k != "alternative"}, "round_limit": 1}
    msg = ExplorerAgent().decide(case, _threads([44.0, 40.0], "open", [38.0]))["message"]
    assert msg["action"] == {"type": "accept", "term_sheet_id": "o1"}


def test_packages_never_cost_more_than_theirs_and_prices_positive():
    for price in (44.0, 5.0, 0.5):
        a = ExplorerAgent(anchor=0.9)
        sheets = _terms(a.decide(CASE, _threads([price]))["message"])
        theirs = total_cost(CASE, {"unit_price": price, "payment_days": 30})
        assert all(t["unit_price"] > 0 and total_cost(CASE, t) <= theirs for t in sheets)
        assert all(t["unit_price"] >= 0.5 * min(x["unit_price"] for x in sheets) for t in sheets)


def test_decide_is_idempotent_per_event_count():
    a, th = ExplorerAgent(), _threads([44.0])
    a.decide(CASE, th)
    _round(a, th, 43.0)
    state = dict(a.state[(CASE["case_id"], "sup:A")]["pref"])
    a.decide(CASE, th)
    assert a.state[(CASE["case_id"], "sup:A")]["pref"] == state


def test_agent_factory_explorer():
    assert agent_factory("explorer", None) is ExplorerAgent
