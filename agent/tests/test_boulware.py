import json

from arena_kit.agents.boulware import BoulwareAgent, target_cost
from arena_kit.cost import total_cost

from test_kit import CASE


def _threads(prices, status="open", sent=()):
    ev = []
    for i, p in enumerate(prices):
        ev.append({"from": "sup:A", "status": status if i == len(prices) - 1 else "open",
                   "term_sheets": [{"term_sheet_id": f"o{i}", "terms": {"unit_price": p, "payment_days": 60}}]})
        if i < len(sent):
            ev.append({"from": "buyer", "term_sheets": [{"terms": {"unit_price": sent[i]}}]})
    return {"sup:A": ev}


def _alt(price, **extra):
    return {**CASE, **extra, "buyer": {**CASE["buyer"], "alternative": {"kind": "x", "ref": None, "terms": {"unit_price": price, "payment_days": 60}}}}


def test_target_curve_rises_from_c_start_to_c_end():
    ts = [target_cost(1000, 900, True, i / 10) for i in range(11)]
    assert all(a <= b for a, b in zip(ts, ts[1:]))  # concession = target cost rises toward the supplier
    assert abs(ts[-1] - 882) < 1e-6  # c_end = 0.98*900 late
    assert abs(ts[0] - 880) < 1e-6 and ts[1] < 881  # starts at c_start, boulware: flat early
    assert abs(target_cost(1000, 0, False, 1.0) - 970) < 1e-6
    assert abs(target_cost(1000, 700, True, 1.0) - 686) < 1e-6 and abs(target_cost(1000, 700, True, 0.0) - 686) < 1e-6  # cheap alternative: never above 0.98*res


def test_offer_never_above_supplier_price():
    msg = BoulwareAgent().decide(_alt(36.0), _threads([44.0, 43.0], "open", [38.0]))["message"]
    assert msg["term_sheets"][0]["terms"]["unit_price"] <= 43.0
    assert set(msg["term_sheets"][0]["terms"]) == {"unit_price", "payment_days"} and "alternative" not in msg["body"]


def test_ac_next_accepts_cheap_standing_sheet():
    msg = BoulwareAgent(ask_payment_days=False).decide(CASE, _threads([44.0, 30.0], "open", [38.0]))["message"]
    assert msg["action"] == {"type": "accept", "term_sheet_id": "o1"}


def test_never_accepts_worse_than_reservation():
    case = _alt(36.0)
    assert total_cost(case, {"unit_price": 40.0, "payment_days": 60}) > total_cost(case, case["buyer"]["alternative"]["terms"])
    for status in ("final_offer", "agreed"):
        assert BoulwareAgent().decide(case, _threads([44.0, 40.0], status, [38.0]))["message"]["action"] == {"type": "walk_away"}
    last = {**case, "round_limit": 1}
    assert BoulwareAgent().decide(last, _threads([44.0, 40.0], "open", [38.0]))["message"]["action"] == {"type": "walk_away"}


def test_final_offer_counter_at_their_price_on_our_terms(monkeypatch):
    monkeypatch.setattr("arena_kit.agents.boulware.standard_terms", lambda ev: {"payment_days": 14})
    th = _threads([44.0, 40.0], "final_offer", [38.0])
    del th["sup:A"][-1]["term_sheets"][0]["terms"]["payment_days"]  # price-only sheet: closes on their 14 days
    msg = BoulwareAgent().decide(_alt(60.0), th)["message"]
    assert msg["term_sheets"][0]["terms"] == {"unit_price": 40.0, "payment_days": 60}
    monkeypatch.setattr("arena_kit.agents.boulware.standard_terms", lambda ev: {})
    assert BoulwareAgent().decide(_alt(60.0), th)["message"]["action"]["type"] == "accept"  # nothing to gain


def test_tit_for_tat_extra_concession_only_when_supplier_moved_more():
    case = _alt(60.0)
    price = lambda prices: BoulwareAgent(ask_payment_days=False).decide(case, _threads(prices, "open", [30.0, 31.0]))["message"]["term_sheets"][0]["terms"]["unit_price"]
    assert price([50.0, 49.0, 46.0]) == 44.35  # moved 1 then 3: plain 44.16 plus 10% of the gap to their cost
    assert price([50.0, 47.0, 46.0]) == 44.16  # moved 3 then 1: plain curve
    assert price([50.0, 49.0, 49.0]) == 44.16  # stalled: plain curve


def test_opponent_model_and_reset_on_new_case():
    a = BoulwareAgent()
    a.decide(CASE, _threads([44.0, 42.0, 41.0], "open", [38.0, 39.0]))
    assert len(a.supplier_costs("sup:A")) == 3 and a.concession_rate("sup:A") > 0
    a.decide({**CASE, "case_id": "case:T02"}, _threads([44.0]))
    assert len(a.supplier_costs("sup:A")) == 1


def test_no_live_threads_does_not_crash():
    ended = {"sup:A": [{"from": "sup:A", "status": "walked_away", "term_sheets": []}]}
    assert BoulwareAgent().decide(CASE, ended)["message"]["action"] == {"type": "walk_away"}
    assert BoulwareAgent().decide(CASE, {})["supplier_id"] is None


def test_crash_falls_back_safely(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(BoulwareAgent, "_decide", boom)
    assert BoulwareAgent().decide(_alt(36.0), _threads([44.0, 40.0]))["message"]["action"] == {"type": "walk_away"}
    assert BoulwareAgent().decide(_alt(60.0), _threads([44.0, 40.0]))["message"]["action"]["type"] in {"accept", "walk_away"}


def _price(msg):
    return msg["term_sheets"][0]["terms"]["unit_price"]


def test_no_leak_of_reservation_or_alternative():
    msg = BoulwareAgent().decide(_alt(36.1234), _threads([44.0, 43.0], "open", [38.0]))["message"]
    dump = json.dumps(msg)
    res = total_cost(_alt(36.1234), {"unit_price": 36.1234, "payment_days": 60})
    for needle in ("36.1234", str(res), "alternative", "reservation"):
        assert needle not in dump


def test_cheap_alternative_never_accepts_worse_via_ac_next():
    case = _alt(30.0)  # alternative far below 0.88 * opening
    for ours in ([30.0], [30.0, 31.0, 32.0]):
        for price in (33.0, 35.0, 38.0):
            act = BoulwareAgent(ask_payment_days=False).decide(case, _threads([44.0, price], "open", ours))["message"]
            assert "term_sheet_id" not in act.get("action", {})


def test_price_less_first_sheet_gives_finite_valid_offer():
    th = {"sup:A": [{"from": "sup:A", "status": "open", "term_sheets": [{"term_sheet_id": "o0", "terms": {}}]},
                    {"from": "buyer", "term_sheets": [{"terms": {"unit_price": 38.0}}]},
                    {"from": "sup:A", "status": "open", "term_sheets": [{"term_sheet_id": "o1", "terms": {"unit_price": 44.0, "payment_days": 60}}]}]}
    for case in (CASE, _alt(60.0)):
        msg = BoulwareAgent().decide(case, th)["message"]
        p = _price(msg)
        assert p == p and abs(p) != float("inf") and 0 < p <= 44.0


def test_non_compliant_cheapest_supplier_loses_to_compliant_one():
    case = {**_alt(60.0), "buyer": {**_alt(60.0)["buyer"], "must_haves": [{"field": "payment_days", "op": ">=", "value": 30}]}}
    th = {"sup:A": [{"from": "sup:A", "status": "open", "term_sheets": [{"term_sheet_id": "a0", "terms": {"unit_price": 30.0, "payment_days": 14}}]}],
          "sup:B": [{"from": "sup:B", "status": "open", "term_sheets": [{"term_sheet_id": "b0", "terms": {"unit_price": 40.0, "payment_days": 60}}]}]}
    assert BoulwareAgent().decide(case, th)["supplier_id"] == "sup:B"


def test_final_offer_counter_respects_must_haves():
    case = {**_alt(60.0), "buyer": {**_alt(60.0)["buyer"], "must_haves": [{"field": "payment_days", "op": "<=", "value": 60}]}}
    msg = BoulwareAgent().decide(case, _threads([44.0, 40.0], "final_offer", [38.0]))["message"]
    assert msg["action"] == {"type": "accept", "term_sheet_id": "o1"}  # asking 90 days would break the must-have


def test_last_move_reaches_c_end():
    case = _alt(36.0)  # c_end = 0.98 * 36 * 8000 -> price ~35.28 at 60 days
    msg = BoulwareAgent(ask_payment_days=False).decide(case, _threads([44.0] * 10, "open", [38.0] * 9))["message"]
    assert abs(_price(msg) - 35.28) < 0.02


def test_ask_payment_days_on_and_off():
    th = _threads([44.0, 43.0], "open", [38.0])
    on = BoulwareAgent().decide(CASE, th)["message"]["term_sheets"][0]["terms"]
    off = BoulwareAgent(ask_payment_days=False).decide(CASE, th)["message"]["term_sheets"][0]["terms"]
    assert on["payment_days"] == 90 and off["payment_days"] == 60
    c = lambda t: total_cost(CASE, t)
    t0 = target_cost(c({"unit_price": 44.0, "payment_days": 60}), 0, False, 1 / 9, 3.0, 0.88, 0.97)
    assert abs(c(on) - min(t0, c({"unit_price": 43.0, "payment_days": 90}))) < 100  # solved in total cost
