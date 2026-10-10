from copy import deepcopy

from test_kit import CASE

from arena_kit.agents.boulware import BoulwareAgent
from arena_kit.agents.confident_boulware import ConfidentBoulwareAgent, effective_time
from arena_kit.confidence import confidence_report
from arena_kit.cost import total_cost

FLOOR = "This is our final offer, our last offer, no further movement."


def _threads(prices, status="open", sent=(), body=None):
    ev = []
    for i, p in enumerate(prices):
        last = i == len(prices) - 1
        m = {"from": "sup:A", "status": status if last else "open",
             "term_sheets": [{"term_sheet_id": f"o{i}", "terms": {"unit_price": p, "payment_days": 60}}]}
        if last and body:
            m["body"] = body
        ev.append(m)
        if i < len(sent):
            ev.append({"from": "buyer", "term_sheets": [{"terms": {"unit_price": sent[i]}}]})
    return {"sup:A": ev}


def _same(a, b):
    assert a["supplier_id"] == b["supplier_id"]
    ma, mb = a["message"], b["message"]
    assert ma.get("action") == mb.get("action")
    assert ma.get("term_sheets") == mb.get("term_sheets")


def test_effective_time():
    assert abs(effective_time(0.3, 1.0) - 0.3) < 1e-9
    assert effective_time(0.3, 0.0) == 1.0
    assert abs(effective_time(0.3, 0.5) - 0.65) < 1e-9
    vals = [effective_time(0.3, c / 10) for c in range(11)]
    assert all(a >= b for a, b in zip(vals, vals[1:], strict=False))


def test_parity_with_boulware_on_fresh_thread():
    th = _threads([44.0])
    assert confidence_report(CASE, th["sup:A"], {}, include_rounds=False)["score"] == 1.0
    _same(ConfidentBoulwareAgent().decide(CASE, th), BoulwareAgent().decide(CASE, deepcopy(th)))


def test_include_rounds_false_late_in_the_case():
    th = _threads([44.0, 43.0, 42.0], sent=[40.0, 40.5, 41.0])
    th["sup:A"] += [{"from": "buyer", "term_sheets": [{"terms": {"unit_price": 41.2}}]}] * 5  # 8 of 10 messages sent
    assert confidence_report(CASE, th["sup:A"], {}, include_rounds=False)["score"] == 1.0
    assert confidence_report(CASE, th["sup:A"], {})["score"] < 1.0
    _same(ConfidentBoulwareAgent().decide(CASE, th), BoulwareAgent().decide(CASE, deepcopy(th)))


def test_low_confidence_early_accept_only_when_not_worse_than_opening():
    th = _threads([44.0, 43.99], sent=[40.0], body=FLOOR)
    assert confidence_report(CASE, th["sup:A"], {}, include_rounds=False)["score"] <= 0.25
    msg = ConfidentBoulwareAgent(ask_payment_days=False).decide(CASE, th)["message"]
    assert msg["action"] == {"type": "accept", "term_sheet_id": "o1"}
    worse = _threads([40.0, 41.0], sent=[38.0], body=FLOOR)
    msg = ConfidentBoulwareAgent(ask_payment_days=False).decide(CASE, worse)["message"]
    assert msg.get("action", {}).get("type") != "accept"


def test_final_offer_same_as_boulware():
    for prices in ([44.0, 40.0], [44.0, 30.0]):
        th = _threads(prices, "final_offer", [38.0])
        _same(ConfidentBoulwareAgent().decide(CASE, th), BoulwareAgent().decide(CASE, deepcopy(th)))
    th = _threads([44.0, 40.0], "final_offer", [38.0])
    assert ConfidentBoulwareAgent(ask_payment_days=False).decide(CASE, th)["message"]["action"]["type"] == "accept"


def test_decide_never_raises_on_broken_threads():
    broken = [{"sup:A": [{"from": "sup:A", "status": "open"}]}, {"sup:A": [{"from": "sup:A", "term_sheets": [{}]}]}]
    for th in broken:
        d = ConfidentBoulwareAgent().decide(CASE, th)
        assert "supplier_id" in d and "message" in d


def test_mid_confidence_counter_is_not_lower_than_boulware():
    th = _threads([44.0, 43.0], sent=[38.0], body="Sorry, there is no room here.")
    rep = confidence_report(CASE, th["sup:A"], {}, include_rounds=False)
    assert 0.0 < rep["score"] < 1.0
    mine = ConfidentBoulwareAgent(ask_payment_days=False).decide(CASE, th)["message"]
    base = BoulwareAgent(ask_payment_days=False).decide(CASE, deepcopy(th))["message"]
    assert mine.get("term_sheets") and base.get("term_sheets")
    assert mine["term_sheets"][0]["terms"]["unit_price"] >= base["term_sheets"][0]["terms"]["unit_price"]


def _low_conf_thread(payment_days=60):
    th = _threads([44.0, 43.99], sent=[40.0], body=FLOOR)
    th["sup:A"][-1]["term_sheets"][0]["terms"]["payment_days"] = payment_days
    return th


def _accepts(decision):
    return decision["message"].get("action", {}).get("type") == "accept"


def test_early_accept_never_on_unsafe_sheet():
    agent = ConfidentBoulwareAgent(ask_payment_days=False)
    assert _accepts(agent.decide(CASE, _low_conf_thread()))  # control: safe sheet is accepted
    must = {**CASE, "buyer": {**CASE["buyer"], "must_haves": [{"field": "payment_days", "op": ">=", "value": 60}]}}
    assert not _accepts(agent.decide(must, _low_conf_thread(payment_days=30)))
    alt = {"kind": "x", "ref": None, "terms": {"unit_price": 30.0, "payment_days": 60}}
    with_alt = {**CASE, "buyer": {**CASE["buyer"], "alternative": alt}}
    sheet = {"unit_price": 43.99, "payment_days": 60}
    assert total_cost(with_alt, alt["terms"]) < total_cost(with_alt, sheet)
    assert not _accepts(agent.decide(with_alt, _low_conf_thread()))
