#!/usr/bin/env python3
"""Independent check of backlog.csv. Stage A: arithmetic (no network). Stage B (--rerun): re-run each
simulator row through the frozen Players/Originals scripts against the LOCAL simulator, twice.
Stage C (--rerun): recompute costs from the finished session + case JSON. Read-only on backlog.csv."""
import csv, json, math, os, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKLOG, REPORT = ROOT / "backlog.csv", Path(__file__).resolve().parent / "report.md"
SIM = "http://127.0.0.1:8000"
FIELDS = ["date", "version", "agent", "environment", "case_id", "deal", "c_open", "c_deal", "c_best", "score", "replay"]
VER_RE = re.compile(r"^v\d+(\.\d+)? - [a-z]+$")
SCRIPT = {"v0": "naive_baseline", "v1": "smart_petra", "v2.1": "patient_hawk", "v3": "curious_fox",
          "v4": "bold_ram", "v5": "chameleon", "v6": "iron_turtle", "v7": "wise_owl"}
ROUTE = {"leverage": "anchor", "routine": "rational", "stabilise": "explorer", "quality_first": "explorer",
         "secure_supply": "switcher"}  # wise_owl.py mapping, goal -> archetype
OPEN_UP, STEP, FLOOR = 0.10, 0.02, 0.90  # copied from agent/arena_kit/sim.py (not imported: needs fastapi)


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def vkey(version):  # 'v1-petra' -> 'v1', 'v2.1 - niko' -> 'v2.1'
    return re.split(r"\s*-\s*", version.strip())[0]


def stage_a(rows):
    """rows: list of dicts. Returns list of (line, problem)."""
    out, seen, consts = [], {}, {}
    for i, r in enumerate(rows, start=2):
        add = lambda m, i=i: out.append((i, m))
        if r.get(None):
            add(f"malformed row: {len(r[None])} extra column(s), an unquoted comma shifts the fields; later checks skipped")
            continue
        missing = [f for f in FIELDS if not (r.get(f) or "").strip()]
        if missing:
            add("missing field(s): " + ",".join(missing))
        v = (r.get("version") or "").strip()
        if not (VER_RE.match(v) or v == "v1-petra"):
            add(f"version label '{v}' does not match 'vN - name'")
        co, cd, cb, sc = (num(r.get(k)) for k in ("c_open", "c_deal", "c_best", "score"))
        if None not in (co, cd, cb, sc):
            if co - cb <= 0.01:
                exp = 1.0 if cd <= cb + 0.01 else 0.0
            else:
                exp = min(1.0, max(0.0, (co - cd) / (co - cb)))
            if cd > co + 0.005:
                add(f"deal worse than opening (c_deal {cd} > c_open {co})" + ("" if sc == 0 else f"; score must be 0, is {sc}"))
            elif cd < cb - 0.005:
                add(f"c_deal {cd} below c_best {cb}")
            if abs(exp - sc) > 0.006:
                add(f"score {sc} but recomputed {exp:.4f}")
        elif not missing:
            add("non-numeric cost/score field")
        env, case, rep = r.get("environment", ""), r.get("case_id", ""), (r.get("replay") or "").strip()
        sim = env == "simulator"
        pat = r"^http://127\.0\.0\.1:8000/replay/sim\d+$" if sim else r"^https://arena\.tacto\.ai/replay/[0-9a-f]+$"
        if rep and not re.match(pat, rep):
            add(f"replay link '{rep}' unexpected for environment '{env}'")
        key = (v, r.get("agent"), case, env)
        if key in seen and "rerun" not in (r.get("notes") or "").lower():
            add(f"duplicate of line {seen[key]} (same version, agent, case)")
        seen.setdefault(key, i)
        if sim and co is not None and cb is not None:
            consts.setdefault(case, []).append((i, co, cb))
    for case, lst in consts.items():
        for idx, name in ((1, "c_open"), (2, "c_best")):
            vals = [x[idx] for x in lst]
            mode = max(set(vals), key=vals.count)
            for x in lst:
                if abs(x[idx] - mode) > 0.005:
                    out.append((x[0], f"{name} outlier for {case}: {x[idx]} vs usual {mode}"))
    return sorted(out)


def selftest():
    base = dict(date="d", version="v9 - niko", agent="a", environment="simulator", case_id="case:S01", deal="yes",
                c_open="100", c_deal="90", c_best="80", score="0.50", replay=f"{SIM}/replay/sim1", notes="")
    mk = lambda **k: {**base, **k}
    ok = stage_a([base])
    assert ok == [], ok
    bad = lambda row, text: (lambda p: p and any(text in m for _, m in p) or (_ for _ in ()).throw(
        AssertionError(f"not detected: {text}: {p}")))(stage_a([row]))
    bad(mk(score="0.80"), "recomputed")
    bad(mk(c_deal="110", score="0.00"), "worse than opening")
    bad(mk(c_deal="110", score="0.40"), "score must be 0")
    bad(mk(version="V9-x"), "version label")
    bad(mk(c_best=""), "missing field")
    bad(mk(replay="http://evil.example/replay/sim1"), "replay link")
    assert any("duplicate" in m for _, m in stage_a([base, base]))
    assert any("c_open outlier" in m for _, m in stage_a([base, mk(c_open="101", version="v8 - x"), mk(version="v7 - x")]))
    assert stage_a([mk(version="v1-petra")]) == []
    print("selftest OK")


# ---- Stage B / C -------------------------------------------------------------------------------
def http(method, path, key, body=None):
    req = urllib.request.Request(SIM + path, method=method, headers={"X-API-Key": key, "Content-Type": "application/json"},
                                 data=json.dumps(body).encode() if body is not None else None)
    with urllib.request.urlopen(req, timeout=60) as f:
        return json.load(f)


def run_once(script, case, key):
    env = {**os.environ, "ARENA_URL": SIM, "ARENA_API_KEY": key, "UV_PROJECT_ENVIRONMENT": os.path.expanduser("~/.venvs/arena-agent"),
           "PATH": os.path.expanduser("~/.local/bin") + os.pathsep + os.environ.get("PATH", "")}
    p = subprocess.run(["uv", "run", "python", f"../Players/Originals/{script}.py", case], cwd=ROOT / "agent", env=env,
                       capture_output=True, text=True, timeout=1800)
    m = re.search(r"\{.*?\n\}", p.stdout, re.S)
    sid = re.search(r"/replay/(sim\d+)", p.stdout)
    if not m:
        return {"error": (p.stderr or p.stdout)[-300:]}
    res = json.loads(m.group(0))
    res["sid"] = sid.group(1) if sid else None
    return res


def case_json(case):
    return json.load(open(ROOT / "agent/arena_kit/sim_cases" / (case.split(":")[1] + ".json")))


def cross_check(res, case, key, cost):
    """Stage C: returns a short string. Recompute c_deal from accepted terms and c_open/c_best from case JSON."""
    c = case_json(case)
    notes = []
    b, sh = c["buyer"], {}
    opts = [c["term_options"].get(f) or [None] for f in c["negotiable"][1:]]
    import itertools
    cur = b.get("current_unit_price") or b["fallback_unit_price"]
    opens = []
    for i, sup in enumerate(c["suppliers"]):
        op = round(cur * (1 + OPEN_UP + STEP * i), 2)
        std = {f: (c["term_options"].get(f) or [None])[0] for f in c["negotiable"][1:]}
        opens.append((op, std))
    co = min(cost(c, {"unit_price": op}, std) for op, std in opens)
    cb = min(cost(c, {**dict(zip(c["negotiable"][1:], combo)), "unit_price": round(op * FLOOR, 2)})
             for op, _ in opens for combo in itertools.product(*opts))
    for name, mine, theirs in (("c_open", co, res.get("c_open")), ("c_best", cb, res.get("c_best"))):
        notes.append(f"{name} {'ok' if theirs is not None and abs(mine - theirs) <= 0.01 else f'DIFF mine {mine:.2f} sim {theirs}'}")
    st = http("GET", f"/v1/sessions/{res['sid']}", key).get("result") or {}
    if st.get("terms") and st.get("c_deal") is not None:
        mine = cost(c, st["terms"])
        notes.append("c_deal " + ("ok" if abs(mine - st["c_deal"]) <= 0.01 else f"DIFF mine {mine:.2f} sim {st['c_deal']}"))
        if abs(st["c_deal"] - (res.get("c_deal") or 0)) > 0.01:
            notes.append("printed c_deal != session c_deal")
    else:
        notes.append("c_deal: session exposes no terms, not recomputed")
    return "; ".join(notes)


def stage_bc(rows, key):
    sys.path.insert(0, str(ROOT / "agent"))
    try:
        from arena_kit.cost import total_cost
    except Exception as e:  # noqa
        total_cost = None
        print("Stage C unavailable:", e)
    cache, results = {}, []
    for i, r in enumerate(rows, start=2):
        v, case = vkey(r["version"]), r["case_id"]
        base = dict(line=i, version=r["version"], case=case, bc=r["c_deal"], bs=r["score"], r1="-", r2="-", cx="-")
        if r.get(None):
            results.append({**base, "status": "MISMATCH", "r1": "malformed csv row"}); continue
        if r["environment"] != "simulator":
            results.append({**base, "status": "not-reproducible (practice arena)"}); continue
        if v == "v2":
            results.append({**base, "status": "superseded, not reproducible"}); continue
        if v not in SCRIPT:
            results.append({**base, "status": "not-reproducible (no script)"}); continue
        k = (SCRIPT[v], case)
        if k not in cache:
            print(f"running {k} twice ...", flush=True)
            a, b = run_once(*k, key), run_once(*k, key)
            cx = cross_check(a, case, key, total_cost) if total_cost and "error" not in a and a.get("sid") else "n/a"
            cache[k] = (a, b, cx)
        a, b, cx = cache[k]
        if "error" in a or "error" in b:
            results.append({**base, "status": "MISMATCH", "r1": "run failed: " + str(a.get("error") or b.get("error"))[:80]}); continue
        f = lambda x: f"{x.get('c_deal')}/{x.get('score')}"
        ok = all(abs((num(r[c]) or 0) - (a.get(c) or 0)) <= t for c, t in (("c_open", .01), ("c_deal", .01), ("c_best", .01), ("score", .006)))
        ok &= abs((a.get("c_deal") or 0) - (b.get("c_deal") or 0)) <= 0.01
        ok &= "DIFF" not in cx and "!=" not in cx
        results.append({**base, "r1": f(a), "r2": f(b), "cx": cx, "status": "OK" if ok else "MISMATCH"})
        if v == "v7":  # router: note must name the archetype the goal maps to
            goal = case_json(case)["buyer"].get("category_goal")
            exp = ROUTE.get(goal, "rational")
            have = exp in (r.get("notes") or "") or (exp == "rational" and "Patient Hawk" in (r.get("notes") or ""))
            results[-1]["cx"] += f"; router goal {goal}->{exp}: note {'ok' if have else 'DIFFERS'}"
            if not have:
                results[-1]["status"] = "MISMATCH"
    # identical c_deal across different agents (informational)
    byk = {}
    for x in results:
        if x["status"] == "OK" and x["r1"] != "-":
            byk.setdefault((x["case"], x["r1"].split("/")[0]), set()).add(x["version"])
    ident = [f"{c} c_deal {d}: {sorted(vs)}" for (c, d), vs in byk.items() if len({vkey(v) for v in vs}) > 1]
    return results, ident


def write_report(problems, results, ident, note):
    mism = [x for x in results if x["status"] == "MISMATCH"]
    verdict = "FAIL" if mism or problems else "PASS"
    L = [f"# Backlog verification report", "", f"**Overall: {verdict}** (Stage A problems: {len(problems)}, Stage B/C mismatches: {len(mism)})", "", note, "",
         "## Problems (Stage A)", ""]
    L += ["| line | problem |", "|---|---|"] + [f"| {a} | {m} |" for a, m in problems] if problems else ["none"]
    L += ["", "## Per-row comparison (Stage B/C)", ""]
    if results:
        L += ["| line | version | case | backlog c_deal/score | rerun | run 2 | cost cross-check | status |", "|---|---|---|---|---|---|---|---|"]
        L += [f"| {x['line']} | {x['version']} | {x['case']} | {x['bc']}/{x['bs']} | {x['r1']} | {x['r2']} | {x['cx']} | {x['status']} |" for x in results]
    else:
        L.append("not run (use --rerun)")
    if ident:
        L += ["", "## Identical c_deal between different agents: confirm by reading both replays", ""] + [f"- {s}" for s in ident]
    REPORT.write_text("\n".join(L) + "\n")
    return verdict, len(mism)


def main():
    if "--selftest" in sys.argv:
        return selftest()
    with open(BACKLOG, newline="") as f:
        rows = list(csv.DictReader(f))
    problems = stage_a(rows)
    print(f"Stage A: {len(rows)} rows, {len(problems)} problem(s)")
    for a, m in problems:
        print(f"  line {a}: {m}")
    results, ident, note = [], [], "Stage B/C not run."
    if "--rerun" in sys.argv:
        try:
            urllib.request.urlopen(SIM + "/health", timeout=5)
        except Exception:
            print("Simulator is not up. Start it: cd agent && uv run arena-sim serve --no-clock")
            sys.exit(2)
        key = os.environ.get("ARENA_API_KEY")
        if not key:
            req = urllib.request.Request(SIM + "/v1/register", method="POST", headers={"Content-Type": "application/json"},
                                         data=json.dumps({"team_name": f"VerifyBot{os.getpid()}", "event_code": "sim"}).encode())
            key = json.load(urllib.request.urlopen(req, timeout=10))["api_key"]
        results, ident = stage_bc(rows, key)
        note = "Stage B/C run against the local simulator " + SIM + "."
    verdict, nm = write_report(problems, results, ident, note)
    print(f"Overall {verdict}; {nm} MISMATCH row(s); report: {REPORT}")
    sys.exit(1 if nm else 0)


if __name__ == "__main__":
    main()
