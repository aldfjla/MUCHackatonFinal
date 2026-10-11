"""Combined2Agent (v8-petra): router between better and combined; CombinedCore's priced-ask fixes."""

import json
from pathlib import Path

from arena_kit.agents.combined2 import Combined2Agent, CombinedCore, route
from arena_kit.cli import agent_factory
from arena_kit.cost import total_cost

ROOT = Path(__file__).parent.parent / "arena_kit/sim_cases"


def case(pid):
    return json.loads((ROOT / "real" / f"{pid}.json").read_text())


def sup(sid, n, status="open", **terms):
    return {"from": "sales@x", "status": status, "body": "Our offer.", "attachments": [],
            "term_sheets": [{"term_sheet_id": f"offer:{sid}-{n}", "terms": terms}]}


def test_route_from_real_runs():
    got = {p: route(case(p)) for p in ("P01", "P02", "P03", "P04", "P05", "P07", "P08", "P10", "P11", "P18")}
    assert {p for p, r in got.items() if r == "combined"} == {"P08", "P18"}


def test_counter_from_their_cheapest_package():
    """Real P11: 46.50 / 1500 ppm / no chargeback, then 50.00 for our 300 ppm / 500 ask: the base goes back to 46.50."""
    c = case("P11")
    ev = [sup("A", 1, unit_price=46.5, ppm_commitment=1500, chargeback_eur_per_complaint=0.0),
          {"from": "buyer", "body": "", "term_sheets": [{"terms": {"unit_price": 40.0, "ppm_commitment": 300, "chargeback_eur_per_complaint": 500.0}}]},
          sup("A", 2, unit_price=50.0, ppm_commitment=300, chargeback_eur_per_complaint=500.0)]
    theirs = ev[-1]["term_sheets"][0]["terms"]
    base = CombinedCore._cheapest_theirs(c, ev, {}, theirs, lambda t: total_cost(c, t))
    assert base["unit_price"] == 46.5 and base["ppm_commitment"] == 1500


def test_small_non_price_ask_dropped_big_one_kept():
    """P11: a 300 ppm promise changes C by nothing (dropped); a 500 EUR chargeback at 1500 ppm saves ~1.5 % (kept)."""
    c = case("P11")
    theirs = {"unit_price": 46.5, "ppm_commitment": 1500, "chargeback_eur_per_complaint": 0.0}
    ours = {**theirs, "unit_price": 44.0, "ppm_commitment": 300, "chargeback_eur_per_complaint": 500.0}
    cost = lambda t: total_cost(c, t)  # noqa: E731
    out = CombinedCore._drop_small_asks(c, {}, [ours], theirs, cost)
    assert out[0]["ppm_commitment"] == 1500 and out[0]["chargeback_eur_per_complaint"] == 500.0
    assert out[0]["unit_price"] == 44.0


def test_router_builds_one_chain_per_case_and_decides():
    a = agent_factory("combined2", None)()
    assert isinstance(a, Combined2Agent)
    d = a.decide(case("P08"), {"sup:A": [sup("A", 1, unit_price=6.05, payment_days=30, contract_months=12, index_clause=None)]})
    assert a.chosen == "combined" and d["message"].get("term_sheets")
    d = a.decide(case("P11"), {"sup:A": [sup("A", 1, unit_price=47.0, ppm_commitment=1500, chargeback_eur_per_complaint=0.0)]})
    assert a.chosen == "better" and d["supplier_id"] == "sup:A"


def _ppm_case():
    """P11 with a fake C: our 300 ppm saves 3.00 of 1000 (< MIN_ASK), so it would normally go back to their 1500."""
    c = case("P11")
    theirs = {"unit_price": 46.5, "ppm_commitment": 1500, "chargeback_eur_per_complaint": 0.0}
    ours = {**theirs, "unit_price": 44.0, "ppm_commitment": 300}
    cost = lambda t: 1000.0 + (0.0 if t["ppm_commitment"] == 300 else 3.0)  # noqa: E731
    return c, theirs, ours, cost


def test_drop_small_ask_keeps_original_when_back_exceeds_upper():
    c, theirs, ours, cost = _ppm_case()
    assert CombinedCore._drop_small_asks(c, {}, [ours], theirs, cost)[0]["ppm_commitment"] == 1500  # unbounded: dropped
    out = CombinedCore._drop_small_asks(c, {}, [ours], theirs, cost, upper=1001.0)
    assert out[0] == ours  # 1003 > upper: keep our sheet


def test_drop_small_ask_keeps_original_when_back_was_sent():
    c, theirs, ours, cost = _ppm_case()
    back = CombinedCore._drop_small_asks(c, {}, [ours], theirs, cost)[0]
    out = CombinedCore._drop_small_asks(c, {}, [ours], theirs, cost, sent=[back])
    assert out[0] == ours  # never turn a sheet into one we already sent


def test_route_without_buyer_block_defaults_to_better():
    assert route({"negotiable": ["unit_price", "index_clause"]}) == "better"
    assert route({}) == "better"
