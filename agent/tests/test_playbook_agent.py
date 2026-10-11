"""PlaybookAgent: replays the best known package at the known floor, accepts near it, else leaves it to the delegate."""

import json

from arena_kit import playbook_build
from arena_kit.agents.playbook_agent import PlaybookAgent
from arena_kit.sim import CASES

KEY = "raw_material/leverage"
BEST = {"unit_price": 5.5, "payment_days": 90, "contract_months": 24, "index_clause": None}


def case(goal="leverage", must=()):
    c = json.loads((CASES / "real" / "P18.json").read_text())
    c["buyer"]["category_goal"], c["buyer"]["must_haves"] = goal, list(must)
    return c


def entry(**kw):
    return {"lowest_offered_price": 5.0, "c_min_price": None, "target": {"price_with_best_levers": 4.5},
            "best_deal": {"price": 5.5, "c_deal": 1e12, "terms": BEST}, **kw}


def sup(price, status="open", n=0):
    return {"from": "sales", "status": status, "term_sheets": [{"term_sheet_id": f"o{n}", "terms": {"unit_price": price, "payment_days": 30, "contract_months": 12, "index_clause": None}}]}


def thread(*prices, status="open"):
    ev = []
    for i, p in enumerate(prices):
        ev.append(sup(p, status if i == len(prices) - 1 else "open", i))
        if i < len(prices) - 1:
            ev.append({"from": "buyer", "term_sheets": [{"terms": BEST}]})
    return {"sup:1": ev}


class Delegate:
    def __init__(self):
        self.calls = 0

    def decide(self, case, threads):
        self.calls += 1
        return {"supplier_id": "sup:1", "message": {"body": "delegate"}}


def agent(e=None, goal_key=KEY):
    d = Delegate()
    return PlaybookAgent(d, {"sup:1": {goal_key: e or entry()}}), d


def sheet(r):
    return r["message"]["term_sheets"][0]["terms"]


def test_first_sheet_is_best_package_two_percent_below_floor():
    a, d = agent()
    t = sheet(a.decide(case(), thread(6.1)))
    assert t["unit_price"] == 4.9 and t["payment_days"] == 90 and t["contract_months"] == 24 and d.calls == 0


def test_second_move_is_the_floor_and_target_is_ignored():
    a, _ = agent(entry(lowest_offered_price=4.4))
    assert sheet(a.decide(case(), thread(6.1)))["unit_price"] == 4.31
    a, _ = agent()
    assert sheet(a.decide(case(), thread(6.1, 5.6)))["unit_price"] == 5.0


def test_accepts_within_one_percent_of_floor():
    a, d = agent()
    r = a.decide(case(), thread(6.1, 5.04))
    assert r["message"]["action"] == {"type": "accept", "term_sheet_id": "o1"} and d.calls == 0


def test_deviation_hands_the_thread_to_the_delegate():
    a, d = agent()
    a.decide(case(), thread(6.1, 5.6))
    assert a.decide(case(), thread(6.1, 5.6, 5.6))["message"]["body"] == "delegate" and d.calls == 1
    a.decide(case(), thread(6.1, 5.6, 5.6))  # stays with the delegate
    assert d.calls == 2


def test_no_entry_goes_to_delegate():
    a, d = agent(goal_key="renewal/routine")
    assert a.decide(case(), thread(6.1))["message"]["body"] == "delegate" and d.calls == 1


def test_relationship_goal_never_below_stored_floor():
    a, _ = agent(entry(c_min_price=5.3, lowest_offered_price=4.0), "raw_material/stabilise")
    assert sheet(a.decide(case("stabilise"), thread(6.1)))["unit_price"] == 5.19  # 0.98 x 5.3
    a, _ = agent(entry(lowest_offered_price=4.0), "raw_material/stabilise")  # no stored minimum: the best deal's price
    assert sheet(a.decide(case("stabilise"), thread(6.1)))["unit_price"] == 5.39


def test_builder_makes_an_entry_from_a_v16_dump(tmp_path):
    dumps = tmp_path / "real_runs_v16"
    dumps.mkdir()
    (tmp_path / "real").mkdir()
    (tmp_path / "targets.md").write_text("| P18 | raw_material | leverage | 1 | 222,651 | 5.5 (open) | 4.52 | 4.73 | payment=90 | x |\n")
    (tmp_path / "real" / "P18.json").write_text(json.dumps(case()))
    (dumps / "a.json").write_text(json.dumps({"case": "P18", "result": {"deal": True, "supplier_id": "sup:1", "score": 0.4, "c_deal": 9.0, "terms": BEST},
        "threads": {"sup:1": {"messages": [sup(6.1), {"from": "buyer"}, sup(5.5, "final_offer"), sup(5.5)]}}}))
    e = playbook_build.build(tmp_path)["sup:1"][KEY]
    assert e["lowest_offered_price"] == 5.5 and e["first_final_offer_round"] == 1 and e["replies_repeating_price"] == 1
    assert e["best_deal"]["price"] == 5.5 and e["target"]["price_with_best_levers"] == 4.73 and e["case_ids"] == ["P18"]


def test_accepts_an_agreed_sheet_that_beats_opening_and_alternative():
    a, d = agent()
    r = a.decide(case(), thread(6.1, 5.0, status="agreed"))
    assert r["message"]["action"] == {"type": "accept", "term_sheet_id": "o1"} and d.calls == 0


def test_agreed_sheet_above_the_opening_is_not_accepted_and_goes_to_delegate():
    a, d = agent()
    r = a.decide(case(), thread(6.1, 9.0, status="agreed"))
    assert "action" not in r["message"] and r["message"]["body"] == "delegate" and d.calls == 1
