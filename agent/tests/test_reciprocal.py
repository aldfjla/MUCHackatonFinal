import json
from pathlib import Path

import pytest

from arena_kit.agents import ClosingAgent, GuardedAgent, ReciprocalAgent
from arena_kit.agents.reciprocal import ANCHOR, ANCHOR_FLOOR, _pinned, case_c_open, closing_accept
from arena_kit.cost import must_haves_ok, total_cost
from arena_kit.play import find_sheet, moves_left, standing

BASE = Path(__file__).parent.parent / "arena_kit/sim_cases"
case = lambda n: json.loads((BASE / f"real/{n}.json").read_text())  # noqa: E731


def dump_thread(run, sid):
    return json.loads((BASE / f"real_runs/{run}.json").read_text())["threads"][sid]["messages"]


def sheet(n, price, **terms):
    return {"term_sheet_id": f"offer:{n}", "terms": {"unit_price": price, **terms}}


def reply(*sheets, status="open", body=""):
    return {"from": "sup", "status": status, "term_sheets": list(sheets), "body": body, "attachments": []}


def ours(*prices, **terms):
    return {"from": "buyer", "term_sheets": [{"terms": {"unit_price": p, **terms}} for p in prices]}


@pytest.mark.parametrize("upto,sheet_id", [(5, "offer:70210-2"), (7, "offer:70210-3"), (9, "offer:70210-4")])
def test_real_p05_accepts_the_28_euro_sheet(upto, sheet_id):
    c = case("P05")
    ev = dump_thread("evidence_router_P05", "sup:70210")[:upto]  # ends with a supplier message
    assert ev[-1]["from"] != "buyer"
    acc = closing_accept(c, {"sup:70210": ev})
    assert acc["message"]["action"] == {"type": "accept", "term_sheet_id": sheet_id}
    assert acc["supplier_id"] == "sup:70210"
    terms = find_sheet(ev, sheet_id)
    assert terms["unit_price"] == 28.0 and terms["payment_days"] == 30 and terms["lead_time_days"] == 35
    # the guarded agents and the wrapper accept it too
    assert GuardedAgent(ReciprocalAgent()).decide(c, {"sup:70210": ev})["message"]["action"]["term_sheet_id"] == sheet_id
    assert ClosingAgent(ReciprocalAgent()).decide(c, {"sup:70210": ev})["message"]["action"]["type"] == "accept"


def test_real_p05_rfq_accepts_cheapest_not_a_rival():
    c = case("P05")
    th = {
        "sup:70210": dump_thread("evidence_router_P05", "sup:70210")[:9],
        "sup:70250": dump_thread("evidence_router_P05", "sup:70250")[:9],
    }
    assert closing_accept(c, th)["supplier_id"] == "sup:70210"


def alt_thread():
    c = case("P18")
    ev = [reply(sheet("0", 6.1, payment_days=30, contract_months=12)), ours(4.9, payment_days=90),
          reply(sheet("1", 6.1, payment_days=90, contract_months=12), sheet("1-a", 6.0, payment_days=30, contract_months=12), status="final_offer")]
    return c, ev


def test_alternative_sheet_is_copied_not_accepted_then_accepted_when_standing():
    c, ev = alt_thread()
    assert total_cost(c, ev[-1]["term_sheets"][1]["terms"]) < total_cost(c, ev[-1]["term_sheets"][0]["terms"])
    for agent in (lambda: ClosingAgent(ReciprocalAgent()), lambda: GuardedAgent(ReciprocalAgent())):
        d = agent().decide(c, {"s": ev})
        assert "action" not in d["message"]  # an `-a` id is never accepted
        (sent,) = d["message"]["term_sheets"]
        assert sent["terms"]["unit_price"] == 6.0 and sent["terms"]["payment_days"] == 30 and sent["terms"]["contract_months"] == 12
    # the supplier agrees: its standing sheet now carries those terms
    ev2 = ev + [{"from": "buyer", **d["message"]}, reply(sheet("2", 6.0, payment_days=30, contract_months=12), status="agreed")]
    acc = GuardedAgent(ReciprocalAgent()).decide(c, {"s": ev2})
    assert acc["message"]["action"] == {"type": "accept", "term_sheet_id": "offer:2"}
    # sent already and not agreed: no loop, the closing rule steps aside
    ev3 = ev + [{"from": "buyer", **d["message"]}, reply(sheet("2", 6.1, payment_days=90, contract_months=12), sheet("2-a", 6.0, payment_days=30, contract_months=12), status="final_offer")]
    assert closing_accept(c, {"s": ev3}) is None


def test_stale_and_alternative_ids_are_rejected_by_the_guard():
    c, ev = alt_thread()

    class Accept:
        def __init__(self, sheet_id):
            self.sheet_id = sheet_id

        def decide(self, case, threads):
            return {"supplier_id": "s", "message": {"action": {"type": "accept", "term_sheet_id": self.sheet_id}}}

    for sheet_id in ("offer:1-a", "offer:0"):
        assert GuardedAgent(Accept(sheet_id)).decide(c, {"s": ev})["message"].get("action", {}).get("term_sheet_id") != sheet_id
    assert GuardedAgent(Accept("offer:1")).decide(c, {"s": ev})["message"]["action"]["term_sheet_id"] == "offer:1"


def test_c_open_is_the_best_opening_of_the_whole_rfq():
    c = case("P05")
    cheap = [reply(sheet("a0", 20.0, payment_days=60, lead_time_days=35), status="walked_away")]
    late = [reply(sheet("b0", 36.0, payment_days=60, lead_time_days=35)), ours(30.0),
            reply(sheet("b1", 28.0, payment_days=30, lead_time_days=35), status="final_offer")]
    assert case_c_open(c, {"a": cheap, "b": late}) == total_cost(c, cheap[0]["term_sheets"][0]["terms"])
    assert closing_accept(c, {"a": cheap, "b": late}) is None  # 28.00 is worse than the 20.00 opening of the RFQ
    assert closing_accept(c, {"b": late})["message"]["action"]["term_sheet_id"] == "offer:b1"
    assert closing_accept(c, {"b": [reply(sheet("b0", 28.0, payment_days=60, lead_time_days=35), status="final_offer")]}) is None  # not below its own opening


def test_stall_rule_needs_every_sheet_repeated():
    c = case("P18")
    main = lambda: sheet("x", 6.0, payment_days=30, contract_months=12)  # noqa: E731
    base = [reply(sheet("o", 7.0, payment_days=30, contract_months=12)), ours(5.5), reply(main(), sheet("x-a", 5.95, payment_days=30, contract_months=12)),
            ours(5.6), reply(main(), sheet("y-a", 5.95, payment_days=30, contract_months=12)), ours(5.7)]
    assert closing_accept(c, {"s": base + [reply(main(), sheet("z-a", 5.94, payment_days=30, contract_months=12))]}) is None
    same = reply(main(), sheet("y-a", 5.95, payment_days=30, contract_months=12))
    assert closing_accept(c, {"s": base + [same]}) is not None


class Walker:
    def decide(self, case, threads):
        return {"supplier_id": next(iter(threads)), "message": {"action": {"type": "walk_away"}}}


def test_real_p07_final_threads_no_push():
    c = case("P07")
    ev = dump_thread("guarded_rational_P07", "sup:70610")[:9]
    assert ev[-1]["status"] == "final_offer"
    # the final 5.65 / 90 d / 12 months sheet costs more than the current contract (the alternative): walking is right
    assert total_cost(c, ev[-1]["term_sheets"][0]["terms"]) > total_cost(c, c["buyer"]["alternative"]["terms"])
    for agent in (ReciprocalAgent(), GuardedAgent(ReciprocalAgent()), GuardedAgent(Walker())):
        d = agent.decide(c, {"s": ev})
        assert d["message"]["action"]["type"] == "walk_away" and "term_sheets" not in d["message"]
    dear = {**c, "buyer": {**c["buyer"], "alternative": {**c["buyer"]["alternative"], "terms": {**c["buyer"]["alternative"]["terms"], "unit_price": 8.0}}}}
    d = GuardedAgent(ReciprocalAgent()).decide(dear, {"s": ev})  # beats the alternative now: take it, no push
    assert d["message"]["action"] == {"type": "accept", "term_sheet_id": "offer:70610-4"}


def test_hard_limit_regex_needs_payment_context():
    sup = lambda body: [reply(sheet("0", 31.0, payment_days=60), body=body)]  # noqa: E731
    assert _pinned(sup("We agree on the EUR 28.00 per unit, but we have to stick to 30 days net."))["payment_days"] == 30
    assert _pinned(sup("Our absolute limit on payment is 30 days."))["payment_days"] == 30
    assert "payment_days" not in _pinned(sup("We have to deliver within 30 days."))
    assert "payment_days" not in _pinned(sup("Lead time limit is 30 days."))


def test_unguarded_agent_survives_empty_threads():
    c = case("P05")
    for th in ({}, {"s": []}, {"s": [ours(1.0)]}):
        assert ReciprocalAgent().decide(c, th)["message"]["action"]["type"] == "walk_away"


@pytest.mark.parametrize("name,price,unit", [("P18", 6.1, 1), ("P18", 0.5, 1), ("P18", 6.1, 100), ("P18", 6.1, 1000), ("P05", 28.0, 1)])
def test_sheets_are_valid_and_prices_sane_at_any_scale(name, price, unit):
    """Prices quoted per 100 or per 1000 pieces: every money field of the case scaled the same way."""
    c = case(name)
    b = c["buyer"]
    alt = {**b["alternative"], "terms": {k: v * unit if k == "unit_price" else v for k, v in b["alternative"]["terms"].items()}}
    c = {**c, "buyer": {**b, "current_unit_price": b["current_unit_price"] * unit, "fallback_unit_price": b["fallback_unit_price"] * unit,
                        "freight_eur_per_unit": {k: v * unit for k, v in b["freight_eur_per_unit"].items()}, "alternative": alt}}
    price *= unit
    agent, ev, mains = GuardedAgent(ReciprocalAgent()), [reply(sheet("0", price, payment_days=30, lead_time_days=35, contract_months=12))], []
    seen = []
    for i in range(5):
        d = agent.decide(c, {"s": ev})
        msg = d["message"]
        if msg.get("action"):
            break
        assert 1 <= len(msg["term_sheets"]) <= 3
        for s in msg["term_sheets"]:
            t = s["terms"]
            assert set(t) == set(c["negotiable"])
            for f, opts in c["term_options"].items():
                assert f not in t or t[f] in opts
            assert t not in seen
            seen.append(t)
        mains.append(msg["term_sheets"][0]["terms"]["unit_price"])
        ev += [{"from": "buyer", **msg}, reply(sheet(str(i + 1), price, payment_days=30, lead_time_days=35, contract_months=12))]
    assert all(b - a >= 0.01 - 1e-9 for a, b in zip(mains, mains[1:])), mains


def test_accept_422_retries_with_the_standing_sheet():
    from arena_kit.client import ArenaError
    from arena_kit.play import play

    c, ev = alt_thread()

    class Table:
        done, closed = None, []

        def open(self, case_id):
            return c, {"s": list(ev)}

        def close(self, sid, msg):
            self.closed.append(msg["action"]["term_sheet_id"])
            if len(self.closed) == 1:
                raise ArenaError(422, "unknown term sheet")
            return {"deal": True}

    class Agent:
        def decide(self, case, threads):
            return {"supplier_id": "s", "message": {"action": {"type": "accept", "term_sheet_id": "offer:1-a"}}}

    t = Table()
    assert play(t, "case:P18", Agent()) == {"deal": True}
    assert t.closed == ["offer:1-a", "offer:1"]


def test_no_accept_while_open_and_not_met():
    c = case("P18")
    ev = [reply(sheet("0", 6.1, payment_days=30, contract_months=12)), ours(5.49), reply(sheet("1", 6.1, payment_days=30, contract_months=12))]
    assert closing_accept(c, {"s": ev}) is None


def test_never_accept_worse_than_alternative():
    c = case("P18")
    alt_c = total_cost(c, c["buyer"]["alternative"]["terms"])
    ev = [reply(sheet("0", 7.5, payment_days=30, contract_months=12), status="final_offer")]
    assert total_cost(c, ev[0]["term_sheets"][0]["terms"]) > alt_c
    assert closing_accept(c, {"s": ev}) is None
    assert GuardedAgent(ReciprocalAgent()).decide(c, {"s": ev})["message"].get("action", {}).get("type") != "accept"


def test_never_accept_a_must_have_breach():
    c = case("P05")  # lead_time_days <= 42
    ev = [reply(sheet("0", 28.0, payment_days=30, lead_time_days=56), status="final_offer")]
    assert closing_accept(c, {"s": ev}) is None


def run_p18(supplier_price=6.1, rounds=6):
    """The real P18 supplier: it never moves. Our agent must still move up and never repeat itself."""
    c = case("P18")
    agent = GuardedAgent(ReciprocalAgent())
    ev, mains, all_sheets = [reply(sheet("0", supplier_price, payment_days=30, contract_months=12, index_clause=None))], [], []
    for i in range(rounds):
        d = agent.decide(c, {"s": ev})
        msg = d["message"]
        if msg.get("action"):
            return c, mains, all_sheets, d
        sheets = msg["term_sheets"]
        assert len(sheets) <= 3
        for s in sheets:
            assert must_haves_ok(c, s["terms"])
            assert total_cost(c, s["terms"]) < total_cost(c, c["buyer"]["alternative"]["terms"])
            assert s["terms"] not in all_sheets
            all_sheets.append(s["terms"])
        mains.append(sheets[0]["terms"]["unit_price"])
        ev += [{"from": "buyer", **msg}, reply(sheet(str(i + 1), supplier_price, payment_days=30, contract_months=12, index_clause=None))]
    return c, mains, all_sheets, None


def test_p18_moves_up_every_round_and_never_repeats():
    c, mains, _, _ = run_p18()
    assert len(mains) >= 3
    assert all(b > a for a, b in zip(mains, mains[1:])), mains
    assert ANCHOR_FLOOR * 6.1 <= mains[0] <= ANCHOR * 6.1 + 0.01
    assert all(b - a >= 0.01 - 1e-9 for a, b in zip(mains, mains[1:])), mains
    assert mains[1] - mains[0] >= 0.1 and mains[2] - mains[1] >= 0.06
    assert mains[-1] <= 6.1


def test_stalled_supplier_is_closed_after_repeating():
    _, mains, _, final = run_p18(rounds=12)
    assert final and final["message"]["action"]["type"] == "accept"


def test_round_one_anchor_rule():
    c = case("P18")  # current 5.84, supplier 6.10
    first = lambda c: GuardedAgent(ReciprocalAgent()).decide(c, {"s": [reply(sheet("0", 6.1, payment_days=30, contract_months=12))]})["message"]["term_sheets"][0]["terms"]["unit_price"]  # noqa: E731
    assert (ANCHOR, ANCHOR_FLOOR) == (0.80, 0.75)
    assert first(c) == pytest.approx(ANCHOR * 6.1, abs=0.011)  # ANCHOR x their price
    low = {**c, "buyer": {**c["buyer"], "current_unit_price": 4.0}}
    assert first(low) == pytest.approx(ANCHOR_FLOOR * 6.1, abs=0.011)  # current price below the floor: the floor wins
    mid = {**c, "buyer": {**c["buyer"], "current_unit_price": 4.7}}
    assert first(mid) == pytest.approx(4.7, abs=0.011)  # never above our current price when it is the lower bound


def first_msgs(run, sid=None):
    """{supplier: [its opening message]} of a real dump."""
    th = json.loads((BASE / f"real_runs/{run}.json").read_text())["threads"]
    return {k: v["messages"][:1] for k, v in th.items() if sid in (None, k)}


def test_real_p18_opening_anchor_is_080():
    c = case("P18")
    th = first_msgs("reciprocal_evidence_P18")
    d = GuardedAgent(ReciprocalAgent()).decide(c, th)
    assert d["message"]["term_sheets"][0]["terms"]["unit_price"] == pytest.approx(0.8 * 6.1, abs=0.011)  # 4.88, not 5.49


def test_real_p05_rfq_starts_cheap_and_hears_everyone_before_accepting():
    c = case("P05")
    th = first_msgs("reciprocal_evidence_P05")
    assert len(th) == 3
    agent, sent = GuardedAgent(ReciprocalAgent()), {k: 0 for k in th}
    first = None
    for _ in range(12):
        d = agent.decide(c, th)
        sid = d["supplier_id"]
        if d["message"].get("action"):
            assert d["message"]["action"]["type"] == "accept"
            assert all(n >= 2 for k, n in sent.items() if k != "sup:70210"), sent  # every live thread (bar the agreed one) had 2 messages
            assert sid == "sup:70210"  # the only valid sheet: 70240 breaks the lead time at 52 days
            break
        first = first or sid
        sent[sid] += 1
        price = d["message"]["term_sheets"][0]["terms"]["unit_price"]
        agreed = sid == "sup:70210"  # this supplier agrees to our first offer at once
        th[sid] += [{"from": "buyer", **d["message"]},
                    reply(sheet(f"{sid}-{sent[sid]}", price if agreed else th[sid][0]["term_sheets"][0]["terms"]["unit_price"], payment_days=30, lead_time_days=35),
                          status="agreed" if agreed else "open")]
    else:
        raise AssertionError("never accepted")
    assert first == "sup:70240"  # the cheapest opening first


def test_accept_target_is_the_lowest_c_sheet():
    c = case("P05")
    mk = lambda n, p: [reply(sheet(n, p, payment_days=30, lead_time_days=35), status="final_offer"), ours(p), reply(sheet(n + "1", p, payment_days=30, lead_time_days=35), status="final_offer")]  # noqa: E731
    th = {"a": mk("a", 34.0), "b": mk("b", 33.0)}
    th["a"][0]["term_sheets"][0]["terms"]["unit_price"] = 36.5
    th["b"][0]["term_sheets"][0]["terms"]["unit_price"] = 36.5
    assert closing_accept(c, th)["supplier_id"] == "b"
    th = {"a": mk("a", 33.0), "b": mk("b", 33.0)}
    th["a"][0]["term_sheets"][0]["terms"]["unit_price"] = th["b"][0]["term_sheets"][0]["terms"]["unit_price"] = 36.5
    assert closing_accept(c, th)["supplier_id"] == "a"  # ties: the thread that arrived first
    th = {"z": th["a"], "a": th["b"]}  # same C; "z" arrived first although "a" sorts first
    assert closing_accept(c, th)["supplier_id"] == "z"


def test_no_accept_before_every_live_thread_has_two_messages():
    c = case("P05")
    open_ = [reply(sheet("o", 36.0, payment_days=60, lead_time_days=35))]
    done = [*open_, ours(30.0), reply(sheet("d1", 30.0, payment_days=30, lead_time_days=35), status="final_offer")]
    assert closing_accept(c, {"a": done, "b": open_}) is None  # b was never answered
    both = closing_accept(c, {"a": done, "b": [*open_, ours(31.0), reply(sheet("o1", 35.0)), ours(32.0), reply(sheet("o2", 34.0))]})
    assert both["message"]["action"] == {"type": "accept", "term_sheet_id": "offer:d1"}  # all heard: the cheaper final sheet
    assert closing_accept(c, {"a": done})["message"]["action"]["term_sheet_id"] == "offer:d1"  # a single supplier is not an RFQ


@pytest.mark.parametrize("name", ["P02", "P08", "P16", "P18"])
def test_index_clause_variant_when_negotiable(name):
    from arena_kit.agents.reciprocal import _c_alt

    c = case(name)
    p = round(c["buyer"]["current_unit_price"] * 1.05, 2)
    th = {"s": [reply(sheet("0", p, payment_days=30, index_clause=None))]}
    sheets = GuardedAgent(ReciprocalAgent()).decide(c, th)["message"]["term_sheets"]
    assert 1 <= len(sheets) <= 3
    main_c = total_cost(c, sheets[0]["terms"])
    assert main_c < _c_alt(c)
    clauses = [x for x in sheets if x["terms"].get("index_clause")]
    for x in clauses:
        assert x["terms"]["index_clause"] in c["term_options"]["index_clause"]
        assert total_cost(c, x["terms"]) < main_c < _c_alt(c)  # offered at a price that lowers C
        assert x["terms"]["unit_price"] >= 0.75 * p - 0.01  # no lowball
    assert clauses or name != "P02"  # P02: the clause really is proposed (the real run never did)


def test_no_index_clause_when_not_negotiable():
    c = case("P05")
    sheets = GuardedAgent(ReciprocalAgent()).decide(c, {"s": [reply(sheet("0", 36.0, payment_days=60, lead_time_days=35))]})["message"]["term_sheets"]
    assert all("index_clause" not in x["terms"] for x in sheets)


def test_current_price_above_supplier_price_does_not_lift_the_anchor():
    c = case("P18")
    high = {**c, "buyer": {**c["buyer"], "current_unit_price": 9.0}}  # supplier (6.10) is below what we pay now
    d = GuardedAgent(ReciprocalAgent()).decide(high, {"s": [reply(sheet("0", 6.1, payment_days=30, contract_months=12))]})
    assert d["message"]["term_sheets"][0]["terms"]["unit_price"] == pytest.approx(ANCHOR * 6.1, abs=0.011)


def test_last_message_takes_the_standing_sheet_not_an_alternative():
    c, ev = alt_thread()  # best sheet is the `-a` one
    ev = [reply(sheet("0", 6.1, payment_days=30, contract_months=12))] + [x for i in range(c["round_limit"] - 1) for x in (ours(5.0 + i * 0.01), reply(sheet("0", 6.1, payment_days=30, contract_months=12)))]
    ev[-1] = reply(sheet("9", 6.1, payment_days=90, contract_months=12), sheet("9-a", 6.0, payment_days=30, contract_months=12))
    assert moves_left(c, ev) == 1
    assert closing_accept(c, {"s": ev})["message"]["action"] == {"type": "accept", "term_sheet_id": "offer:9"}


def test_422_retry_only_with_a_safe_standing_sheet():
    from arena_kit.client import ArenaError
    from arena_kit.play import play

    class Table:
        done = None

        def __init__(self, c, ev):
            self.c, self.ev, self.closed = c, ev, []

        def open(self, case_id):
            return self.c, {"s": list(self.ev)}

        def close(self, sid, msg):
            self.closed.append(msg["action"]["term_sheet_id"])
            raise ArenaError(422, "unknown term sheet") if len(self.closed) == 1 else AssertionError

    class Agent:
        def decide(self, case, threads):
            return {"supplier_id": "s", "message": {"action": {"type": "accept", "term_sheet_id": "offer:1-a"}}}

    c, ev = alt_thread()
    dear = {**c, "buyer": {**c["buyer"], "alternative": {**c["buyer"]["alternative"], "terms": {**c["buyer"]["alternative"]["terms"], "unit_price": 3.0}}}}
    t = Table(dear, ev)  # the standing sheet no longer beats the alternative: no retry
    with pytest.raises(ArenaError):
        play(t, "case:P18", Agent())
    assert t.closed == ["offer:1-a"]


def test_pinned_payment_days_are_not_asked_again():
    c = case("P05")
    ev = [reply(sheet("0", 31.0, payment_days=30, lead_time_days=35)), ours(28.0, payment_days=90, lead_time_days=35),
          reply(sheet("1", 30.0, payment_days=30, lead_time_days=35), body="we have to stick to 30 days net")]
    d = GuardedAgent(ReciprocalAgent()).decide(c, {"s": ev})
    assert {s["terms"]["payment_days"] for s in d["message"]["term_sheets"]} == {30}


def test_last_message_accepts_valid_sheet():
    c = case("P05")
    ev = [reply(sheet("0", 33.0, payment_days=60, lead_time_days=35))]
    for i in range(c["round_limit"] - 1):
        ev += [ours(30.0 + i * 0.01, payment_days=30, lead_time_days=35), reply(sheet(str(i), 32.0, payment_days=60, lead_time_days=35 if i % 2 else 28))]
    assert moves_left(c, ev) == 1
    assert closing_accept(c, {"s": ev})["message"]["action"] == {"type": "accept", "term_sheet_id": f"offer:{c['round_limit'] - 2}"}


@pytest.mark.parametrize("threads", [{}, {"s": []}, {"s": [{"from": "sup", "status": "open", "body": "?"}]},
                                     {"s": [{"from": "buyer"}, {"from": "sup", "status": "walked_away"}]}])
def test_odd_threads_never_crash(threads):
    c = case("P05")
    for agent in (GuardedAgent(ReciprocalAgent()), ClosingAgent(GuardedAgent(ReciprocalAgent()))):
        assert "message" in agent.decide(c, threads)


def test_question_only_reply_looks_back_to_the_last_sheet():
    c = case("P18")
    ev = [reply(sheet("0", 6.1, payment_days=30, contract_months=12)), ours(5.49),
          {"from": "sup", "status": "open", "body": "Can you explain?", "term_sheets": [], "attachments": []}]
    d = GuardedAgent(ReciprocalAgent()).decide(c, {"s": ev})
    assert d["message"]["term_sheets"][0]["terms"]["unit_price"] > 5.49
    assert standing(ev)[0] is None
