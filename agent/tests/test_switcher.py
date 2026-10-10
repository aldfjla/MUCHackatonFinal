from arena_kit.agents.switcher import SwitcherAgent
from arena_kit.cost import total_cost

from test_kit import CASE


def _threads(prices, status="open"):
    ev = []
    for i, p in enumerate(prices):
        if i:
            ev.append({"from": "buyer", "term_sheets": [{"terms": {"unit_price": p - 1}}]})
        ev.append({"from": "sup:A", "status": status if i == len(prices) - 1 else "open",
                   "term_sheets": [{"term_sheet_id": f"o{i}", "terms": {"unit_price": p, "payment_days": 30}}]})
    return {"sup:A": ev}


def _alt(price, **kw):
    return {**CASE, **kw, "buyer": {**CASE["buyer"], "alternative": {"kind": "x", "ref": None, "terms": {"unit_price": price, "payment_days": 60}}}}


def test_starts_collaborating_with_question_and_two_packages():
    msg = SwitcherAgent().decide(CASE, _threads([44.0]))["message"]
    sheets = msg["term_sheets"]
    assert "?" in msg["body"] and len(sheets) == 2
    assert sheets[0]["terms"]["unit_price"] == round(44.0 * 0.92, 2)
    assert sheets[1]["terms"]["payment_days"] > sheets[0]["terms"]["payment_days"]
    assert sheets[1]["terms"]["unit_price"] > sheets[0]["terms"]["unit_price"]
    assert "alternative" not in msg["body"]


def test_two_stalls_switch_to_firm_one_sheet_no_question_then_back():
    a, prices = SwitcherAgent(), [44.0, 44.0, 44.0]
    thr = _threads(prices)
    out = None
    for i in (1, 3, 5):  # the supplier's 1st, 2nd and 3rd (unchanged) sheet
        out = a.decide(CASE, {"sup:A": thr["sup:A"][:i]})["message"]
        assert len(out["term_sheets"]) == (2 if i < 5 else 1)
    assert len(out["term_sheets"]) == 1 and "?" not in out["body"] and a.state["sup:A"]["mode"] == "firm"
    firm_price = out["term_sheets"][0]["terms"]["unit_price"]
    assert firm_price == round(44.0 * 0.92 + (44.0 - 44.0 * 0.92) * 0.10, 2)  # one small 10% step
    thr = _threads([44.0, 44.0, 44.0, 42.0])
    back = a.decide(CASE, thr)["message"]
    assert a.state["sup:A"]["mode"] == "collaborate" and len(back["term_sheets"]) == 2


def test_closing_accepts_within_two_percent_only_if_beats_reservation():
    # best seen 40.0 (agreed-style final), then 40.4 is within 2% of it
    a = SwitcherAgent()
    a.decide(_alt(60.0), _threads([44.0, 40.0]))
    near = a.decide(_alt(60.0), _threads([44.0, 40.0, 40.4], "final_offer"))["message"]
    assert near["action"] == {"type": "accept", "term_sheet_id": "o2"}
    # same sheets, but the alternative is cheaper than 40.4: never accept
    b = SwitcherAgent()
    b.decide(_alt(36.0), _threads([44.0, 40.0]))
    assert b.decide(_alt(36.0), _threads([44.0, 40.0, 40.4], "final_offer"))["message"]["action"] == {"type": "walk_away"}


def test_never_accepts_worse_than_reservation():
    case = _alt(36.0)
    assert total_cost(case, {"unit_price": 40.0, "payment_days": 30}) > total_cost(case, case["buyer"]["alternative"]["terms"])
    for status in ("agreed", "final_offer"):
        msg = SwitcherAgent().decide(case, _threads([44.0, 40.0], status))["message"]
        assert msg["action"] == {"type": "walk_away"}
    msg = SwitcherAgent().decide(case, _threads([44.0, 40.0], "open"))["message"]
    assert msg.get("action", {}).get("type") != "accept"


def test_final_offer_counters_at_their_price_on_our_terms():
    case = _alt(80.0)
    a = SwitcherAgent()
    a.decide(case, _threads([44.0]))  # best known cost: 44.0, so 45.0 is not within 2%
    msg = a.decide(case, _threads([44.0, 45.0], "final_offer"))["message"]
    terms = msg["term_sheets"][0]["terms"]
    assert terms["unit_price"] == 45.0 and terms["payment_days"] == 90
    assert "alternative" not in msg["body"]


def test_no_live_threads_does_not_crash():
    thr = {"sup:A": [{"from": "sup:A", "status": "walked_away", "term_sheets": []}]}
    assert SwitcherAgent().decide(CASE, thr)["message"]["action"] == {"type": "walk_away"}


def test_crash_falls_back_safely(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(SwitcherAgent, "_decide", boom)
    assert SwitcherAgent().decide(_alt(36.0), _threads([44.0, 40.0]))["message"]["action"] == {"type": "walk_away"}
    assert SwitcherAgent().decide(_alt(60.0), _threads([44.0, 40.0]))["message"]["action"] == {"type": "accept", "term_sheet_id": "o1"}


def test_state_resets_for_new_case_id():
    a = SwitcherAgent()
    a.decide(CASE, _threads([44.0]))
    for i in (1, 3, 5):
        a.decide(CASE, {"sup:A": _threads([44.0, 44.0, 44.0])["sup:A"][:i]})
    assert a.state["sup:A"]["mode"] == "firm" and a.state["sup:A"]["stalls"] == 2
    a.decide({**CASE, "case_id": "case:T02"}, _threads([50.0]))
    st = a.state["sup:A"]
    assert a.case_id == "case:T02" and st["best"] > 45 and st["mode"] == "collaborate" and st["stalls"] == 0
    assert list(a.state) == ["sup:A"] and st["base"] == round(50.0 * 0.92, 2)


def test_more_demanding_supplier_goes_firm_with_one_sheet():
    a = SwitcherAgent()
    a.decide(CASE, _threads([44.0]))
    msg = a.decide(CASE, _threads([44.0, 46.0]))["message"]
    assert a.state["sup:A"]["mode"] == "firm" and len(msg["term_sheets"]) == 1


def _case_days(options):
    return {**CASE, "term_options": {"payment_days": options}}


def test_package_b_needs_longer_days_and_price_stays_sane():
    short = SwitcherAgent().decide(_case_days([14, 20]), _threads([44.0]))["message"]  # max 20 < their 30
    assert len(short["term_sheets"]) == 1
    msg = SwitcherAgent().decide(_case_days([30, 90]), _threads([44.0]))["message"]
    a, b = (s["terms"] for s in msg["term_sheets"])
    assert b["payment_days"] == 90 and 0.5 * a["unit_price"] <= b["unit_price"] <= 44.0


def test_repeated_call_is_idempotent():
    a = SwitcherAgent()
    thr = _threads([44.0, 44.0])
    first = a.decide(CASE, thr)
    state = {k: dict(v) for k, v in a.state.items()}
    assert a.decide(CASE, thr) == first and a.state == state


def test_no_alternative_accepts_compliant_agreed_sheet():
    assert CASE["buyer"]["alternative"]["terms"] == {}
    a = SwitcherAgent()
    assert a.decide(CASE, _threads([44.0], "agreed"))["message"]["action"] == {"type": "accept", "term_sheet_id": "o0"}


def test_last_proposal_then_accept_at_last_move():
    first = SwitcherAgent().decide(_alt(80.0, round_limit=2), _threads([44.0]))["message"]
    assert "action" not in first  # no accepting the opening quote before any offer of ours
    case = _alt(80.0, round_limit=3)
    a = SwitcherAgent()
    a.decide(case, _threads([44.0]))
    msg = a.decide(case, _threads([44.0, 50.0]))["message"]  # left == 2: last proposal below their price
    assert "action" not in msg and msg["term_sheets"][0]["terms"]["unit_price"] < 50.0
    msg = a.decide(case, _threads([44.0, 50.0, 49.0]))["message"]  # left == 1, >2% worse than best but beats reservation
    assert msg["action"] == {"type": "accept", "term_sheet_id": "o2"}


def _multi(pa, pb, status="open"):
    def ev(sup, p, st):
        return [{"from": sup, "status": st, "term_sheets": [{"term_sheet_id": f"{sup}1", "terms": {"unit_price": p, "payment_days": 30}}]}]
    return {"sup:A": ev("sup:A", pa, "open"), "sup:B": ev("sup:B", pb, status)}


def test_multi_supplier_messages_cheapest_with_per_supplier_state():
    a = SwitcherAgent()
    out = a.decide(CASE, _multi(44.0, 42.0))
    assert out["supplier_id"] == "sup:B" and set(a.state) == {"sup:A", "sup:B"}
    assert a.state["sup:A"]["idle"] and "base" not in a.state["sup:A"]
    assert a.state["sup:B"]["base"] == round(42.0 * 0.92, 2)
    done = a.decide(CASE, _multi(44.0, 42.0, "agreed"))
    assert done["supplier_id"] == "sup:B" and done["message"]["action"] == {"type": "accept", "term_sheet_id": "sup:B1"}


def test_final_offer_counter_is_sent_once():
    case = _alt(80.0)
    a = SwitcherAgent()
    a.decide(case, _threads([44.0]))
    assert "term_sheets" in a.decide(case, _threads([44.0, 45.0], "final_offer"))["message"]
    again = a.decide(case, _threads([44.0, 45.0, 44.8], "final_offer"))["message"]
    assert again["action"] == {"type": "accept", "term_sheet_id": "o2"}


def test_resume_does_not_reanchor_lower():
    a = SwitcherAgent()  # fresh state, but we already sent 43.0 earlier
    msg = a.decide(CASE, _threads([44.0, 44.0]))["message"]
    assert a.state["sup:A"]["base"] >= 43.0
    assert msg["term_sheets"][0]["terms"]["unit_price"] >= 43.0
