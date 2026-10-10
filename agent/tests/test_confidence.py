from arena_kit.agents import ConfidentAgent
from arena_kit.confidence import PHRASE_CAP, TINY_PENALTY, confidence, confidence_report
from arena_kit.cost import must_haves_ok, total_cost

CASE = {
    "case_id": "case:C01", "title": "Test RFQ", "negotiable": ["unit_price", "payment_days"],
    "fixed_terms": {"incoterm": "DAP", "lead_time_days": 35, "contract_months": 24, "volume_per_year": 4000},
    "term_options": {"payment_days": [30, 45, 60, 90]},
    "buyer": {"need_per_year": 4000, "horizon_years": 2, "current_unit_price": 40.0, "fallback_unit_price": 46.0,
              "interest_rate": 0.08, "reference_payment_days": 60, "need_lead_time_days": 35,
              "freight_eur_per_unit": {"EXW": 1.9, "FCA": 1.2, "DAP": 0.0}, "must_haves": [],
              "alternative": {"kind": "none", "ref": None, "terms": {}}},
    "round_limit": 10,
}  # fmt: skip


def sheet(price, n=1):
    return [{"term_sheet_id": f"offer:{n}", "terms": {"unit_price": price, "payment_days": 60}}]


def sup(price=50.0, n=1, **kw):
    return {"from": "sales@a", "status": "open", "body": "Hello", "term_sheets": sheet(price, n), **kw}


def buyer(price=45.0):
    return {"from": "buyer", "term_sheets": [{"terms": {"unit_price": price, "payment_days": 60}}]}


def parts(events):
    return confidence_report(CASE, events)["parts"]


def test_closed_statuses_score_zero():
    r = confidence_report(CASE, [sup(status="final_offer")])
    assert r["score"] == 0.0 and r["notes"]
    assert confidence(CASE, [sup(status="agreed")]) == 0.0
    assert confidence(CASE, [sup(status="walked_away")]) == 0.0


def test_fresh_quote_is_full_confidence():
    assert confidence(CASE, [sup()]) == 1.0
    assert parts([sup()])["concession"] == 0.0


def test_tiny_last_concession():
    events = [sup(50.0), buyer(), sup(49.99, 2)]
    assert parts(events)["concession"] == -TINY_PENALTY
    assert confidence(CASE, events) < 1.0 - TINY_PENALTY + 0.01


def test_wording_and_cap():
    assert parts([sup(body="This is our final offer.")])["wording"] < 0
    many = sup(body="final offer, no further, no room, last word")
    assert parts([many])["wording"] == -PHRASE_CAP


def test_trust_and_timeouts():
    bad = sup(claim_results=[{"index": 0, "result": "contradicted"}])
    assert parts([sup(), buyer(), bad])["trust"] < 0
    timeout = {"from": "arena", "status": "open", "body": "(no reply)"}
    assert parts([sup(), buyer(), timeout])["timeouts"] < 0


def test_rounds_factor():
    fresh = [sup()]
    late = [sup()] + [buyer(), sup(49.0)] * 9
    assert confidence(CASE, late) < confidence(CASE, fresh)


def test_agent_accepts_final_offer():
    events = [sup(50.0), buyer(), sup(46.0, 2, status="final_offer")]
    move = ConfidentAgent().decide(CASE, {"sup:A": events})
    assert move["message"]["action"] == {"type": "accept", "term_sheet_id": "offer:2"}


def test_agent_counters_a_fresh_quote():
    events = [sup(50.0)]
    message = ConfidentAgent().decide(CASE, {"sup:A": events})["message"]
    assert 1 <= len(message["term_sheets"]) <= 3
    c_open = total_cost(CASE, events[0]["term_sheets"][0]["terms"])
    for s in message["term_sheets"]:
        assert must_haves_ok(CASE, s["terms"]) and total_cost(CASE, s["terms"]) <= c_open


def test_timeout_is_not_a_concession():
    timeout = {"from": "arena", "status": "open", "body": "(no reply)", "term_sheets": sheet(50.0, 1)}
    p = parts([sup(50.0), buyer(), timeout])
    assert p["concession"] == 0.0 and abs(p["timeouts"] + 0.10) < 1e-9


def test_repeated_sheet_is_not_a_move():
    again = sup(50.0, 1, body="Answering your question")
    assert parts([sup(50.0), buyer(), again])["concession"] == 0.0
    no_ids = {"from": "sales@a", "status": "open", "term_sheets": [{"terms": sheet(50.0)[0]["terms"]}]}
    assert parts([no_ids, buyer(), dict(no_ids)])["concession"] == 0.0


def tired(payment_days=60, price=49.99):
    """Open thread whose index is driven low: tiny last move plus final-sounding wording."""
    last = sup(price, 2, body="This is our last word, no further room.")
    last["term_sheets"][0]["terms"]["payment_days"] = payment_days
    return [sup(50.0), buyer(), last]


def test_early_accept_when_confidence_is_low_and_sheet_safe():
    events = tired()
    assert confidence(CASE, events) <= 0.25
    move = ConfidentAgent().decide(CASE, {"sup:A": events})
    assert move["message"]["action"] == {"type": "accept", "term_sheet_id": "offer:2"}


def test_no_early_accept_when_sheet_breaks_a_must_have():
    case = {**CASE, "buyer": {**CASE["buyer"], "must_haves": [{"field": "payment_days", "op": ">=", "value": 60}]}}
    events = tired(payment_days=30)
    move = ConfidentAgent().decide(case, {"sup:A": events})
    assert "action" not in move["message"] or move["message"]["action"]["type"] != "accept"


def test_step_grows_as_confidence_falls():
    a = ConfidentAgent()
    assert a.step_for(1.0) < a.step_for(0.5) < a.step_for(0.0)


def test_never_messages_a_final_offer_thread():
    a = [sup(50.0), buyer(), sup(46.0, 2, status="final_offer")]
    b = [sup(52.0)]
    move = ConfidentAgent().decide(CASE, {"sup:A": a, "sup:B": b})
    assert move["supplier_id"] == "sup:A" and move["message"].get("action", {}).get("type") == "accept" or (
        move["supplier_id"] == "sup:B"
    )


def test_fallback_never_sends_an_unsafe_sheet():
    case = {**CASE, "buyer": {**CASE["buyer"], "must_haves": [{"field": "lead_time_days", "op": "<=", "value": 10}]}}
    events = [sup(50.0), buyer(), sup(51.0, 2)]
    move = ConfidentAgent().decide(case, {"sup:A": events})["message"]
    assert not move.get("term_sheets") and move.get("action", {}).get("type") != "accept"


def test_report_survives_missing_fields():
    odd = {"from": "sales@a", "status": "open", "body": None, "claim_results": None, "term_sheets": []}
    assert confidence_report(CASE, [sup(), buyer(), odd])["score"] <= 1.0
