"""The real-like supplier (sim_real), its fitted profile, the case generator and the evaluator's guards."""

import json
from pathlib import Path

import pytest

from arena_kit import evaluate, gen_cases
from arena_kit.cost import score, total_cost
from arena_kit.sim import CASES, load_cases
from arena_kit.sim_real import PROFILE, SimReal, draw, load_profile, package_cost

SUP = "sup:70110"
P01 = load_cases(CASES / "real")["case:P01"]
DATA = Path.home() / "Documents/Codex/negotiation-arena-kit/data"
needs_data = pytest.mark.skipif(not (DATA / "world.sqlite").is_file(), reason="data package not on this machine")


def offer(price, pd=60):
    return {
        "term_sheets": [{"terms": {"unit_price": price, "effective_date": "2026-11-01", "payment_days": pd}}],
        "body": "",
    }


def session(seed=1, **force):
    sim = SimReal({P01["case_id"]: P01}, no_clock=True, seed=seed)
    sim.teams["k"] = "t"
    sid = sim.open("k", P01["case_id"])["session_id"]
    th = sim.sessions[sid]["threads"][SUP]
    th["p"].update(force)
    return sim, sid, th


def test_profile_marks_every_parameter_fitted_or_assumed():
    params = load_profile()
    assert params and PROFILE.name == "supplier_profile.json"
    for name, p in params.items():
        assert p["status"] in ("fitted", "fitted_n1", "assumed"), name
        assert isinstance(p["n"], int) and p["evidence"] and p["uncertainty"], name
        assert p["status"] != "fitted" or p["n"] >= 3, f"{name}: 'fitted' needs at least 3 cases or threads"
        assert p["status"] != "fitted_n1" or 1 <= p["n"] <= 2, name
    for name in ("payment_days_hard_limit_30", "volume_cap", "first_reply_drop_multi_supplier", "accept_tolerance"):
        assert params[name]["status"] != "fitted", name  # one thread, one case, or only bounds
    assert {"floor_cap", "pass_through_jitter", "single_sample_halfwidth", "standard_terms_gaps"} <= set(params)


def test_standard_payment_days_are_read_per_supplier_not_always_30():
    p = load_profile()["standard_payment_days"]
    assert set(p["samples"]) > {30} and 45 in p["samples"]
    prof = load_profile()
    days = {draw(prof, P01, f"sup:7{i}", 0, 1, 1)["std_pd"] for i in range(200)}
    assert days >= {30, 45}


def test_same_seed_same_supplier_other_seed_other_supplier():
    prof = load_profile()
    a, b = draw(prof, P01, SUP, 0, 1, 3), draw(prof, P01, SUP, 0, 1, 3)
    assert a == b and a != draw(prof, P01, SUP, 0, 1, 4)
    opened = [session(seed)[2]["opening"] for seed in (3, 3, 4)]
    assert opened[0] == opened[1] == 138.55  # P01 opens at its announced +9.5 %, whatever the seed
    assert session(3)[2]["floor"] == session(3)[2]["floor"] != session(4)[2]["floor"]


def test_floor_makes_c_best_computable_and_reachable():
    sim, sid, th = session()
    c_open, c_best = sim._bounds(P01, sim.sessions[sid]["threads"])
    assert c_best < c_open
    # the cheapest package at the floor really costs C_best (or the alternative does)
    pk = package_cost(P01, th["standard"], th["p"]["r"], th["floor"], th["p"]["pd_limit"], th["p"]["vol_cap"])
    assert c_best == min(pk, total_cost(P01, P01["buyer"]["alternative"]["terms"]))
    assert score(c_open, c_best, c_best) == 1.0 and score(c_open, c_open, c_best) == 0.0
    # a lower floor leaves more room (C_best falls), a floor at the opening leaves none of the supplier's side
    th["floor"] = round(th["opening"] * 0.8, 2)
    assert sim._bounds(P01, sim.sessions[sid]["threads"])[1] < c_best


def test_oscillating_offers_pay_the_pass_through_only_once():
    sim, sid, th = session(g=1.0, idle=0.0, first=0.0, final_round=99, tol=0.0, walk_after=99)
    th["floor"] = 1.0
    sim.message("k", sid, SUP, offer(100.0))  # reply 1: only the first-reply drop (0)
    asks = []
    for price in (110.0, 100.0, 110.0, 100.0, 110.0):  # H, L, H, L, H
        sim.message("k", sid, SUP, offer(price))
        asks.append(th["ask"])
    assert asks[0] < th["opening"]  # the first high offer is a new best: it pays
    assert asks[1] == asks[0] and asks[2] == asks[1] and asks[3] == asks[2] and asks[4] == asks[3]


def test_never_accepts_below_its_floor_so_score_one_needs_c_best():
    sim, sid, th = session(tol=0.5, floor=0.0)  # a huge tolerance
    th["floor"] = th["ask"] - 1.0  # floor just under the ask
    reply = sim.message("k", sid, SUP, offer(th["floor"] - 5.0, 30))
    assert reply["status"] != "agreed"
    reply = sim.message("k", sid, SUP, offer(th["floor"] + 0.5, 30))
    assert reply["status"] == "agreed"


def test_agrees_to_a_sheet_worth_its_ask_and_the_deal_scores():
    sim, sid, th = session()
    reply = sim.message("k", sid, SUP, offer(th["opening"], 30))
    assert reply["status"] == "agreed"
    done = sim.message(
        "k", sid, SUP, {"action": {"type": "accept", "term_sheet_id": reply["term_sheets"][0]["term_sheet_id"]}}
    )
    assert done["result"]["deal"] and done["result"]["score"] == pytest.approx(0, abs=0.01)


def test_final_offer_then_walk_away_when_we_keep_pushing():
    sim, sid, th = session(final_round=2, walk_after=2, tol=0.0)
    status = [sim.message("k", sid, SUP, offer(100.0))["status"] for _ in range(4)]
    # reply 1 open, reply 2 final_offer (its drawn round), first push after it is repeated, the second walks away
    assert status == ["open", "final_offer", "final_offer", "walked_away"]
    assert sim.sessions[sid]["status"] == "ended" and not sim.sessions[sid]["result"]["deal"]


def test_payment_days_hard_limit_answers_at_30_days():
    sim, sid, th = session(pd_limit=30, tol=0.0)
    reply = sim.message("k", sid, SUP, offer(100.0, 90))
    assert reply["term_sheets"][0]["terms"]["payment_days"] == 30


def test_old_script_unchanged_by_default():
    sim = __import__("arena_kit.sim", fromlist=["Sim"]).Sim({P01["case_id"]: P01}, no_clock=True)
    sim.teams["k"] = "t"
    s = sim.sessions[sim.open("k", P01["case_id"])["session_id"]]
    assert s["threads"][SUP]["opening"] == round(126.53 * 1.10, 2)


def test_generated_sets_exist_are_valid_and_do_not_share_parts():
    sets = {w: load_cases(CASES / f"gen_{w}") for w in ("dev", "test")}
    assert all(len(v) == 30 for v in sets.values())
    parts = {w: {p for c in v.values() for p in c["parts"]} for w, v in sets.items()}
    assert not parts["dev"] & parts["test"]
    real_keys = set(P01)
    for cases in sets.values():
        for c in cases.values():
            assert set(c) == real_keys and c["buyer"]["need_per_year"] > 0
            assert total_cost(c, gen_cases.complete_offer(c, {"unit_price": c["buyer"]["current_unit_price"]})) > 0
    assert {c["type"] for c in sets["dev"].values()} == set(gen_cases.TYPES)


@needs_data
def test_generator_is_reproducible_and_validates():
    world, tmpls = gen_cases.World(DATA), gen_cases.templates()
    world.split({(p, s) for cs in tmpls.values() for c in cs for p in c["parts"] for s in c["suppliers"]})
    ratios = gen_cases.fallback_ratios(tmpls)
    a = gen_cases.build(world, tmpls, ratios, "dev", 3, "1.0")
    assert (
        a
        == gen_cases.build(world, tmpls, ratios, "dev", 3, "1.0")
        != gen_cases.build(world, tmpls, ratios, "dev", 3, "1.1")
    )
    for f in sorted((CASES / "gen_test").glob("*.json"))[:10]:
        assert gen_cases.validate(json.loads(f.read_text(encoding="utf-8")), world) == []


def test_evaluate_refuses_a_remote_arena_and_the_llm_agent(monkeypatch):
    monkeypatch.setenv("ARENA_URL", "https://arena.example.com")
    with pytest.raises(SystemExit, match="not local"):
        evaluate.check_local()
    monkeypatch.setenv("ARENA_URL", "http://127.0.0.1:8000")
    evaluate.check_local()
    with pytest.raises(SystemExit, match="llm"):
        evaluate.main(["--agents", "llm", "--set", "dev"])
