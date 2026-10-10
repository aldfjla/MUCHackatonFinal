import logging

from arena_kit.agents.router import RouterAgent

from test_kit import CASE


def _threads(price=40.0):
    return {"sup:A": [{"from": "sup:A", "status": "open",
                       "term_sheets": [{"term_sheet_id": "o0", "terms": {"unit_price": price, "payment_days": 30}}]}]}


def _case(goal, cid="case:T01", alt_price=None):
    buyer = {**CASE["buyer"], "category_goal": goal}
    if alt_price:
        buyer["alternative"] = {"kind": "x", "ref": None, "terms": {"unit_price": alt_price, "payment_days": 60}}
    return {**CASE, "case_id": cid, "buyer": buyer}


def _stub(name):
    class Stub:
        made = []

        def __init__(self):
            self.calls = 0
            Stub.made.append(self)

        def decide(self, case, threads):
            self.calls += 1
            return {"supplier_id": "sup:A", "message": {"subject": name, "body": name}}

    return Stub


def _router(**over):
    stubs = {n: _stub(n) for n in ("anchor", "rational", "explorer", "switcher")}
    return RouterAgent(agents={**stubs, **over}), stubs


def test_each_goal_routes_to_its_archetype():
    for goal, name in [("leverage", "anchor"), ("routine", "rational"), ("stabilise", "explorer"),
                       ("quality_first", "explorer"), ("secure_supply", "switcher")]:
        r, _ = _router()
        assert r.decide(_case(goal), _threads())["message"]["body"] == name
        assert (r.chosen, r.goal) == (name, goal)


def test_unknown_or_missing_goal_routes_to_rational():
    for goal in ("weird", None):
        r, _ = _router()
        assert r.decide(_case(goal), _threads())["message"]["body"] == "rational"
        assert r.chosen == "rational" and r.goal == goal


def test_one_delegate_per_case_reset_on_new_case(caplog):
    r, stubs = _router()
    with caplog.at_level(logging.INFO):
        r.decide(_case("leverage"), _threads())
        r.decide(_case("leverage"), _threads())
    assert len(stubs["anchor"].made) == 1 and stubs["anchor"].made[0].calls == 2
    assert sum("goal" in m for m in caplog.messages) == 1  # logged once
    r.decide(_case("leverage", cid="case:T02"), _threads())
    assert len(stubs["anchor"].made) == 2


def test_raising_delegate_falls_back_to_valid_closing_move():
    class Boom:
        def decide(self, case, threads):
            raise RuntimeError("boom")

    r, _ = _router(anchor=Boom)
    msg = r.decide(_case("leverage", alt_price=36.0), _threads(40.0))["message"]
    assert msg["action"] == {"type": "walk_away"}  # 40.0 is worse than the alternative 36.0
    msg = r.decide(_case("leverage", alt_price=80.0), _threads(40.0))["message"]
    assert msg["action"]["type"] in {"accept", "walk_away"}


def test_failing_factory_falls_back():
    def bad():
        raise ImportError("broken sibling")

    r, _ = _router(anchor=bad)
    assert "action" in r.decide(_case("leverage", alt_price=36.0), _threads())["message"]


def test_worse_than_alternative_accept_is_replaced():
    class Greedy:
        def decide(self, case, threads):
            return {"supplier_id": "sup:A", "message": {"action": {"type": "accept", "term_sheet_id": "o0"}}}

    r, _ = _router(anchor=Greedy)
    assert r.decide(_case("leverage", alt_price=36.0), _threads(40.0))["message"]["action"] == {"type": "walk_away"}
    ok = r.decide(_case("leverage", cid="case:T02", alt_price=80.0), _threads(40.0))["message"]["action"]
    assert ok == {"type": "accept", "term_sheet_id": "o0"}
