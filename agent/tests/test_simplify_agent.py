"""`simplify` finishes every real-like mock case with a deal, must-haves ok, never worse than the opening cost."""

import pytest

from arena_kit import evaluate
from arena_kit.client import ArenaClient
from arena_kit.data import DataPackage
from arena_kit.play import RemoteTable, hosted, play_all
from arena_kit.sim import load_cases
from arena_kit.sim_real import SimReal


@pytest.mark.skipif(not (evaluate.DEFAULT_DATA / "facts.json").is_file(), reason="no data package")
def test_simplify_closes_every_real_case():
    data = evaluate.DEFAULT_DATA
    cases = load_cases(evaluate.case_folder("real"))
    ids = [c["case_id"] for c in hosted(list(cases.values()))]
    sim = SimReal(cases, DataPackage(data).facts, "sim", no_clock=True, seed=0)
    sim.max_calls = 10**9
    with evaluate.Server(sim) as url:
        key = ArenaClient(url, api_key="x").register("simplify-0", "sim")["api_key"]
        client = ArenaClient(url, key, rate=1000)
        done = play_all(lambda: RemoteTable(client), ids, evaluate.agent_factory("simplify", data), 1)
    assert set(done) == set(ids)
    for cid, r in done.items():
        assert isinstance(r, dict), f"{cid}: {r!r}"
        assert r["deal"] and r["must_haves_ok"], f"{cid}: {r}"
        assert r["c_deal"] <= r["c_open"], f"{cid}: {r}"
