"""`better`: simplify plus a c_open guard (real P02), a third sheet, a cost-share anchor, cash-short and late accept."""

import glob
import json
from pathlib import Path

import pytest

from arena_kit import evaluate
from arena_kit.agents import EvidenceAgent, GuardedAgent
from arena_kit.agents.better_agent import BetterAgent, HealthScope, _health, _with_health
from arena_kit.agents.reciprocal import case_c_open
from arena_kit.cost import total_cost
from arena_kit.docs import standard_terms
from arena_kit.evidence import load_package
from arena_kit.play import find_sheet

CASES = Path(evaluate.__file__).parent / "sim_cases"


needs_data = pytest.mark.skipif(load_package() is None, reason="no data package (set ARENA_DATA)")


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
            assert BetterAgent._est_c(case, ev, find_sheet(ev, m["action"]["term_sheet_id"]), std) <= c_open
        for s in m.get("term_sheets", []):
            assert BetterAgent._est_c(case, ev, s["terms"], std) <= c_open


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


def test_hold_for_final_counters_an_open_offer_but_closes_on_final_repeat_or_late():
    case = _hold_case()
    ev = [_sup(30.0, 0), _mine(24.0), _sup(24.0, 1)]  # open and met our price, 7 messages left
    assert BetterAgent().decide(case, {"t": ev})["message"].get("term_sheets")  # counter
    assert BetterAgent().decide(case, {"t": _status(ev, "final_offer")})["message"]["action"]["type"] == "accept"
    rep = [_sup(30.0, 0), _mine(24.0), _sup(28.0, 1), _mine(25.0), _sup(27.0, 2), _mine(26.0), _sup(27.0, 3)]  # same price twice: its floor
    assert BetterAgent().decide(case, {"t": rep})["message"]["action"]["type"] == "accept"
    late = [_sup(30.0, 0), _mine(24.0), _sup(27.0, 1), _mine(25.0), _sup(26.5, 2), _mine(25.5), _sup(26.0, 3), _mine(25.8), _sup(25.9, 4)]  # 4 sent
    case["round_limit"] = 6  # 2 left
    assert BetterAgent().decide(case, {"t": late})["message"]["action"]["type"] == "accept"  # <= 2 left
    BetterAgent.HOLD_FOR_FINAL = False
    try:
        assert BetterAgent().decide(_hold_case(), {"t": ev})["message"]["action"]["type"] == "accept"
    finally:
        BetterAgent.HOLD_FOR_FINAL = True


@needs_data
@pytest.mark.parametrize("pid", ["P01", "P02", "P03"])
def test_health_estimate_fits_the_arena_c_deal(pid):
    case = json.loads((CASES / "real" / f"{pid}.json").read_text())
    assert _health(case)["full_cost"] > 0
    dumps = [json.loads(Path(f).read_text()) for f in glob.glob(str(CASES / "real_runs*" / f"*_{pid}.json"))]
    deals = [d["result"] for d in dumps if d["result"].get("deal")]
    assert deals
    for r in deals:
        with _with_health(case):
            c = total_cost(case, r["terms"], {})
        assert abs(c / r["c_deal"] - 1) < 0.035, (pid, c, r["c_deal"])  # the should-cost sits 1-2 % above the fitted full cost


@needs_data
def test_p02_recorded_deal_is_not_chosen_and_the_price_stays_above_the_health_floor():
    case = json.loads((CASES / "real" / "P02.json").read_text())
    d = json.loads((CASES / "real_runs_v17" / "simplify_P02.json").read_text())
    recorded, msgs = d["result"]["terms"], d["threads"]["sup:70510"]["messages"]
    ev, std = msgs[: max(i for i, m in enumerate(msgs) if m["from"] != "buyer" and m.get("term_sheets")) + 1], {}
    ev = _status(ev, "open")
    c_open = BetterAgent()._open_c(case, {"sup:70510": ev})
    assert BetterAgent._est_c(case, ev, recorded, std) > c_open  # the recorded deal is the loss
    m = BetterAgent().decide(case, {"sup:70510": ev})["message"]
    assert m.get("action", {}).get("term_sheet_id") != d["result"]["offer_id"]
    for s in m.get("term_sheets", []):
        assert not (s["terms"]["unit_price"] == recorded["unit_price"] and s["terms"]["payment_days"] == recorded["payment_days"])
        assert BetterAgent._est_c(case, ev, s["terms"], std) < c_open


@needs_data
def test_full_stack_never_accepts_p02_final_and_never_walks():
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
            assert BetterAgent._est_c(case, ev, find_sheet(ev, m["action"]["term_sheet_id"]), {}) <= c_open
        else:
            assert all(BetterAgent._est_c(case, ev, s["terms"], {}) <= c_open for s in m["term_sheets"])
    assert m["term_sheets"][0]["terms"]["unit_price"] >= ask  # the final_offer is countered, not accepted or walked from
