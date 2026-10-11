import copy
import json
from pathlib import Path

import pytest

from arena_kit.agents import FinalAgent, GuardedAgent
from arena_kit.agents.evidence import EvidenceAgent
from arena_kit.agents.final import ANCHOR, JUMP, _std_full, _target, _value
from arena_kit.agents.reciprocal import _c_alt, _tick
from arena_kit.cli import AGENTS, agent_factory
from arena_kit.cost import must_haves_ok, total_cost
from arena_kit.play import closing_move, moves_left

BASE = Path(__file__).parent.parent / "arena_kit/sim_cases"
SCRATCH = "/tmp/claude-1000/-home-fpvmaster-fpvmaster-EHL-HACKATHON-FINALE-MUCHackatonFinal"
DATA = Path(SCRATCH) / "a8a923ef-f5a7-45c6-9846-733930fb99a7/scratchpad/kit/data"
case = lambda n: json.loads((BASE / f"real/{n}.json").read_text())  # noqa: E731
ASK = {"from": "buyer", "body": "Could you please send us your quote?"}


def dump_thread(run, sid):
    return json.loads((BASE / f"real_runs/{run}.json").read_text())["threads"][sid]["messages"]


def sheet(n, price, **terms):
    return {"term_sheet_id": f"offer:{n}", "terms": {"unit_price": price, **terms}}


def reply(*sheets, status="open", body=""):
    return {"from": "sup", "status": status, "term_sheets": list(sheets), "body": body, "attachments": []}


def ours(*prices, **terms):
    return {"from": "buyer", "term_sheets": [{"terms": {"unit_price": p, **terms}} for p in prices]}


def first_price(d):
    return d["message"]["term_sheets"][0]["terms"]["unit_price"]


def silent_rfq():
    return {
        "sup:A": [reply(sheet("A0", 30.0, payment_days=30, lead_time_days=35))],
        "sup:B": [reply(body="we will quote later"), ASK, reply(body="still checking"), ASK,
                  reply(body="no sheet yet")],
    }


@pytest.mark.parametrize("agent", [FinalAgent(), GuardedAgent(FinalAgent())])
def test_rfq_silent_supplier_is_skipped_not_walked_away_from(agent):
    """A supplier with no sheet after max_asks messages is skipped; the case goes on with the other thread."""
    d = agent.decide(case("P05"), silent_rfq())
    assert d["supplier_id"] == "sup:A"
    assert d["message"].get("term_sheets") or d["message"]["action"]["type"] == "accept"


def test_all_silent_and_exhausted_closes_with_walk_away():
    """With no sheet anywhere, closing_move is the only way out: a walk_away."""
    th = {"sup:B": silent_rfq()["sup:B"]}
    assert FinalAgent().decide(case("P05"), th)["message"] == {"action": {"type": "walk_away"}}


def test_silent_supplier_below_max_asks_is_asked_for_a_quote():
    """A thread with fewer than max_asks messages and no sheet gets the plain quote request."""
    d = FinalAgent().decide(case("P05"), {"sup:B": [reply(body="hi")]})
    assert d["message"]["body"] == "Could you please send us your quote?" and "term_sheets" not in d["message"]


def mirrored_thread():
    terms = {"payment_days": 30, "contract_months": 12}
    return [reply(sheet("0", 5.51, **terms)), ours(4.79, payment_days=90, contract_months=12),
            reply(sheet("1", 5.49, **terms))]

P05_TERMS = {"payment_days": 30, "lead_time_days": 35}


def value_thread(*steps):
    """P05 thread: their quote 34.0, then (our message, their price) pairs."""
    ev = [reply(sheet("0", 34.0, **P05_TERMS))]
    for i, price in enumerate(steps, 1):
        ev += [ours(20.0, **P05_TERMS), reply(sheet(str(i), price, **P05_TERMS))]
    return ev


def val(c, ev, terms):
    return _value(c, _std_full(c, ev), terms)


def sent(d):
    return [s["terms"] for s in d["message"]["term_sheets"]]


def play(c, ev, rounds):
    """Run FinalAgent against a supplier that drops its price 0.5 a round; the decisions it made."""
    out, price = [], 34.0
    for i in range(rounds):
        d = FinalAgent().decide(c, {"sup:A": ev})
        out.append(d)
        if d["message"].get("action"):
            break
        price -= 0.5
        ev += [{"from": "buyer", **d["message"]}, reply(sheet(f"r{i}", price, **P05_TERMS))]
    return out


def test_anchor_value_is_76_percent_of_theirs_and_price_only_sheet_is_included():
    c, ev = case("P05"), [reply(sheet("0", 34.0, **P05_TERMS))]
    d = FinalAgent().decide(c, {"sup:A": ev})
    sheets = sent(d)
    theirs = val(c, ev, ev[0]["term_sheets"][0]["terms"])
    values = [val(c, ev, t) for t in sheets]
    assert min(values) == pytest.approx(ANCHOR * theirs, abs=0.1)
    assert any(t["payment_days"] == 30 and t["lead_time_days"] == 35 for t in sheets)  # their own terms, re-priced
    assert len(sheets) <= 3


def test_second_message_closes_55_percent_of_the_value_gap():
    c, ev = case("P05"), value_thread(33.0)
    first = ev[1]["term_sheets"][0]["terms"]
    std = _std_full(c, ev)
    a, o1 = val(c, ev, ev[2]["term_sheets"][0]["terms"]), _value(c, std, {**P05_TERMS, **first})
    want = o1 + JUMP * (a - o1)
    d = FinalAgent().decide(c, {"sup:A": ev})
    assert min(val(c, ev, t) for t in sent(d)) == pytest.approx(want, abs=0.1)


def test_third_message_uses_the_fixed_point_and_stays_below_their_value():
    c = case("P05")
    ev = [reply(sheet("0", 34.0, **P05_TERMS)), ours(25.0, **P05_TERMS), reply(sheet("1", 33.0, **P05_TERMS)),
          ours(28.0, **P05_TERMS), reply(sheet("2", 32.6, **P05_TERMS))]
    std = _std_full(c, ev)
    o = _target(c, ev, std)
    t1, t2 = (_value(c, std, {**P05_TERMS, "unit_price": p}) for p in (33.0, 32.6))
    o1, o2 = (_value(c, std, {**P05_TERMS, "unit_price": p}) for p in (25.0, 28.0))
    g = min(0.8, max(0.1, (_value(c, std, {**P05_TERMS, "unit_price": 33.0}) - t2) / (o2 - o1)))
    star = (1 - 0.012) * (t2 + g * o2) / (1 + g * (1 - 0.012))
    assert o == pytest.approx(min(t2 - _tick(t2), max(star, o2 + 0.01 * t2)), abs=1e-6)
    assert o2 <= o <= t2 - _tick(t2) and t1 > t2


def test_last_two_messages_offer_their_value_minus_a_tick():
    c = {**case("P05"), "round_limit": 4}
    ev = [reply(sheet("0", 34.0, **P05_TERMS)), ours(25.0, **P05_TERMS), reply(sheet("1", 33.0, **P05_TERMS)),
          ours(28.0, **P05_TERMS), reply(sheet("2", 32.6, **P05_TERMS))]
    assert moves_left(c, ev) <= 2
    std = _std_full(c, ev)
    a = _value(c, std, {**P05_TERMS, "unit_price": 32.6})
    assert _target(c, ev, std) == pytest.approx(a - _tick(a))


def test_every_sheet_beats_the_alternative_keeps_must_haves_and_valid_options():
    c = case("P05")
    for ev in ([reply(sheet("0", 34.0, **P05_TERMS))], value_thread(33.0), value_thread(33.0, 32.0)):
        d = FinalAgent().decide(c, {"sup:A": ev})
        for t in sent(d):
            assert total_cost(c, t, _std_full(c, ev)) < _c_alt(c)
            assert must_haves_ok(c, t, _std_full(c, ev))
            assert set(t) == set(c["negotiable"])
            for f, opts in c["term_options"].items():
                if opts and f in t:
                    assert t[f] in opts


def test_lever_bundle_asks_long_payment_at_a_higher_price_with_lower_cost():
    c, ev = case("P05"), [reply(sheet("0", 34.0, **P05_TERMS))]
    sheets = sent(FinalAgent().decide(c, {"sup:A": ev}))
    std = _std_full(c, ev)
    first, own = sheets[0], next(t for t in sheets if t["payment_days"] == 30)
    assert first["payment_days"] == 90 and first["unit_price"] > own["unit_price"]
    assert total_cost(c, first, std) < total_cost(c, own, std)
    assert val(c, ev, first) == pytest.approx(val(c, ev, own), abs=0.05)


def test_pinned_payment_days_are_never_exceeded():
    c = case("P05")
    ev = [reply(sheet("0", 34.0, **P05_TERMS)), ours(25.0, payment_days=90, lead_time_days=35),
          reply(sheet("1", 33.0, **P05_TERMS), body="Our payment limit is 30 days.")]
    for t in sent(FinalAgent().decide(c, {"sup:A": ev})):
        assert t["payment_days"] <= 30


def test_index_clause_repeated_by_the_supplier_is_kept_in_every_sheet():
    c = case("P08")
    clause = c["term_options"]["index_clause"][2]
    terms = {"payment_days": 30, "contract_months": 12, "index_clause": clause}
    ev = [reply(sheet("0", 6.05, **terms)), ours(4.8, payment_days=30, contract_months=12, index_clause=None),
          reply(sheet("1", 6.0, **terms))]
    for t in sent(FinalAgent().decide(c, {"sup:A": ev})):
        assert t["index_clause"] == clause


def test_no_identical_sheet_twice_over_a_long_negotiation():
    c, seen = case("P05"), []
    for d in play(c, [reply(sheet("0", 34.0, **P05_TERMS))], 7):
        if d["message"].get("action"):
            break
        new = sent(d)
        assert all(t not in seen for t in new)
        seen += new


def test_value_offers_never_fall():
    c = case("P05")
    ev = [reply(sheet("0", 34.0, **P05_TERMS))]
    play(c, ev, 6)
    vals = [val(c, ev, m["term_sheets"][0]["terms"]) for m in ev if m["from"] == "buyer"]
    assert vals == sorted(vals) and len(vals) >= 3


def test_final_offer_with_acceptable_sheet_is_accepted():
    """A final_offer with an acceptable sheet is accepted, not countered."""
    c = case("P05")
    th = {"sup:A": [reply(sheet("0", 34.0, payment_days=30, lead_time_days=35)), ours(30.0, lead_time_days=35),
                    reply(sheet("1", 32.0, payment_days=30, lead_time_days=35), status="final_offer")]}
    d = FinalAgent().decide(c, th)
    assert d["message"]["action"] == {"type": "accept", "term_sheet_id": "offer:1"}


def test_final_offer_breaking_a_must_have_is_not_countered():
    """A final_offer that breaks a must-have is left alone: we work the other thread, no walk_away."""
    c = case("P05")
    th = {"sup:A": [reply(sheet("0", 34.0, payment_days=30, lead_time_days=35)), ours(30.0, lead_time_days=35),
                    reply(sheet("1", 31.0, payment_days=30, lead_time_days=56), status="final_offer")],
          "sup:B": [reply(sheet("B0", 35.0, payment_days=30, lead_time_days=35))]}
    d = FinalAgent().decide(c, th)
    assert d["supplier_id"] == "sup:B" and d["message"].get("term_sheets")


def test_last_message_is_never_a_counter():
    """With one move left the decision is an accept or a closing move, not a counter."""
    c = {**case("P05"), "round_limit": 2}
    ev = [reply(sheet("0", 34.0, payment_days=30, lead_time_days=35)), ours(30.0, lead_time_days=35),
          reply(sheet("1", 33.0, payment_days=30, lead_time_days=35))]
    assert moves_left(c, ev) == 1
    d = FinalAgent().decide(c, {"sup:A": ev})
    assert d["message"].get("action")


def test_every_sheet_keeps_must_haves_and_negotiable_fields():
    """Outgoing sheets satisfy the lead-time must-have and carry every negotiable field with a valid option."""
    c = case("P05")
    d = FinalAgent().decide(c, {"sup:A": [reply(sheet("0", 34.0, payment_days=30, lead_time_days=52))]})
    sheets = d["message"]["term_sheets"]
    assert sheets
    for s in sheets:
        t = s["terms"]
        assert t["lead_time_days"] <= 42
        for f in c["negotiable"]:
            assert f in t
            if c["term_options"].get(f):
                assert t[f] in c["term_options"][f]


def test_no_identical_sheet_twice():
    """A repeating supplier never gets the same sheet from us twice."""
    c = case("P05")
    sup = reply(sheet("0", 34.0, payment_days=30, lead_time_days=35))
    ev, sent = [sup], []
    for _ in range(4):
        d = FinalAgent().decide(c, {"sup:A": ev})
        if d["message"].get("action"):
            return
        new = [s["terms"] for s in d["message"]["term_sheets"]]
        assert all(t not in sent for t in new)
        sent += new
        ev += [{"from": "buyer", **d["message"]}, copy.deepcopy(sup)]


def test_stateless():
    """Same threads, same decision; the agent holds only its two knobs."""
    th = {"sup:A": value_thread()}
    a = FinalAgent()
    assert a.decide(case("P05"), copy.deepcopy(th)) == a.decide(case("P05"), copy.deepcopy(th))
    assert set(vars(a)) == {"anchor", "max_asks"}


class Stub:
    def decide(self, case, threads):
        sid = next(iter(threads))
        message = {"subject": "s", "body": "b", "term_sheets": [{"terms": {"unit_price": 1.0}}]}
        return {"supplier_id": sid, "message": message}


@pytest.mark.skipif(not DATA.exists(), reason="data package missing")
def test_evidence_questions_off_keeps_only_the_quote_ask():
    """questions=False drops the breakdown and limit questions but keeps the quote request."""
    c = case("P05")
    has = {"sup:A": [reply(sheet("0", 34.0, payment_days=30, lead_time_days=35))]}
    none = {"sup:A": [reply(body="later")]}
    on, off = EvidenceAgent(Stub(), str(DATA)), EvidenceAgent(Stub(), str(DATA), questions=False)
    assert "breakdown" in on.decide(c, has)["message"]["body"]
    assert "breakdown" not in off.decide(c, has)["message"]["body"]
    limit = reply(sheet("0", 34.0, payment_days=30, lead_time_days=35), status="final_offer", body="our limit")
    th = {"sup:A": [limit, ASK, limit]}
    assert "reason behind the limit" in on.decide(c, th)["message"]["body"]
    assert "reason behind" not in off.decide(c, th)["message"]["body"]
    assert "Could you please send us your quote?" in off.decide(c, none)["message"]["body"]


def test_factory_builds_final_agents():
    """The registered name builds an agent; the match variant is gone."""
    assert "final" in AGENTS and "final_match" not in AGENTS
    assert agent_factory("final", None)().decide


def is_walk(d):
    return d["message"].get("action", {}).get("type") == "walk_away"


def test_thread_without_supplier_message_does_not_crash_and_is_asked():
    """A thread that never wrote is asked for a quote; only an exhausted one lets us walk."""
    ev = [reply(body="x"), ASK, reply(body="y"), ASK, reply(body="z")]
    d = FinalAgent().decide(case("P05"), {"A": ev, "B": []})
    assert d["supplier_id"] == "B" and d["message"]["body"] == ASK["body"] and not is_walk(d)
    d = FinalAgent().decide(case("P05"), {"B": []})
    assert d["supplier_id"] == "B" and d["message"]["body"] == ASK["body"]
    assert is_walk(FinalAgent().decide(case("P05"), {"B": [ASK, ASK]}))
    assert is_walk(FinalAgent().decide(case("P05"), {"A": ev, "B": [ASK, ASK]}))


def test_must_have_rescue_before_walking():
    """A final_offer that only breaks a must-have is answered with the fixed sheet instead of a walk_away."""
    from arena_kit.cost import total_cost
    from arena_kit.docs import standard_terms
    c = case("P05")
    a = [reply(sheet("A0", 60.0, payment_days=30, lead_time_days=52), status="final_offer")]
    th = {"sup:A": a, "sup:B": silent_rfq()["sup:B"]}
    d = FinalAgent().decide(c, th)
    fixed = {**a[0]["term_sheets"][0]["terms"], "lead_time_days": 42}
    alt = c["buyer"]["alternative"]["terms"]
    if total_cost(c, fixed, standard_terms(a)) < total_cost(c, alt):
        sheets = d["message"]["term_sheets"]
        assert len(sheets) == 1 and sheets[0]["terms"]["lead_time_days"] <= 42
        assert sheets[0]["terms"]["unit_price"] >= 60.0  # value-match re-pricing may add the payment-days premium
    else:
        assert is_walk(d)


def test_last_message_accepts_the_standing_sheet():
    """With one move left and an open supplier holding 30.0, we accept instead of countering."""
    c = case("P05")
    stand = sheet("S", 30.0, payment_days=30, lead_time_days=35)
    ev = [reply(sheet("0", 34.0, payment_days=30, lead_time_days=35))]
    for i in range(9):
        ev += [ours(25.0 + i * 0.1, payment_days=30, lead_time_days=35), reply(stand)]
    assert moves_left(c, ev) == 1
    d = FinalAgent().decide(c, {"sup:A": ev})
    assert d["message"]["action"] == {"type": "accept", "term_sheet_id": "offer:S"}


def test_value_match_rescue_instead_of_walking():
    """A final_offer whose sheet costs more than the opening is met at its own value, not walked away from."""
    c = case("P05")
    ev = [reply(sheet("0", 34.0, payment_days=30, lead_time_days=35)), ours(25.0, payment_days=90, lead_time_days=35),
          reply(sheet("1", 33.9, payment_days=30, lead_time_days=56), status="final_offer")]
    assert is_walk(closing_move(c, {"sup:A": ev}))  # the plain closing rule would walk away
    d = FinalAgent().decide(c, {"sup:A": ev})
    assert not is_walk(d) and not d["message"].get("action")
    t = d["message"]["term_sheets"][0]["terms"]
    std = _std_full(c, ev)
    assert total_cost(c, t, std) < total_cost(c, ev[0]["term_sheets"][0]["terms"], std)
    assert must_haves_ok(c, t, std)
    theirs = val(c, ev, ev[-1]["term_sheets"][0]["terms"])
    assert abs(val(c, ev, t) - theirs) <= 0.005 * theirs


def test_sheets_stay_below_the_opening_cost():
    """No sheet may cost as much as the opening quote: a deal at or above it scores 0."""
    c, ev = case("P05"), value_thread(33.0)
    theirs = ev[-1]["term_sheets"][0]["terms"]
    free = FinalAgent()._sheets(c, ev, {}, theirs)
    assert free
    std = _std_full(c, ev)
    cap = max(total_cost(c, t, std) for t in free)
    limited = FinalAgent()._sheets(c, ev, {}, theirs, c_open=cap)
    assert all(total_cost(c, t, std) < cap for t in limited)
