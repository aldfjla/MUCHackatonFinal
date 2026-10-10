"""`simplify` finishes every real-like mock case with a deal, must-haves ok, never worse than the opening cost; its sheets price the five parts of C."""

import pytest

from arena_kit import evaluate
from arena_kit.agents.simplify_agent import SimplifyAgent
from arena_kit.client import ArenaClient
from arena_kit.cost import cost_breakdown, total_cost
from arena_kit.data import DataPackage
from arena_kit.play import RemoteTable, hosted, play_all
from arena_kit.sim import load_cases
from arena_kit.sim_real import SimReal


@pytest.mark.skipif(not (evaluate.DEFAULT_DATA / "facts.json").is_file(), reason="no data package")
def test_simplify_closes_every_real_case():
    pytest.importorskip("uvicorn")  # the local arena needs the `sim` extra
    data = evaluate.DEFAULT_DATA
    cases = load_cases(evaluate.case_folder("real"))
    ids = [c["case_id"] for c in hosted(list(cases.values()))]
    sim = SimReal(cases, DataPackage(data).facts, "sim", no_clock=True, seed=0)
    sim.max_calls = 10**9
    with evaluate.Server(sim) as url:
        key = ArenaClient(url, api_key="x").register("simplify-0", "sim")["api_key"]
        client = ArenaClient(url, key, rate=1000)
        done = play_all(lambda: RemoteTable(client), ids, evaluate.agent_factory("simplify", data), 1)
    assert set(done) == set(ids)
    for cid, r in done.items():
        assert isinstance(r, dict), f"{cid}: {r!r}"
        assert r["deal"] and r["must_haves_ok"], f"{cid}: {r}"
        assert r["c_deal"] <= r["c_open"], f"{cid}: {r}"


def _agent_sheets(case, body=""):
    """The sheets simplify sends for a case whose supplier quotes 30.00 at its standard terms (`body`: its message)."""
    std = {"unit_price": 30.0, "payment_days": 30}
    events = [{"from": "supplier", "status": "open", "body": body, "term_sheets": [{"term_sheet_id": "a", "terms": std}]}]
    return SimplifyAgent()._sheets(case, events, std, std)


def _case(**options):
    b = {"need_per_year": 1000, "horizon_years": 2, "fallback_unit_price": 40.0, "interest_rate": 0.1, "reference_payment_days": 30,
         "freight_eur_per_unit": {"DAP": 0.0, "EXW": 2.0}, "need_lead_time_days": 10, "current_unit_price": 30.0, "alternative": None}
    return {"buyer": b, "negotiable": ["unit_price", *options], "term_options": options}


def test_index_variant_offered_when_negotiable_and_keeps_main_levers():
    clause = {"series": "steel", "material_share": 0.5, "deadband_pct": 2.0}
    case = _case(index_clause=[None, clause], payment_days=[30, 60])
    case["buyer"]["index_paths"] = {"steel": 0.10}
    case["buyer"]["index_risk_pct"] = 5
    main, *variant = _agent_sheets(case)
    assert variant and variant[0]["index_clause"] and variant[0]["payment_days"] == main["payment_days"] == 60
    case["negotiable"].remove("index_clause")
    assert not any(s.get("index_clause") for s in _agent_sheets(case))


def test_sheets_keep_need_covered():
    case = _case(contract_months=[6, 12, 24], volume_per_year=[500, 1000, 2000])
    sheets = _agent_sheets(case)
    assert sheets and all((s["contract_months"], s["volume_per_year"]) == (24, 1000) for s in sheets)
    assert all(cost_breakdown(case, s)["uncovered_need"] == 0 for s in sheets)


def test_levers_take_lowest_cost_option():
    case = _case(payment_days=[30, 60, 90], lead_time_days=[20, 10, 15], incoterm=["EXW", "DAP"], ppm_commitment=[500, 100])
    case["buyer"].update(late_cost_per_day=100, cost_per_defect=50)
    s = _agent_sheets(case)[0]
    assert (s["payment_days"], s["lead_time_days"], s["incoterm"], s["ppm_commitment"]) == (90, 10, "DAP", 100)


def test_pinned_payment_is_never_offered():
    case = _case(payment_days=[30, 60, 90])
    assert all(s["payment_days"] == 30 for s in _agent_sheets(case, "Our payment limit is 30 days."))


def test_must_have_beats_cheaper_option():
    case = _case(payment_days=[30, 60, 90])
    case["buyer"]["must_haves"] = [{"field": "payment_days", "op": "<=", "value": 60}]
    assert all(s["payment_days"] <= 60 for s in _agent_sheets(case))


def test_relationship_goal_eases_anchor_and_keeps_suppliers_terms():
    case = _case(payment_days=[30, 90])
    normal = _agent_sheets(case)[0]
    case["buyer"].update(category_goal="stabilise", relationship_eur_per_point=5000, sustainable_margin_pct=4)
    eased = _agent_sheets(case)[0]
    assert (normal["unit_price"], normal["payment_days"]) == (24.0, 90)
    assert (eased["unit_price"], eased["payment_days"]) == (27.0, 30)


def test_index_variant_takes_lowest_cost_deadband():
    lo = {"series": "steel", "material_share": 0.5, "deadband_pct": 0.0}
    hi = {**lo, "deadband_pct": 5.0}
    case = _case(index_clause=[None, lo, hi])
    case["buyer"].update(index_paths={"steel": 0.04}, index_risk_pct=0)  # a 4% rise: the deadband 5 clause costs nothing
    variant = _agent_sheets(case)[1]
    assert variant["index_clause"] == hi


def _thread(prices, mine=(24.0,)):
    """Supplier quotes `prices` in turn (30.00 standard terms), we answered `mine`."""
    ev = []
    for i, p in enumerate(prices):
        ev.append({"from": "supplier", "status": "open", "body": "", "term_sheets": [{"term_sheet_id": str(i), "terms": {"unit_price": p, "payment_days": 30}}]})
        if i < len(mine):
            ev.append({"from": "buyer", "term_sheets": [{"terms": {"unit_price": mine[i], "payment_days": 30}}]})
    return ev


def _next_price(prices, mine=(24.0,), c_open=float("inf")):
    case, std = _case(), {"unit_price": prices[0], "payment_days": 30}
    ev, agent = _thread(prices, mine), SimplifyAgent()
    agent._c_open = c_open
    sheets = agent._sheets(case, ev, std, ev[-1]["term_sheets"][0]["terms"])
    return sheets[0]["unit_price"], case


def test_stalled_supplier_gap_closes_to_five_percent():
    price, case = _next_price([30.0, 30.0, 30.0])
    c = lambda p: total_cost(case, {"unit_price": p, "payment_days": 30})
    assert 0.95 * c(30.0) - 0.05 <= c(price) <= 0.95 * c(30.0) + 0.05 and price <= 30.0


def test_moving_supplier_gets_no_extra_jump():
    price, _ = _next_price([30.0, 29.0, 28.0])
    assert price < 26.0


def test_no_jump_before_we_opened_or_seen_two_replies():
    assert _next_price([30.0, 30.0], mine=(24.0,))[0] < 26.0  # only one reply
    assert _next_price([30.0, 30.0, 30.0], mine=())[0] < 26.0  # no opening yet


def test_stalled_jump_never_passes_c_open():
    case = _case()
    c_open = total_cost(case, {"unit_price": 27.0, "payment_days": 30})
    price, _ = _next_price([30.0, 30.0, 30.0], c_open=c_open)
    assert price <= 27.01


def test_stalled_jump_rounding_stays_within_c_open():
    case = _case()
    c_open = total_cost(case, {"unit_price": 27.003, "payment_days": 30})  # between two cents
    price, _ = _next_price([30.0, 30.0, 30.0], c_open=c_open)
    assert total_cost(case, {"unit_price": price, "payment_days": 30}) <= c_open
