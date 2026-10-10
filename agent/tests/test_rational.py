from arena_kit.agents import RationalAgent
from arena_kit.agents.rational import estimate_floor
from arena_kit.cost import total_cost

from test_kit import CASE


def _threads(prices, status="open", sent=()):
    ev = []
    for i, p in enumerate(prices):
        ev.append({"from": "sup:A", "status": status if i == len(prices) - 1 else "open",
                   "term_sheets": [{"term_sheet_id": f"o{i}", "terms": {"unit_price": p, "payment_days": 30}}]})
        if i < len(sent):
            ev.append({"from": "buyer", "term_sheets": [{"terms": {"unit_price": sent[i]}}]})
    return {"sup:A": ev}


def _alt(price):
    return {**CASE, "buyer": {**CASE["buyer"], "alternative": {"kind": "x", "ref": None, "terms": {"unit_price": price, "payment_days": 60}}}}


def test_accepts_agreed_offer_that_beats_reservation():
    msg = RationalAgent().decide(_alt(44.0), _threads([44.0, 40.0], "agreed", [38.0]))["message"]
    assert msg["action"] == {"type": "accept", "term_sheet_id": "o1"}


def test_never_accepts_worse_than_reservation():
    case = _alt(36.0)
    assert total_cost(case, {"unit_price": 40.0, "payment_days": 30}) > total_cost(case, case["buyer"]["alternative"]["terms"])
    msg = RationalAgent().decide(case, _threads([44.0, 40.0], "final_offer", [38.0]))["message"]
    assert msg["action"] == {"type": "walk_away"}


def test_opens_below_supplier_price_with_longer_payment():
    msg = RationalAgent().decide(CASE, _threads([44.0]))["message"]
    terms = msg["term_sheets"][0]["terms"]
    assert terms["unit_price"] < 44.0 * 0.9 and terms["payment_days"] == 90
    assert "alternative" not in msg["body"]


def test_crash_in_decide_closes_safely(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(RationalAgent, "_decide", boom)
    case = _alt(36.0)  # the standing 40.0 is worse than the alternative: no accept after a crash
    msg = RationalAgent().decide(case, _threads([44.0, 40.0]))["message"]
    assert msg["action"] == {"type": "walk_away"}
    good = RationalAgent().decide(_alt(60.0), _threads([44.0, 40.0]))["message"]
    assert good["action"]["type"] in {"accept", "walk_away"}  # closing_move's call, never a crash


def test_no_alternative_accepts_compliant_final_offer_above_opening():
    case = {**CASE, "buyer": {k: v for k, v in CASE["buyer"].items() if k != "alternative"}}
    msg = RationalAgent().decide(case, _threads([44.0, 45.0], "final_offer", [38.0]))["message"]
    assert "action" not in msg or msg["action"]["type"] == "accept"  # never a walk-away
    if "term_sheets" in msg:  # their price on our terms (they pay later), not a lower price
        assert msg["term_sheets"][0]["terms"]["unit_price"] == 45.0


def test_no_moves_left_worse_than_reservation_walks_away():
    case = {**_alt(36.0), "round_limit": 1}
    msg = RationalAgent().decide(case, _threads([44.0, 40.0], "open", [38.0]))["message"]
    assert msg["action"] == {"type": "walk_away"}


def test_estimate_floor():
    assert estimate_floor([100.0, 90.0, 85.0]) == 85.0 - 5.0 * 0.5 / 0.5  # geometric limit: 80
    assert estimate_floor([100.0, 90.0]) is None
    assert estimate_floor([100.0, 90.0, 95.0]) is None  # supplier went back up
