"""Generate varied cases in the schema of the real case files (sim_cases/real) from real data rows.

    python -m arena_kit.gen_cases [--data <data package>] [--n 30] [--seed 1]

Writes sim_cases/gen_dev/ and sim_cases/gen_test/ (n cases each). Each case takes a real template of
its type (the structure: negotiable fields, options, must-have kinds, alternative kind) and moves it to
another supplier/part pair of the data package: the current price is the pair's latest price_conditions
row, the need comes from its purchase orders, refs are real IDs (contract, scorecard, quote, cost, doc).
The development and the held-out set use disjoint PARTS (World.split: bundling suppliers are alternated
first and bring their parts, the other parts alternate within their category), so tuning on dev never sees
a test part. They do NOT use disjoint suppliers: a supplier can sell several parts (see README). A
(parts, suppliers) combination is drawn at most twice per set. Reproducible: the same --seed gives the same files. Reads local files only.

What is varied is NOT all observed in the real cases: every real case has interest rate 0.08 and payment
reference 60 days, horizons are 1 and 2 years only; the generator varies them (assumed, see README):
interest 0.08 in 70 % of the cases, horizon 3 years in 10 %.
"""
# ruff: noqa: E501  (long text templates)

import argparse
import glob
import json
import random
import sqlite3
from collections import Counter
from pathlib import Path

from .cost import complete_offer, total_cost

HERE = Path(__file__).parent / "sim_cases"
DATA = Path.home() / "Documents/Codex/negotiation-arena-kit/data"
TYPES = ["price_increase", "renewal", "rfq", "bundling", "raw_material", "capacity", "quality"]
GOAL_TEXT = {
    "stabilise": "stabilise a strategic supply: a healthy supplier and stable prices count, not only the lowest price.",
    "routine": "routine: fewer suppliers and less process cost.",
    "leverage": "leverage: competition and data should bring the price down.",
    "secure_supply": "secure supply of a bottleneck part: coverage of the full need and a supplier that stays healthy come first.",
    "quality_first": "quality first: defects and late deliveries cost more than a few cents of price.",
}  # copied from the real briefings
NO_FALLBACK = "There is no fallback supplier: without a deal the demand is bought at the fallback price."
INTEREST = [0.04, 0.06, 0.10, 0.12] + [0.08] * 10  # real cases: 0.08 only; 30 % is a variation


class World:
    def __init__(self, data):
        self.con = sqlite3.connect(f"file:{Path(data) / 'world.sqlite'}?mode=ro", uri=True)
        self.con.row_factory = sqlite3.Row
        self.facts = json.loads((Path(data) / "facts.json").read_text(encoding="utf-8"))
        q = lambda sql: [dict(r) for r in self.con.execute(sql)]  # noqa: E731
        self.parts = {r["id"]: r for r in q("select * from parts")}
        self.sups = {r["id"]: r for r in q("select * from suppliers where detail = 'full'")}
        self.sourcing = [r for r in q("select * from sourcing") if r["supplier_id"] in self.sups]
        self.price = {}
        for r in q("select * from price_conditions order by valid_from"):
            self.price[(r["part_id"], r["supplier_id"])] = r["price"] / (r["price_unit"] or 1)
        self.qty = {}
        for r in q(
            "select part_id, supplier_id, sum(qty) n from po_lines where order_date >= '2025-10-01' group by 1, 2"
        ):
            self.qty[(r["part_id"], r["supplier_id"])] = r["n"]
        self.docs = {}
        for r in q("select * from documents order by date desc"):
            self.docs.setdefault(r["supplier_id"], []).append(r["id"])
        self.sc = {}
        for r in q("select * from scorecards order by quarter"):
            self.sc[r["supplier_id"]] = r
        self.ctr = {r["supplier_id"]: r for r in q("select * from contracts")}
        self.quotes = {}
        for r in q("select * from quotes"):
            self.quotes.setdefault(r["part_id"], []).append(r)
        self.cost = {r["part_id"]: r["id"] for r in q("select id, part_id from should_cost where id not like '%-%'")}
        self.drivers = {}
        for r in q("select * from cost_drivers order by weight desc"):
            self.drivers.setdefault(r["part_id"], []).append(r)
        self.asked = [r["asked_pct"] for r in q("select asked_pct from negotiation_history where asked_pct >= 1")]

    def split(self, real_pairs):
        """Dev/test split of the unused (part, supplier) pairs with a price and a purchase history. A part
        belongs to one set only. Suppliers that can bundle (>= 3 unused parts) are alternated first and bring
        their parts; the other parts alternate within their category, so every type has candidates in both."""
        free = sorted((r["part_id"], r["supplier_id"]) for r in self.sourcing
                      if (r["part_id"], r["supplier_id"]) in self.price and (r["part_id"], r["supplier_id"]) in self.qty
                      and (r["part_id"], r["supplier_id"]) not in real_pairs)  # fmt: skip
        by_sup = {}
        for p, s in free:
            by_sup.setdefault(s, []).append(p)
        which, order = {}, ("dev", "test")
        for i, s in enumerate(sorted(s for s, ps in by_sup.items() if len(ps) >= 3)):
            for p in by_sup[s]:
                which.setdefault(p, order[i % 2])
        seen = {}
        for p in sorted({p for p, _ in free}, key=lambda p: (self.parts[p]["category"], p)):
            if p not in which:
                c = self.parts[p]["category"]
                which[p], seen[c] = order[seen.get(c, 0) % 2], seen.get(c, 0) + 1
        self.free, self.which = free, which

    def pairs(self, which):
        return [(p, s) for p, s in self.free if self.which[p] == which]


def templates():
    out = {}
    for f in sorted(glob.glob(str(HERE / "real" / "*.json"))):
        c = json.load(open(f, encoding="utf-8"))
        if not c["buyer"].get("current_unit_price"):
            continue  # D02 has no current price: nothing to scale from
        out.setdefault(c["type"], []).append(c)
    return out


def fallback_ratios(tmpls):
    out = {}
    for cs in tmpls.values():
        for c in cs:
            b = c["buyer"]
            if b["fallback_unit_price"] != b["current_unit_price"]:
                out.setdefault(b["category_goal"], []).append(b["fallback_unit_price"] / b["current_unit_price"])
    return out


def r2(x):
    return round(x, 2)


def build(world, tmpls, ratios, which, idx, seed, typ=None):
    rng = random.Random(f"{seed}|{which}|{idx}")
    typ = typ or TYPES[idx % len(TYPES)]
    pairs = world.pairs(which)
    tmpl = rng.choice(tmpls[typ])
    t = json.loads(json.dumps(tmpl))
    b = t["buyer"]
    # -- which supplier/part ---------------------------------------------------------------------
    if typ == "bundling":
        by_sup = {}
        for p, s in pairs:
            by_sup.setdefault(s, []).append(p)
        sup = rng.choice(sorted(s for s, ps in by_sup.items() if len(ps) >= 3))
        parts, sups = sorted(by_sup[sup])[: rng.choice([3, 4])], [sup]
    elif typ == "rfq":
        by_part = {}
        for p, s in pairs:
            by_part.setdefault(p, []).append(s)
        part = rng.choice(sorted(p for p, ss in by_part.items() if len(ss) >= 2))
        parts, sups = [part], rng.sample(sorted(by_part[part]), min(len(by_part[part]), rng.choice([2, 3])))
    else:
        pool = [(p, s) for p, s in pairs if (world.parts[p]["category"] == "raw material") == (typ == "raw_material")]
        if typ in ("raw_material", "price_increase", "renewal") and "index_clause" in t["negotiable"]:
            pool = [(p, s) for p, s in pool if world.drivers.get(p)]
        part, sup = rng.choice(sorted(pool))
        parts, sups = [part], [sup]
    first = sups[0]
    cur = r2(
        sum(world.price[(p, first)] if (p, first) in world.price else world.parts[p]["standard_price"] for p in parts)
    )
    # -- numbers ---------------------------------------------------------------------------------
    need0 = min(world.qty.get((p, first), 1000) for p in parts) if len(parts) > 1 else world.qty[(parts[0], first)]
    need = int(round(need0 * rng.uniform(0.7, 1.4), -1)) or 1
    horizon = rng.choices([1, 2, 3], [45, 45, 10])[0]  # real: 1 and 2 years; 3 is a rare variation
    goal = b["category_goal"] if rng.random() < 0.75 else rng.choice(sorted(GOAL_TEXT))
    donors = [c for cs in tmpls.values() for c in cs if c["buyer"]["category_goal"] == goal]
    donor = rng.choice(donors)["buyer"]
    dspend = donor["need_per_year"] * donor["current_unit_price"]
    spend_k = need * cur / (b["need_per_year"] * b["current_unit_price"])
    price_k = cur / b["current_unit_price"]
    vol_k = need / b["need_per_year"]
    jitter = lambda: rng.uniform(0.8, 1.25)  # noqa: E731
    fb = (
        cur
        if b["fallback_unit_price"] == b["current_unit_price"]
        else r2(cur * rng.uniform(min(ratios[goal]), max(ratios[goal])))
    )
    lead_plan = world.parts[parts[0]]["planned_lead_time_days"]
    tl = tmpl["fixed_terms"].get("lead_time_days") or tmpl["term_options"].get("lead_time_days", [lead_plan])[0]
    lead_k = lead_plan / (tl or lead_plan)
    b.update(
        need_per_year=need, horizon_years=float(horizon) if isinstance(b["horizon_years"], float) else horizon,
        current_unit_price=cur, fallback_unit_price=fb, interest_rate=rng.choice(INTEREST), category_goal=goal,
        fallback_risk_pct=donor["fallback_risk_pct"], need_lead_time_days=max(1, round(b["need_lead_time_days"] * lead_k)),
        late_cost_per_day=int(round(b["late_cost_per_day"] * spend_k * jitter(), -1)) or 10,
        cost_per_defect=int(round(b["cost_per_defect"] * price_k * jitter())),
        freight_eur_per_unit={k: r2(v * price_k * jitter()) for k, v in b["freight_eur_per_unit"].items()},
    )  # fmt: skip
    for k in ("index_risk_pct", "sustainable_margin_pct"):
        b.pop(k, None)
        if k in donor:
            b[k] = donor[k]
    b.pop("relationship_eur_per_point", None)
    if "relationship_eur_per_point" in donor:
        b["relationship_eur_per_point"] = int(round(donor["relationship_eur_per_point"] * need * cur / dspend, -1))
    # -- term structure --------------------------------------------------------------------------
    fx, opt = t["fixed_terms"], t["term_options"]
    if "volume_per_year" in fx:
        fx["volume_per_year"] = need
    if "volume_per_year" in opt:
        opt["volume_per_year"] = [int(round(v * vol_k)) for v in opt["volume_per_year"]]
    if "contract_months" in fx and fx["contract_months"] == 12 * tmpl["buyer"]["horizon_years"]:
        fx["contract_months"] = 12 * horizon
    if "lead_time_days" in fx:
        fx["lead_time_days"] = lead_plan
    if "lead_time_days" in opt:
        opt["lead_time_days"] = sorted({max(1, round(v * lead_k)) for v in opt["lead_time_days"]})
    if "tooling_eur" in opt:
        opt["tooling_eur"] = [int(round(v * spend_k, -2)) for v in opt["tooling_eur"]]
    if "chargeback_eur_per_complaint" in opt:
        opt["chargeback_eur_per_complaint"] = [
            int(round(v * price_k * jitter(), -1)) for v in opt["chargeback_eur_per_complaint"]
        ]
    if "index_clause" in opt:
        drv = world.drivers[parts[0]][0]
        opt["index_clause"] = [
            None if o is None else {**o, "series": drv["series_id"], "material_share": drv["weight"]}
            for o in opt["index_clause"]
        ]
        b["index_paths"] = {drv["series_id"]: round(rng.uniform(0.02, 0.08), 2)}
    elif b["index_paths"]:
        b["index_paths"] = {}
    # must-haves: a field we can negotiate, feasible with its options
    b["must_haves"] = []
    cands = []
    if opt.get("lead_time_days"):
        cands.append(
            {
                "field": "lead_time_days",
                "op": "<=",
                "value": opt["lead_time_days"][min(2, len(opt["lead_time_days"]) - 1)],
            }
        )
    if opt.get("volume_per_year"):
        cands.append({"field": "volume_per_year", "op": ">=", "value": int(round(0.95 * need))})
    if opt.get("ppm_commitment"):
        cands.append({"field": "ppm_commitment", "op": "<=", "value": opt["ppm_commitment"][2]})
    if cands and (tmpl["buyer"]["must_haves"] or rng.random() < 0.3):
        b["must_haves"] = [rng.choice(cands)]
    # alternative: real quote of the same part from another supplier, or today's terms, or none
    # the kinds a real case of this type has (a current_contract alternative at today's price would make
    # walking away the best move in a price_increase or a renewal)
    kinds = sorted({c["buyer"]["alternative"]["kind"] for c in tmpls[typ]})
    if rng.random() < 0.7:
        kinds = [tmpl["buyer"]["alternative"]["kind"]]
    kind = rng.choice(kinds)
    rows = [
        q
        for q in world.quotes.get(parts[0], [])
        if q["supplier_id"] not in sups and cur * 0.97 <= q["unit_price"] / (q["price_unit"] or 1) <= cur * 1.4
    ]
    if kind == "quote" and not rows or len(parts) > 1 and kind == "quote":
        kind = (
            "current_contract"
            if "current_contract" in {c["buyer"]["alternative"]["kind"] for c in tmpls[typ]}
            else "none"
        )
    std = {"payment_days": b["reference_payment_days"], "lead_time_days": lead_plan, "volume_per_year": need,
           "contract_months": 12 * horizon, "effective_date": (opt.get("effective_date") or [fx.get("effective_date")])[0],
           "index_clause": None, "incoterm": fx.get("incoterm", "DAP"), "tooling_eur": 0}  # fmt: skip
    if kind == "quote":
        q = rng.choice(rows)
        ppm = world.sc.get(q["supplier_id"], {}).get("ppm")
        alt = {"kind": "quote", "ref": q["id"], "terms": {**std, "unit_price": r2(q["unit_price"] / (q["price_unit"] or 1)), "payment_days": q["payment_days"],
               "lead_time_days": q["lead_time_days"], "incoterm": q["incoterm"], "tooling_eur": q["tooling_eur"] or 0, **({"ppm_commitment": ppm} if ppm is not None else {})}}  # fmt: skip
    elif kind == "current_contract":
        c = world.ctr[first]
        ppm = world.sc.get(first, {}).get("ppm")
        alt = {"kind": "current_contract", "ref": c["id"], "terms": {**std, "unit_price": cur, "payment_days": c["payment_days"], "incoterm": c["incoterm"],
               **({"ppm_commitment": ppm} if ppm is not None else {})}}  # fmt: skip
    else:
        alt = {"kind": "none", "ref": None, "terms": {}}
    b["alternative"] = alt
    # -- text and refs ---------------------------------------------------------------------------
    names = [world.sups[s]["name"] for s in sups]
    desc = world.parts[parts[0]]["description"]
    pct = rng.choice(world.asked)
    title = {"price_increase": f"{names[0].split()[0]} announces +{pct} % on {desc}",
             "renewal": f"Contract renewal for {desc}", "rfq": f"RFQ: {desc}", "bundling": f"Bundle {len(parts)} items with one supplier",
             "raw_material": f"Base price and surcharge for {desc}", "capacity": f"{names[0].split()[0]} cuts the allocation for {desc}",
             "quality": f"{names[0].split()[0]}: quality problems with {desc}"}[typ]  # fmt: skip
    kit = "kits" if typ == "bundling" else world.parts[parts[0]]["uom"]
    fallback = {
        "quote": f"the second-source quote {alt['ref']}",
        "current_contract": "today's terms continue unchanged",
    }.get(kind)
    brief = (
        f"You negotiate for Hollerau Pumpenwerke with {', '.join(names)}. {title}. Need: {need} {kit} a year. Category goal: {GOAL_TEXT[goal]} "
        f"Score: the lowest total cost C as defined in the rules, valued with this case's rates (need lead time {b['need_lead_time_days']} days). "
        + (f"Fallback if you walk away: {fallback}. " if fallback else NO_FALLBACK + " ")
        + "Must-haves: "
        + (", ".join(f"{m['field']} {m['op']} {m['value']}" for m in b["must_haves"]) or "none")
        + ". Prepare from the data package."
    )  # fmt: skip
    doc = (world.docs.get(first) or [None])[0]
    refs = [r for r in [doc, world.ctr[first]["id"], *[f"sc:{s.split(':')[1]}@{world.sc[s]['quarter']}" for s in sups if s in world.sc],
                        alt["ref"] if kind == "quote" else None, world.cost.get(parts[0])] if r]  # fmt: skip
    t.update(
        case_id=f"case:G{which[0].upper()}{idx + 1:02d}", set="practice", type=typ, title=title, briefing=brief, trigger_doc=doc,
        parts=[f"{p}" for p in parts], suppliers=sups, fixed_terms=fx, term_options=opt, refs=list(dict.fromkeys(refs)), hosted=True,
    )  # fmt: skip
    return t


def validate(case, world):
    """The checks the simulator and the cost code rely on; returns a list of problems."""
    bad = []
    real = next(c for cs in templates().values() for c in cs if "hosted" in c)
    if set(case) != set(real):
        bad.append(f"keys differ from the real schema: {set(case) ^ set(real)}")
    b = case["buyer"]
    if "unit_price" not in case["negotiable"]:
        bad.append("no unit_price in negotiable")
    for r in [*case["refs"], case["trigger_doc"]]:
        if r and r not in world.facts:
            bad.append(f"unknown ref {r}")
    try:
        offer = complete_offer(case, {"unit_price": b["current_unit_price"]})
        if not total_cost(case, offer) > 0:
            bad.append("total_cost not positive")
        if b["alternative"]["terms"].get("unit_price") and not total_cost(case, b["alternative"]["terms"]) > 0:
            bad.append("alternative cost not positive")
        for m in b["must_haves"]:
            opts = case["term_options"].get(m["field"]) or []
            if not any(m["op"] == "<=" and v <= m["value"] or m["op"] == ">=" and v >= m["value"] for v in opts):
                bad.append(f"must-have {m} cannot be met with the options")
        from .sim_real import SimReal  # the real-like supplier must leave room to negotiate: C_open > C_best

        for seed in range(3):
            sim = SimReal({case["case_id"]: case}, no_clock=True, seed=seed)
            sim.open("k", case["case_id"])
            c_open, c_best = sim._bounds(case, next(iter(sim.sessions.values()))["threads"])
            alt = case["buyer"]["alternative"]["terms"]
            if alt.get("unit_price") and c_best >= 0.995 * total_cost(case, alt):
                bad.append("the alternative beats every deal: walking away would score 1")
                break
            if c_open - c_best < 0.005 * c_open:
                bad.append(f"no room to negotiate with seed {seed}: C_open {c_open}, C_best {c_best}")
                break
    except Exception as e:  # any failure of the cost code is a problem with the case
        bad.append(f"cost code failed: {e!r}")
    return bad


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", default=str(DATA))
    ap.add_argument("--n", type=int, default=30, help="cases per set")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=str(HERE))
    a = ap.parse_args(argv)
    world, tmpls = World(a.data), templates()
    world.split({(p, s) for cs in tmpls.values() for c in cs for p in c["parts"] for s in c["suppliers"]})
    ratios = fallback_ratios(tmpls)
    for which in ("dev", "test"):
        folder = Path(a.out) / f"gen_{which}"
        folder.mkdir(parents=True, exist_ok=True)
        for old in folder.glob("*.json"):
            old.unlink()
        used = Counter()
        for i in range(a.n):
            for k in range(len(TYPES)):  # the next type when this one has no free combination left (few bundlers)
                typ = TYPES[(i + k) % len(TYPES)]
                for attempt in range(60):  # a draw that fails the checks, or repeats a combination twice, is redrawn
                    case = build(world, tmpls, ratios, which, i, f"{a.seed}.{attempt}", typ)
                    key = (tuple(case["parts"]), tuple(case["suppliers"]))
                    if used[key] < 2 and not validate(case, world):
                        break
                else:
                    continue
                used[key] += 1
                break
            else:
                raise SystemExit(f"{which} {i}: no valid draw of any type")
            (folder / f"{case['case_id'][5:]}.json").write_text(
                json.dumps(case, indent=1, ensure_ascii=False), encoding="utf-8"
            )
        pairs = {(p, s) for k in used for p in k[0] for s in k[1]}
        print(
            f"{folder}: {a.n} cases, {len(used)} distinct (parts, suppliers) combinations, {len(pairs)} supplier/part pairs"
        )


if __name__ == "__main__":
    main()
