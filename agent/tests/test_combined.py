"""CombinedAgent (v6-petra): FinalAgent's visible steps + the Listener's supplier model."""

import json
from pathlib import Path

import pytest

from arena_kit.agents import CombinedAgent, GuardedAgent
from arena_kit.cli import agent_factory
from arena_kit.cost import must_haves_ok, total_cost

ROOT = Path(__file__).parent.parent / "arena_kit/sim_cases"


def case(pid):
    return json.loads((ROOT / "real" / f"{pid}.json").read_text())


def sup(body, status="open", sid="x", n=1, **terms):
    return {"from": "sales@x", "status": status, "body": body, "attachments": [],
            "term_sheets": [{"term_sheet_id": f"offer:{sid}-{n}", "terms": terms}] if terms else []}


def buyer(**terms):
    return {"from": "buyer", "body": "", "term_sheets": [{"terms": terms}]}


def sheets(d):
    return [s["terms"] for s in d["message"].get("term_sheets") or []]


P05 = dict(payment_days=30, lead_time_days=35)


def test_opening_is_alexs_anchor():
    d = CombinedAgent().decide(case("P05"), {"sup:A": [sup("Our offer.", unit_price=40.0, **P05)]})
    assert sheets(d)[0]["unit_price"] == pytest.approx(32.0, abs=0.02)  # 0.80 x their price


def test_visible_step_while_they_move():
    ev = [sup("Offer.", n=0, unit_price=40.0, **P05), buyer(unit_price=32.0, **P05),
          sup("We can move a little.", n=1, unit_price=39.0, **P05)]
    d = CombinedAgent().decide(case("P05"), {"sup:A": ev})
    assert sheets(d) and sheets(d)[0]["unit_price"] > 32.0  # a visible step up, below theirs
    assert sheets(d)[0]["unit_price"] < 39.0


def test_limit_holds_price_and_switches_to_packages():
    ev = [sup("Offer.", n=0, unit_price=40.0, **P05), buyer(unit_price=32.0, **P05),
          sup("No further concessions on price are possible.", n=1, unit_price=39.0, **P05)]
    d = CombinedAgent().decide(case("P05"), {"sup:A": ev})
    out = sheets(d)
    assert out, d
    assert all(t["unit_price"] <= 32.0 + 1e-9 for t in out)  # our price holds


def test_never_volunteers_14_days():
    ev = [sup("Offer.", n=0, unit_price=40.0, **P05)]
    for _ in range(3):
        d = CombinedAgent().decide(case("P05"), {"sup:A": ev})
        if not d["message"].get("term_sheets"):
            break
        assert all(t.get("payment_days", 30) >= 30 for t in sheets(d))
        ev = ev + [{"from": "buyer", "body": "", "term_sheets": d["message"]["term_sheets"]},
                   sup("We can move a little.", n=len(ev),
                       unit_price=ev[-1]["term_sheets"][0]["terms"]["unit_price"] - 0.5, **P05)]


def test_tied_terms_kept_in_the_try_after_a_final_offer():
    c = case("P10")
    base = {k: v for k, v in c["fixed_terms"].items()}
    a = {**base, "unit_price": 31.9, "volume_per_year": 23400, "contract_months": 24, "lead_time_days": 56}
    b = {**base, "unit_price": 34.9, "volume_per_year": 23400, "contract_months": 24, "lead_time_days": 35}
    final = {"from": "sales@x", "status": "final_offer", "body": "Final offer: 31.90 only with 56 days lead time.",
             "attachments": [], "term_sheets": [{"term_sheet_id": "offer:x-2", "terms": a},
                                                {"term_sheet_id": "offer:x-2-a", "terms": b}]}
    ev = [sup("Offer.", n=0, **{**base, "unit_price": 32.2, "volume_per_year": 19890, "lead_time_days": 56}),
          buyer(**{**base, "unit_price": 28.3, "volume_per_year": 23400, "lead_time_days": 35}), final]
    d = CombinedAgent().decide(c, {"sup:70410": ev})
    for t in sheets(d):  # if it tries a sheet, their 31.90 stays with 56 days
        if t["unit_price"] == pytest.approx(31.9):
            assert t["lead_time_days"] == 56
    if d["message"].get("action"):
        assert d["message"]["action"]["type"] == "accept"


def test_closing_takes_the_cheapest_valid_sheet_across_threads():
    c = case("P05")
    a = [sup("Offer.", sid="A", n=0, unit_price=33.0, **P05), buyer(unit_price=30.0, **P05),
         sup("This is our final offer.", status="final_offer", sid="A", n=1, unit_price=31.0, **P05)]
    b = [sup("Offer.", sid="B", n=0, unit_price=34.0, **P05), buyer(unit_price=30.0, **P05),
         sup("This is our final offer.", status="final_offer", sid="B", n=1, unit_price=32.5, **P05)]
    c = {**c, "round_limit": 2}  # no move left for a try: close
    d = CombinedAgent().decide(c, {"sup:A": a, "sup:B": b})
    assert d["supplier_id"] == "sup:A" and d["message"]["action"]["type"] == "accept"


@pytest.mark.parametrize("threads", [{}, {"sup:A": []}, {"sup:A": [sup(None)]},
                                     {"sup:A": [{"from": "sales@x", "body": None, "term_sheets": None}]}])
def test_no_crash_on_empty_or_none(threads):
    d = GuardedAgent(CombinedAgent()).decide(case("P05"), threads)
    assert "message" in d


def test_sheets_are_compliant_and_never_worse_than_the_opening():
    c = case("P05")
    ev = [sup("Offer.", n=0, unit_price=40.0, payment_days=30, lead_time_days=56)]  # breaks lead <= 42
    d = CombinedAgent().decide(c, {"sup:A": ev})
    opening = total_cost(c, ev[0]["term_sheets"][0]["terms"])
    for t in sheets(d):
        assert must_haves_ok(c, t)
        assert total_cost(c, t) <= opening


def test_registered_with_guard_and_evidence():
    a = agent_factory("combined", None)()
    assert type(a.delegate.delegate).__name__ == "CombinedAgent" and a.questions is False


def _until_final(run, extra=()):
    """The saved real thread up to the supplier's first final offer (plus `extra` events)."""
    th = json.loads((ROOT / "real_runs" / f"{run}.json").read_text())["threads"]
    out = {}
    for sid, t in th.items():
        ms = t["messages"]
        i = next((i for i, m in enumerate(ms) if m.get("from") != "buyer" and m.get("status") == "final_offer"), None)
        out[sid] = (ms[: i + 1] if i is not None else ms) + list(extra)
    return out


def test_p07_final_worse_than_alternative_tries_24_months():
    c, threads = case("P07"), _until_final("evidence_router_P07")
    d = CombinedAgent().decide(c, threads)
    out = sheets(d)
    assert out, d  # no walk-away: the same price at 24 months beats the alternative
    t, std = out[0], {}
    assert t["contract_months"] == 24 and t["unit_price"] == pytest.approx(5.64)
    alt = total_cost(c, c["buyer"]["alternative"]["terms"])
    assert total_cost(c, t, std) < alt


def test_p10_no_alternative_must_have_met_at_24_months_keeps_tied_lead_time():
    c, threads = case("P10"), _until_final("evidence_router_P10")
    d = GuardedAgent(CombinedAgent()).decide(c, threads)
    out = sheets(d)
    assert out, d
    t = out[0]
    assert must_haves_ok(c, t, {}) and t["contract_months"] == 24
    assert t["lead_time_days"] == 56  # the supplier moved 54 -> 56 with its price: kept


def test_refused_try_is_not_resent():
    c, threads = case("P07"), _until_final("evidence_router_P07")
    sid = next(iter(threads))
    first = CombinedAgent().decide(c, threads)
    tried = first["message"]["term_sheets"]
    final = next(m for m in threads[sid] if m.get("status") == "final_offer")
    refused = {**final, "body": "We must maintain our final offer."}
    threads[sid] = threads[sid] + [{"from": "buyer", "body": "", "term_sheets": tried}, refused]
    d = GuardedAgent(CombinedAgent()).decide(c, threads)
    assert all(t != tried[0]["terms"] for t in sheets(d))


def test_guard_does_not_resend_a_refused_counter():
    c = case("P05")
    t = dict(unit_price=40.0, payment_days=30, lead_time_days=35)
    ev = [sup("Offer.", n=0, **t), buyer(**{**c["fixed_terms"], **t}), sup("No.", n=1, **t)]
    g = GuardedAgent(CombinedAgent())
    g.RESEND_CHECK = True
    g._case_id, g._tried = c["case_id"], {}
    from arena_kit.cost import complete_offer
    from arena_kit.guard import satisfy_must_haves
    sheet = complete_offer(c, satisfy_must_haves(c, dict(t), {}))
    ev[1] = {"from": "buyer", "body": "", "term_sheets": [{"terms": sheet}]}
    assert not g._eligible(c, {"sup:A": ev}, "sup:A")


def test_guard_resend_check_is_off_by_default():
    c = case("P05")
    t = dict(unit_price=40.0, payment_days=30, lead_time_days=35)
    from arena_kit.cost import complete_offer
    from arena_kit.guard import satisfy_must_haves
    sent = complete_offer(c, satisfy_must_haves(c, dict(t), {}))
    ev = [sup("Offer.", n=0, **t), {"from": "buyer", "body": "", "term_sheets": [{"terms": sent}]}, sup("No.", n=1, **t)]
    g = GuardedAgent(CombinedAgent())
    g._case_id, g._tried = c["case_id"], {}
    assert not GuardedAgent.RESEND_CHECK and g._eligible(c, {"sup:A": ev}, "sup:A")


def test_acceptable_final_offer_is_accepted_at_once():
    c = case("P05")  # no alternative; must-have lead <= 42
    ev = [sup("Offer.", n=0, unit_price=40.0, **P05), buyer(unit_price=32.0, **P05),
          sup("This is our final offer.", status="final_offer", n=1, unit_price=38.0, **P05)]
    d = CombinedAgent().decide(c, {"sup:A": ev})
    assert d["message"].get("action", {}).get("type") == "accept", d  # no "slower payment" push


def test_unacceptable_final_offer_gets_one_try():
    c, threads = case("P07"), _until_final("evidence_router_P07")
    d = CombinedAgent().decide(c, threads)
    assert len(sheets(d)) == 1 and not d["message"].get("action")


def test_guard_last_move_does_not_resend_an_old_counter():
    c = {**case("P05"), "round_limit": 2}
    t = dict(unit_price=40.0, payment_days=30, lead_time_days=35)
    from arena_kit.cost import complete_offer
    from arena_kit.guard import satisfy_must_haves
    old = complete_offer(c, satisfy_must_haves(c, dict(t), {}))
    ev = [sup("Offer.", n=0, **t), {"from": "buyer", "body": "", "term_sheets": [{"terms": old}]},
          sup("No.", n=1, **t)]
    g = GuardedAgent(CombinedAgent())
    g.RESEND_CHECK = True
    d = g.decide(c, {"sup:A": ev})
    assert all(x != old for x in sheets(d))


def _first_sheets(pid):
    th = json.loads((ROOT / "real_runs" / f"reciprocal_evidence_{pid}.json").read_text())["threads"]
    sid, t = next(iter(th.items()))
    ms = t["messages"]
    i = next(i for i, m in enumerate(ms) if m.get("from") != "buyer")
    return sheets(CombinedAgent().decide(case(pid), {sid: ms[: i + 1]}))


@pytest.mark.parametrize("pid", ["P08", "P18"])
def test_no_index_clause_when_it_costs_us_more(pid):
    """P08/P18: a 5 % deadband clause cost 2-9k more than none at the same price; our sheets leave it out."""
    out = _first_sheets(pid)
    assert out and all(not s.get("index_clause") for s in out)


def test_required_index_clause_is_kept():
    """A must-have that requires an index clause: Alex's and the combined sheets keep a compliant one."""
    from arena_kit.agents import FinalAgent

    c = case("P08")
    c["buyer"]["must_haves"] = [{"field": "index_clause", "op": "!=", "value": None}]
    th = json.loads((ROOT / "real_runs" / "reciprocal_evidence_P08.json").read_text())["threads"]
    sid, t = next(iter(th.items()))
    ms = t["messages"]
    i = next(i for i, m in enumerate(ms) if m.get("from") != "buyer")
    for agent in (FinalAgent(), CombinedAgent()):
        out = sheets(agent.decide(c, {sid: ms[: i + 1]}))
        assert out and all(s.get("index_clause") for s in out)


def test_index_clause_offered_when_it_is_cheaper(monkeypatch):
    """If total_cost says an index option is cheaper than none, cheapest_index keeps the cheapest one."""
    from arena_kit.agents import reciprocal

    c = case("P08")
    opts = [o for o in c["term_options"]["index_clause"] if o]
    monkeypatch.setattr(reciprocal, "total_cost", lambda case, t, std=None: -t["index_clause"]["deadband_pct"] if t.get("index_clause") else 0)
    best = reciprocal.cheapest_index(c, {"unit_price": 5.0, "index_clause": opts[0]}, {})
    assert best["index_clause"] == max(opts, key=lambda o: o["deadband_pct"])
    monkeypatch.undo()
    assert reciprocal.cheapest_index(c, {"unit_price": 5.0, "index_clause": opts[0]}, {})["index_clause"] is None
