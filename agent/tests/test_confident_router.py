from test_confident_boulware import _threads
from test_router import _case, _stub

from arena_kit.agents.confident_boulware import ConfidentBoulwareAgent
from arena_kit.agents.confident_router import ConfidentRouterAgent
from arena_kit.agents.rational import RationalAgent


def test_leverage_routes_to_confident_boulware():
    r = ConfidentRouterAgent()
    r.decide(_case("leverage"), _threads([44.0]))
    assert r.chosen == "confident_boulware" and isinstance(r.delegate.delegate, ConfidentBoulwareAgent)


def test_routine_and_unknown_route_to_rational():
    for goal in ("routine", "weird", None):
        r = ConfidentRouterAgent()
        r.decide(_case(goal), _threads([44.0]))
        assert r.chosen == "rational" and isinstance(r.delegate.delegate, RationalAgent)


def test_user_overrides_merge():
    r = ConfidentRouterAgent(mapping={"routine": "mine"}, agents={"mine": _stub("mine")})
    assert r.decide(_case("routine"), _threads([44.0]))["message"]["body"] == "mine"
    r2 = ConfidentRouterAgent(agents={"confident_boulware": _stub("stub")})
    assert r2.decide(_case("leverage"), _threads([44.0]))["message"]["body"] == "stub"
    r3 = ConfidentRouterAgent(agents={"mine": _stub("mine")})
    r3.decide(_case("secure_supply"), _threads([44.0]))
    assert r3.chosen == "switcher"
