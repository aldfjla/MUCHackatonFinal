"""BetterAgent: SimplifyAgent plus switchable additions (each a small method, off by its class constant).

0. GUARD_C_OPEN + HEALTH_ESTIMATE. In a strategic / bottleneck case C charges for the supplier's margin below
   `sustainable_margin_pct`; `total_cost` without a supplier estimate sees 0 (real P02 v17: 140k health cost, c_deal >
   c_open, score 0). The estimate here: full cost = the data package's should-cost for the part (within 1-2% of the
   arena's own fitted value on P01/P02/P03), interest rate = the buyer's. It is set through cost.HEALTH for the whole
   decision, so price choice, caps, closing rule and stall jump all see the health term; a sheet is never priced
   below the price that minimises estimated C; a sheet or accept above c_open gets its price raised until it fits.
1. THIRD_SHEET: a third equivalent sheet (shorter payment or another contract length, price lowered to equal C).
2. ANCHOR_BY_SHARE: first offer = max(floor, price x (1 - share x index drop)) where the case data show a drop.
3. CASH_SHORT: a cash-short supplier gets shorter payment days against a lower price.
4. LATE_ACCEPT: with <= 2 messages left, accept a standing sheet within 1% of the best known C.
5. HOLD_FOR_FINAL: no accept while the supplier's latest message is a plain "open" offer with >= HOLD_MESSAGES
   messages left, unless it repeated its price (its floor): we keep countering until it sends final_offer.
Rival-quote citation (RESEARCH rule 12) is not here: EvidenceAgent._rewrite already cites the best real rival offer ID."""

import math
import re
from contextlib import contextmanager
from contextvars import ContextVar

from ..cost import HEALTH, complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..evidence import _q, load_package
from ..guard import satisfy_must_haves
from ..play import find_sheet, latest, moves_left, standing
from . import simplify_agent
from .reciprocal import ANCHOR_FLOOR, _c_alt, _live, _mine, _pinned, _sheets, _sup
from .simplify_agent import FREE_LEVERS, SimplifyAgent, _health_at_stake

CASH_SHORT = re.compile(r"liquidity|working[- ]capital|cash[- ]?flow|short of cash|cash[- ]?(?:tight|short|constrain|crunch)", re.I)

HOLD = ContextVar("hold", default=None)  # set while BetterAgent decides: (case, threads, decision) -> True to veto a close


def _gate(real):
    """simplify's decide() starts with the closing rule; this lets BetterAgent veto it (only inside its own decide)."""
    def closing_accept(case, threads, *a, **k):
        r = real(case, threads, *a, **k)
        hold = HOLD.get()
        return None if r and hold and hold(case, threads, r) else r
    return closing_accept


simplify_agent.closing_accept = _gate(simplify_agent.closing_accept)


def _health(case):
    """{full_cost, interest_rate} of the supplier for cost.HEALTH, or None (no relationship cost / no should-cost row)."""
    if not _health_at_stake(case) or not (pkg := load_package()):
        return None
    try:
        rows = _q(pkg, "select supplier_id, unit_cost, price_unit from should_cost where part_id=?", case["parts"][0])
    except Exception:
        return None
    # the row for one of this case's suppliers, else the generic one (shortcut: a multi-supplier case uses the first match)
    row = next((r for r in sorted(rows, key=lambda r: r["supplier_id"] not in case.get("suppliers", []))), None)
    return {"full_cost": row["unit_cost"] / (row["price_unit"] or 1), "interest_rate": case["buyer"]["interest_rate"]} if row else None


@contextmanager
def _with_health(case, on=True):
    token = HEALTH.set(_health(case) if on else None)
    try:
        yield
    finally:
        HEALTH.reset(token)


def _holds(case, threads, decision):
    """True: do not close on this thread yet (plain open offer, messages to spare, price still moving)."""
    ev = threads[decision["supplier_id"]]
    ps = [min(s["terms"]["unit_price"] for s in m["term_sheets"] if s["terms"].get("unit_price") is not None)
          for m in _sup(ev) if any(s["terms"].get("unit_price") is not None for s in m["term_sheets"])]
    repeated = len(ps) >= 2 and ps[-1] == ps[-2]
    return latest(ev).get("status") == "open" and moves_left(case, ev) >= BetterAgent.HOLD_MESSAGES and not repeated


class HealthScope:
    """Outermost wrapper: the health estimate and the hold rule apply to the WHOLE delegate chain (the guard's
    closing_move and accept checks too), not only to BetterAgent.decide."""

    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        if name == "delegate":
            raise AttributeError(name)
        return getattr(self.delegate, name)

    def decide(self, case, threads):
        token = HOLD.set(_holds if BetterAgent.HOLD_FOR_FINAL else None)
        try:
            with _with_health(case, BetterAgent.HEALTH_ESTIMATE):
                return self.delegate.decide(case, threads)
        finally:
            HOLD.reset(token)


class BetterAgent(SimplifyAgent):
    GUARD_C_OPEN = THIRD_SHEET = ANCHOR_BY_SHARE = CASH_SHORT_OFFER = LATE_ACCEPT = HEALTH_ESTIMATE = HOLD_FOR_FINAL = True
    LATE_MESSAGES, LATE_TOLERANCE, HOLD_MESSAGES = 2, 0.01, 3

    def decide(self, case, threads):
        token = HOLD.set(_holds if self.HOLD_FOR_FINAL else None)
        try:
            with _with_health(case, self.HEALTH_ESTIMATE):
                if self.LATE_ACCEPT and (late := self._late_accept(case, threads)):
                    return self._guard(case, threads, late)
                return self._guard(case, threads, super().decide(case, threads))
        finally:
            HOLD.reset(token)

    # 0. never offer or accept above c_open ------------------------------------------------------------------
    @staticmethod
    def _est_c(case, events, t, std):
        """C of a sheet, with the supplier's margin priced when the case charges for it."""
        with _with_health(case):
            return total_cost(case, t, std)

    def _open_c(self, case, threads):
        out = math.inf
        for ev in threads.values():
            std = standard_terms(ev)
            for m in _sup(ev):
                if m.get("term_sheets"):
                    for s in m["term_sheets"]:
                        t = s.get("terms") or {}
                        if t.get("unit_price") is not None and must_haves_ok(case, t, std):
                            out = min(out, self._est_c(case, ev, t, std))
                    break
        return out

    def _repair(self, case, events, std, t, c_open, top):
        """The sheet with the lowest price >= its own at which C <= c_open (up to `top`), else None."""
        if self._est_c(case, events, t, std) <= c_open:
            return t
        lo = t["unit_price"]
        for i in range(1, 101):
            v = {**t, "unit_price": round(lo + (top - lo) * i / 100, 2)}
            if self._est_c(case, events, v, std) <= c_open:
                return v
        return None

    def _guard(self, case, threads, d):
        if not self.GUARD_C_OPEN:
            return d
        sid, msg = d.get("supplier_id"), d.get("message") or {}
        ev = threads.get(sid)
        if not ev:
            return d
        std, c_open = standard_terms(ev), self._open_c(case, threads)
        act = msg.get("action") or {}
        if act.get("type") == "walk_away":
            return self._not_walk(case, ev, sid, std, c_open) or d
        if act.get("type") == "accept":
            theirs = find_sheet(ev, act.get("term_sheet_id"))
            if theirs is None or self._est_c(case, ev, theirs, std) <= c_open:
                return d
            base = {k: std[k] for k in case["negotiable"] if k in std}
            sheets = [complete_offer(case, {**base, **theirs})]
        elif msg.get("term_sheets"):
            sheets = [s["terms"] for s in msg["term_sheets"]]
        else:
            return d
        first = next((m["term_sheets"][0]["terms"]["unit_price"] for m in _sup(ev) if m.get("term_sheets")), 0)
        fixed = [r for t in sheets if (r := self._repair(case, ev, std, t, c_open, max(first, t["unit_price"])))]
        if fixed == sheets:
            return d
        body = {"subject": case.get("title", "Our proposal"), "body": "Thank you for your offer. Please see our updated terms."}
        return {"supplier_id": sid, "message": {**body, "term_sheets": [{"terms": t} for t in fixed]} if fixed else
                {"subject": body["subject"], "body": "Could you please send us your best terms?"}}

    def _not_walk(self, case, ev, sid, std, c_open):
        """Instead of a walk: a counter at the supplier's own terms, priced at the lowest-C price in [its ask, its
        opening] with C <= c_open (a price above the health floor can beat the opening); None if there is none."""
        sheet_id, t = standing(ev)
        if not sheet_id or t.get("unit_price") is None or moves_left(case, ev) < 1:
            return None
        ask = t["unit_price"]
        top = max(ask, next((m["term_sheets"][0]["terms"]["unit_price"] for m in _sup(ev) if m.get("term_sheets")), ask))
        grid = [round(ask + (top - ask) * i / 100, 2) for i in range(101)]
        # their terms, or the same without an index clause (a clause they attach can cost more than the price gap)
        variants = [t, {**t, "index_clause": None}] if t.get("index_clause") and "index_clause" in case["negotiable"] else [t]
        v = min(({**u, "unit_price": x} for u in variants for x in grid), key=lambda v: self._est_c(case, ev, v, std))
        if self._est_c(case, ev, v, std) > c_open:
            return None
        sheet = complete_offer(case, satisfy_must_haves(case, v, std))
        return {"supplier_id": sid, "message": {"subject": case.get("title", "Our proposal"),
                                                "body": "Thank you for your offer. Please see our final terms.", "term_sheets": [{"terms": sheet}]}}

    # 6. late accept ----------------------------------------------------------------------------------------
    def _late_accept(self, case, threads):
        c_alt, c_open = _c_alt(case), self._open_c(case, threads)
        known, cand = math.inf, None
        for sid in _live(threads):
            ev, std = threads[sid], standard_terms(threads[sid])
            for s in _sheets(ev):
                if (t := s.get("terms") or {}).get("unit_price") is not None and must_haves_ok(case, t, std):
                    known = min(known, self._est_c(case, ev, t, std))
            sheet_id, t = standing(ev)
            if sheet_id and moves_left(case, ev) <= self.LATE_MESSAGES and t.get("unit_price") is not None and must_haves_ok(case, t, std):
                c = self._est_c(case, ev, t, std)
                if c < c_alt and c <= c_open:
                    cand = min(cand or (c, sid, sheet_id), (c, sid, sheet_id))
        if cand and cand[0] <= (1 + self.LATE_TOLERANCE) * known:
            return {"supplier_id": cand[1], "message": {"action": {"type": "accept", "term_sheet_id": cand[2]}}}
        return None

    # 3. cost-share anchor -----------------------------------------------------------------------------------
    @staticmethod
    def _share_factor(case):
        """1 - share x drop for the best index driver the case shows falling (index_paths < 0), else None."""
        paths = case["buyer"].get("index_paths") or {}
        hits = [c["material_share"] * -paths[c["series"]] for c in (case.get("term_options") or {}).get("index_clause", [])
                if c and paths.get(c["series"], 0) < 0]
        return 1 - max(hits) if hits else None

    def _price(self, case, events, p):
        if self.ANCHOR_BY_SHARE and not _mine(events) and not _health_at_stake(case) and (f := self._share_factor(case)):
            return max(ANCHOR_FLOOR * p, min(f * p, case["buyer"].get("current_unit_price") or p))
        return super()._price(case, events, p)

    # 2 + 5. third equivalent sheet / cash-short -------------------------------------------------------------
    @staticmethod
    def _cash_short(case, events):
        text = " ".join([*(m.get("body") or "" for m in _sup(events)), str(case.get("suppliers", ""))])
        return bool(CASH_SHORT.search(text))

    def _trade_sheet(self, case, events, std, main, p, pins, seen):
        """Same C as main with another lever: shorter payment days (or another contract length) for a lower price."""
        short = self.CASH_SHORT_OFFER and self._cash_short(case, events)
        levers = ("payment_days",) if short else ("payment_days", "contract_months") if self.THIRD_SHEET else ()
        opts, best = case.get("term_options") or {}, None
        cost = lambda t: total_cost(case, t, std)  # noqa: E731
        for f in levers:
            if f not in case["negotiable"] or f in pins or (_health_at_stake(case) and f not in FREE_LEVERS):
                continue
            for o in (o for o in opts.get(f, []) if o and o != main.get(f) and (f != "payment_days" or o < main[f])):
                t = satisfy_must_haves(case, {**main, f: o}, std)
                slope = cost({**t, "unit_price": t["unit_price"] + 1}) - cost(t)
                if t.get(f) != o or slope <= 0:
                    continue
                price = round(min(p, t["unit_price"] - (cost(t) - cost(main)) / slope - 0.01), 2)
                v = {**t, "unit_price": price}
                if price > 0.75 * p and v not in seen and v != main and (best is None or price > best["unit_price"]):
                    best = v
            if best:
                break
        return best

    def _sheets(self, case, events, std, theirs):
        out = super()._sheets(case, events, std, theirs)
        if out and HEALTH.get():  # never below the price that minimises C: under it the health term grows faster than the saving
            seen = [s["terms"] for m in _mine(events) for s in m.get("term_sheets") or []]
            fixed = []
            for t in out:
                grid = [round(t["unit_price"] + (theirs["unit_price"] - t["unit_price"]) * i / 100, 2) for i in range(101)]
                t = complete_offer(case, {**t, "unit_price": min(grid, key=lambda x: total_cost(case, {**t, "unit_price": x}, std))})
                if t not in fixed and t not in seen:
                    fixed.append(t)
            out = fixed
        if out and (self.THIRD_SHEET or self.CASH_SHORT_OFFER):
            seen = [s["terms"] for m in _mine(events) for s in m.get("term_sheets") or []]
            if extra := self._trade_sheet(case, events, std, out[0], theirs["unit_price"], _pinned(events), seen):
                if (extra := complete_offer(case, extra)) not in out:
                    out.append(extra)
        return out
