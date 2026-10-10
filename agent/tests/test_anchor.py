from arena_kit.agents.anchor import AnchorAgent, _non_round
from arena_kit.cost import total_cost

from test_kit import CASE


def _threads(prices, status="open", sent=()):
    ev = []
    for i, p in enumerate(prices):
        ev.append({"from": "sup:A", "status": status if i == len(prices) - 1 else "open",
                   "term_sheets": [{"term_sheet_id": f"o{i}", "terms": {"unit_price": p, "payment_days": 30}}]})
        if i < len(sent):
            ev.append({"from": "buyer", "term_sheets": [{"terms": {"unit_price": sent[i]}}]})
    return {"sup:A": ev}


def _alt(price):
    return {**CASE, "buyer": {**CASE["buyer"], "alternative": {"kind": "x", "ref": None, "terms": {"unit_price": price, "payment_days": 60}}}}


def _price(msg):
    return msg["term_sheets"][0]["terms"]["unit_price"]


def test_opens_twelve_percent_below_non_round_with_rationale():
    msg = AnchorAgent().decide(CASE, _threads([44.0]))["message"]
    p = _price(msg)
    assert 44.0 * 0.87 < p <= 44.0 * 0.88 and round(p * 100) % 50 != 0
    assert "cost review" in msg["body"] and "alternative" not in msg["body"].lower()


def test_concession_steps_shrink_and_are_framed_with_an_ask():
    agent, sent, prices = AnchorAgent(), [], []
    for _ in range(3):
        msg = agent.decide(CASE, _threads([44.0] * (len(sent) + 1), sent=sent))["message"]
        sent.append(_price(msg)), prices.append(_price(msg))
    steps = [b - a for a, b in zip(prices, prices[1:])]
    assert 0 < steps[1] < steps[0]
    assert "significant move" in msg["body"] and msg["term_sheets"][0]["terms"]["payment_days"] == 90


def test_never_accepts_worse_than_reservation():
    case = _alt(36.0)
    assert total_cost(case, {"unit_price": 40.0, "payment_days": 30}) > total_cost(case, case["buyer"]["alternative"]["terms"])
    for status in ("final_offer", "agreed"):
        msg = AnchorAgent().decide(case, _threads([44.0, 40.0], status, [38.0]))["message"]
        assert msg["action"] == {"type": "walk_away"}


def test_accepts_agreed_strictly_better_offer():
    msg = AnchorAgent().decide(_alt(44.0), _threads([44.0, 40.0], "agreed", [38.0]))["message"]
    assert msg == {"action": {"type": "accept", "term_sheet_id": "o1"}}  # bare accept, no body


def test_no_live_threads_does_not_crash():
    out = AnchorAgent().decide(CASE, {"sup:A": [{"from": "sup:A", "status": "walked_away", "term_sheets": []}]})
    assert out["message"]["action"] == {"type": "walk_away"}


def test_crash_falls_back_safely(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(AnchorAgent, "_decide", boom)
    assert AnchorAgent().decide(_alt(36.0), _threads([44.0, 40.0]))["message"]["action"] == {"type": "walk_away"}


def test_state_resets_for_a_new_case_id():
    agent = AnchorAgent()
    first = _price(agent.decide(CASE, _threads([44.0]))["message"])
    agent.decide(CASE, _threads([44.0, 44.0], sent=[first]))
    # new case with an already-sent offer: state is rebuilt from it, not carried over from the old case
    again = agent.decide({**CASE, "case_id": "case:T02"}, _threads([44.0, 44.0], sent=[30.0]))["message"]
    fresh = AnchorAgent().decide({**CASE, "case_id": "case:T02"}, _threads([44.0, 44.0], sent=[30.0]))["message"]
    assert _price(again) == _price(fresh) and 30.0 < _price(again) < 44.0


def test_accepts_good_sheet_on_the_last_move_even_before_min_rounds():
    for limit in (2, 3):
        sent = [38.0] * (limit - 1)
        msg = AnchorAgent().decide({**_alt(44.0), "round_limit": limit}, _threads([44.0, 40.0], sent=sent))["message"]
        assert msg == {"action": {"type": "accept", "term_sheet_id": "o1"}}


def test_min_rounds_gate_blocks_early_accept_of_non_agreed_sheet():
    msg = AnchorAgent().decide(_alt(44.0), _threads([44.0, 40.0], sent=[38.0]))["message"]
    assert "action" not in msg and "term_sheets" in msg


def test_final_offer_is_countered_at_their_price():
    msg = AnchorAgent().decide(_alt(44.0), _threads([44.0, 40.0], "final_offer", [38.0]))["message"]
    assert _price(msg) == 40.0 and msg["term_sheets"][0]["terms"]["payment_days"] == 90


def test_non_round_boundaries():
    assert _non_round(41.5, 50) == 41.49 and _non_round(41.0, 50) == 40.99
    assert _non_round(41.5, 41.5) == 41.49  # never above the ceiling
    assert _non_round(0, 5) == 0.01 and _non_round(-3, 5) == 0.01 and _non_round(0.5, 5) == 0.49


def test_resume_with_fresh_state_does_not_reopen_lower():
    msg = AnchorAgent().decide(CASE, _threads([44.0, 44.0], sent=[38.5]))["message"]
    assert 38.5 < _price(msg) < 44.0


def test_concession_always_moves_at_least_a_cent_below_their_price():
    msg = AnchorAgent().decide(CASE, _threads([44.0, 44.0], sent=[43.99]))["message"]
    assert 43.99 <= _price(msg) <= 44.0
    msg = AnchorAgent().decide(CASE, _threads([44.0, 44.0], sent=[43.0, 43.2]))["message"]
    assert _price(msg) > 43.2


def test_no_retreat_when_supplier_price_falls_below_ours():
    msg = AnchorAgent().decide(CASE, _threads([44.0, 38.0], sent=[39.0]))["message"]
    assert "action" in msg or _price(msg) == 38.0  # capped at their price, never a lower retreat
