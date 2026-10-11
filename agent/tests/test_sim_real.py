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


def synthetic():
    """The profile without the exact real-set values: P01 is then drawn like a generated case."""
    prof = json.loads(json.dumps(load_profile()))
    prof["real_suppliers"].update(threads={}, bounds={})
    prof["health"]["threads"] = {}
    return prof


SYN = synthetic()


def offer(price, pd=60):
    return {
        "term_sheets": [{"terms": {"unit_price": price, "effective_date": "2026-11-01", "payment_days": pd}}],
        "body": "",
    }


def session(seed=1, **force):
    sim = SimReal({P01["case_id"]: P01}, no_clock=True, seed=seed, profile=SYN)
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
        assert p["status"] != "fitted_n1" or 0 <= p["n"] <= 2, name  # n=0: its only evidence was reserved
    for name in ("payment_days_hard_limit_30", "volume_cap", "first_reply_drop_multi_supplier", "accept_tolerance"):
        assert params[name]["status"] != "fitted", name  # one thread, one case, or only bounds
    assert {"floor_cap", "pass_through_jitter", "single_sample_halfwidth", "standard_terms_gaps"} <= set(params)


def test_standard_payment_days_are_read_per_supplier_not_always_30():
    p = load_profile()["standard_payment_days"]
    assert set(p["samples"]) > {30} and 45 in p["samples"]
    prof = SYN
    days = {draw(prof, P01, f"sup:7{i}", 0, 1, 1)["std_pd"] for i in range(200)}
    assert days >= {30, 45}


def test_same_seed_same_supplier_other_seed_other_supplier():
    prof = SYN
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
    pk = package_cost(
        P01, th["standard"], th["p"]["r"], th["floor"], th["p"]["pd_limit"], th["p"]["vol_cap"], th["p"], th["opening"]
    )
    assert c_best == min(pk, total_cost(P01, P01["buyer"]["alternative"]["terms"]))
    assert score(c_open, c_best, c_best) == 1.0 and score(c_open, c_open, c_best) == 0.0
    # a lower floor leaves more room (C_best falls), a floor at the opening leaves none of the supplier's side
    # (not far below: past the supplier's sustainable margin the health term makes a deal costlier again)
    th["floor"] = round(th["floor"] + 1.0, 2)
    assert sim._bounds(P01, sim.sessions[sid]["threads"])[1] > c_best  # a higher floor costs more
    th["floor"] = round(th["floor"] - 2.0, 2)
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
        bad = gen_cases.validate(json.loads(f.read_text(encoding="utf-8")), world)
        # the realistic floors (fit_real) sit close to the opening: GT06 (a 0.41 EUR part, 1 cent = 2.4 %) and the
        # cases whose real-quote alternative is as cheap as the best supplier deal have no room in the mock
        assert [b for b in bad if not b.startswith(("no room", "the alternative beats"))] == [], f


def test_evaluate_refuses_a_remote_arena_and_the_llm_agent(monkeypatch):
    monkeypatch.setenv("ARENA_URL", "https://arena.example.com")
    with pytest.raises(SystemExit, match="not local"):
        evaluate.check_local()
    monkeypatch.setenv("ARENA_URL", "http://127.0.0.1:8000")
    evaluate.check_local()
    with pytest.raises(SystemExit, match="llm"):
        evaluate.main(["--agents", "llm", "--set", "dev"])


REAL = SimReal({P01["case_id"]: P01}, no_clock=True, seed=1)  # the exact real-set values


def real_session(seed=1):
    REAL.teams["k"] = "t"
    sid = REAL.open("k", P01["case_id"])["session_id"]
    return sid, REAL.sessions[sid]["threads"][SUP]


def test_real_set_uses_exact_values_whatever_the_seed_and_the_arenas_bounds():
    thr = load_profile()["real_suppliers"]["threads"]["P01|sup:70110"]
    for seed in (1, 2):
        sim = SimReal({P01["case_id"]: P01}, no_clock=True, seed=seed)
        sim.teams["k"] = "t"
        th = sim.sessions[sim.open("k", P01["case_id"])["session_id"]]["threads"][SUP]
        assert th["floor"] == thr["floor"] and th["p"]["final_round"] == thr["final_round"]
        assert (th["p"]["fc"], th["p"]["r"]) == (130.04, 0.0959)  # fitted from the arena's relationship values
    sid, th = real_session()
    assert REAL._bounds(P01, REAL.sessions[sid]["threads"]) == (1153779.74, 1096815.78)


def test_health_term_is_priced_in_the_deal_like_the_arena():
    sid, th = real_session()
    th["p"].update(tol=0.0)
    sheet = offer(132.8, 30)  # reciprocal_evidence's real P01 deal: the arena recorded relationship 4473.39
    reply = REAL.message("k", sid, SUP, sheet)
    done = REAL.message(
        "k", sid, SUP, {"action": {"type": "accept", "term_sheet_id": reply["term_sheets"][0]["term_sheet_id"]}}
    )
    if reply["status"] == "agreed":  # a sheet worth its ask closes at its own price
        assert done["result"]["cost_breakdown"]["relationship"] > 0
    assert SimReal._health(REAL, th)["full_cost"] == 130.04


def test_fit_health_recovers_the_arenas_values_and_a_clause_cuts_the_price():
    from arena_kit import fit_real

    f = fit_real.fit(["real_runs"])
    assert f["health"]["P01|sup:70110"]["full_cost"] == pytest.approx(130.04, abs=0.5)
    sid, th = real_session()
    th["p"].update(b_clause=0.1, b_long=0.0, bw0=1.0, tol=0.0)
    th["bw"] = 1.0
    s = REAL.sessions[sid]
    plain = {"unit_price": 130.0, "payment_days": 60}
    clause = {**plain, "index_clause": {"series": "X", "material_share": 0.2, "deadband_pct": 3.0}}
    assert REAL._value(s, th, clause) - REAL._value(s, th, plain) == pytest.approx(0.1 * th["opening"], abs=0.01)


def test_reserved_split_is_disjoint_and_suppliers_wholly_reserved():
    from arena_kit.fit_real import ALL_DIRS, dumps, load_split, make_split

    sp = load_split()
    assert sp == make_split(seed=sp["seed"])  # holdout.json is the deterministic split
    assert sp["unseen"] and sp["train"] and not set(sp["unseen"]) & set(sp["train"])
    for d in dumps(ALL_DIRS):
        reserved = set(sp["suppliers"]) & set(d["threads"])
        assert not reserved or d["case"] in sp["unseen"]  # a reserved supplier never trains
        assert (d["case"] in sp["unseen"]) != (d["case"] in sp["train"])
    cases = load_cases(CASES / "real")
    for c in sp["unseen"]:
        assert [cases[f"case:{c}"]["type"], cases[f"case:{c}"]["buyer"]["category_goal"]] in sp["combos"] or any(
            s in cases[f"case:{c}"]["suppliers"] for s in sp["suppliers"]
        )


def test_evaluate_split_flag_selects_reserved_cases():
    from arena_kit.fit_real import load_split

    sp = load_split()
    assert evaluate.split_ids("all") is None
    assert evaluate.split_ids("unseen") == {f"case:{c}" for c in sp["unseen"]}
    assert not evaluate.split_ids("unseen") & evaluate.split_ids("train")
    with pytest.raises(SystemExit):
        evaluate.main(["--set", "dev", "--split", "unseen"])
