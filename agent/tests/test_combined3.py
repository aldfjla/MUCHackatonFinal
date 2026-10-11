"""Combined3Agent (v11-petra experiment): combined2 + a supplier-floor estimate on our side only."""

import json
from pathlib import Path

from arena_kit.agents.combined3 import FLOOR_FACTOR, Combined3Agent, FloorCore, floor_estimate
from arena_kit.cli import agent_factory

ROOT = Path(__file__).parent.parent / "arena_kit/sim_cases"


def case(pid):
    return json.loads((ROOT / "real" / f"{pid}.json").read_text())


def sup(sid, n, status="open", **terms):
    return {"from": "sales@x", "status": status, "body": "Our offer.", "attachments": [],
            "term_sheets": [{"term_sheet_id": f"offer:{sid}-{n}", "terms": terms}]}


def buyer(price, **terms):
    return {"from": "buyer", "body": "", "term_sheets": [{"terms": {"unit_price": price, **terms}}]}


P08 = dict(payment_days=30, contract_months=24, index_clause=None)


def test_floor_estimate_by_goal_and_off_for_health():
    assert abs(floor_estimate(case("P08"), [sup("A", 1, unit_price=6.05, **P08)]) - 6.05 * FLOOR_FACTOR["leverage"]) < 1e-9
    assert floor_estimate(case("P02"), [sup("A", 1, unit_price=370.96)]) is None  # health route untouched
    assert floor_estimate(case("P08"), []) is None  # no quote yet


def test_small_gap_acts_like_combined2(monkeypatch):
    import arena_kit.agents.combined3 as c3

    monkeypatch.setitem(c3.FLOOR_FACTOR, "leverage", 0.99)
    assert floor_estimate(case("P08"), [sup("A", 1, unit_price=6.05, **P08)]) is None


def test_first_offer_no_higher_than_floor_and_not_under_anchor_floor():
    c, ev = case("P08"), [sup("A", 1, unit_price=6.05, **P08)]
    p = FloorCore()._price(c, ev, 6.05)
    assert 0.75 * 6.05 - 1e-9 <= p <= 6.05 * FLOOR_FACTOR["leverage"] + 1e-9


def test_counter_stays_under_target_then_moves_again():
    c = case("P08")
    target = 6.05 * FLOOR_FACTOR["leverage"] * 1.03
    ev = [sup("A", 1, unit_price=6.05, **P08), buyer(4.70), sup("A", 2, unit_price=5.60, **P08)]
    p = FloorCore()._price(c, ev, 5.60)
    assert p <= max(target, 4.70 + 0.011) + 1e-9
    # two tick-sized moves in a row: the normal step comes back (suppliers walk when we stop moving)
    ev = ev + [buyer(4.71), sup("A", 3, unit_price=5.55, **P08), buyer(4.72), sup("A", 4, unit_price=5.50, **P08)]
    assert FloorCore()._price(c, ev, 5.50) > 4.72 + 0.02


def test_early_accept_above_target_becomes_counter_final_offer_is_accepted():
    c = case("P08")
    accept = {"supplier_id": "sup:A", "message": {"action": {"type": "accept", "term_sheet_id": "offer:A-2"}}}
    ev = [sup("A", 1, unit_price=6.05, **P08), buyer(4.70, **P08), sup("A", 2, unit_price=5.60, **P08)]
    d = Combined3Agent._gate(c, {"sup:A": ev}, accept)
    assert d["message"].get("term_sheets") and d["message"]["term_sheets"][0]["terms"]["unit_price"] < 5.60
    ev[-1] = sup("A", 2, status="final_offer", unit_price=5.60, **P08)
    assert Combined3Agent._gate(c, {"sup:A": ev}, accept) is accept


def test_registered_and_decides():
    a = agent_factory("combined3", None)()
    d = a.decide(case("P08"), {"sup:A": [sup("A", 1, unit_price=6.05, **P08)]})
    assert d["message"].get("term_sheets")
    d = agent_factory("combined3", None)().decide(case("P02"), {"sup:A": [sup("A", 1, unit_price=370.96, payment_days=30)]})
    assert d["supplier_id"] == "sup:A"
