"""`better`: simplify plus a c_open guard (real P02), a third sheet, a cost-share anchor, cash-short and late accept."""

import glob
import json
import math
import sys
from pathlib import Path

import pytest

from arena_kit import evaluate
from arena_kit.agents import EvidenceAgent, GuardedAgent
from arena_kit.agents.better_agent import BetterAgent, HealthScope, _c_at, _health, _vetoes, _with_health
from arena_kit.agents.reciprocal import case_c_open
from arena_kit.cost import total_cost
from arena_kit.docs import standard_terms
from arena_kit.evidence import load_package
from arena_kit.play import find_sheet

CASES = Path(evaluate.__file__).parent / "sim_cases"


needs_data = pytest.mark.skipif(load_package() is None, reason="no data package (set ARENA_DATA)")


P_STD = {"P01": (900, "FCA"), "P02": (250, "DAP"), "P03": (350, "DAP")}  # supplier standard ppm / incoterm (quote PDFs are not in the dumps)


def _std(pid):
    return {"payment_days": 30, "ppm_commitment": P_STD[pid][0], "incoterm": P_STD[pid][1], "chargeback_eur_per_complaint": 0, "tooling_eur": 0}


@pytest.fixture
def p02_quote(monkeypatch):
    """The dumps carry no quote PDF text: give every module P02's standard terms."""
    for name, mod in list(sys.modules.items()):
        if name.startswith("arena_kit") and hasattr(mod, "standard_terms"):
            monkeypatch.setattr(mod, "standard_terms", lambda events: _std("P02"))


def _offer_ok(case, ev, t, std):
    """Our offer is no worse than the opening package in the centre and the optimistic world."""
    with _with_health(case):
        return BetterAgent()._fits(case, {"t": ev}, )(ev, t, std)


def _accept_ok_centre(case, ev, t, std):
    """The weakest accept test (final offers): the centre-world C is within the centre-world c_open."""
    return BetterAgent._est_c(case, ev, t, std, 1) <= BetterAgent()._open_c(case, {"t": ev}, 1)


def _case(**options):
    b = {"need_per_year": 1000, "horizon_years": 2, "fallback_unit_price": 40.0, "interest_rate": 0.1, "reference_payment_days": 30,
         "freight_eur_per_unit": {"DAP": 0.0, "EXW": 2.0}, "need_lead_time_days": 10, "current_unit_price": 30.0, "alternative": None}
    return {"buyer": b, "negotiable": ["unit_price", *options], "term_options": options, "round_limit": 10}


def _sup(price, i, body="", **terms):
    return {"from": "supplier", "status": "open", "body": body, "term_sheets": [{"term_sheet_id": f"s{i}", "terms": {"unit_price": price, "payment_days": 30, **terms}}]}


def _mine(price):
    return {"from": "buyer", "term_sheets": [{"terms": {"unit_price": price, "payment_days": 30}}]}


def test_p02_never_accepts_or_offers_above_c_open():
    case = json.loads((CASES / "real" / "P02.json").read_text())
    msgs = json.loads((CASES / "real_runs_v17" / "simplify_P02.json").read_text())["threads"]["sup:70510"]["messages"]
    ends = [i for i, m in enumerate(msgs) if m["from"] != "buyer" and m.get("term_sheets")]
    agent = BetterAgent()
    for i in ends[1:]:  # every supplier reply the real run saw, the final_offer at 345.51 last
        ev = msgs[: i + 1]
        d = agent.decide(case, {"sup:70510": ev})
        c_open, std = BetterAgent()._open_c(case, {"sup:70510": ev}), standard_terms(ev)
        m = d["message"]
        if m.get("action", {}).get("type") == "accept":
            assert _accept_ok_centre(case, ev, find_sheet(ev, m["action"]["term_sheet_id"]), std)
        for s in m.get("term_sheets", []):
            assert _offer_ok(case, ev, s["terms"], std)


def test_third_sheet_is_equal_cost_with_shorter_payment_and_lower_price():
    case = _case(payment_days=[14, 30, 60])
    std = {"unit_price": 30.0, "payment_days": 30}
    ev = [_sup(30.0, 0)]
    out = BetterAgent()._sheets(case, ev, std, std)
    main, third = out[0], out[-1]
    assert len(out) == 3 or len(out) == 2 and "index_clause" not in main  # main, (variant,) third
    assert third["payment_days"] < main["payment_days"] and third["unit_price"] < main["unit_price"]
    assert abs(total_cost(case, third, std) - total_cost(case, main, std)) < 0.01 * total_cost(case, main, std)  # equal C up to a cent of price
    BetterAgent.THIRD_SHEET = False
    try:
        assert len(BetterAgent()._sheets(case, ev, std, std)) == len(out) - 1
    finally:
        BetterAgent.THIRD_SHEET = True


def test_cost_share_anchor_uses_the_index_drop_and_is_skipped_without_data():
    clause = {"series": "steel", "material_share": 0.5, "deadband_pct": 2.0}
    case = _case(index_clause=[None, clause])
    ev = [_sup(30.0, 0)]
    assert BetterAgent()._price(case, ev, 30.0) == 24.0  # no index path: the 0.80 rule
    case["buyer"]["index_paths"] = {"steel": -0.40}
    assert BetterAgent()._price(case, ev, 30.0) == 24.0  # max(0.75, 1 - 0.5 x 0.40) = 0.80 x 30
    case["buyer"]["index_paths"] = {"steel": -0.30}
    assert abs(BetterAgent()._price(case, ev, 30.0) - 0.85 * 30) < 1e-9


def test_cash_short_supplier_gets_a_shorter_payment_sheet():
    case = _case(payment_days=[14, 30, 60])
    std = {"unit_price": 30.0, "payment_days": 30}
    ev = [_sup(30.0, 0, body="We are short of cash this quarter.")]
    assert BetterAgent._cash_short(case, ev) and not BetterAgent._cash_short(case, [_sup(30.0, 0)])
    BetterAgent.THIRD_SHEET = False
    try:
        out = BetterAgent()._sheets(case, ev, std, std)
        assert len(out) == 2 and out[1]["payment_days"] < out[0]["payment_days"]
        assert len(BetterAgent()._sheets(case, [_sup(30.0, 0)], std, std)) == 1
    finally:
        BetterAgent.THIRD_SHEET = True


def test_late_accept_within_one_percent():
    case = _case()
    case["round_limit"] = 4
    ev = [_sup(30.0, 0), _mine(24.0), _sup(29.0, 1), _mine(26.0), _sup(28.9, 2)]  # 2 messages left; 28.9 is the best C
    d = BetterAgent().decide(case, {"t": ev})
    assert d["message"]["action"] == {"type": "accept", "term_sheet_id": "s2"}
    BetterAgent.LATE_ACCEPT = False
    try:
        assert BetterAgent().decide(case, {"t": ev})["message"].get("action") is None
    finally:
        BetterAgent.LATE_ACCEPT = True


def _hold_case():
    case = _case()
    case["round_limit"] = 8
    return case


def _status(ev, status):
    return [*ev[:-1], {**ev[-1], "status": status}]


def test_hold_for_final_counters_an_open_offer_but_closes_on_final_repeat_or_late(monkeypatch):
    monkeypatch.setattr(BetterAgent, "HOLD_FOR_FINAL", True)
    case = _hold_case()
    ev = [_sup(30.0, 0), _mine(24.0), _sup(24.0, 1)]  # open and met our price, 7 messages left
    assert BetterAgent().decide(case, {"t": ev})["message"].get("term_sheets")  # counter
    assert BetterAgent().decide(case, {"t": _status(ev, "final_offer")})["message"]["action"]["type"] == "accept"
    rep = [_sup(30.0, 0), _mine(24.0), _sup(28.0, 1), _mine(25.0), _sup(27.0, 2), _mine(26.0), _sup(27.0, 3)]  # same price twice: its floor
    assert BetterAgent().decide(case, {"t": rep})["message"]["action"]["type"] == "accept"
    late = [_sup(30.0, 0), _mine(24.0), _sup(27.0, 1), _mine(25.0), _sup(26.5, 2), _mine(25.5), _sup(26.0, 3), _mine(25.8), _sup(25.9, 4)]  # 4 sent
    case["round_limit"] = 6  # 2 left
    assert BetterAgent().decide(case, {"t": late})["message"]["action"]["type"] == "accept"  # <= 2 left
    monkeypatch.setattr(BetterAgent, "HOLD_FOR_FINAL", False)
    assert BetterAgent().decide(_hold_case(), {"t": ev})["message"]["action"]["type"] == "accept"


@needs_data
@pytest.mark.parametrize("pid", ["P01", "P02", "P03"])
def test_health_band_brackets_the_arena_c_deal(pid):
    """The arena's own C of every recorded deal lies inside the C band of the data-package estimate (no memorised factor)."""
    case = json.loads((CASES / "real" / f"{pid}.json").read_text())
    lo, hi = _health(case)["band"]
    dumps = [json.loads(Path(f).read_text()) for f in glob.glob(str(CASES / "real_runs*" / f"*_{pid}.json"))]
    deals = [d["result"] for d in dumps if d["result"].get("deal")]
    assert deals
    for r in deals:
        with _with_health(case):
            c_lo, c_hi = _c_at(case, r["terms"], _std(pid), lo), _c_at(case, r["terms"], _std(pid), hi)
        assert c_lo <= r["c_deal"] * 1.01 and c_hi >= r["c_deal"] * 0.99, (pid, c_lo, c_hi, r["c_deal"])  # 1%: the buyer rate, not the arena's fitted supplier rate


@needs_data
def test_p02_recorded_deal_is_not_chosen_and_the_price_stays_above_the_health_floor(p02_quote):
    case = json.loads((CASES / "real" / "P02.json").read_text())
    d = json.loads((CASES / "real_runs_v17" / "simplify_P02.json").read_text())
    recorded, msgs = d["result"]["terms"], d["threads"]["sup:70510"]["messages"]
    ev, std = msgs[: max(i for i, m in enumerate(msgs) if m["from"] != "buyer" and m.get("term_sheets")) + 1], _std("P02")
    ev = _status(ev, "open")
    c_open = BetterAgent()._open_c(case, {"sup:70510": ev})
    assert BetterAgent._est_c(case, ev, recorded, std) > c_open  # the recorded deal is the loss
    m = BetterAgent().decide(case, {"sup:70510": ev})["message"]
    assert m.get("action", {}).get("term_sheet_id") != d["result"]["offer_id"]
    for s in m.get("term_sheets", []):
        assert not (s["terms"]["unit_price"] == recorded["unit_price"] and s["terms"]["payment_days"] == recorded["payment_days"])
        assert _offer_ok(case, ev, s["terms"], std)


@needs_data
def test_full_stack_never_accepts_p02_final_and_never_walks(p02_quote):
    case = json.loads((CASES / "real" / "P02.json").read_text())
    msgs = json.loads((CASES / "real_runs_v17" / "simplify_P02.json").read_text())["threads"]["sup:70510"]["messages"]
    ends = [i for i, m in enumerate(msgs) if m["from"] != "buyer" and m.get("term_sheets") and m["status"] != "agreed"]
    assert msgs[ends[-1]]["status"] == "final_offer"
    for i in ends:
        ev = msgs[: i + 1]
        agent = EvidenceAgent(HealthScope(GuardedAgent(BetterAgent())), str(load_package().root))
        m = agent.decide(case, {"sup:70510": ev})["message"]
        c_open, ask = BetterAgent()._open_c(case, {"sup:70510": ev}), min(s["terms"]["unit_price"] for s in ev[-1]["term_sheets"])
        assert m.get("action", {}).get("type") != "walk_away", i
        if m.get("action", {}).get("type") == "accept":
            assert _accept_ok_centre(case, ev, find_sheet(ev, m["action"]["term_sheet_id"]), _std("P02"))
        else:
            assert all(_offer_ok(case, ev, s["terms"], _std("P02")) for s in m["term_sheets"])
    assert m["term_sheets"][0]["terms"]["unit_price"] >= ask  # the final_offer is countered, not accepted or walked from


@needs_data
def test_health_estimate_is_the_suppliers_should_cost_with_a_band():
    case = json.loads((CASES / "real" / "P02.json").read_text())
    h = _health(case)
    assert h["full_cost"] == 374.95 and h["interest_rate"] == case["buyer"]["interest_rate"]  # the supplier's own row, the buyer's rate
    assert h["band"][0] < 1 < h["band"][1]
    assert 0.03 <= h["band"][1] - 1 <= 0.06  # BAND_SPECIFIC, plus BAND_WEAK for a weak supplier


@needs_data
def test_pessimistic_band_guard_repairs_a_sheet_that_is_only_safe_at_the_estimate(p02_quote):
    case = json.loads((CASES / "real" / "P02.json").read_text())
    first = json.loads((CASES / "real_runs_v17" / "simplify_P02.json").read_text())["threads"]["sup:70510"]["messages"][0]
    ev = [first, _mine(360.0), _sup(369.0, 1, index_clause=None)]
    std, agent = _std("P02"), BetterAgent()
    c_open = agent._open_c(case, {"t": ev})
    sheet = ev[-1]["term_sheets"][0]["terms"]
    with _with_health(case):
        assert _c_at(case, sheet, std, 1) <= c_open < agent._est_c(case, ev, sheet, std)  # fine at the estimate, over at the pessimistic end
        d = agent._guard(case, {"t": ev}, {"supplier_id": "t", "message": {"action": {"type": "accept", "term_sheet_id": "s1"}}})
        assert d["message"].get("action") is None and d["why"]["rule"] in ("guard_repair", "not_walk")
        assert all(agent._fits(case, {"t": ev})(ev, s["terms"], std) for s in d["message"]["term_sheets"])


@needs_data
def test_final_offer_is_accepted_at_the_centre_when_only_the_pessimistic_end_fails(p02_quote):
    case = json.loads((CASES / "real" / "P02.json").read_text())
    first = json.loads((CASES / "real_runs_v17" / "simplify_P02.json").read_text())["threads"]["sup:70510"]["messages"][0]
    ev = [first, _mine(360.0), {**_sup(369.0, 1, index_clause=None), "status": "final_offer"}]
    with _with_health(case):
        d = BetterAgent()._guard(case, {"t": ev}, {"supplier_id": "t", "message": {"action": {"type": "accept", "term_sheet_id": "s1"}}})
    assert d["message"]["action"] == {"type": "accept", "term_sheet_id": "s1"}  # never walk or stall when accepting is no worse than c_open


def _fake_package(monkeypatch, rows, intel):
    from arena_kit.agents import better_agent

    monkeypatch.setattr(better_agent, "load_package", lambda: object())
    monkeypatch.setattr(better_agent, "_q", lambda pkg, sql, *a: rows if "should_cost" in sql else intel)


def _health_case():
    case = _case()
    case.update(parts=["p"], suppliers=["s1"])
    case["buyer"].update(category_goal="stabilise", relationship_eur_per_point=1000.0)
    return case


def test_health_band_widths_generic_specific_and_weak(monkeypatch):
    from arena_kit.agents.better_agent import BAND_GENERIC, BAND_SPECIFIC, BAND_WEAK

    case, own, generic = _health_case(), {"supplier_id": "s1", "unit_cost": 100.0, "price_unit": 1}, {"supplier_id": "", "unit_cost": 100.0, "price_unit": 1}
    ok = [{"equity_ratio_pct": 40.0, "credit_index": 200, "credit_index_12m_ago": 200}]
    for rows, intel, width in [([generic], ok, BAND_GENERIC), ([own], ok, BAND_SPECIFIC),
                               ([own], [{**ok[0], "equity_ratio_pct": 0.0}], BAND_SPECIFIC + BAND_WEAK),  # equity 0 is weak, not healthy
                               ([own], [{**ok[0], "credit_index": 190}], BAND_SPECIFIC + BAND_WEAK),
                               ([generic], [{**ok[0], "credit_index": 190}], BAND_GENERIC + BAND_WEAK)]:
        _fake_package(monkeypatch, rows, intel)
        h = _health(case)
        assert h["band"] == pytest.approx((1 - width, 1 + width)) and h["full_cost"] == 100.0


@needs_data
def test_accept_above_the_opening_price_is_tested_at_the_lower_end_too(p02_quote):
    """Priced above the opening, the accept's health term is less sensitive to the full cost: it is worse than the opening at
    the lower end of the band (+25k) although better at the pessimistic end (-4k)."""
    from arena_kit.agents.better_agent import _accept_ok

    case = json.loads((CASES / "real" / "P02.json").read_text())
    first = json.loads((CASES / "real_runs_v17" / "simplify_P02.json").read_text())["threads"]["sup:70510"]["messages"][0]
    ev = [first, _mine(360.0), _sup(375.0, 1, index_clause=None)]
    std, t = _std("P02"), ev[-1]["term_sheets"][0]["terms"]
    with _with_health(case):
        lo, hi = _health(case)["band"]
        assert BetterAgent._est_c(case, ev, t, std) <= BetterAgent()._open_c(case, {"t": ev})  # the old (pessimistic only) test passed
        assert BetterAgent._est_c(case, ev, t, std, lo) > BetterAgent()._open_c(case, {"t": ev}, lo)
        assert not _accept_ok(case, {"t": ev}, "t", t)
        final = {"t": [*ev[:-1], {**ev[-1], "status": "final_offer"}]}
        assert _accept_ok(case, final, "t", t) == (BetterAgent._est_c(case, ev, t, std, 1) <= BetterAgent()._open_c(case, final, 1))  # final: centre test only


def test_no_redirect_to_a_thread_that_fails_accept_ok():
    case = _case(incoterm=["DAP", "EXW"])
    case["buyer"]["alternative"] = {"terms": {"unit_price": 20.0, "payment_days": 30}}  # both standing sheets are worse than the alternative
    a = [_sup(30.0, 0, incoterm="DAP"), _mine(24.0), {**_sup(27.0, 1, incoterm="EXW"), "status": "final_offer"}]
    b = [_sup(30.0, 0, incoterm="DAP"), _mine(24.0), {**_sup(28.0, 1, incoterm="DAP"), "status": "final_offer"}]
    d = BetterAgent()._guard(case, {"A": a, "B": b}, {"supplier_id": "A", "message": {"action": {"type": "accept", "term_sheet_id": "s1"}}})
    assert d["message"].get("action") is None  # neither is acceptable: a counter, not a redirect


def test_accept_needs_the_best_complete_package_across_threads():
    case = _case(incoterm=["DAP", "EXW"])
    a = [_sup(30.0, 0, incoterm="DAP"), _mine(24.0), {**_sup(27.0, 1, incoterm="EXW"), "status": "final_offer"}]  # cheaper unit price, +2 freight: C of 29
    b = [_sup(30.0, 0, incoterm="DAP"), _mine(24.0), {**_sup(28.0, 1, incoterm="DAP"), "status": "final_offer"}]  # C of 28
    threads = {"A": a, "B": b}
    accept_a = {"supplier_id": "A", "message": {"action": {"type": "accept", "term_sheet_id": "s1"}}}
    assert _vetoes(case, threads, accept_a)  # closing rule: not the best complete package
    assert not _vetoes(case, threads, {**accept_a, "supplier_id": "B"})
    d = BetterAgent()._guard(case, threads, accept_a)
    assert d["supplier_id"] == "B" and d["message"]["action"] == {"type": "accept", "term_sheet_id": "s1"} and d["why"]["rule"] == "accept_best_package"
    assert BetterAgent().decide(case, threads)["supplier_id"] == "B"


def test_every_decision_carries_a_plain_why():
    case = _case()
    case["round_limit"] = 4
    ev = [_sup(30.0, 0), _mine(24.0), _sup(29.0, 1), _mine(26.0), _sup(28.9, 2)]
    for threads in ({"t": ev}, {"t": ev[:1]}):
        d = BetterAgent().decide(case, threads)
        why = json.loads(json.dumps(d["why"]))  # plain, serialisable
        assert {"rule", "c_open", "c_offer", "c_breakdown", "band", "alternative"} <= why.keys()
        assert why["c_offer"] is not None and abs(sum(why["c_breakdown"].values()) - why["c_offer"]) < 0.1 * len(why["c_breakdown"])
    assert BetterAgent().decide(case, {"t": ev})["why"]["rule"] == "late_accept"


def test_step_answers_their_move_in_full():
    from arena_kit.agents.simplify_agent import SimplifyAgent

    ev = [_sup(30.0, 0), _mine(24.0), _sup(27.0, 1)]  # they moved 3.0; frac x gap = 0.9
    assert abs(BetterAgent()._price(_case(), ev, 27.0) - 24.9) < 1e-9
    assert abs(SimplifyAgent()._price(_case(), ev, 27.0) - 24.75) < 1e-9  # MATCH 0.25 x 3.0


def test_step_never_exceeds_their_price():
    ev = [_sup(30.0, 0), _mine(24.0), _sup(26.0, 1), _mine(25.5), _sup(25.0, 2)]  # they dropped below our last offer
    assert BetterAgent()._price(_case(), ev, 25.0) == 25.0


# --- FIXED_PRICE_ALT + concession log ---------------------------------------------------------------------
def _hist(monkeypatch, series):
    monkeypatch.setattr(BetterAgent, "FIXED_TWIN", True)
    monkeypatch.setattr(BetterAgent, "INDEX_PREMIUM", True)
    """A fake data package whose index_values are `series` (None: no package)."""
    import arena_kit.agents.better_agent as ba
    monkeypatch.setattr(ba, "load_package", lambda: None if series is None else object())
    monkeypatch.setattr(ba, "_q", lambda pkg, sql, *p: [{"value": v} for v in series])


def _clause_case(index_paths=None):
    case = _case(index_clause=[None, {"series": "x", "material_share": 0.5, "deadband_pct": 0.0}], payment_days=[30])
    case["buyer"]["index_paths"] = index_paths or {"x": 0.05}
    case["buyer"]["horizon_years"] = 1
    return case


def _vol(sigma, drift=0.0, n=24):
    return [100 * math.exp(drift * i + sigma * (-1) ** i) for i in range(n)]


def _clause_sheet(case, price=28.0):
    return {"terms": {"unit_price": price, "payment_days": 30, "index_clause": case["term_options"]["index_clause"][1]}}


def _decide_fixed(case, monkeypatch, series, price=28.0):
    _hist(monkeypatch, series)
    ev = [_sup(30.0, 0), _mine(25.0), _sup(29.0, 1)]
    d = {"supplier_id": "t", "message": {"term_sheets": [_clause_sheet(case, price)]}}
    with _with_health(case):
        return BetterAgent()._with_fixed_price(case, {"t": ev}, d)["message"]["term_sheets"], ev


def test_fixed_price_sheet_always_beside_a_clause_sheet(monkeypatch):
    case = _clause_case()
    sheets, ev = _decide_fixed(case, monkeypatch, _vol(0.01))
    assert any(not s["terms"].get("index_clause") for s in sheets) and any(s["terms"].get("index_clause") for s in sheets)
    fixed = next(s["terms"] for s in sheets if not s["terms"].get("index_clause"))
    assert total_cost(case, fixed, {}) <= total_cost(case, _clause_sheet(case)["terms"], {}) + 1e-6  # fixed C no worse than the clause sheet offered


def test_clause_price_is_below_fixed_by_the_premium_derived_from_history(monkeypatch):
    case, gaps = _clause_case(), []
    for sigma in (0.005, 0.01, 0.02):
        sheets, _ = _decide_fixed(case, monkeypatch, _vol(sigma))
        fixed = next(s["terms"] for s in sheets if not s["terms"].get("index_clause"))
        clause = next(s["terms"] for s in sheets if s["terms"].get("index_clause"))
        prem = BetterAgent._index_premium(case, clause["index_clause"], fixed["unit_price"], 12)
        assert clause["unit_price"] <= fixed["unit_price"] - prem + 1e-9
        gaps.append(prem / fixed["unit_price"])
    assert gaps[0] < gaps[1] < gaps[2]  # monotone in volatility
    _hist(monkeypatch, _vol(0.01, 0.0))
    flat = BetterAgent._index_premium(case, case["term_options"]["index_clause"][1], 30.0, 12)
    _hist(monkeypatch, _vol(0.01, 0.01))
    assert BetterAgent._index_premium(case, case["term_options"]["index_clause"][1], 30.0, 12) > flat  # and in drift


def test_no_index_history_clause_sheet_is_at_least_as_good_in_expected_c(monkeypatch):
    case = _clause_case()
    sheets, ev = _decide_fixed(case, monkeypatch, None)
    fixed = next(s["terms"] for s in sheets if not s["terms"].get("index_clause"))
    clause = next(s["terms"] for s in sheets if s["terms"].get("index_clause"))
    assert BetterAgent._index_premium(case, clause["index_clause"], 30.0, 12) is None
    assert total_cost(case, clause, {}) <= total_cost(case, fixed, {}) + 1e-6


def test_concession_log_fields():
    case = _case()
    ev = [_sup(30.0, 0), _mine(24.0), _sup(29.0, 1)]
    why = BetterAgent().decide(case, {"t": ev})["why"]["concession"]
    assert why["round"] == 2 and why["ours"]["prev"] == 24.0 and why["ours"]["step"] == round(why["ours"]["new"] - 24.0, 2)
    assert why["supplier"] == {"prev": 30.0, "new": 29.0, "step": -1.0}
    assert isinstance(why["levers_changed"], list) and why["c_after"] is not None and why["c_before"] is not None


def _mirror_sheets(flag, **case_kw):
    case = _case(payment_days=[14, 30, 60, 90])
    case["buyer"].update(case_kw)
    std = {"unit_price": 30.0, "payment_days": 30}
    agent = BetterAgent()
    agent.PAY_MIRROR = flag
    return agent._sheets(case, [_sup(30.0, 0)], std, std)


def test_pay_mirror_keeps_the_suppliers_opening_payment_days():
    assert {s["payment_days"] for s in _mirror_sheets(True)} == {30}
    assert any(s["payment_days"] > 30 for s in _mirror_sheets(False))  # default: unchanged, asks for longer


def test_pay_mirror_is_off_when_health_is_at_stake():
    health = {"category_goal": "stabilise", "relationship_eur_per_point": 100.0}
    assert _mirror_sheets(True, **health) == _mirror_sheets(False, **health)


def _date_sheets(flag):
    case = _case(effective_date=["2026-11-01", "2027-01-01", "2027-04-01"])
    case["buyer"]["current_unit_price"] = 28.0  # price increase: the old price runs until the effective date
    std = {"unit_price": 30.0, "payment_days": 30}
    agent = BetterAgent()
    if flag is not None:
        agent.DATE_LEVER = flag
    return case, std, agent._sheets(case, [_sup(30.0, 0)], std, std)


def test_date_lever_picks_the_c_minimising_effective_date():
    case, std, sheets = _date_sheets(None)  # default on
    best = min(case["term_options"]["effective_date"], key=lambda o: total_cost(case, {**sheets[0], "effective_date": o}, std))
    assert sheets and all(s["effective_date"] == best for s in sheets)


def test_date_lever_off_keeps_the_default_effective_date():
    _, _, sheets = _date_sheets(False)
    assert sheets and {s["effective_date"] for s in sheets} == {"2026-11-01"}  # complete_offer default, not a lever


def _idx_sheets(monkeypatch, always):  # always: set explicitly on the instance
    _fake_package(monkeypatch, [{"supplier_id": "s1", "unit_cost": 20.0, "price_unit": 1}], [{"equity_ratio_pct": 40.0, "credit_index": 200, "credit_index_12m_ago": 200}])
    case = _health_case()  # a clause that only costs us (positive path): its sheet is not cheaper than main's
    case["term_options"] = {"index_clause": [None, {"series": "x", "material_share": 0.5, "deadband_pct": 0.0}]}
    case["negotiable"].append("index_clause")
    case["buyer"].update(index_paths={"x": 0.0}, index_risk_pct=50.0)
    std = {"unit_price": 30.0, "payment_days": 30}
    agent = BetterAgent()
    if always is not None:
        agent.IDX_SHEET_ALWAYS = always
    with _with_health(case):
        return agent._sheets(case, [_sup(30.0, 0)], std, std)


def test_health_index_sheet_only_when_cheaper_for_us_with_flag_off(monkeypatch):
    assert not any(s.get("index_clause") for s in _idx_sheets(monkeypatch, False))


def test_health_index_sheet_is_added_by_default(monkeypatch):  # v30 behaviour: IDX_SHEET_ALWAYS = True
    assert any(s.get("index_clause") for s in _idx_sheets(monkeypatch, None))


def _lead_sheets(flag):  # flag None: the class default
    case = json.loads((CASES / "real" / "P10.json").read_text())  # secure_supply: health at stake, lead_time_days [35, 42, 56], need 42
    std = {"unit_price": 30.0, "payment_days": 30}
    agent = BetterAgent()
    if flag is not None:
        agent.LEAD_LEVER = flag
    with _with_health(case):
        return {s["lead_time_days"] for s in agent._sheets(case, [_sup(30.0, 0, lead_time_days=54)], std, std)}


def test_lead_lever_picks_the_c_minimising_lead_time_in_a_health_case():
    assert _lead_sheets(True) == {35}  # plain C ties 35 / 42 (both on time): the shorter


def test_lead_lever_off_by_default_leaves_the_sheets_as_before():
    assert _lead_sheets(None) == _lead_sheets(False) == {42}
