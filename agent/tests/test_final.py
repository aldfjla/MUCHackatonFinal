import copy
import json
from pathlib import Path

import pytest

from arena_kit.agents import FinalAgent, GuardedAgent
from arena_kit.agents.evidence import EvidenceAgent
from arena_kit.agents.reciprocal import ANCHOR_FLOOR, KEEP
from arena_kit.cli import AGENTS, agent_factory
from arena_kit.play import moves_left

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


def test_price_increase_anchors_at_the_current_price():
    """P02: the quote is above what we pay today, so the first sheet is our current price."""
    c = case("P02")
    ev = dump_thread("reciprocal_evidence_P02", "sup:70510")[:1]
    assert ev[0]["term_sheets"][0]["terms"]["unit_price"] > c["buyer"]["current_unit_price"]
    d = FinalAgent().decide(c, {"sup:70510": ev})
    assert first_price(d) == pytest.approx(c["buyer"]["current_unit_price"], abs=0.01)


def test_leverage_anchor_is_80_percent():
    """P05 (quote below our current price): anchor 0.80 x their price, never under the 0.75 floor."""
    th = {"sup:A": [reply(sheet("0", 30.0, payment_days=30, lead_time_days=35))]}
    price = first_price(FinalAgent().decide(case("P05"), th))
    assert price == pytest.approx(round(0.80 * 30.0, 2), abs=0.01) and price >= ANCHOR_FLOOR * 30.0


def test_p18_leverage_case_anchors_at_80_percent():
    """P18 (raw_material, quote 6.10 above current 5.84) still anchors at 0.80 x their price."""
    ev = dump_thread("reciprocal_evidence_P18", "sup:70740")[:1]
    d = FinalAgent().decide(case("P18"), {"sup:70740": ev})
    assert first_price(d) == pytest.approx(round(0.80 * 6.10, 2), abs=0.01)


def test_p08_quote_above_current_is_not_a_price_increase():
    """P08 (quote 6.05, current 5.45, not labelled price_increase) anchors at 0.80 x the quote."""
    sid = next(iter(json.loads((BASE / "real_runs/reciprocal_evidence_P08.json").read_text())["threads"]))
    ev = dump_thread("reciprocal_evidence_P08", sid)[:1]
    assert ev[0]["term_sheets"][0]["terms"]["unit_price"] == 6.05
    assert first_price(FinalAgent().decide(case("P08"), {sid: ev})) == pytest.approx(round(0.80 * 6.05, 2), abs=0.01)


def test_p01_price_increase_anchors_at_the_current_price():
    """P01 (price_increase): the first sheet is our current price 126.53 when the quote is above it."""
    ev = dump_thread("reciprocal_evidence_P01", "sup:70110")[:1]
    assert ev[0]["term_sheets"][0]["terms"]["unit_price"] > 126.53
    assert first_price(FinalAgent().decide(case("P01"), {"sup:70110": ev})) == pytest.approx(126.53, abs=0.01)


def mirrored_thread():
    terms = {"payment_days": 30, "contract_months": 12}
    return [reply(sheet("0", 5.51, **terms)), ours(4.79, payment_days=90, contract_months=12),
            reply(sheet("1", 5.49, **terms))]


def test_steps_are_visible_without_throttle():
    """match=None makes a real step after a tiny supplier move; match=0.25 stays a tick."""
    c, th = case("P18"), {"sup:70740": mirrored_thread()}
    free, throttled = (first_price(FinalAgent(match=m).decide(c, th)) for m in (None, 0.25))
    assert 4.79 + 0.01 * 5.49 < free <= 5.49 * (1 - KEEP) + 0.01
    assert throttled < free and throttled <= 4.79 + 0.25 * 0.02 + 0.01 * 5.49 + 0.01


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
    """Same threads, same decision; the agent holds only its three knobs."""
    th = {"sup:A": mirrored_thread()}
    a = FinalAgent()
    assert a.decide(case("P18"), copy.deepcopy(th)) == a.decide(case("P18"), copy.deepcopy(th))
    assert set(vars(a)) == {"match", "anchor", "max_asks"}


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
    """Both registered names build an agent."""
    assert "final" in AGENTS and "final_match" in AGENTS
    for name in ("final", "final_match"):
        assert agent_factory(name, None)().decide


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
        assert sheets[0]["terms"]["unit_price"] == 60.0
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
