"""Score agents against the real-like local arena: every case x seed, no API, no credits.

    python -m arena_kit.evaluate --agents guarded_rational,confident_router --set dev --seeds 5

--set dev|test: the generated cases (gen_cases.py; tune on dev, score on test once); real: the 10 hosted
real practice cases, plus a comparison with the scores the same agents really got (sim_cases/real_runs).
It starts arena-sim itself on a free local port (one server per seed, the suppliers' draws follow the seed),
plays with the kit's own client and agents, and stops the servers at the end. It refuses a non-local
ARENA_URL and the `llm` agent (it would call a model API). Reads local files only.
"""

import argparse
import json
import os
import socket
import statistics as st
import threading
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

from .cli import AGENTS, agent_factory
from .client import ArenaClient
from .play import RemoteTable, hosted, play_all
from .sim import CASES, load_cases
from .sim_real import PROFILE, SimReal

LOCAL = {"127.0.0.1", "localhost", "::1"}
DEFAULT_DATA = Path.home() / "Documents/Codex/negotiation-arena-kit/data"


def check_local():
    url = os.environ.get("ARENA_URL")
    if url and urlparse(url).hostname not in LOCAL:
        raise SystemExit(f"refusing to run: ARENA_URL={url} is not local; evaluate only talks to its own simulator")


class Server:
    """arena-sim with the real-like supplier, on a free local port, in a thread."""

    def __init__(self, sim):
        import uvicorn

        from .sim import create_app

        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            self.port = s.getsockname()[1]
        self.server = uvicorn.Server(
            uvicorn.Config(create_app(sim), host="127.0.0.1", port=self.port, log_level="error")
        )
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def __enter__(self):
        self.thread.start()
        for _ in range(200):
            if self.server.started:
                return f"http://127.0.0.1:{self.port}"
            time.sleep(0.05)
        raise RuntimeError("the simulator did not start")

    def __exit__(self, *exc):
        self.server.should_exit = True
        self.thread.join(10)


def case_folder(which):
    return {"dev": CASES / "gen_dev", "test": CASES / "gen_test", "real": CASES / "real"}[which]


def play_set(agents, which, seeds, data, parallel, profile=None):
    """(cases, {agent: {(case_id, seed): score}}, {agent: [(case_id, seed) of crashed games]})"""
    cases = load_cases(case_folder(which))
    ids = [c["case_id"] for c in hosted(list(cases.values()))]
    facts = {}
    if data and (Path(data) / "facts.json").is_file():
        from .data import DataPackage

        facts = DataPackage(data).facts
    else:
        print(
            f"WARNING: no data package at {data!r} (--data): cited IDs cannot be verified and evidence agents degrade"
        )
    out = {a: {} for a in agents}
    crashed = {a: [] for a in agents}
    for seed in range(seeds):
        sim = SimReal(
            cases, facts, "sim", no_clock=True, seed=seed, profile=profile
        )  # no 60 s rule: agents here are fast
        sim.max_calls = 10**9  # and no 10-calls-per-second limit: one machine plays many games at once
        with Server(sim) as url:
            for name in agents:
                key = ArenaClient(url, api_key="x").register(f"{name}-{seed}", "sim")["api_key"]
                client = ArenaClient(url, key, rate=1000)
                done = play_all(lambda client=client: RemoteTable(client), ids, agent_factory(name, data), parallel)
                for cid, r in done.items():
                    if isinstance(r, dict):
                        out[name][(cid, seed)] = r.get("score") or 0.0
                    else:  # a crashed game is not a score of 0: it is left out of the means and counted
                        crashed[name].append((cid, seed))
                        print(f"  CRASHED {name} {cid} seed {seed}: {r!r}")
    return cases, out, crashed


def mean(xs):
    return st.mean(xs) if xs else float("nan")


def report(cases, scores, crashed):
    print(f"\n{'agent':20} {'mean':>6} {'deal>0':>7} {'crashed':>8} {'worst case (mean over seeds)':>34}")
    for a, res in scores.items():
        per_case = defaultdict(list)
        for (cid, _), v in res.items():
            per_case[cid].append(v)
        worst = min(per_case, key=lambda c: mean(per_case[c]))
        allv = list(res.values())
        print(
            f"{a:20} {mean(allv):6.3f} {mean([v > 0 for v in allv]):7.2f} {len(crashed[a]):8d} "
            f"{worst:>22} {mean(per_case[worst]):6.3f}"
        )
    types = sorted({c["type"] for c in cases.values()})
    print(f"\n{'mean score by case type':24}" + "".join(f"{a[:14]:>16}" for a in scores))
    for t in types:
        row = []
        for res in scores.values():
            row.append(mean([v for (cid, _), v in res.items() if cases[cid]["type"] == t]))
        print(f"{t:24}" + "".join(f"{x:16.3f}" for x in row))


def real_scores(dirs=None):
    """The scores the agents really got on the practice arena: {(agent, 'case:Pxx'): mean score of its runs}."""
    from .fit_real import ALL_DIRS, dumps

    runs = defaultdict(list)
    for d in dumps(dirs or ALL_DIRS):
        runs[(d["agent"], f"case:{d['case']}")].append(d["result"]["score"])
    return {k: mean(v) for k, v in runs.items()}


def compare(cases, scores):
    real = real_scores()
    agents = [a for a in scores if any(k[0] == a for k in real)]
    rows = []
    for a in agents:
        for cid in sorted({c for (x, c) in real if x == a}):
            m = mean([v for (c, _), v in scores[a].items() if c == cid])
            rows.append((a, cid, real[(a, cid)], m))
    print("\nMOCK vs REAL (the same agents, the same 10 hosted cases; real = mean over all dumps of the agent)")
    print("IN-SAMPLE: the supplier profile was fitted on these same real runs, so this checks the fit, not the mock's")
    print("           power to predict; it says nothing about cases or agents the profile never saw.")
    print(f"{'agent':20} {'real mean':>9} {'mock mean':>9}")
    for a in agents:
        r = [x[2] for x in rows if x[0] == a]
        m = [x[3] for x in rows if x[0] == a]
        print(f"{a:20} {mean(r):9.3f} {mean(m):9.3f}")
    if len(rows) > 2:
        r_all = st.correlation([x[2] for x in rows], [x[3] for x in rows])
        print(f"in-sample correlation over {len(rows)} (agent, case) pairs: {r_all:.2f}")
        by_case = defaultdict(list)
        for _, cid, r, m in rows:
            by_case[cid].append((r, m))
        cm = {c: (mean([r for r, _ in v]), mean([m for _, m in v])) for c, v in by_case.items()}
        if len(cm) > 2:
            print(f"in-sample correlation over {len(cm)} case means (does the mock find the same cases hard?): "
                  f"{st.correlation([v[0] for v in cm.values()], [v[1] for v in cm.values()]):.2f}")  # fmt: skip
    print("biggest mismatches (agent, case, real, mock):")
    for a, cid, r, m in sorted(rows, key=lambda x: -abs(x[2] - x[3]))[:8]:
        print(f"  {a:20} {cid:10} {r:6.3f} {m:6.3f}")


def holdout(
    agents, seeds, data, parallel, fit_dirs=("real_runs", "real_runs_v16"), test_dirs=("real_runs_v17", "real_runs_v19")
):
    """HOLD-OUT: fit the supplier on `fit_dirs` only, play the mock, compare with the real scores of `test_dirs`."""
    import copy

    from .fit_real import dumps, fit, to_parameters

    prof = copy.deepcopy(json.loads(PROFILE.read_text(encoding="utf-8")))
    prof["parameters"].update(to_parameters(fit(list(fit_dirs), prof), sum(1 for _ in dumps(fit_dirs))))
    real = real_scores(list(test_dirs))
    agents = [a for a in agents if any(k[0] == a for k in real)]
    cases, scores, _ = play_set(agents, "real", seeds, data, parallel, prof["parameters"])
    errs = []
    print(f"\nHOLD-OUT: profile fitted on {list(fit_dirs)}, predicting {list(test_dirs)}")
    for (a, cid), r in sorted(real.items()):
        if a in scores:
            m = mean([v for (c, _), v in scores[a].items() if c == cid])
            errs.append(abs(r - m))
            print(f"  {a:20} {cid:10} real {r:6.3f} mock {m:6.3f} abs err {errs[-1]:.3f}")
    print(f"hold-out mean abs error of the score per (agent, case): {mean(errs):.3f} over {len(errs)} pairs")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--agents", default="guarded_rational,confident_router")
    ap.add_argument("--set", choices=["dev", "test", "real"], default="dev")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--data", default=os.environ.get("ARENA_DATA") or str(DEFAULT_DATA))
    ap.add_argument("--holdout", action="store_true", help="fit on real_runs+v16 only, predict the v17 and v19 dumps")
    ap.add_argument("--parallel", type=int, default=8)
    a = ap.parse_args(argv)
    check_local()
    agents = a.agents.split(",")
    bad = [x for x in agents if x not in AGENTS or x == "llm"]
    if bad:
        raise SystemExit(
            f"unknown or not allowed (llm calls a model API): {bad}; choose from {[x for x in AGENTS if x != 'llm']}"
        )
    if a.holdout:
        return holdout(agents, a.seeds, a.data, a.parallel)
    cases, scores, crashed = play_set(agents, a.set, a.seeds, a.data, a.parallel)
    report({k: v for k, v in cases.items() if v.get("hosted", True)}, scores, crashed)
    if a.set == "real":
        compare(cases, scores)


if __name__ == "__main__":
    main()
