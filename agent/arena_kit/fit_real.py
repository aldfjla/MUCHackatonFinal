"""Refit the real-like supplier on ALL real dumps (real_runs, real_runs_v16, v17, v19): what fit_supplier.py
(first 40 dumps only) misses. Merges into sim_cases/supplier_profile.json; run it AFTER fit_supplier.py.

    python -m arena_kit.fit_real [--dirs real_runs,real_runs_v16,...]   # writes the profile
    fit(dirs) -> dict                                                    # no write: the hold-out test uses it

Per supplier thread (exact values for the `real` set), over every run of it:
- floor: the lowest value (cash at its standard terms) of any plain sheet (contract <= 12 months, no index clause);
- bonus_long / bonus_clause: how much lower (share of its opening) it quotes for a contract >= 24 months /
  with an index clause (P18 6.10 -> 5.50, P02 370.96 -> 345.51);
- final_round: the earliest round it sent final_offer (a fixed index of its own messages);
- health (stabilise cases): full_cost and interest rate that reproduce the arena's recorded `relationship` term.
For generated cases the same quantities become per-type / pooled distributions. Reads local files only.
"""

import argparse
import glob
import hashlib
import json
import statistics as st
from pathlib import Path

from .cost import RELATIONSHIP_GOALS, closing_terms, relationship_cost, supplier_value
from .sim import CASES, load_cases
from .sim_real import PROFILE

ALL_DIRS = ["real_runs", "real_runs_v16", "real_runs_v17", "real_runs_v19"]
LONG = 24  # months: the contract length that earns a supplier bonus
HOLDOUT = Path(__file__).parent / "holdout.json"


def dumps(dirs, exclude=()):
    """Every dump of `dirs`, except those of the cases named in `exclude` (e.g. {"P04"})."""
    for d in dirs:
        for f in sorted(glob.glob(str(CASES / d / "*_P*.json"))):
            x = json.loads(Path(f).read_text(encoding="utf-8"))
            if x["case"] not in exclude:
                yield x


def make_split(seed=0, n_sup=3, n_combo=2, dirs=ALL_DIRS):
    """Deterministic reserved split of the real cases: n_sup whole suppliers (every case they appear in) plus
    n_combo (case type, goal) combinations that those cases do not cover (every case of the combination)."""
    cases = load_cases(CASES / "real")
    sups, combo_of = {}, {}
    for d in dumps(dirs):
        combo_of[d["case"]] = tuple([cases[f"case:{d['case']}"]["type"], cases[f"case:{d['case']}"]["buyer"]["category_goal"]])
        for s in d["threads"]:
            sups.setdefault(s, set()).add(d["case"])
    order = lambda names: sorted(names, key=lambda n: hashlib.sha256(f"{seed}|{n}".encode()).hexdigest())  # noqa: E731
    picked = order(sups)[:n_sup]
    unseen = set().union(*(sups[s] for s in picked))
    covered = {combo_of[c] for c in unseen}
    combos = order(sorted({c for c in combo_of.values() if c not in covered}))[:n_combo]
    unseen |= {c for c, k in combo_of.items() if k in combos}
    return {
        "seed": seed,
        "suppliers": sorted(picked),
        "combos": sorted(map(list, combos)),
        "unseen": sorted(unseen),
        "train": sorted(set(combo_of) - unseen),
    }


def load_split():
    return json.loads(HOLDOUT.read_text(encoding="utf-8"))


def spread(xs):
    return {"min": min(xs), "median": st.median(xs), "max": max(xs)} if xs else {}


def fit_health(case, std, rows, rate=None):
    """(full_cost, rate) of the relationship term from [(terms, recorded relationship)]; None without a nonzero row.
    A grid on the rate, a scan on full_cost, then a local refinement; zero rows must stay zero."""
    if not any(rel for _, rel in rows):
        return None
    op = case["buyer"]["current_unit_price"] or rows[0][0]["unit_price"]

    def err(fc, r):
        sup = {"standard": std, "interest_rate": r, "full_cost": fc}
        return sum((relationship_cost(case, t, supplier=sup) - rel) ** 2 for t, rel in rows)

    best = min(
        ((err(fc, r), fc, r) for r in ([rate] if rate else [0.04 + 0.002 * i for i in range(41)]) for fc in [op * (0.6 + 0.001 * j) for j in range(800)]),
        key=lambda x: x[0],
    )  # fmt: skip
    _, fc, r = best
    for step in (0.2, 0.02, 0.002):
        _, fc, r = min(
            ((err(fc + dx * step, r + dr * step / 100), fc + dx * step, r + dr * step / 100) for dx in range(-10, 11) for dr in ([0] if rate else range(-10, 11))),
            key=lambda x: x[0],
        )  # fmt: skip
    return round(fc, 2), round(r, 4), round(err(fc, r) ** 0.5, 2)


def fit(dirs=ALL_DIRS, profile=None, exclude=()):
    prof = profile or json.loads(PROFILE.read_text(encoding="utf-8"))
    cases = load_cases(CASES / "real")
    std_days = prof["meta"]["standard_days"]
    rates = prof["parameters"]["supplier_interest_rate"]["per_case"]
    rate_med = prof["parameters"]["supplier_interest_rate"]["median"]
    threads, health_rows, bounds = {}, {}, {}
    for d in dumps(dirs, exclude):
        cid, res = f"case:{d['case']}", d["result"]
        case = cases[cid]
        bounds[d["case"]] = {"c_open": res["c_open"], "c_best": res["c_best"]}
        if res.get("deal") and res.get("cost_breakdown"):
            health_rows.setdefault(d["case"], []).append(
                (res["terms"], res["cost_breakdown"]["relationship"], res["supplier_id"])
            )
        for sup, th in d["threads"].items():
            key = f"{d['case']}|{sup}"
            spd = std_days.get(key, [30])[0]
            std = closing_terms(case, {"payment_days": spd})
            r = rates.get(d["case"], rate_med)
            t = threads.setdefault(
                key, {"plain": [], "long": [], "clause": [], "final": [], "opening": None, "std": std, "r": r}
            )
            for i, m in enumerate(x for x in th["messages"] if x["from"] != "buyer"):
                for ts in m.get("term_sheets") or []:
                    tm = ts["terms"]
                    if not tm.get("unit_price"):
                        continue
                    v = supplier_value(
                        case,
                        {**tm, "contract_months": tm.get("contract_months") or 12},
                        {"standard": std, "interest_rate": r},
                    )
                    kind = (
                        "clause"
                        if tm.get("index_clause")
                        else "long"
                        if (tm.get("contract_months") or 0) >= LONG
                        else "plain"
                    )
                    t[kind].append(v)
                    if i == 0:
                        t["opening"] = v
                if m.get("status") == "final_offer":
                    t["final"].append(i)
                    break
    real = {}
    for key, t in threads.items():
        if not t["plain"] or t["opening"] is None:
            continue
        floor = min(t["plain"])
        e = {"opening": t["opening"], "floor": round(floor, 2)}
        if t["final"]:
            e["final_round"] = min(st.multimode(t["final"]))
        if t["long"]:
            e["bonus_long"] = round(max(0.0, floor - min(t["long"])) / t["opening"], 4)
        if t["clause"]:
            e["bonus_clause"] = round(max(0.0, floor - min(t["clause"])) / t["opening"], 4)
        real[key] = e
    health = {}
    for c, rows in health_rows.items():
        case = cases[f"case:{c}"]
        if case["buyer"].get("category_goal") not in RELATIONSHIP_GOALS:
            continue
        sups = {s for _, _, s in rows}
        key = next(k for k in threads if k.startswith(f"{c}|") and k.split("|")[1] in sups)
        nonzero = {rel for _, rel, _ in rows if rel}
        # one nonzero value cannot identify both unknowns: price it at the rate of the cases that can
        f = fit_health(case, threads[key]["std"], [(t, rel) for t, rel, _ in rows], None if len(nonzero) > 1 else 0.081)
        if f:
            health[key] = {
                "full_cost": f[0],
                "rate": f[1],
                "residual_eur": f[2],
                "full_cost_ratio": round(f[0] / real[key]["opening"], 4),
            }
    # distributions for generated cases, by case type (or pooled when the type has < 2 threads)
    by_type, pooled = {}, []
    for key, e in real.items():
        ratio = e["floor"] / e["opening"]
        by_type.setdefault(cases[f"case:{key.split('|')[0]}"]["type"], []).append(ratio)
        pooled.append(ratio)
    return {
        "real_suppliers": real,
        "real_bounds": bounds,
        "health": health,
        "floor_ratio": {
            "by_type": {k: spread(v) | {"n": len(v)} for k, v in by_type.items()},
            "pooled": spread(pooled),
        },
        "bonus_long": [e["bonus_long"] for e in real.values() if "bonus_long" in e],
        "bonus_clause": [e["bonus_clause"] for e in real.values() if "bonus_clause" in e],
        "final_round": [e["final_round"] for e in real.values() if "final_round" in e],
    }


def to_parameters(f, n_dumps):
    ev = f"{n_dumps} real dumps (fit_real.py), {len(f['real_suppliers'])} supplier threads"
    h = [v["full_cost_ratio"] for v in f["health"].values()]
    return {
        "real_suppliers": {
            "status": "fitted",
            "n": len(f["real_suppliers"]),
            "evidence": ev,
            "uncertainty": "floor = lowest plain quote seen over all runs: an upper bound of the true floor",
            "threads": f["real_suppliers"],
            "bounds": f["real_bounds"],
        },
        "floor_ratio": {
            "status": "fitted",
            "n": len(f["real_suppliers"]),
            "evidence": ev + ": lowest plain quote / opening",
            "uncertainty": "1-3 threads per case type",
            **f["floor_ratio"],
        },
        "bonus_long": {
            "status": "fitted_n1" if len(f["bonus_long"]) < 3 else "fitted",
            "n": len(f["bonus_long"]),
            "evidence": ev + ": price cut for a contract >= 24 months, share of opening",
            "uncertainty": "threads that never tried it are missing",
            "samples": f["bonus_long"],
        },
        "bonus_clause": {
            "status": "fitted_n1" if len(f["bonus_clause"]) < 3 else "fitted",
            "n": len(f["bonus_clause"]),
            "evidence": ev + ": price cut for an index clause (with 24 months), share of opening",
            "uncertainty": "P02/P08/P18 only",
            "samples": f["bonus_clause"],
        },
        "final_round_index": {
            "status": "fitted",
            "n": len(f["final_round"]),
            "evidence": ev + ": earliest round of final_offer per thread",
            "uncertainty": "fixed per supplier, not by our moves; a thread we accepted early shows none",
            "samples": f["final_round"],
        },
        "health": {
            "status": "fitted_n1" if len(h) < 3 else "fitted",
            "n": len(h),
            "evidence": "arena's recorded `relationship` term of the deals (P01, P02, P03), grid fit of (full_cost, rate)",
            "uncertainty": "P03 has one nonzero value, so its rate is not identified",
            "threads": f["health"],
            "full_cost_ratio": spread(h),
            "rate": spread([v["rate"] for v in f["health"].values()]),
        },
        "floor_cap": {
            "status": "assumed",
            "n": 0,
            "evidence": "a generated case always leaves room: the floor is at most 0.98 of the opening (real plain floors reach 0.99-1.0, the room there came from long contracts and clauses)",
            "uncertainty": "no evidence",
            "value": 0.98,
        },
        "package_bonus_start": {
            "status": "assumed",
            "n": 0,
            "evidence": "first quote for a long/clause package gives this share of the bonus (P18 first quotes 5.7-5.8 vs 5.5 final)",
            "uncertainty": "no evidence beyond P18",
            "min": 0.3,
            "max": 0.6,
        },
        "package_bonus_gain": {
            "status": "assumed",
            "n": 0,
            "evidence": "per round the share of the bonus rises by base + slope * (our step / its opening)",
            "uncertainty": "P18: step +0.02 -> 5.70, +0.25 -> 5.60, more -> 5.50",
            "base": 0.1,
            "slope": 8.0,
            "max": 0.5,
        },
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dirs", default=",".join(ALL_DIRS))
    ap.add_argument("--out", default=str(PROFILE))
    ap.add_argument("--all", action="store_true", help="fit on ALL cases incl. the reserved ones (no unseen score is valid after)")
    ap.add_argument("--make-split", action="store_true", help="(re)write holdout.json; do it once, then keep it")
    a = ap.parse_args(argv)
    if a.make_split:
        HOLDOUT.write_text(json.dumps(make_split(), indent=1) + "\n", encoding="utf-8")
    dirs = a.dirs.split(",")
    ex = set() if a.all else set(load_split()["unseen"])
    from . import fit_supplier  # the base profile (pooled parameters) is refitted without the reserved cases too

    out = fit_supplier.fit(str(Path.home() / "Documents/Codex/negotiation-arena-kit/data"), ex)
    n = sum(1 for _ in dumps(dirs, ex))
    out["parameters"].update(to_parameters(fit(dirs, out, ex), n))
    out["meta"]["split"] = "all (in-sample)" if a.all else f"train only; reserved: {sorted(ex)}"
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {a.out} from {n} dumps ({out['meta']['split']})")


if __name__ == "__main__":
    main()
