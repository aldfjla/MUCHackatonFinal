"""The Listener: supplier model from real phrases, anti-repetition, currency packages, no crashes."""

import json
from pathlib import Path

import pytest

from arena_kit.agents.listener import ListenerAgent
from arena_kit.cost import must_haves_ok, total_cost
from arena_kit.guard import GuardedAgent
from arena_kit.listener import focus, supplier_model

ROOT = Path(__file__).parent.parent / "arena_kit/sim_cases"


def case(pid):
    return json.loads((ROOT / "real" / f"{pid}.json").read_text())


def run(pid, agent="evidence_router"):
    return json.loads((ROOT / "real_runs" / f"{agent}_{pid}.json").read_text())


def upto(pid, sid, n):
    """The thread as the buyer saw it after the supplier's n-th message (0 = the opening)."""
    msgs = run(pid)["threads"][sid]["messages"]
    idx = [i for i, m in enumerate(msgs) if m.get("from") != "buyer"][n]
    return msgs[: idx + 1]


def sup(body, status="open", **terms):
    return {
        "from": "sales@x",
        "status": status,
        "body": body,
        "term_sheets": [{"term_sheet_id": "offer:x-1", "terms": terms}] if terms else [],
    }


def buyer(**terms):
    return {"from": "buyer", "body": "", "term_sheets": [{"terms": terms}]}


# --- signals from real phrases ---------------------------------------------------------------


def test_capacity_full_is_a_hard_volume_constraint():
    m = supplier_model(case("P10"), upto("P10", "sup:70410", 1))
    assert m["currency"] == "capacity" and "volume_per_year" in m["hard"] and "volume_per_year" in m["frozen"]


def test_cash_short_supplier_has_payment_as_currency():
    m = supplier_model(case("P05"), upto("P05", "sup:70210", 1))
    assert m["currency"] == "payment" and "payment_days" in m["hard"]


def test_two_packages_price_the_payment_days():
    m = supplier_model(case("P18"), upto("P18", "sup:70740", 1))  # 6.10 at 90 days next to 6.00 at 30 days
    assert m["priced"]["payment_days"] == pytest.approx(0.10)
    assert m["preferred"]["payment_days"] == 30 and m["currency"] == "payment"


def test_small_moves_and_frozen_price_are_heard():
    m = supplier_model(case("P07"), upto("P07", "sup:70610", 2))  # "As your adjustment was minimal ..."
    assert m["small_moves"]
    m = supplier_model(case("P04"), upto("P04", "sup:70620", 2))  # "unable to offer further concessions"
    assert m["price_frozen"]


def test_dismissed_evidence_is_noted_and_focus_has_a_question():
    m = supplier_model(case("P10"), upto("P10", "sup:70410", 2))
    assert {"po", "sc"} <= m["dismissed"]
    f = focus(m, case("P10"))
    assert "capacity" in f["question"] and "volume_per_year" in f["frozen"]


# --- anti-repetition -------------------------------------------------------------------------


def test_capacity_full_stops_volume_asks_beyond_the_must_have():
    c = case("P10")
    a = ListenerAgent()
    d = a.decide(c, {"sup:70410": upto("P10", "sup:70410", 1)})
    vols = {s["terms"]["volume_per_year"] for s in d["message"]["term_sheets"]}
    assert vols <= {23400}  # only what the must-have needs (the guard's floor), never "more" as a lever
    assert any(s["terms"]["contract_months"] == 36 for s in d["message"]["term_sheets"])  # what could free capacity


def test_thirty_days_insisted_stops_ninety_day_asks():
    c = case("P05")
    d = ListenerAgent().decide(c, {"sup:70210": upto("P05", "sup:70210", 2)})
    days = [s["terms"]["payment_days"] for s in d["message"]["term_sheets"]]
    assert days and max(days) <= 30


def test_never_repeats_an_offer():
    c = case("P04")
    events = upto("P04", "sup:70620", 0)
    a = ListenerAgent()
    first = a.decide(c, {"sup:70620": events})["message"]["term_sheets"]
    events = (
        events
        + [{"from": "buyer", "body": "", "term_sheets": first}]
        + [
            sup(
                "We are unable to offer further concessions on this part.",
                unit_price=5.02,
                payment_days=90,
                contract_months=12,
            )
        ]
    )
    second = a.decide(c, {"sup:70620": events})
    sent = second["message"].get("term_sheets") or []
    assert all(s not in first for s in sent)


# --- packages --------------------------------------------------------------------------------


def test_packages_trade_payment_for_price_and_are_priced():
    c = case("P05")
    events = upto("P05", "sup:70210", 2)
    d = ListenerAgent().decide(c, {"sup:70210": events})
    sheets = [s["terms"] for s in d["message"]["term_sheets"]]
    assert 2 <= len(sheets) <= 3
    by_days = sorted(sheets, key=lambda t: t["payment_days"])
    assert (
        by_days[0]["unit_price"] < by_days[-1]["unit_price"]
        or by_days[0]["payment_days"] == by_days[-1]["payment_days"]
    )
    assert sheets[0]["payment_days"] <= 30  # leads with their currency
    for t in sheets:
        assert must_haves_ok(c, t) and total_cost(c, t) < total_cost(c, events[0]["term_sheets"][0]["terms"])


def test_final_offer_tries_a_longer_contract_at_their_price_then_accepts():
    c = case("P07")  # 12 months at 5.64 is worse than the alternative; 24 months at 5.64 is far better
    events = upto("P07", "sup:70610", 4)
    d = ListenerAgent().decide(c, {"sup:70610": events})
    t = d["message"]["term_sheets"][0]["terms"]
    assert t["unit_price"] == 5.64 and t["contract_months"] == 24
    events = events + [
        {"from": "buyer", "body": "", "term_sheets": [{"terms": t}]},
        sup("We can accept your terms.", status="agreed", **t),
    ]
    assert ListenerAgent().decide(c, {"sup:70610": events})["message"]["action"]["type"] == "accept"


# --- robustness ------------------------------------------------------------------------------


@pytest.mark.parametrize("body", [None, "", "x" * 5])
def test_no_crash_on_empty_text(body):
    c = case("P02")
    events = [sup(body, unit_price=370.96, payment_days=30, index_clause=None)]
    events[0]["body"] = body
    m = supplier_model(c, events)
    assert m["currency"] == "price"
    d = GuardedAgent(ListenerAgent()).decide(c, {"sup:70510": events})
    assert d["supplier_id"] == "sup:70510"


def test_no_crash_without_any_quote():
    c = case("P02")
    d = ListenerAgent().decide(c, {"sup:70510": [{"from": "sales@x", "status": "open", "body": None}]})
    assert "quote" in d["message"]["body"]


@pytest.mark.parametrize("path", sorted((ROOT / "real_runs").glob("*_P*.json")), ids=lambda p: p.stem)
def test_every_real_turn_gives_a_safe_decision(path):
    d = json.loads(path.read_text())
    c = case(d["case"])
    for sid, t in d["threads"].items():
        msgs = t["messages"]
        for i, m in enumerate(msgs):
            if m.get("from") == "buyer" or m.get("status") in ("walked_away", "no_bid"):
                continue
            dec = GuardedAgent(ListenerAgent()).decide(c, {sid: msgs[: i + 1]})
            msg = dec["message"]
            for s in msg.get("term_sheets") or []:
                assert must_haves_ok(c, s["terms"]) or not c["buyer"].get("must_haves")
            if (msg.get("action") or {}).get("type") == "accept":
                alt = (c["buyer"].get("alternative") or {}).get("terms") or {}
                terms = next(x for x in reversed(msgs[: i + 1]) if x.get("from") != "buyer")["term_sheets"][0]["terms"]
                assert not alt.get("unit_price") or total_cost(c, terms) < total_cost(c, alt)
