"""Fit the real-like supplier from evidence: every real practice dump (sim_cases/real_runs), the
real case files (sim_cases/real) and the data package. Writes sim_cases/supplier_profile.json.

    python -m arena_kit.fit_supplier [--data <data package>] [--out supplier_profile.json]

Every parameter carries `status` ("fitted": n >= 3 cases or threads; "fitted_n1": 1-2, a single anecdote;
"assumed": no evidence, or only bounds), the evidence it comes from and its uncertainty. Nothing is
invented: what the dumps cannot show is marked assumed, and so are the constants the mock needs. Reads local files only; never calls the arena.
"""
# ruff: noqa: E501  (the evidence texts of the profile are long sentences)

import argparse
import glob
import itertools
import json
import re
import sqlite3
import statistics as st
from pathlib import Path

from .cost import total_cost
from .sim_real import levers, package_cost

HERE = Path(__file__).parent / "sim_cases"
STD_PD = 30  # the default when a supplier never states its standard payment days


def sheets(msg, spd=STD_PD):
    """(price, payment_days) of each term sheet of a message; no payment days = the supplier's standard."""
    return [
        (x["terms"]["unit_price"], x["terms"].get("payment_days") or spd)
        for x in (msg.get("term_sheets") or [])
        if x["terms"].get("unit_price")
    ]


def value(price, pd, r, spd=STD_PD):
    """Cash-equivalent of a price at the standard payment days, for a supplier whose money costs r a year."""
    return price * (1 - r * (pd - spd) / 360)


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


def spread(xs):
    return {"min": min(xs), "median": st.median(xs), "max": max(xs)} if xs else {}


def param(status, n, evidence, uncertainty, **vals):
    """status 'fitted' with fewer than 3 cases or threads is a single anecdote: it is stored as 'fitted_n1'."""
    if status == "fitted" and n < 3:
        status = "fitted_n1"
    return {"status": status, "n": n, "evidence": evidence, "uncertainty": uncertainty, **vals}


STD_RE = re.compile(r"standard Zahlungsziel is (\d+) days")


def standard_days(runs):
    """{(case_id, supplier): (days, source)}: the standard payment days each supplier states in its e-mails
    ('text'), or the case's fixed payment_days ('fixed'), else the default 30 ('default')."""
    out = {}
    for run in runs:
        for sup, t in run["d"]["threads"].items():
            got = [int(x) for m in t["messages"] if m["from"] != "buyer" for x in STD_RE.findall(m.get("body") or "")]
            key = (run["case_id"], sup)
            if got:
                out[key] = (st.mode(got), "text")
            elif key not in out:
                fixed = run["case"].get("fixed_terms", {}).get("payment_days")
                out[key] = (fixed, "fixed") if fixed else (STD_PD, "default")
    return out


def load():
    runs = []
    for f in sorted(glob.glob(str(HERE / "real_runs" / "*_P*.json"))):
        d = json.load(open(f))
        case = json.load(open(HERE / "real" / f"{d['case']}.json"))
        runs.append({"agent": d["agent"], "case_id": d["case"], "case": case, "d": d, "r": d["result"]})
    return runs


def pair_rates(msgs, spd=STD_PD):
    """The supplier's cost of money r from messages that quote the same offer at two payment terms."""
    out = []
    for m in msgs:
        s = sheets(m, spd)
        for (p1, d1), (p2, d2) in itertools.combinations(s, 2):
            if d1 != d2 and spd in (d1, d2) and p1 and p2:  # equal-value pair: one is the standard term
                den = p1 * (d1 - spd) - p2 * (d2 - spd)
                if den and 0 < (r := 360 * (p1 - p2) / den) < 0.5:
                    out.append(r)
    return out


def standard_terms(case, run_results, quote=None, spd=STD_PD):
    """The supplier's standard terms: fields it states in its opening quote, then non-negotiated fields
    (ppm, chargeback) from any deal on the case, then the supplier's standard payment days / the first option for gaps."""
    std = {}
    for r in run_results:
        if r["terms"]:
            std = {k: v for k, v in r["terms"].items() if k not in case["negotiable"]}
            break
    for f in levers(case):
        o = case["term_options"].get(f) or [None]
        std[f] = spd if f == "payment_days" else o[0]
    std.update({k: v for k, v in (quote or {}).items() if k != "unit_price"})
    return std


def implied_floor(case, std, r_s, c_best, opening):
    """The supplier's floor V (cash value per unit at its standard terms) that reproduces the arena's
    C_best: bisect V so that the cheapest package it would accept (every lever) costs c_best."""
    lo, hi = 0.2 * opening, 1.6 * opening
    if not package_cost(case, std, r_s, lo) < c_best < package_cost(case, std, r_s, hi):
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if package_cost(case, std, r_s, mid) < c_best else (lo, mid)
    return (lo + hi) / 2


def fit(data_dir):
    runs = load()
    by_case = {}
    for r in runs:
        by_case.setdefault(r["case_id"], []).append(r)
    P = {}
    spd = standard_days(runs)
    n_threads = len({k for k in spd})
    n_thread_runs = sum(len(r["d"]["threads"]) for r in runs)
    n_dumps = len(runs)

    # -- supplier cost of money from price pairs at two payment terms --------------------------
    rates = {}
    for cid, rs in by_case.items():
        vals = [
            x
            for run in rs
            for sup, t in run["d"]["threads"].items()
            for x in pair_rates([m for m in t["messages"] if m["from"] != "buyer"], spd[(cid, sup)][0])
        ]
        if vals:
            rates[cid] = st.median(vals)
    r_all = st.median(rates.values())
    P["supplier_interest_rate"] = param(
        "fitted", len(rates),
        "price pairs in one supplier message at two payment terms (e.g. P01: 137.50 at 60 days vs 136.40 at 30)",
        f"per-case values {spread(list(rates.values()))}; the buyer rates in the cases are 0.04-0.12; per case rate not given by the arena",
        per_case={k: round(v, 4) for k, v in rates.items()}, min=round(min(rates.values()), 4),
        median=round(r_all, 4), max=round(max(rates.values()), 4),
    )  # fmt: skip
    texts_pd = {k: v[0] for k, v in spd.items() if v[1] == "text"}
    neg_pd = {
        (r["case_id"], sup) for r in runs if "payment_days" in r["case"]["negotiable"] for sup in r["d"]["threads"]
    }
    samples_pd = sorted(v for k, v in texts_pd.items() if k in neg_pd)
    P["standard_payment_days"] = param(
        "fitted", len(samples_pd),
        f"'our standard Zahlungsziel is N days net' in the supplier e-mails, per supplier thread (payment_days negotiable): {dict(sorted(((str(k), v) for k, v in texts_pd.items() if k in neg_pd)))}; "
        f"P11 sup:70140 says 60 and has payment_days fixed at 60; threads that never say it default to 30 ({sum(1 for v in spd.values() if v[1] == 'default')} of {n_threads})",
        "not always 30: P05 sup:70240 says 45; the default 30 for silent threads is an assumption",
        samples=samples_pd, default=STD_PD,
    )  # fmt: skip

    # -- opening price relative to the buyer's current/fallback price --------------------------
    opens, c_open_check, std_of = [], {}, {}
    for cid, rs in by_case.items():
        case, b = rs[0]["case"], rs[0]["case"]["buyer"]
        costs = []
        for sup, t in rs[0]["d"]["threads"].items():
            first = next(m for m in t["messages"] if m["from"] != "buyer")
            quote = first["term_sheets"][0]["terms"]
            op = quote["unit_price"]
            opens.append({"case": cid, "type": case["type"], "supplier": sup, "opening": op,
                          "vs_current": round(op / b["current_unit_price"], 4) if b.get("current_unit_price") else None,
                          "vs_fallback": round(op / b["fallback_unit_price"], 4)})  # fmt: skip
            std = standard_terms(case, [x["r"] for x in rs], quote, spd[(cid, sup)][0])
            costs.append((total_cost(case, {f: std[f] for f in levers(case)} | {"unit_price": op}, std), op, std))
        c, op, std_of[cid] = min(costs, key=lambda x: x[0])
        # the arena's C_open = the cheapest opening quote: does it match our standard-terms recomputation?
        c_open_check[cid] = {
            "reported": rs[0]["r"]["c_open"],
            "recomputed_min": c,
            "match_pct": round(100 * (c / rs[0]["r"]["c_open"] - 1), 3),
        }
    cur = [o["vs_current"] for o in opens if o["vs_current"]]
    types = {}
    for o in opens:
        if o["vs_current"]:
            types.setdefault(o["type"], []).append(o["vs_current"])
    P["opening_vs_current_price"] = param(
        "fitted", len(cur),
        f"first supplier quote / the case's current_unit_price, 10 hosted cases, {n_threads} supplier threads",
        "ratio ranges 0.91 (bundling, below current) to 1.13; by case type only 1-2 samples each; P05 (rfq) has no current price",
        by_type={k: {"n": len(v), **spread(v)} for k, v in types.items()},
        pooled_excl_rfq=spread([x for k, v in types.items() if k != "rfq" for x in v]), **{k: v for k, v in spread(cur).items() if k != "n"},
        samples=sorted(cur),
    )  # fmt: skip
    facts = json.loads((Path(data_dir) / "facts.json").read_text(encoding="utf-8"))
    ann = []
    for cid, rs in by_case.items():
        asked = (facts.get(rs[0]["case"]["trigger_doc"]) or {}).get("asked_price")
        if asked:
            op = next(o["opening"] for o in opens if o["case"] == cid)
            ann.append({"case": cid, "asked_price": asked, "opening": op})
    P["opening_equals_announced_price"] = param(
        "fitted", len(ann), "price_increase letters (documents.asked_price) vs the supplier's opening quote (2 cases)",
        "P01 and P02 open exactly at the announced price; P13/P17 letters exist but were not played; other types have no letter (fitted ratio used)",
        pairs=ann,
    )  # fmt: skip

    # -- which terms the opening quote states ------------------------------------------------------
    seen, st_n, tot_n = set(), {}, {}
    for run in runs:
        for sup, t in run["d"]["threads"].items():
            if (run["case_id"], sup) in seen:
                continue
            seen.add((run["case_id"], sup))
            stated = set(t["messages"][0]["term_sheets"][0]["terms"])
            for f in levers(run["case"]):
                tot_n[f], st_n[f] = tot_n.get(f, 0) + 1, st_n.get(f, 0) + (f in stated)
    P["opening_omits_field"] = param(
        "fitted", len(seen), f"terms the first quote states vs leaves out (missing_fields), {n_threads} supplier threads: payment_days omitted in 4 of 10, lead_time_days 2 of 4 (rfq P05), chargeback 1 of 1",
        "small counts per field; other fields were always stated (contract_months 6/6, index_clause 3/3, volume 2/2, ppm 1/1); fields not in the list default to 0",
        rates={f: {"omit": round(1 - st_n[f] / tot_n[f], 3), "n": tot_n[f]} for f in tot_n},
    )  # fmt: skip

    # -- floor implied by the arena's own C_best -------------------------------------------------
    floors, floor_rows, ftypes = [], {}, {}
    for cid, rs in by_case.items():
        case, res = rs[0]["case"], rs[0]["r"]
        std = std_of[cid]
        ok = abs(c_open_check[cid]["match_pct"]) < 0.5
        ops = [o["opening"] for o in opens if o["case"] == cid]
        row = {"c_open_matches": ok, "c_best": res["c_best"], "c_open": res["c_open"]}
        if ok and res["c_best"] < (res["c_alt"] or 1e18) - 1:
            r_s = rates.get(cid, r_all)
            lo = implied_floor(case, std, min(r_s, r_all) * 0.7, res["c_best"], min(ops))
            mid = implied_floor(case, std, r_s, res["c_best"], min(ops))
            hi = implied_floor(case, std, max(r_s, r_all) * 1.3, res["c_best"], min(ops))
            row.update(floor_ratio=round(mid / min(ops), 4) if mid else None,
                       floor_ratio_range=[round(x / min(ops), 4) for x in (lo, hi) if x],
                       r_used=round(r_s, 4), rate_fitted=cid in rates)  # fmt: skip
            if mid:
                floors.append(mid / min(ops))
                ftypes.setdefault(case["type"], []).append(mid / min(ops))
        floor_rows[cid] = row
    P["floor_vs_opening"] = param(
        "fitted", len(floors),
        "the supplier's cheapest accepted package: V such that the cheapest lever package at V costs the arena's C_best (cost.supplier_value, cost.total_cost); ratio V / best opening quote",
        "assumes C_best = supplier_value floor with every lever (brief.md section 6); standard terms rebuilt from the deals; rate varies +-30%; "
        "the floors of P03/P07/P08/P18 lie far below anything a supplier conceded (it froze first), so they bound room, not behaviour",
        per_case=floor_rows, by_type={k: {"n": len(v), **{x: round(y, 4) for x, y in spread(v).items()}} for k, v in ftypes.items()}, **{k: round(v, 4) for k, v in spread(floors).items() if k != "n"}, samples=sorted(round(f, 4) for f in floors),
    )  # fmt: skip

    # -- concession, final offer, walk-away, claims --------------------------------------------
    g_runs, idle_steps, step1_claims, step1_plain, step1_multi, pass_rows = [], [], [], [], [], []
    finals, walks, last_ask_ratio, accepts = [], [], [], []
    for run in runs:
        cid, b = run["case_id"], run["case"]["buyer"]
        r_s = rates.get(cid, r_all)
        for sup, t in run["d"]["threads"].items():
            d0 = spd[(cid, sup)][0]
            S = [m for m in t["messages"] if m["from"] != "buyer"]
            B = [m for m in t["messages"] if m["from"] == "buyer" and sheets(m, d0)]
            if not S or not sheets(S[0], d0):
                continue
            sv = [value(*sheets(m, d0)[0], r_s, d0) if sheets(m, d0) else None for m in S]
            bv = [max(value(p, d, r_s, d0) for p, d in sheets(m, d0)) for m in B]
            bv = list(itertools.accumulate(bv, max))  # only a NEW best offer of ours earns a pass-through
            o = sv[0]
            fin = next((i for i, m in enumerate(S) if m["status"] == "final_offer"), None)
            if fin is not None:
                last_ask_ratio.append(sv[fin] / o)
            finals.append({"run": run["agent"] + "_" + cid, "supplier": sup, "round": fin,
                           "idle_moves_before": sum(1 for i in range(1, min(fin or 0, len(bv))) if bv[i] - bv[i - 1] < 0.002 * o) if fin else None,
                           "buyer_moves_before": min(fin or 0, len(B))})  # fmt: skip
            end = min(fin if fin is not None else len(S) - 1, len(S) - 1)
            dsum = bsum = 0.0
            for i in range(1, end + 1):
                if sv[i] is None or i - 1 >= len(bv):
                    break
                ds = sv[i - 1] - sv[i]
                n_ver = sum(c.get("result") == "verified" for c in (S[i].get("claim_results") or []))
                if i == 1:
                    (
                        step1_multi if len(run["case"]["suppliers"]) > 1 else step1_claims if n_ver else step1_plain
                    ).append((ds / o, n_ver))
                    continue
                db = bv[i - 1] - bv[i - 2] if i >= 2 and i - 1 < len(bv) else 0
                if db < 0.002 * o:
                    idle_steps.append(ds / o)
                else:
                    dsum, bsum = dsum + ds, bsum + db
                pass_rows.append((cid, round(db / o, 4), round(ds / o, 4)))
            if bsum > 0.01 * o:
                g_runs.append(dsum / bsum)
            # walk-away / agreement after final: pushes that did not meet the ask
            if fin is not None:
                pushes = [m for m in B[fin:] if sheets(m, d0)]
                walked = S[-1]["status"] == "walked_away"
                (walks if walked else accepts).append(
                    {"run": run["agent"] + "_" + cid, "supplier": sup, "pushes_after_final": len(pushes)}
                )
    P["concession_pass_through"] = param(
        "fitted", len(g_runs), "per thread: sum(supplier ask drop) / sum(our rise in the best offer's value so far), rounds 2..final, rounds where we moved >0.2% of the opening",
        "range is wide (P02 about 0.02: supplier froze while we moved 10 EUR; P01 about 0.4-0.6); case dependent, not predictable from case fields",
        **spread([round(g, 3) for g in g_runs]), samples=sorted(round(g, 3) for g in g_runs),
    )  # fmt: skip
    P["idle_step"] = param(
        "fitted", len(idle_steps), "supplier ask drop per round (share of opening) in rounds where we moved <0.2% of the opening",
        "mostly 0 or tiny; sometimes a small step; samples listed", **spread([round(x, 4) for x in idle_steps]), samples=sorted(round(x, 4) for x in idle_steps),
    )  # fmt: skip
    P["first_reply_drop_with_verified_claims"] = param(
        "fitted", len(step1_claims), "first supplier reply drop (share of opening) when it verified >=1 cited fact (evidence_router runs)",
        "tiny sample; supplier text also moves the effective date after a verified notice-period claim (P01)",
        samples=[round(x, 4) for x, _ in step1_claims],
    )  # fmt: skip
    P["first_reply_drop_plain"] = param(
        "fitted", len(step1_plain), "first supplier reply drop (share of opening), single-supplier cases, no verified claim",
        "negative values (supplier raised its price for 90 days) are kept as measured; the mock clips them to 0", samples=sorted(round(x, 4) for x, _ in step1_plain),
    )  # fmt: skip
    P["first_reply_drop_multi_supplier"] = param(
        "fitted", 1, f"first reply drop in P05 (rfq, 3 suppliers compete): much larger than single-supplier ({len(step1_multi)} samples, ONE case)",
        "one case, three suppliers; assumed to generalise to every case with >1 supplier", samples=sorted(round(x, 4) for x, _ in step1_multi),
    )  # fmt: skip
    fr = [f["round"] for f in finals if f["round"] is not None]
    P["final_offer_round"] = param(
        "fitted", len(fr), f"reply index of the first final_offer in each supplier thread ({n_dumps} dumps, {n_thread_runs} thread-runs)",
        f"{len(finals) - len(fr)} threads never sent one (agreed at once, or the run ended); depends little on how much we moved; round limit is 10",
        **spread(fr), samples=sorted(fr), threads=finals,
    )  # fmt: skip
    wp = [w["pushes_after_final"] for w in walks]
    P["walk_after_pushes_post_final"] = param(
        "fitted", len(wp), "pushes (our term sheets that did not meet the ask) after final_offer before the supplier walked away",
        f"{len(wp)} walks but only 3 cases (P05 two suppliers, P10): "
        "walks: P05 70210 (4), 70250 (1 and 3), P10 (1,1,1). Not walks: P01 2 pushes then price re-quoted for 90 days, P07 1 push matched",
        samples=sorted(wp), walks=walks, no_walk=accepts,
    )  # fmt: skip
    P["final_offer_ask_vs_opening"] = param(
        "fitted", len(last_ask_ratio), "value of the final_offer / opening value (at the standard payment days)",
        "the supplier's frozen position: how far it actually came down in all dumps", **spread([round(x, 4) for x in last_ask_ratio]),
        samples=sorted(round(x, 4) for x in last_ask_ratio),
    )  # fmt: skip

    # -- term trades and hard limits ---------------------------------------------------------
    texts = [
        (run["case_id"], s, m.get("body") or "")
        for run in runs
        for s, t in run["d"]["threads"].items()
        for m in t["messages"]
        if m["from"] != "buyer"
    ]
    limit_threads = {(c, s) for c, s, b in texts if "absolute limit" in b and "30 days" in b}
    all_threads = {(c, s) for c, s, _ in texts}
    cap_threads = {(c, s) for c, s, b in texts if "allocation cap" in b}
    P["payment_days_trade"] = param(
        "fitted", len(rates), "= supplier_interest_rate: a longer payment term costs the buyer about r * days / 360 of the price",
        "pairs fit one rate per case with spread; whether the supplier accepts 90 days at all is the hard limit below",
    )  # fmt: skip
    P["payment_days_hard_limit_30"] = param(
        "fitted", len(limit_threads), f"'30 days is our absolute limit / strictly tied to 30 days' said by {sorted(limit_threads)}",
        f"1 of {len(all_threads)} threads (8%), ONE thread: P05 sup:70210, a small owner-run shop; the other threads traded 60 or 90 days for a higher price (the 'absolute limit' of P05 sup:70240 is about price, not days)",
        share=round(len(limit_threads) / len(all_threads), 3),
    )  # fmt: skip
    lifted = [
        run["agent"]
        for run in runs
        if run["case_id"] == "P10" and run["r"]["terms"] and run["r"]["terms"].get("volume_per_year", 0) > 19890
    ]
    P["volume_cap"] = param(
        "fitted",
        len(cap_threads),
        f"P10 capacity: 'our allocation cap strictly limits the volume to 19,890 pieces per year' (middle of options 16379/19890/23400); {sorted(cap_threads)}. "
        f"The cap was lifted for a 23,400 pcs / 24 months sheet (run of {lifted}); the other agents never asked for 24 months",
        "one case; the lift by contract length is one run; the mock applies it to every capacity case (assumed) and lifts at >= 24 months",
        cap_option_index=1,
        lift_contract_months=24,
    )  # fmt: skip
    asked = []
    con = sqlite3.connect(f"file:{Path(data_dir) / 'world.sqlite'}?mode=ro", uri=True)
    for a, s_ in con.execute(
        "select asked_pct, settled_pct from negotiation_history where asked_pct is not null and settled_pct is not null"
    ):
        if a >= 1:
            asked.append(round(s_ / a, 3))
    P["history_settle_share_of_ask"] = param(
        "fitted", len(asked), "world.sqlite negotiation_history: settled_pct / asked_pct for past asks >= 1 % (share of a price increase the supplier kept)",
        "past real-world events of the fictional firm, not arena sessions; the arena's suppliers may differ; used as a cross-check of the floor, not in the mock",
        **spread(asked), q25=q(asked, 0.25), q75=q(asked, 0.75), share_settled_at_or_below_zero=round(sum(x <= 0 for x in asked) / len(asked), 3),
    )  # fmt: skip
    P["accept_tolerance"] = param(
        "assumed", 4, "four observations only BOUND it: agreed at an offer worth less than its ask in P03 (-1.1%: 438.21 at 90 vs at 30 days, with a 36-month contract) and P07 (-1%, payment days); refused P01 (-1.6%) and P05 70210 (30 vs 90 days)",
        "the value inside [0, 0.016) is assumed uniform; P03's acceptance may be paid for by the contract length, not by a tolerance", min=0.0, max=0.016,
    )  # fmt: skip
    P["answers_to_questions"] = param(
        "fitted", 3, "supplier questions in the dumps: 'Which volume can you commit to?' (P03,P08,P10, when we have a volume term), "
        "'Which figures is that based on / please send the data' (P01, after an unsupported claim of analysis); 'breakdown' requests answered by cost-breakdown.xlsx",
        "no dump shows a concession after we answer; the mock only asks and ignores the answer (assumed), cited facts that verify earn the first-reply bonus",
    )  # fmt: skip
    A = lambda n, ev, un, **v: param("assumed", 0, ev, un, **v)  # noqa: E731
    P["single_sample_halfwidth"] = A(
        0,
        "a case type with one sample draws its opening ratio and floor within +-0.03 of it",
        "no evidence; the width is a guess",
        value=0.03,
    )
    P["pass_through_jitter"] = A(
        0,
        "each supplier's pass-through is a fitted sample times U(0.85, 1.15), so seeds differ",
        "no evidence; a guess",
        low=0.85,
        high=1.15,
    )
    P["standard_terms_gaps"] = A(
        0,
        "standard lead time = the slowest option; standard ppm = 2.5 x the loosest option (P11: 6400 vs 2500); chargeback = first option",
        "lead time: P10 54 and P05 52 days sit near the slowest options; ppm: one sample",
        lead="slowest option",
        ppm_multiplier=2.5,
    )
    P["floor_cap"] = A(
        0,
        "the floor is at most 0.995 of the opening, so a supplier always has room to concede",
        "no evidence",
        value=0.995,
    )
    P["final_at_floor_margin"] = A(
        0, "a supplier whose ask is within 0.3% of its floor sends its final_offer", "no evidence", value=1.003
    )
    P["idle_threshold"] = A(
        0,
        "we moved when our best offer's value rose by more than 0.2% of the opening",
        "a threshold of the analysis, not a measurement",
        value=0.002,
    )
    P["volume_cap_applies_to"] = A(
        0,
        "the volume cap (P10) is drawn for every capacity case: a capacity case has the cap at its middle volume option",
        "one case; capacity cases of the hidden final may differ",
        probability=1.0,
    )
    P["overpay_agreed_at_buyer_price"] = A(
        0, "a sheet worth more than the ask is agreed as sent (term sheets bind)", "no dump shows it", value=True
    )
    P["contract_volume_levers_free"] = A(
        0,
        "contract length and volume change nothing in the supplier's cash value (cost.supplier_value), so they are accepted at the same price; P03 accepted 36 months, P10 lifted its cap for 24 months",
        "2 cases of evidence, no case where it refused",
        value=True,
    )
    return {
        "meta": {
            "source": f"sim_cases/real_runs ({n_dumps} dumps, 10 cases, {n_thread_runs} thread-runs, {n_threads} distinct supplier threads) + sim_cases/real + data package",
            "cases": sorted(by_case),
            "standard_days": {f"{c}|{s}": list(v) for (c, s), v in spd.items()},
            "c_open_check": c_open_check,
        },
        "parameters": P,
        "pass_through_rows": pass_rows,
        "opening_rows": opens,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default=str(Path.home() / "Documents/Codex/negotiation-arena-kit/data"))
    ap.add_argument("--out", default=str(HERE / "supplier_profile.json"))
    a = ap.parse_args(argv)
    out = fit(a.data)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for k, v in out["parameters"].items():
        print(f"{k:42} {v['status']:8} n={v['n']:<3}", {x: v[x] for x in ("min", "median", "max", "value") if x in v})


if __name__ == "__main__":
    main()
