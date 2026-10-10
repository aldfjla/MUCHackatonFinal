"""Evidence layer: candidate claims for a case, computed ONLY from the data package and shaped for the
arena's claim checker (api.md, "What counts"): each claim is one sentence with one figure that ends with
its IDs. `check_claim` recomputes the figure from the raw tables with the arena's tolerance rules.

build_claims(case, package, supplier=None, price=None) -> [{kind, ids, sentence, strength, figure, ...}],
strongest first. `price`: the supplier's standing unit price (default: the price asked in its letter, else
our current price) - quotes and should-cost only count as leverage against it. A claim with no ids (kind
"calc") is a computed figure, not a checked claim.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path

log = logging.getLogger("arena")

DEFAULT_DATA = "~/Documents/Codex/negotiation-arena-kit/data"
GREEN = 85.0  # scorecard on-time-delivery green line, %


@lru_cache(maxsize=4)
def _open(path):
    from .data import DataPackage

    return DataPackage(path)


def load_package(path=None):
    """The data package at `path`, else ARENA_DATA, else the default folder - or None (logged once)."""
    path = Path(path or os.environ.get("ARENA_DATA") or DEFAULT_DATA).expanduser()
    try:
        return _open(str(path))
    except Exception as e:
        _missing(f"{path}: {e}")


def package_problem(path=None):
    """Why the evidence layer cannot cite data from this package, or None when it can. Checked at startup:
    a package without its SQLite file silently drops every citation (all 10 v4-petra runs, 2026-10-10)."""
    pkg = load_package(path)
    if pkg is None:
        return f"no data package at {Path(path or os.environ.get('ARENA_DATA') or DEFAULT_DATA).expanduser()}"
    if pkg.db is None:
        return f"data package at {pkg.root} has no world.sqlite"
    return None


@lru_cache(maxsize=None)
def _missing(why):  # lru_cache: logs once per reason
    log.warning("evidence: no data package (%s) - messages stay as the delegate wrote them", why)


def _q(pkg, sql, *params):
    return pkg.query(sql, params, limit=100000)


def _mi(month):
    return int(month[:4]) * 12 + int(month[5:7]) - 1


def _month(index):
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _tol_ok(figure, value, pct):
    """The arena's tolerance: +-0.5 percentage points for a %, else +-0.5 % of the value (at least 0.01)."""
    return abs(figure - value) <= (0.5 if pct else max(0.01, 0.005 * abs(value))) + 1e-9


def _data_end(pkg):
    return _mi(_q(pkg, "select max(last_month) m from index_series")[0]["m"])


def _name(pkg, series):
    n = _q(pkg, "select name from index_series where id=?", series)[0]["name"]
    return n.split(" (")[0].split(", seasonally")[0]


def _change(pkg, series, start, end):
    v = {r["month"]: r["value"] for r in _q(pkg, "select month, value from index_values where series_id=? and month in (?,?)", series, start, end)}
    return (v[end] / v[start] - 1) * 100 if start in v and end in v and v[start] else None


def _drivers(pkg, parts):
    """[(series, weight, change %, start, end)]: cost drivers of the parts over the 12 months to the series' last month."""
    out, seen = [], set()
    for part in parts:
        for r in _q(pkg, "select d.series_id s, d.weight w, i.last_month e from cost_drivers d join index_series i on i.id=d.series_id where d.part_id=?", part):
            start = _month(_mi(r["e"]) - 12)
            chg = _change(pkg, r["s"], start, r["e"])
            if chg is not None and r["s"] not in seen and _mi(r["e"]) >= _data_end(pkg) - 11:
                seen.add(r["s"])
                out.append((r["s"], r["w"], chg, start, r["e"]))
    return out


def _per(pkg, part):
    """'per unit', or 'per 100 units' when the part is priced per 100."""
    pu = _q(pkg, "select price_unit from parts where id=?", part)[0]["price_unit"]
    return "per unit" if pu == 1 else f"per {pu:g} units"


def _of(parts, part):
    """How a sentence names the part: 'this part', or its id when the case has several."""
    return f"part {part}" if len(parts) > 1 else "this part"


def _case_docs(case):
    return [r for r in [case.get("trigger_doc"), *case.get("refs", [])] if r and r.startswith("doc:")]


def build_claims(case, package, supplier=None, price=None):
    pkg, parts = package, case.get("parts", [])
    supplier = supplier or case["suppliers"][0]
    sid = supplier.split(":")[-1]
    docs = [d for r in dict.fromkeys(_case_docs(case)) for d in _q(pkg, "select * from documents where id=? and supplier_id=?", r, supplier)]
    ask = next((d["asked_pct"] for d in docs if d["asked_pct"] is not None), None)
    ref = price or next((d["asked_price"] for d in docs if d["asked_price"]), None) or case["buyer"]["current_unit_price"]
    out = []

    def add(kind, ids, sentence, strength, figure=None, **extra):
        out.append({"kind": kind, "ids": ids, "sentence": sentence, "strength": strength, "figure": figure,
                    "part": parts[0] if parts else None, "supplier": supplier, **extra})

    # (a) index: cost drivers that fell or rose little undercut a cost story; the weighted figure is a calculation
    drivers = _drivers(pkg, parts)
    limit = ask if ask is not None else 3.0
    for s, w, chg, start, end in sorted(drivers, key=lambda d: d[2])[:2]:
        if chg < limit:
            add("idx", [f"idx:{s}@{start}", f"idx:{s}@{end}"],
                f"{_name(pkg, s)} changed {chg:+.1f}% from {start} to {end} (idx:{s}@{start}, idx:{s}@{end}).",
                60 + min(limit - chg, 30) + (10 if chg < 0 else 0), chg)
    n_all = sum(len(_q(pkg, "select 1 from cost_drivers where part_id=?", p)) for p in parts)
    if drivers and ask is not None and len(drivers) == n_all:  # skip when a driver was dropped (missing months)
        total, share = sum(w * chg for _, w, chg, _, _ in drivers), sum(w for _, w, _, _, _ in drivers) * 100
        if total < ask:
            add("calc", [], f"The cost drivers we track (about {share:.0f}% of the cost of {'this part' if len(parts) == 1 else 'these parts'}) moved {total:+.1f}% weighted over the last twelve months, against the {ask:.1f}% you ask.",
                75, total, parts=parts)
    # (b) a cheaper quote of this case (citing it reveals it to this supplier)
    qrefs = [r for r in case.get("refs", []) if r.startswith("quote:")] + [case["buyer"].get("alternative", {}).get("ref")]
    for r in dict.fromkeys(x for x in qrefs if x):
        for row in _q(pkg, "select * from quotes where id=?", r):
            if row["part_id"] in parts and row["currency"] == "EUR" and row["supplier_id"] != supplier and row["unit_price"] < ref:
                add("quote", [r], f"We hold another quote for {_of(parts, row['part_id'])} at EUR {row['unit_price']:.2f} {_per(pkg, row['part_id'])} ({r}).",
                    80 + (ref - row["unit_price"]) / ref * 100, row["unit_price"], part=row["part_id"])
    # (c) our scorecard of this supplier
    sc = _q(pkg, "select * from scorecards where supplier_id=? order by quarter desc limit 4", supplier)
    if sc and case.get("type") == "quality" and sc[0]["ppm"] > 0:
        add("sc", [sc[0]["id"]], f"Your defect rate was {sc[0]['ppm']} ppm in {sc[0]['quarter']} ({sc[0]['id']}).", 70, sc[0]["ppm"], metric="ppm")
    elif sc:
        mean, weighted = sum(r["otd_pct"] for r in sc) / len(sc), sum(r["otd_pct"] * r["gr_lines"] for r in sc) / max(1, sum(r["gr_lines"] for r in sc))
        rows = sc if abs(mean - weighted) <= 0.3 and mean < GREEN else sc[:1]
        value = sum(r["otd_pct"] for r in rows) / len(rows)
        if value < GREEN:
            add("sc", [r["id"] for r in rows], f"Your on-time delivery averaged {value:.1f}% {f'over the last {len(rows)} quarters' if len(rows) > 1 else 'in the latest quarter'} ({', '.join(r['id'] for r in rows)}).",
                40 + (GREEN - value) * 3, value, metric="otd_pct")
    # (d) price history: the latest run of orders at one price
    for part in parts:
        po = _q(pkg, "select id, price, order_date from po_lines where supplier_id=? and part_id=? order by order_date desc, id desc limit 8", supplier, part)
        run = [r for i, r in enumerate(po) if all(x["price"] == po[0]["price"] for x in po[: i + 1])][:3]
        # only a price history that undercuts the supplier's current price, from the last 24 months
        if len(run) >= 2 and po[0]["price"] < ref and po[0]["order_date"] >= _month(_data_end(pkg) - 24):
            ids = [r["id"] for r in run]
            add("po", ids, f"We placed our last {len(ids)} orders for {_of(parts, part)} at EUR {po[0]['price']:.2f} {_per(pkg, part)} ({', '.join(ids)}).", 30, po[0]["price"], part=part)
            break
    # (e) forecast change, should-cost, news about this supplier
    for r in case.get("refs", []):
        fact = pkg.facts.get(r) or {}
        if r.startswith("fc:") and fact.get("part") in parts and fact["change_pct"] > 0:
            add("fc", [r], f"Our forecast for {_of(parts, fact['part'])} shows a recorded change of {fact['change_pct']:+.1f}% ({r}).", 45, fact["change_pct"], part=fact["part"])
    costs = _q(pkg, "select * from should_cost where supplier_id=? or supplier_id is null order by supplier_id is null", supplier)
    for part in parts:  # the supplier-specific estimate if there is one, else the generic one
        row = next((r for r in costs if r["part_id"] == part), None)
        if row and row["unit_cost"] < ref:
            add("cost", [row["id"]], f"Our should-cost estimate for {_of(parts, part)} is EUR {row['unit_cost']:.2f} {_per(pkg, part)}, before any margin ({row['id']}).",
                50 + (ref - row["unit_cost"]) / ref * 100, row["unit_cost"], part=part)
    for row in _q(pkg, "select * from news where supplier_id=? and topic != 'noise' and date >= ?", supplier, _month(_data_end(pkg) - 12)):
        add("news", [row["id"]], f'We noted the report "{row["headline"]}" ({row["id"]}).', 25)
    # (f) the letter gives less notice than the contract requires
    if case.get("type") == "price_increase":
        for d in docs:
            c = next(iter(_q(pkg, "select * from contracts where supplier_id=? and valid_from<=? and valid_to>=?", supplier, d["date"], d["date"])), None)
            if c and d["notice_days"] and c["notice_days"] and d["notice_days"] < c["notice_days"]:
                add("doc", [d["id"], c["id"]], f"Your letter gives {d['notice_days']} days of notice for the price change, which falls short of the notice period in our contract ({d['id']}, {c['id']}).",
                    85, d["notice_days"])
                break
    return sorted(out, key=lambda c: -c["strength"])


def check_claim(claim, package):
    """True if the claim's figure matches the raw tables the way the arena checks it (see api.md)."""
    pkg, ids, fig, kind = package, claim["ids"], claim["figure"], claim["kind"]
    try:
        if kind == "calc":
            return _tol_ok(fig, sum(w * c for _, w, c, _, _ in _drivers(pkg, claim["parts"])), True)
        if kind == "idx":
            (s1, m1), (s2, m2) = (i[4:].split("@") for i in ids)
            end = _q(pkg, "select last_month from index_series where id=?", s1)[0]["last_month"]
            ok = s1 == s2 and 0 < _mi(m2) - _mi(m1) <= 12 and _mi(m2) <= _mi(end) and _mi(m2) >= _data_end(pkg) - 11
            return ok and _tol_ok(fig, _change(pkg, s1, m1, m2), True)
        if kind == "quote":
            r = _q(pkg, "select * from quotes where id=?", ids[0])[0]
            return r["part_id"] == claim["part"] and r["currency"] == "EUR" and _tol_ok(fig, r["unit_price"], False)
        if kind == "sc":
            rows = [_q(pkg, "select * from scorecards where id=?", i)[0] for i in ids]
            return all(r["supplier_id"] == claim["supplier"] for r in rows) and _tol_ok(fig, sum(r[claim["metric"]] for r in rows) / len(rows), False if claim["metric"] == "ppm" else True)
        if kind == "po":
            rows = [_q(pkg, "select * from po_lines where id=?", i)[0] for i in ids]
            return 2 <= len(rows) <= 8 and all(r["part_id"] == claim["part"] and _tol_ok(fig, r["price"], False) for r in rows)
        if kind == "fc":
            f = pkg.facts[ids[0]]
            return bool(_q(pkg, "select 1 from forecasts where id=?", ids[0])) and f["part"] == claim["part"] and _tol_ok(fig, f["change_pct"], True)
        if kind == "cost":
            r = _q(pkg, "select * from should_cost where id=?", ids[0])[0]
            return r["part_id"] == claim["part"] and _tol_ok(fig, r["unit_cost"], False)
        if kind == "news":
            return _q(pkg, "select supplier_id from news where id=?", ids[0])[0]["supplier_id"] == claim["supplier"]
        if kind == "doc":
            d, c = _q(pkg, "select * from documents where id=?", ids[0])[0], _q(pkg, "select * from contracts where id=?", ids[1])[0]
            return (d["supplier_id"] == c["supplier_id"] == claim["supplier"] and d["notice_days"] == fig < c["notice_days"]
                    and c["valid_from"] <= d["date"] <= c["valid_to"])
    except (IndexError, KeyError, TypeError, ValueError):
        return False
    return False
