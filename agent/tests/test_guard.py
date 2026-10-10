import logging

from test_kit import CASE

from arena_kit.agents.confident_boulware import ConfidentBoulwareAgent
from arena_kit.agents.confident_router import ConfidentRouterAgent
from arena_kit.agents.explorer import ExplorerAgent
from arena_kit.agents.rational import RationalAgent
from arena_kit.cost import must_haves_ok
from arena_kit.guard import GuardedAgent, fix_sheets, satisfy_must_haves

PPM = [300, 800, 1500, 2500]


def _case(must, negotiable, options, **extra):
    buyer = {**CASE["buyer"], "must_haves": must, "category_goal": "quality_first"}
    return {**CASE, "case_id": "case:G1", "negotiable": negotiable, "term_options": options, "buyer": buyer, **extra}


def _p11(**extra):
    return _case([{"field": "ppm_commitment", "op": "<=", "value": 1500}],
                 ["ppm_commitment", "chargeback_eur_per_complaint", "unit_price"],
                 {"ppm_commitment": PPM, "chargeback_eur_per_complaint": [0, 50, 100]}, **extra)


def _ev(sid="sup:A", terms=None, status="open", sent=1, price=47.0):
    terms = {"unit_price": price, "ppm_commitment": 6400} if terms is None else terms
    ev = [{"from": sid, "status": "open", "term_sheets": [{"term_sheet_id": "o0", "terms": terms}]}]
    for i in range(sent):
        ev += [{"from": "buyer", "term_sheets": [{"terms": {"unit_price": 40.0}}]},
               {"from": sid, "status": status, "term_sheets": [{"term_sheet_id": f"o{i + 1}", "terms": terms}]}]
    return ev


def _moved(sid="sup:A", opening=47.0, now=38.0, status="open", ppm=800):
    """A thread where the supplier opened at `opening` and now stands at `now` (sheet o1)."""
    mk = lambda price, i, st: {"from": sid, "status": st, "term_sheets": [  # noqa: E731
        {"term_sheet_id": f"o{i}", "terms": {"unit_price": price, "ppm_commitment": ppm}}]}
    return {sid: [mk(opening, 0, "open"), {"from": "buyer", "term_sheets": [{"terms": {"unit_price": 40.0}}]},
                  mk(now, 1, status)]}


class Stub:
    def __init__(self, decision=None, error=False):
        self.decision, self.error = decision, error

    def decide(self, case, threads):
        if self.error:
            raise RuntimeError("boom")
        return self.decision


def _walk(sid="sup:A"):
    return {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}


def _counter(sid="sup:A", price=40.0, ppm=2500):
    sheet = {"terms": {"unit_price": price, "ppm_commitment": ppm, "chargeback_eur_per_complaint": 0}}
    return {"supplier_id": sid, "message": {"subject": "s", "body": "b", "term_sheets": [sheet]}}


def _type(d):
    return (d["message"].get("action") or {}).get("type")


def test_satisfy_options():
    case = _p11()
    out = satisfy_must_haves(case, {"unit_price": 47.0, "ppm_commitment": 2500})
    assert out["ppm_commitment"] == 1500 and set(out) == set(case["negotiable"]) and must_haves_ok(case, out)
    case = _case([{"field": "lead_time_days", "op": "<=", "value": 42}], ["unit_price", "lead_time_days"],
                 {"lead_time_days": [28, 35, 42, 56]})
    assert satisfy_must_haves(case, {"unit_price": 40.0, "lead_time_days": 56})["lead_time_days"] == 42
    case = _case([{"field": "volume_per_year", "op": ">=", "value": 22230}], ["unit_price", "volume_per_year"],
                 {"volume_per_year": [16379, 19890, 23400]})
    out = satisfy_must_haves(case, {"unit_price": 40.0})
    assert out["volume_per_year"] == 23400 and must_haves_ok(case, out)


def test_satisfy_eq_noopts_and_nonnegotiable():
    case = _case([{"field": "payment_days", "op": "==", "value": 60}], ["unit_price", "payment_days"], 
                 {"payment_days": [30, 60]})
    assert satisfy_must_haves(case, {"unit_price": 40.0, "payment_days": 30})["payment_days"] == 60
    case = _case([{"field": "payment_days", "op": "<=", "value": 45}], ["unit_price", "payment_days"], {})
    assert satisfy_must_haves(case, {"unit_price": 40.0, "payment_days": 60})["payment_days"] == 45
    case = _case([{"field": "payment_days", "op": "<", "value": 45}], ["unit_price", "payment_days"], {})
    assert satisfy_must_haves(case, {"unit_price": 40.0, "payment_days": 60})["payment_days"] == 44
    case = _case([{"field": "payment_days", "op": "!=", "value": 30}], ["unit_price", "payment_days"], 
                 {"payment_days": [30, 60]})
    assert satisfy_must_haves(case, {"unit_price": 40.0, "payment_days": 30})["payment_days"] == 60
    case = _case([{"field": "incoterm", "op": "==", "value": "EXW"}], ["unit_price", "payment_days"], {})
    out = satisfy_must_haves(case, {"unit_price": 40.0, "payment_days": 30})
    assert out == {"unit_price": 40.0, "payment_days": 30} and not must_haves_ok(case, out)


def test_fix_sheets_dedup_and_cap():
    sheets = [{"terms": {"unit_price": 40.0, "ppm_commitment": 2500}}] * 2 + [
        {"terms": {"unit_price": p, "ppm_commitment": 2500}} for p in (39.0, 38.0, 37.0)]
    out, changes = fix_sheets(_p11(), sheets)
    assert changes and len(out) == 3 and all(s["terms"]["ppm_commitment"] == 1500 for s in out)


def test_counter_sheets_fixed():
    d = GuardedAgent(Stub(_counter(ppm=2500))).decide(_p11(), {"sup:A": _ev(sent=1)})
    assert d["message"]["term_sheets"][0]["terms"]["ppm_commitment"] == 1500


def test_walk_becomes_counter_twice_then_closing():
    case, g = _p11(), GuardedAgent(Stub(_walk()))
    th = {"sup:A": _ev(sent=1)}
    for _ in range(2):
        d = g.decide(case, th)
        sheet = d["message"]["term_sheets"][0]["terms"]
        assert sheet["unit_price"] == 47.0 and sheet["ppm_commitment"] == 1500
    assert _type(g.decide(case, th)) == "walk_away"  # closing_move: nothing safe


def test_exception_treated_as_walk():
    d = GuardedAgent(Stub(error=True)).decide(_p11(), {"sup:A": _ev(sent=1)})
    assert d["message"]["term_sheets"][0]["terms"]["ppm_commitment"] == 1500


def test_walk_with_safe_sheet_accepts():
    d = GuardedAgent(Stub(_walk())).decide(_p11(), _moved())
    assert d["message"]["action"] == {"type": "accept", "term_sheet_id": "o1"}


def test_final_offer_one_guard_counter_then_closing():
    case, g = _p11(), GuardedAgent(Stub(_walk()))
    th = {"sup:A": _ev(status="final_offer", sent=1)}
    assert g.decide(case, th)["message"]["term_sheets"][0]["terms"]["ppm_commitment"] == 1500
    assert _type(g.decide(case, th)) == "walk_away"


def test_last_move_rule():
    case = _p11(round_limit=2)  # one buyer message sent -> left == 1
    th = {"sup:A": _ev(sent=1)}
    d = GuardedAgent(Stub(_counter(price=40.0))).decide(case, th)
    assert d["message"]["term_sheets"][0]["terms"]["unit_price"] == 47.0  # their price, must-have fixed
    assert d["message"]["term_sheets"][0]["terms"]["ppm_commitment"] == 1500
    safe = {"sup:A": _ev(terms={"unit_price": 38.0, "ppm_commitment": 800}, sent=1)}
    assert _type(GuardedAgent(Stub(_counter(price=30.0))).decide(case, safe)) == "accept"
    done = {**case, "round_limit": 1}  # left == 0
    assert _type(GuardedAgent(Stub(_counter(price=30.0))).decide(done, safe)) == "accept"
    assert _type(GuardedAgent(Stub(_counter(price=30.0))).decide(done, th)) == "walk_away"  # nothing safe


def test_rfq_continues_on_other_thread():
    case = _p11(round_limit=10)
    th = {"sup:A": _ev("sup:A", status="final_offer", sent=1), "sup:B": _ev("sup:B", price=50.0, sent=1)}
    g = GuardedAgent(Stub(_walk("sup:A")))
    assert g.decide(case, th)["supplier_id"] == "sup:A"
    d = g.decide(case, th)  # A already tried once and is a final_offer
    assert d["supplier_id"] == "sup:B" and d["message"]["term_sheets"][0]["terms"]["ppm_commitment"] == 1500


def test_no_quote_asks_for_one():
    th = {"sup:A": [{"from": "sup:A", "status": "open", "term_sheets": [], "body": "hello"}]}
    d = GuardedAgent(Stub(_walk())).decide(_p11(), th)
    assert "term_sheets" not in d["message"] and "quote" in d["message"]["body"]


def test_new_case_resets_state():
    g = GuardedAgent(Stub(_walk()))
    th = {"sup:A": _ev(status="final_offer", sent=1)}
    g.decide(_p11(), th)
    assert _type(g.decide(_p11(), th)) == "walk_away"
    assert "term_sheets" in g.decide({**_p11(), "case_id": "case:G2"}, th)["message"]


def test_logs_intervention(caplog):
    with caplog.at_level(logging.INFO, logger="arena"):
        GuardedAgent(Stub(_walk())).decide(_p11(), {"sup:A": _ev(sent=1)})
    assert any("guard:" in r.getMessage() for r in caplog.records)


def test_p11_regression_all_delegates():
    case, th = _p11(), {"sup:A": _ev(sent=0)}
    th["sup:A"] = [th["sup:A"][0]]
    for agent in (GuardedAgent(ExplorerAgent()), GuardedAgent(RationalAgent()),
                  GuardedAgent(ConfidentBoulwareAgent()), ConfidentRouterAgent()):
        msg = agent.decide(case, th)["message"]
        assert msg.get("action") is None, agent
        assert msg["term_sheets"] and all(s["terms"]["ppm_commitment"] <= 1500 for s in msg["term_sheets"])


def test_router_delegates_are_guarded():
    from arena_kit.agents.confident_router import GUARDED
    from arena_kit.agents.router import FACTORIES

    expected = {**{n: type(f()) for n, f in FACTORIES.items()}, "confident_boulware": ConfidentBoulwareAgent}
    assert set(GUARDED) == set(expected)
    for name, make in GUARDED.items():
        g = make()
        assert isinstance(g, GuardedAgent) and type(g.delegate) is expected[name]


def test_dedup_collapse_does_not_crash():
    both = {"supplier_id": "sup:A", "message": {"subject": "s", "body": "b", "term_sheets": [
        {"terms": {"unit_price": 40.0, "ppm_commitment": 2500, "chargeback_eur_per_complaint": 0}},
        {"terms": {"unit_price": 40.0, "ppm_commitment": 1500, "chargeback_eur_per_complaint": 0}}]}}
    d = GuardedAgent(Stub(both)).decide(_p11(), {"sup:A": _ev(sent=1)})
    assert len(d["message"]["term_sheets"]) == 1 and d["message"]["term_sheets"][0]["terms"]["ppm_commitment"] == 1500


def test_fix_sheets_keeps_extra_keys():
    out, _ = fix_sheets(_p11(), [{"terms": {"unit_price": 40.0, "ppm_commitment": 2500}, "note": "x"}])
    assert out[0]["note"] == "x"


def test_snap_before_check():
    case = _case([{"field": "lead_time_days", "op": "<=", "value": 55}], ["unit_price", "lead_time_days"],
                 {"lead_time_days": [28, 60]})
    out = satisfy_must_haves(case, {"unit_price": 40.0, "lead_time_days": 50})  # 50 would snap to 60
    assert out["lead_time_days"] == 28 and must_haves_ok(case, out)
    case = _case([{"field": "volume_per_year", "op": ">=", "value": 22000}], ["unit_price", "volume_per_year"],
                 {"volume_per_year": [20000, 21000, 25000]})
    out = satisfy_must_haves(case, {"unit_price": 40.0, "volume_per_year": 21500})  # snaps to 21000
    assert out["volume_per_year"] == 25000 and must_haves_ok(case, out)


def test_sheet_overrides_breaking_standard(monkeypatch):
    case = _case([{"field": "lead_time_days", "op": "<=", "value": 42}], ["unit_price", "lead_time_days"],
                 {"lead_time_days": [28, 35, 42, 56]})
    monkeypatch.setattr("arena_kit.guard.standard_terms", lambda ev: {"lead_time_days": 56})
    th = {"sup:A": _ev(terms={"unit_price": 47.0, "lead_time_days": 56}, status="final_offer", sent=1)}
    d = GuardedAgent(Stub(_walk())).decide(case, th)
    terms = d["message"]["term_sheets"][0]["terms"]
    assert terms["lead_time_days"] == 42 and terms["unit_price"] == 47.0
    assert must_haves_ok(case, terms, {"lead_time_days": 56})


def test_agreed_thread_gets_no_guard_counter():
    th = _moved(status="agreed", now=47.0)  # breaks nothing we can fix: ppm 800 ok -> accept path
    d = GuardedAgent(Stub(_walk())).decide(_p11(), th)
    assert _type(d) == "accept"
    th = _moved(status="agreed", now=47.0, ppm=2500)  # unsafe agreed sheet
    d = GuardedAgent(Stub(_walk())).decide(_p11(), th)
    assert "term_sheets" not in d["message"] and _type(d) == "walk_away"


def test_unsafe_delegate_accepts_are_not_accepts():
    acc = lambda sid="o1": {"supplier_id": "sup:A", "message": {"action": {"type": "accept", "term_sheet_id": sid}}}  # noqa: E731
    bad = _moved(ppm=2500)  # must-have broken
    assert _type(GuardedAgent(Stub(acc())).decide(_p11(), bad)) != "accept"
    assert _type(GuardedAgent(Stub(acc("o0"))).decide(_p11(), _moved(now=47.0))) != "accept"  # stale id
    case = _p11()
    case["buyer"] = {**case["buyer"], "alternative": {"kind": "x", "ref": None, "terms": {"unit_price": 30.0}}}
    assert _type(GuardedAgent(Stub(acc())).decide(case, _moved())) != "accept"  # not better than the alternative
    assert GuardedAgent(Stub(acc())).decide(_p11(), _moved())["message"]["action"]["term_sheet_id"] == "o1"


def test_early_accept_rule():
    fresh = {"sup:A": [{"from": "sup:A", "status": "open", "term_sheets": [
        {"term_sheet_id": "o0", "terms": {"unit_price": 47.0, "ppm_commitment": 800}}]}]}
    d = GuardedAgent(Stub(_walk())).decide(_p11(), fresh)
    assert _type(d) is None and d["message"]["term_sheets"][0]["terms"]["unit_price"] == 47.0
    assert _type(GuardedAgent(Stub(_walk())).decide(_p11(), _moved(now=47.0 * 0.95))) == "accept"
    assert _type(GuardedAgent(Stub(_walk())).decide(_p11(), _moved(now=47.0 * 0.98))) is None
    assert _type(GuardedAgent(Stub(_walk())).decide(_p11(round_limit=2), _moved(now=47.0 * 0.98))) == "accept"


def test_rfq_left_zero_on_a_open_b():
    case = _p11(round_limit=2)
    th = {"sup:A": _ev("sup:A", sent=2), "sup:B": _ev("sup:B", price=50.0, sent=1)}
    d = GuardedAgent(Stub(_walk("sup:A"))).decide(case, th)
    assert d["supplier_id"] == "sup:B" and d["message"]["term_sheets"][0]["terms"]["ppm_commitment"] == 1500


def test_getattr_passthrough():
    r = ConfidentRouterAgent()
    g = GuardedAgent(r)
    assert g.delegate is r and g.goal is None and g.chosen is None


def _fresh(sid="sup:A", price=47.0, ppm=800):
    return {sid: [{"from": sid, "status": "open", "term_sheets": [
        {"term_sheet_id": "o0", "terms": {"unit_price": price, "ppm_commitment": ppm}}]}]}


def _accept(sid="sup:A", sheet="o0"):
    return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet}}}


def test_accept_on_ended_thread_is_not_returned():
    for status in ("walked_away", "no_bid"):
        d = GuardedAgent(Stub(_accept(sheet="o1"))).decide(_p11(), _moved(status=status))
        assert _type(d) != "accept"


def test_round_one_accept_deferred(caplog):
    with caplog.at_level(logging.INFO, logger="arena"):
        g = GuardedAgent(Stub(_accept()))
        d = g.decide(_p11(), _fresh())
    terms = d["message"]["term_sheets"][0]["terms"]
    assert d["supplier_id"] == "sup:A" and terms["unit_price"] == 47.0 and terms["ppm_commitment"] <= 1500
    assert g._tried[("case:G1", "sup:A")] == 1 and "deferred round-1 accept" in caplog.text
    th = _moved(opening=47.0, now=47.0 * 0.95)
    th["sup:A"] = [th["sup:A"][0], th["sup:A"][2]]  # moved, but we never wrote
    assert _type(GuardedAgent(Stub(_accept(sheet="o1"))).decide(_p11(), th)) == "accept"
    assert _type(GuardedAgent(Stub(_accept())).decide(_p11(round_limit=1), _fresh())) == "accept"


def test_decide_survives_empty_threads():
    assert _type(GuardedAgent(Stub(_walk())).decide(_p11(), {})) == "walk_away"
    assert _type(GuardedAgent(Stub(_walk())).decide(_p11(), {"sup:A": []})) == "walk_away"


def test_unknown_action_logged(caplog):
    odd = {"supplier_id": "sup:A", "message": {"action": {"type": "ponder"}}}
    with caplog.at_level(logging.INFO, logger="arena"):
        GuardedAgent(Stub(odd)).decide(_p11(), {"sup:A": _ev(sent=1)})
    assert "unknown action ponder" in caplog.text
