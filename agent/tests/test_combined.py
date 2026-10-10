"""CombinedAgent (v6-petra): FinalAgent's visible steps + the Listener's supplier model."""

import json
from pathlib import Path

import pytest

from arena_kit.agents import CombinedAgent, GuardedAgent
from arena_kit.cli import agent_factory
from arena_kit.cost import must_haves_ok, total_cost

ROOT = Path(__file__).parent.parent / "arena_kit/sim_cases"


def case(pid):
    return json.loads((ROOT / "real" / f"{pid}.json").read_text())


def sup(body, status="open", sid="x", n=1, **terms):
    return {"from": "sales@x", "status": status, "body": body, "attachments": [],
            "term_sheets": [{"term_sheet_id": f"offer:{sid}-{n}", "terms": terms}] if terms else []}


def buyer(**terms):
    return {"from": "buyer", "body": "", "term_sheets": [{"terms": terms}]}


def sheets(d):
    return [s["terms"] for s in d["message"].get("term_sheets") or []]


P05 = dict(payment_days=30, lead_time_days=35)


def test_opening_is_alexs_anchor():
    d = CombinedAgent().decide(case("P05"), {"sup:A": [sup("Our offer.", unit_price=40.0, **P05)]})
    assert sheets(d)[0]["unit_price"] == pytest.approx(32.0, abs=0.02)  # 0.80 x their price


def test_visible_step_while_they_move():
    ev = [sup("Offer.", n=0, unit_price=40.0, **P05), buyer(unit_price=32.0, **P05),
          sup("We can move a little.", n=1, unit_price=39.0, **P05)]
    d = CombinedAgent().decide(case("P05"), {"sup:A": ev})
    assert sheets(d) and sheets(d)[0]["unit_price"] > 32.0  # a visible step up, below theirs
    assert sheets(d)[0]["unit_price"] < 39.0


def test_limit_holds_price_and_switches_to_packages():
    ev = [sup("Offer.", n=0, unit_price=40.0, **P05), buyer(unit_price=32.0, **P05),
          sup("No further concessions on price are possible.", n=1, unit_price=39.0, **P05)]
    d = CombinedAgent().decide(case("P05"), {"sup:A": ev})
    out = sheets(d)
    assert out, d
    assert all(t["unit_price"] <= 32.0 + 1e-9 for t in out)  # our price holds


def test_never_volunteers_14_days():
    ev = [sup("Offer.", n=0, unit_price=40.0, **P05)]
    for _ in range(3):
        d = CombinedAgent().decide(case("P05"), {"sup:A": ev})
        if not d["message"].get("term_sheets"):
            break
        assert all(t.get("payment_days", 30) >= 30 for t in sheets(d))
        ev = ev + [{"from": "buyer", "body": "", "term_sheets": d["message"]["term_sheets"]},
                   sup("We can move a little.", n=len(ev),
                       unit_price=ev[-1]["term_sheets"][0]["terms"]["unit_price"] - 0.5, **P05)]


def test_tied_terms_kept_in_the_try_after_a_final_offer():
    c = case("P10")
    base = {k: v for k, v in c["fixed_terms"].items()}
    a = {**base, "unit_price": 31.9, "volume_per_year": 23400, "contract_months": 24, "lead_time_days": 56}
    b = {**base, "unit_price": 34.9, "volume_per_year": 23400, "contract_months": 24, "lead_time_days": 35}
    final = {"from": "sales@x", "status": "final_offer", "body": "Final offer: 31.90 only with 56 days lead time.",
             "attachments": [], "term_sheets": [{"term_sheet_id": "offer:x-2", "terms": a},
                                                {"term_sheet_id": "offer:x-2-a", "terms": b}]}
    ev = [sup("Offer.", n=0, **{**base, "unit_price": 32.2, "volume_per_year": 19890, "lead_time_days": 56}),
          buyer(**{**base, "unit_price": 28.3, "volume_per_year": 23400, "lead_time_days": 35}), final]
    d = CombinedAgent().decide(c, {"sup:70410": ev})
    for t in sheets(d):  # if it tries a sheet, their 31.90 stays with 56 days
        if t["unit_price"] == pytest.approx(31.9):
            assert t["lead_time_days"] == 56
    if d["message"].get("action"):
        assert d["message"]["action"]["type"] == "accept"


def test_closing_takes_the_cheapest_valid_sheet_across_threads():
    c = case("P05")
    a = [sup("Offer.", sid="A", n=0, unit_price=33.0, **P05), buyer(unit_price=30.0, **P05),
         sup("This is our final offer.", status="final_offer", sid="A", n=1, unit_price=31.0, **P05)]
    b = [sup("Offer.", sid="B", n=0, unit_price=34.0, **P05), buyer(unit_price=30.0, **P05),
         sup("This is our final offer.", status="final_offer", sid="B", n=1, unit_price=32.5, **P05)]
    c = {**c, "round_limit": 2}  # no move left for a try: close
    d = CombinedAgent().decide(c, {"sup:A": a, "sup:B": b})
    assert d["supplier_id"] == "sup:A" and d["message"]["action"]["type"] == "accept"


@pytest.mark.parametrize("threads", [{}, {"sup:A": []}, {"sup:A": [sup(None)]},
                                     {"sup:A": [{"from": "sales@x", "body": None, "term_sheets": None}]}])
def test_no_crash_on_empty_or_none(threads):
    d = GuardedAgent(CombinedAgent()).decide(case("P05"), threads)
    assert "message" in d


def test_sheets_are_compliant_and_never_worse_than_the_opening():
    c = case("P05")
    ev = [sup("Offer.", n=0, unit_price=40.0, payment_days=30, lead_time_days=56)]  # breaks lead <= 42
    d = CombinedAgent().decide(c, {"sup:A": ev})
    opening = total_cost(c, ev[0]["term_sheets"][0]["terms"])
    for t in sheets(d):
        assert must_haves_ok(c, t)
        assert total_cost(c, t) <= opening


def test_registered_with_guard_and_evidence():
    a = agent_factory("combined", None)()
    assert type(a.delegate.delegate).__name__ == "CombinedAgent" and a.questions is False
