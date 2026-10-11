"""BetterAgent: SimplifyAgent plus switchable additions (each a small method, off by its class constant).

0. GUARD_C_OPEN + HEALTH_ESTIMATE. In a strategic / bottleneck case C charges for the supplier's margin below
   `sustainable_margin_pct`; `total_cost` without a supplier estimate sees 0 (real P02 v17: 140k health cost, c_deal >
   c_open, score 0). The estimate here comes from the data package only: full cost = the should-cost row of the
   part (the supplier's own row, else the generic one), as a BAND (BAND_SPECIFIC / BAND_GENERIC, wider for a supplier
   whose credit index fell or equity is thin); interest rate = the buyer's. It is set through cost.HEALTH for the whole
   decision, so price choice, caps, closing rule and stall jump all see the health term; prices minimise the C expected
   over the band; no offer or accept may exceed c_open at the band's pessimistic end; an accept must also be the best
   complete package (against the alternative and the standing sheets of the other threads).
1. THIRD_SHEET: a third equivalent sheet (shorter payment or another contract length, price lowered to equal C).
2. ANCHOR_BY_SHARE: first offer = max(floor, price x (1 - share x index drop)) where the case data show a drop.
3. CASH_SHORT: a cash-short supplier gets shorter payment days against a lower price.
4. LATE_ACCEPT: with <= 2 messages left, accept a standing sheet within 1% of the best known C.
5. FIXED_TWIN / INDEX_PREMIUM: a message carrying an index-clause sheet also carries the same terms without the clause at a C no worse
   than the clause sheet's; the clause sheet's price is then at least the index risk premium below the fixed price
   (see _index_premium), so index risk is only taken when paid for.
6. HOLD_FOR_FINAL: no accept while the supplier's latest message is a plain "open" offer with >= HOLD_MESSAGES
   messages left, unless it repeated its price (its floor): we keep countering until it sends final_offer.
Rival-quote citation (RESEARCH rule 12) is not here: EvidenceAgent._rewrite already cites the best real rival offer ID."""

import math
import re
import statistics
from contextlib import contextmanager
from contextvars import ContextVar

from ..cost import HEALTH, complete_offer, cost_breakdown, must_haves_ok, total_cost
from ..docs import standard_terms
from ..evidence import DISTRESS, _q, load_package
from ..guard import satisfy_must_haves
from ..play import find_sheet, latest, moves_left, standing
from . import simplify_agent
from .reciprocal import ANCHOR_FLOOR, FRAC0, FRAC_MAX, FRAC_STEP, KEEP, MIN_STEP, MOVING_MIN, _c_alt, _live, _mine, _pinned, _sheets, _sup, _tick
from .simplify_agent import FREE_LEVERS, SimplifyAgent, _health_at_stake

CASH_SHORT = re.compile(r"liquidity|working[- ]capital|cash[- ]?flow|short of cash|cash[- ]?(?:tight|short|constrain|crunch)", re.I)

HOLD = ContextVar("hold", default=None)  # set while BetterAgent decides: (case, threads, decision) -> True to veto a close (see _vetoes)


def _gate(real):
    """simplify's decide() starts with the closing rule; this lets BetterAgent veto it (only inside its own decide)."""
    def closing_accept(case, threads, *a, **k):
        r = real(case, threads, *a, **k)
        hold = HOLD.get()
        return None if r and hold and hold(case, threads, r) else r
    return closing_accept


simplify_agent.closing_accept = _gate(simplify_agent.closing_accept)


BAND_SPECIFIC = 0.03  # +-3% around the should-cost: the row is a bottom-up estimate of this supplier's plant
BAND_GENERIC = 0.08  # +-8% when only the generic (German cost base) row exists: another plant, another cost base
BAND_WEAK = 0.02  # extra width for a supplier with a falling credit index or equity below WEAK_EQUITY: its real cost is less certain
WEAK_EQUITY = 20.0  # equity ratio, %


def _health(case, distress=False, scale=1.0):
    """{full_cost, interest_rate, band: (lo, hi) multipliers of full_cost} of the supplier for cost.HEALTH, or None
    (no relationship cost / no should-cost row). Only the data package and the case are used."""
    if not _health_at_stake(case) or not (pkg := load_package()):
        return None
    try:
        rows = _q(pkg, "select supplier_id, unit_cost, price_unit from should_cost where part_id=?", case["parts"][0])
    except Exception:
        return None
    suppliers = case.get("suppliers", [])
    own = [r for r in rows if r["supplier_id"] in suppliers]
    row = next(iter(own or [r for r in rows if not r["supplier_id"]] or rows), None)  # own row, else the generic one, else any
    if not row:
        return None
    width = (BAND_SPECIFIC if own else BAND_GENERIC) if BetterAgent.BAND else 0.0  # BAND off: the centre estimate only
    sup, weak = row["supplier_id"] or (suppliers or [None])[0], False
    try:
        intel = _q(pkg, "select equity_ratio_pct, credit_index, credit_index_12m_ago from supplier_intel where supplier_id=?", sup)
        weak = bool(intel and ((intel[0]["credit_index"] or 0) < (intel[0]["credit_index_12m_ago"] or 0) or (100 if intel[0]["equity_ratio_pct"] is None else intel[0]["equity_ratio_pct"]) < WEAK_EQUITY))
    except Exception:
        pass
    try:  # RELEASE_DISTRESS: Sunday release news (insolvency, withdrawn credit cover) counts like a falling credit index
        weak = weak or bool(distress) and any(n.get("supplier_id") in {sup, *suppliers} and n.get("topic") in DISTRESS for n in pkg.release_rows("news"))
    except Exception:
        pass
    if weak:
        width += BAND_WEAK * (width > 0)
    return {"full_cost": row["unit_cost"] / (row["price_unit"] or 1), "interest_rate": case["buyer"]["interest_rate"], "band": (1 - width, 1 + width), "scale": scale}


@contextmanager
def _with_health(case, on=True, distress=False, scale=1.0):
    token = HEALTH.set(_health(case, distress, scale) if on else None)
    try:
        yield
    finally:
        HEALTH.reset(token)


@contextmanager
def _ensure_health(case):
    """The ambient estimate, or this case's own when none is set."""
    if HEALTH.get() is None:
        with _with_health(case):
            yield
    else:
        yield


@contextmanager
def _scaled(k):
    """The estimate's full cost x k (k = 1: unchanged)."""
    est = HEALTH.get()
    token = HEALTH.set({**est, "full_cost": est["full_cost"] * k}) if est and k != 1 else None
    try:
        yield
    finally:
        if token:
            HEALTH.reset(token)


def _c_at(case, t, std, k=None):
    """C with the supplier's full cost x k; default k = the band's pessimistic end (C rises with the full cost)."""
    est = HEALTH.get() or {}
    with _scaled(est.get("band", (1, 1))[1] if k is None else k):
        return total_cost(case, t, std)


def _exp_c(case, t, std):
    """C expected over the band (lower end, estimate, upper end equally weighted): what prices are chosen by."""
    lo, hi = (HEALTH.get() or {}).get("band", (1, 1))
    return sum(_c_at(case, t, std, k) for k in (lo, 1, hi)) / 3


def _num(x):
    return None if x is None or x == math.inf else round(x, 2)


def _sheet_of(ev, d):
    """The terms a decision accepts or offers first, else None."""
    msg = d.get("message") or {}
    if (act := msg.get("action") or {}).get("type") == "accept":
        return find_sheet(ev, act.get("term_sheet_id"))
    return msg["term_sheets"][0]["terms"] if msg.get("term_sheets") else None


def _best_standing(case, threads, skip=None, k=None):
    """(C at the pessimistic end (k: another multiple of the full cost), sid, sheet_id) of the best valid sheet of the newest message of another live thread."""
    best = None
    for sid in _live(threads):
        if sid != skip:
            ev, std = threads[sid], standard_terms(threads[sid])
            for s in _sheets(ev):
                t = s.get("terms") or {}
                if s.get("term_sheet_id") and t.get("unit_price") is not None and must_haves_ok(case, t, std):
                    best = min(best or (math.inf, sid, None), (BetterAgent._est_c(case, ev, t, std, k), sid, s["term_sheet_id"]))
    return best


def _why(case, threads, d, rule):
    """Plain-dict log of a decision: the complete-package C (pessimistic end of the band) against c_open and the alternative."""
    out = {"rule": rule, "supplier_id": d.get("supplier_id")}
    try:
        ev = threads.get(d.get("supplier_id"))
        with _ensure_health(case):
            est = HEALTH.get()
            out["c_open"] = _num(BetterAgent()._open_c(case, threads))
            out["band"] = [round(est["full_cost"] * k, 2) for k in est["band"]] if est else None
            out["alternative"] = {"c_alt": _num(_c_alt(case)), "best_other_thread": (lambda b: _num(b[0]) if b else None)(_best_standing(case, threads, d.get("supplier_id")))}
            t = _sheet_of(ev, d) if ev else None
            out["c_offer"], out["c_breakdown"] = None, None
            if t and t.get("unit_price") is not None:
                std = standard_terms(ev)
                out["c_offer"] = _num(BetterAgent._est_c(case, ev, t, std))
                b = BetterAgent()  # C of the offer minus c_open, in each world of the band (negative: a saving there)
                out["vs_open"] = {w: _num(b._est_c(case, ev, t, std, k) - b._open_c(case, threads, k)) for w, k in zip(("lo", "mid", "hi"), (est["band"][0], 1, est["band"][1]) if est else (1, 1, 1))}
                with _scaled((est or {}).get("band", (1, 1))[1]):
                    out["c_breakdown"] = {k: round(v, 2) for k, v in cost_breakdown(case, t, std).items()}
                out["concession"] = _concession(case, ev, t, std)
    except Exception as e:  # a log line must never break a decision
        out["error"] = repr(e)
    return out


def _concession(case, ev, t, std):
    """Plain dict of this move: round, our previous / new first-sheet price and step, the supplier's previous / new price and
    step, the levers (fields) that changed against our previous sheet, and the package C (centre world) before / after."""
    first = lambda m: m["term_sheets"][0]["terms"]  # noqa: E731
    mine, theirs = [m for m in _mine(ev) if m.get("term_sheets")], [m for m in _sup(ev) if m.get("term_sheets")]
    prev = first(mine[-1]) if mine else None
    sp = [first(m).get("unit_price") for m in theirs]
    step = lambda a, b: None if a is None or b is None else round(b - a, 2)  # noqa: E731
    return {"round": len(mine) + 1,
            "ours": {"prev": prev and prev.get("unit_price"), "new": t["unit_price"], "step": step(prev and prev.get("unit_price"), t["unit_price"])},
            "supplier": {"prev": sp[-2] if len(sp) > 1 else None, "new": sp[-1] if sp else None, "step": step(sp[-2], sp[-1]) if len(sp) > 1 else None},
            "levers_changed": sorted(k for k in {*t, *(prev or {})} if k != "unit_price" and t.get(k) != (prev or {}).get(k)) if prev else [],
            "c_before": prev and prev.get("unit_price") is not None and _num(BetterAgent._est_c(case, ev, prev, std, 1)) or None,
            "c_after": _num(BetterAgent._est_c(case, ev, t, std, 1))}


def _accept_ok(case, threads, sid, t):
    """May we accept `t`, the standing sheet of thread `sid`? In every world k of the band (lower end, centre, upper end: C is
    piecewise linear in k, so the ends suffice; an accept priced above the opening has a less sensitive health term, so the
    worst case can be the lower end) its C is within c_open and below the alternative, and no other thread's standing sheet
    is cheaper there. On a final_offer or our last message the centre world alone is enough: never walk when accepting is
    no worse than c_open."""
    ev, std, b = threads[sid], standard_terms(threads[sid]), BetterAgent()
    lo, hi = (HEALTH.get() or {}).get("band", (1, 1))

    def ok(k):
        c, other = b._est_c(case, ev, t, std, k), _best_standing(case, threads, sid, k)
        with _scaled(k):
            c_alt = _c_alt(case)  # the alternative in the same world as the offer
        return c <= b._open_c(case, threads, k) and c < c_alt and not (other and other[0] < c - 0.005)

    final = latest(ev).get("status") == "final_offer" or moves_left(case, ev) <= 1
    return ok(1) if final else all(ok(k) for k in dict.fromkeys((lo, 1, hi)))


def _vetoes(case, threads, r):
    """True: do not close with this decision (closing rule, inside BetterAgent / HealthScope only): the hold rule, or the
    sheet is not an acceptable best complete package (_accept_ok)."""
    if BetterAgent.HOLD_FOR_FINAL and _holds(case, threads, r):
        return True
    if not BetterAgent.GUARD_C_OPEN or not (t := _sheet_of(threads[r["supplier_id"]], r)):
        return False
    return not _accept_ok(case, threads, r["supplier_id"], t)


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
        token = HOLD.set(_vetoes)
        try:
            with _with_health(case, BetterAgent.HEALTH_ESTIMATE, getattr(self.delegate, "RELEASE_DISTRESS", False), getattr(self.delegate, "HEALTH_SCALE", 1.0)):
                d = self.delegate.decide(case, threads)
                if isinstance(d, dict) and d.get("message"):  # the wrappers inside may have changed the message: log the final one
                    d = {**d, "why": _why(case, threads, d, (d.get("why") or {}).get("rule") or "wrapper")}
                return d
        finally:
            HOLD.reset(token)


class BetterAgent(SimplifyAgent):
    RELEASE_DISTRESS = False  # True: Sunday-release distress news widens the health band (set on the instance, per chain)
    HEALTH_SCALE = 1.0  # x the relationship term of C (arena charged 3-22x less than our estimate: P01 3.7k vs 12.5k, P02 18.9k vs 51.4k, P03 1.0k vs 21.1k)
    BAND = True  # False: the centre estimate only (no uncertainty band)
    # both OFF: the arena's C prices the clause through a single index path, so a risk premium is not rewarded in score; the twin alone was not better (train 0.505 vs 0.509)
    FIXED_TWIN = INDEX_PREMIUM = False  # twin: a no-clause sheet beside each clause sheet; premium: clause price below the twin's by the index risk premium
    GUARD_C_OPEN = THIRD_SHEET = ANCHOR_BY_SHARE = CASH_SHORT_OFFER = LATE_ACCEPT = HEALTH_ESTIMATE = True
    HOLD_FOR_FINAL = False  # dead on the real bots: final_offer comes at a fixed message whatever we do
    LATE_MESSAGES, LATE_TOLERANCE, HOLD_MESSAGES = 2, 0.01, 3
    # PAY_MIRROR (opt-in, `better_pay`): real runs show suppliers lift their whole price ladder 1-3% when we ask for 90 days (P08: 5.40 at 30d
    # unasked vs 5.63/5.69 after asking; P07: 5.35 at 30d vs 5.48 at 60d) while C values 30 extra days at only 0.3-0.6%: without health at stake, mirror their opening term
    PAY_MIRROR = False
    IDX_SHEET_ALWAYS = True  # the health branch always adds the index-clause sheet; v32: real P02 3/3 0.30 vs 0.67 without it: the clause buys the price (off: `better_noidx`)
    # DATE_LEVER (default on; real P01 3/3 runs 0.88 vs 0.69 with the lever off, v29 - niko; off: `better_nodate`): in price-increase cases effective_date is negotiable and C charges the old price until it, so a later date lowers C
    # directly (P01/P13); `better` only adopts a later date when the supplier volunteers one (P01: 1 of 6 runs, 0.84 vs 0.69)
    DATE_LEVER = True
    IDX_SHEET_FIRST = False  # non-health cases send no index-clause sheet in the first message (real P08 3/3 0.54/0.56/0.55 vs 0.53, P18 identical 0.51, v34; Petra's combined does the same; on: `better_idx1`)
    LEAD_LEVER = False  # health cases: pick the plain-C-minimising lead_time_days (simplify's loop skips it there); v32: real P10 3/3 0.65 vs 0.67: asking 35 days hardened the supplier (on: `better_lead`)
    MATCH_FACTOR = 1.0  # our step answers their last move in full (simplify: 0.25): the bot's last concession scales with our last step

    def decide(self, case, threads):
        token = HOLD.set(_vetoes)
        try:
            with _with_health(case, self.HEALTH_ESTIMATE, self.RELEASE_DISTRESS, self.HEALTH_SCALE):
                if self.LATE_ACCEPT and (late := self._late_accept(case, threads)):
                    d, rule = self._guard(case, threads, late), "late_accept"
                else:
                    d = super().decide(case, threads)
                    rule = {"accept": "accept", "walk_away": "walk_away"}.get(((d.get("message") or {}).get("action") or {}).get("type"), "counter")
                    d = self._guard(case, threads, d)
                if self.FIXED_TWIN or self.INDEX_PREMIUM:
                    d = self._with_fixed_price(case, threads, d)
                return {**d, "why": _why(case, threads, d, (d.get("why") or {}).get("rule") or rule)}
        finally:
            HOLD.reset(token)

    # 7. fixed-price alternative beside every clause sheet ----------------------------------------------------
    @staticmethod
    def _index_premium(case, clause, price, months):
        """Per-unit risk premium of an index clause, or None without index history:
        price x material_share x (max(0, mu x H) + sigma x sqrt(H)), mu / sigma = mean / stdev of the series' monthly log
        returns in the data package, H = contract months (the drift we expect to pay plus one standard deviation of it)."""
        if not (pkg := load_package()):
            return None
        try:
            v = [r["value"] for r in _q(pkg, "select value from index_values where series_id=? order by month", clause["series"]) if r["value"]]
        except Exception:
            return None
        if len(v) < 4:
            return None
        r = [math.log(b / a) for a, b in zip(v, v[1:])]
        return price * clause["material_share"] * (max(0.0, statistics.mean(r) * months) + statistics.stdev(r) * math.sqrt(months))

    @staticmethod
    def _max_price(ok, hi):
        """The largest price in (0, hi] (to the cent, bisection: C rises with the price) with ok(price), else None."""
        if ok(hi):
            return hi
        lo = 0.01
        if not ok(lo):
            return None
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if ok(mid) else (lo, mid)
        return math.floor(lo * 100) / 100

    def _with_fixed_price(self, case, threads, d):
        """Every clause sheet of the message gets a no-clause sheet beside it (see FIXED_TWIN); at most 3 sheets."""
        msg, ev = d.get("message") or {}, threads.get(d.get("supplier_id"))
        sheets = msg.get("term_sheets") or []
        if not ev or not any(s["terms"].get("index_clause") for s in sheets):
            return d
        std, out, fixed_twins = standard_terms(ev), [], []
        c, fits = (lambda t: _exp_c(case, t, std)), self._fits(case, threads)
        ask = standing(ev)[1].get("unit_price") if standing(ev)[0] else None
        for s in sheets:
            t = s["terms"]
            if not t.get("index_clause"):
                out.append(s)
                continue
            fixed = next((o["terms"] for o in sheets if not o["terms"].get("index_clause") and c(o["terms"]) <= c(t)), None)
            if fixed is None:  # same terms, no clause, the highest price at no more than the clause sheet's C (never above their ask)
                f = self._max_price(lambda x: c(complete_offer(case, {**t, "index_clause": None, "unit_price": x})) <= c(t), max(t["unit_price"], ask or 0))
                fixed = f and complete_offer(case, {**t, "index_clause": None, "unit_price": f})
            if not fixed:
                continue  # no fixed alternative at that C: do not offer the clause
            prem = self._index_premium(case, t["index_clause"], fixed["unit_price"], t.get("contract_months") or case["buyer"]["horizon_years"] * 12)
            if not self.INDEX_PREMIUM:
                p = t["unit_price"]
            elif prem is None:  # no history: the clause sheet must be at least as good as the fixed one in expected C
                p = self._max_price(lambda x: c({**t, "unit_price": x}) <= c(fixed), t["unit_price"])
            else:
                p = math.floor(min(t["unit_price"], fixed["unit_price"] - prem) * 100) / 100
            fixed_twins.append(fixed)
            if self.FIXED_TWIN and fixed not in [o["terms"] for o in out]:
                out.append({"terms": fixed})
            if p and p > 0 and fits(ev, {**t, "unit_price": p}, std):  # a lower price can raise C (health term): then no clause sheet
                out.append({**s, "terms": {**t, "unit_price": p}})
        out = [s for i, s in enumerate(out) if s["terms"] not in [o["terms"] for o in out[:i]]]
        head = [s for s in out if s["terms"].get("index_clause") or s["terms"] in fixed_twins]  # a clause sheet and its twin never get cut
        out = (head + [s for s in out if s not in head])[:3]
        return {**d, "message": {**msg, "term_sheets": out}}

    # 0. never offer or accept above c_open ------------------------------------------------------------------
    @staticmethod
    def _est_c(case, events, t, std, k=None):
        """C of a sheet at the pessimistic end of the band (k: another multiple of the full cost), with the supplier's margin priced when the case charges for it."""
        with _ensure_health(case):
            return _c_at(case, t, std, k)

    def _open_c(self, case, threads, k=None):
        out = math.inf
        for ev in threads.values():
            std = standard_terms(ev)
            for m in _sup(ev):
                if m.get("term_sheets"):
                    for s in m["term_sheets"]:
                        t = s.get("terms") or {}
                        if t.get("unit_price") is not None and must_haves_ok(case, t, std):
                            out = min(out, self._est_c(case, ev, t, std, k))  # c_open in the same world as the offer it is compared with
                    break
        return out

    def _fits(self, case, threads, cap=math.inf):
        """fits(events, t, std): our own offer t is no worse than the opening package in the centre AND the optimistic world
        (it may lose in the pessimistic one - that world is a hard rule for accepts only, see _accept_ok) and at the centre costs <= cap."""
        lo = (HEALTH.get() or {}).get("band", (1, 1))[0]
        opens = {k: self._open_c(case, threads, k) for k in dict.fromkeys((lo, 1))}
        return lambda ev, t, std: all(self._est_c(case, ev, t, std, k) <= c for k, c in opens.items()) and self._est_c(case, ev, t, std, 1) <= cap

    def _repair(self, case, events, std, t, fits, top):
        """The sheet with the lowest price >= its own that `fits` (up to `top`), else None."""
        if fits(events, t, std):
            return t
        lo = t["unit_price"]
        for i in range(1, 101):
            v = {**t, "unit_price": round(lo + (top - lo) * i / 100, 2)}
            if fits(events, v, std):
                return v
        return None

    def _guard(self, case, threads, d):
        if not self.GUARD_C_OPEN:
            return d
        sid, msg = d.get("supplier_id"), d.get("message") or {}
        ev = threads.get(sid)
        if not ev:
            return d
        std, fits = standard_terms(ev), self._fits(case, threads)
        act = msg.get("action") or {}
        accepting = act.get("type") == "accept"
        if act.get("type") == "walk_away":
            return self._not_walk(case, ev, sid, std, fits) or d
        if accepting:
            theirs = find_sheet(ev, act.get("term_sheet_id"))
            if theirs is None or _accept_ok(case, threads, sid, theirs):
                return d
            other = _best_standing(case, threads, sid)  # the best complete package wins, whatever the thread
            if other and _accept_ok(case, threads, other[1], find_sheet(threads[other[1]], other[2])):
                return {"supplier_id": other[1], "message": {"action": {"type": "accept", "term_sheet_id": other[2]}}, "why": {"rule": "accept_best_package"}}
            fits = self._fits(case, threads, _c_alt(case) - 0.01)  # the counter must also beat the alternative
            base = {k: std[k] for k in case["negotiable"] if k in std}
            sheets = [complete_offer(case, {**base, **theirs})]
        elif msg.get("term_sheets"):
            sheets = [s["terms"] for s in msg["term_sheets"]]
        else:
            return d
        first = next((m["term_sheets"][0]["terms"]["unit_price"] for m in _sup(ev) if m.get("term_sheets")), 0)
        fixed = [r for t in sheets if (r := self._repair(case, ev, std, t, fits, max(first, t["unit_price"])))]
        if fixed == sheets and not accepting:
            return d
        if not fixed and (counter := self._not_walk(case, ev, sid, std, fits)):  # no sheet fits: their own terms at the best fitting price
            return counter
        body = {"subject": case.get("title", "Our proposal"), "body": "Thank you for your offer. Please see our updated terms."}
        return {"supplier_id": sid, "message": {**body, "term_sheets": [{"terms": t} for t in fixed]} if fixed else
                {"subject": body["subject"], "body": "Could you please send us your best terms?"}, "why": {"rule": "guard_repair"}}

    def _not_walk(self, case, ev, sid, std, fits):
        """Instead of a walk: a counter at the supplier's own terms, priced at the lowest expected-C price in [its ask, its
        opening] that `fits` (a price above the health floor can beat the opening); None if there is none."""
        sheet_id, t = standing(ev)
        if not sheet_id or t.get("unit_price") is None or moves_left(case, ev) < 1:
            return None
        ask = t["unit_price"]
        top = max(ask, next((m["term_sheets"][0]["terms"]["unit_price"] for m in _sup(ev) if m.get("term_sheets")), ask))
        grid = [round(ask + (top - ask) * i / 100, 2) for i in range(101)]
        # their terms, or the same without an index clause (a clause they attach can cost more than the price gap)
        variants = [t, {**t, "index_clause": None}] if t.get("index_clause") and "index_clause" in case["negotiable"] else [t]
        safe = [v for u in variants for x in grid if fits(ev, v := {**u, "unit_price": x}, std)]
        if not safe:
            return None
        v = min(safe, key=lambda v: _exp_c(case, v, std))  # of those, the lowest expected C
        sheet = complete_offer(case, satisfy_must_haves(case, v, std))
        return {"supplier_id": sid, "message": {"subject": case.get("title", "Our proposal"),
                                                "body": "Thank you for your offer. Please see our final terms.", "term_sheets": [{"terms": sheet}]}, "why": {"rule": "not_walk"}}

    # 6. late accept ----------------------------------------------------------------------------------------
    def _late_accept(self, case, threads):
        c_alt = _c_alt(case)
        known, cand = math.inf, None
        for sid in _live(threads):
            ev, std = threads[sid], standard_terms(threads[sid])
            for s in _sheets(ev):
                if (t := s.get("terms") or {}).get("unit_price") is not None and must_haves_ok(case, t, std):
                    known = min(known, self._est_c(case, ev, t, std))
            sheet_id, t = standing(ev)
            if sheet_id and moves_left(case, ev) <= self.LATE_MESSAGES and t.get("unit_price") is not None and must_haves_ok(case, t, std):
                c = self._est_c(case, ev, t, std)
                if c < c_alt and _accept_ok(case, threads, sid, t):
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
        mine = [m["term_sheets"][0]["terms"]["unit_price"] for m in _mine(events) if m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")]
        if not mine:
            return super()._price(case, events, p)
        frac = min(FRAC_MAX, FRAC0 + FRAC_STEP * len(mine))
        move = self._their_move(events)
        step = max(frac * (p - mine[-1]), MIN_STEP * p, _tick(p))
        if move > 0:
            step = max(MOVING_MIN * p, _tick(p), min(step, self.MATCH_FACTOR * move))
        top = p if moves_left(case, events) <= 2 else p * (1 - KEEP)
        return min(p, max(mine[-1], min(top, mine[-1] + step)))  # never above their standing price

    # 2 + 5. third equivalent sheet / cash-short -------------------------------------------------------------
    @staticmethod
    def _cash_short(case, events):
        text = " ".join([*(m.get("body") or "" for m in _sup(events)), str(case.get("suppliers", ""))])
        return bool(CASH_SHORT.search(text))

    def _mirror(self, case, events):
        """The supplier's opening payment_days when PAY_MIRROR applies to this case, else None."""
        if not self.PAY_MIRROR or _health_at_stake(case) or "payment_days" not in case["negotiable"]:
            return None
        first = next((m["term_sheets"][0] for m in _sup(events) if m.get("term_sheets")), None)  # their FIRST sheet only
        return ((first or {}).get("terms") or {}).get("payment_days")

    def _trade_sheet(self, case, events, std, main, p, pins, seen):
        """Same C as main with another lever: shorter payment days (or another contract length) for a lower price."""
        short = self.CASH_SHORT_OFFER and self._cash_short(case, events)
        levers = ("payment_days",) if short else ("payment_days", "contract_months") if self.THIRD_SHEET else ()
        opts, best = case.get("term_options") or {}, None
        cost = lambda t: total_cost(case, t, std)  # noqa: E731
        for f in levers:
            if f not in case["negotiable"] or f in pins or (f == "payment_days" and self._mirror(case, events) is not None) or (_health_at_stake(case) and f not in FREE_LEVERS):
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
        if out and HEALTH.get():  # health cases: payment days as a lever, never below the C-minimising price, an index-clause sheet
            seen = [s["terms"] for m in _mine(events) for s in m.get("term_sheets") or []]
            opts, pins, p = case.get("term_options") or {}, _pinned(events), theirs["unit_price"]

            def best(t):  # t at the price in [its price, theirs] that minimises C
                grid = [round(t["unit_price"] + (p - t["unit_price"]) * i / 100, 2) for i in range(101)]
                return min(({**t, "unit_price": x} for x in grid), key=lambda v: _exp_c(case, v, std))

            pay = [o for o in opts.get("payment_days", []) if o] if "payment_days" in case["negotiable"] and "payment_days" not in pins else []
            fixed = []
            for t in out:
                t = min((best({**t, "payment_days": o}) for o in dict.fromkeys([t.get("payment_days"), *pay]) if o is not None), key=lambda v: _exp_c(case, v, std), default=best(t))
                if (t := complete_offer(case, t)) not in fixed and t not in seen:
                    fixed.append(t)
            out = fixed
            clauses = [c for c in opts.get("index_clause", []) if c] if "index_clause" in case["negotiable"] and "index_clause" not in pins else []
            if out and clauses:  # the clause sheet at its own C-minimising price
                v = complete_offer(case, min((best({**out[0], "index_clause": c}) for c in clauses), key=lambda v: _exp_c(case, v, std)))
                need = any(m["field"] == "index_clause" for m in case["buyer"].get("must_haves", []))
                if v not in out and v not in seen and (self.IDX_SHEET_ALWAYS or need or _exp_c(case, v, std) < _exp_c(case, out[0], std)):
                    out.append(v)
        if out and (self.THIRD_SHEET or self.CASH_SHORT_OFFER):
            seen = [s["terms"] for m in _mine(events) for s in m.get("term_sheets") or []]
            if extra := self._trade_sheet(case, events, std, out[0], theirs["unit_price"], _pinned(events), seen):
                if (extra := complete_offer(case, extra)) not in out:
                    out.append(extra)
        if out and (days := self._mirror(case, events)) is not None:  # never longer than their opening term; keep a shorter one of ours
            seen = [s["terms"] for m in _mine(events) for s in m.get("term_sheets") or []]
            fixed = []
            for t in out:
                t = {**t, "payment_days": min(days, t["payment_days"]) if t.get("payment_days") is not None else days}
                if (t := complete_offer(case, satisfy_must_haves(case, t, std))) not in fixed and t not in seen:
                    fixed.append(t)
            out = fixed
        opts = case.get("term_options") or {}
        if out and self.DATE_LEVER and "effective_date" in case["negotiable"] and "effective_date" not in _pinned(events) and any(opts.get("effective_date") or []):
            seen = [s["terms"] for m in _mine(events) for s in m.get("term_sheets") or []]
            fixed = []
            for t in out:  # the C-minimising date (ties: later), never earlier than the sheet's own
                dates = [o for o in opts["effective_date"] if o and o >= (t.get("effective_date") or "")]
                if dates:
                    tok = HEALTH.set(None)  # our health estimate overstates the later-date charge (~24k vs ~2.2k real, P01): choose by price cost only
                    try:
                        t = {**t, "effective_date": min(sorted(dates, reverse=True), key=lambda o: total_cost(case, {**t, "effective_date": o}, std))}
                    finally:
                        HEALTH.reset(tok)
                if (t := complete_offer(case, satisfy_must_haves(case, t, std))) not in fixed and t not in seen:
                    fixed.append(t)
            out = fixed or out
        if not self.IDX_SHEET_FIRST and not _health_at_stake(case) and not _mine(events):
            out = [t for t in out if not t.get("index_clause")] or out
        if out and self.LEAD_LEVER and _health_at_stake(case) and "lead_time_days" in case["negotiable"] and "lead_time_days" not in _pinned(events) and any(opts.get("lead_time_days") or []):
            seen = [s["terms"] for m in _mine(events) for s in m.get("term_sheets") or []]
            fixed = []
            tok = HEALTH.set(None)  # plain C; ties: the shorter lead time
            try:
                picked = [{**t, "lead_time_days": min(sorted(o for o in opts["lead_time_days"] if o), key=lambda o: total_cost(case, {**t, "lead_time_days": o}, std))} for t in out]
            finally:
                HEALTH.reset(tok)
            for t in picked:
                if (t := complete_offer(case, satisfy_must_haves(case, t, std))) not in fixed and t not in seen:
                    fixed.append(t)
            out = fixed or out
        return out
