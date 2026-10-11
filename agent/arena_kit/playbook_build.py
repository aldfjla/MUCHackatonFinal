"""Build playbook.json: what the real practice runs taught us per (supplier, case type, goal).

    python -m arena_kit.playbook_build

Reads sim_cases/real_runs*/*.json (session dumps) and sim_cases/targets.md (C_best target deals). Local files only.
backlog.csv is not read: it has no term sheets or supplier threads, the dumps hold the same deals in full.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
CASES = HERE / "sim_cases"
OUT = HERE / "playbook.json"


def _num(s):
    s = (s or "").strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def parse_targets(text):
    """({case: {...target fields}}, {(case, sid): price of the C-minimising health floor})."""
    targets, cmin, case, sid = {}, {}, None, None
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if re.match(r"\| P\d+ \|", line) and len(cells) >= 9:
            targets[cells[0]] = {"c_best": _num(cells[4]), "price_on_supplier_terms": _num(cells[6]),
                                 "price_with_best_levers": _num(cells[7]), "levers": cells[8]}
        elif m := re.match(r"### (P\d+)", line):
            case = m.group(1)
        elif m := re.match(r"- (sup:\d+):", line):
            sid = m.group(1)
        elif m := re.search(r"health floor on supplier terms: min C [\d,]+ at P=([\d.]+)", line):
            cmin[(case, sid)] = float(m.group(1))
    return targets, cmin


def _price(m):
    ps = [s["terms"]["unit_price"] for s in m.get("term_sheets") or [] if s["terms"].get("unit_price") is not None]
    return min(ps) if ps else None


def build(cases_dir=CASES):
    targets, cmin = parse_targets((cases_dir / "targets.md").read_text(encoding="utf-8"))
    acc = defaultdict(lambda: {"deals": [], "offers": [], "final_rounds": [], "repeats": 0, "replies": 0, "cases": set(), "runs": 0})
    for f in sorted(cases_dir.glob("real_runs*/*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        case = json.loads((cases_dir / "real" / f"{d['case']}.json").read_text(encoding="utf-8"))
        res = d.get("result") or {}
        for sid, th in (d.get("threads") or {}).items():
            a = acc[(sid, case["type"], case["buyer"]["category_goal"])]
            a["cases"].add(d["case"])
            a["runs"] += 1
            sent, prev = 0, None
            for m in th.get("messages", []):
                if m.get("from") == "buyer":
                    sent += 1
                    continue
                p = _price(m)
                if p is None:
                    continue
                a["offers"].append(p)
                a["replies"] += 1
                a["repeats"] += p == prev
                prev = p
                if m.get("status") == "final_offer":
                    a["final_rounds"].append(sent)
            if res.get("deal") and res.get("supplier_id") == sid and (res.get("score") or 0) > 0:
                a["deals"].append({"c_deal": res["c_deal"], "score": round(res["score"], 3), "price": res["terms"]["unit_price"],
                                   "terms": res["terms"], "from": f"{f.parent.name}/{f.name}"})
    out = {}
    for (sid, typ, goal), a in sorted(acc.items()):
        if not a["offers"]:
            continue
        best = min(a["deals"], key=lambda x: x["c_deal"]) if a["deals"] else None
        case = sorted(a["cases"])[0]
        e = {"case_ids": sorted(a["cases"]), "runs": a["runs"], "lowest_offered_price": min(a["offers"]),
             "first_final_offer_round": min(a["final_rounds"]) if a["final_rounds"] else None,
             "replies": a["replies"], "replies_repeating_price": a["repeats"], "best_deal": best,
             "target": targets.get(case)}
        if (case, sid) in cmin:
            e["c_min_price"] = cmin[(case, sid)]
        out.setdefault(sid, {})[f"{typ}/{goal}"] = e
    return out


if __name__ == "__main__":
    pb = build()
    OUT.write_text(json.dumps(pb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{OUT}: {sum(len(v) for v in pb.values())} entries, {len(pb)} suppliers")
