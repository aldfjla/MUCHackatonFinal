"""FinalAgent: bargains in SUPPLIER-VALUE space with lever bundles, not on unit price.

Why: the supplier prices every sheet by what it is worth to it in cash (price at its standard terms, minus
the cost of the payment days we ask), and terms such as contract months, lead time or an index clause are
free for it. So we (1) fix the VALUE we offer each round, (2) pick the lever combination that is cheapest
for US at that value (long payment, short lead time, ...), and set the price that gives exactly that value.
- Value schedule: anchor at 0.76 x the value of their sheet, then close 55% of the gap, then jump to the
  fixed point of "their ask falls by g x our rise" (g estimated, default 0.25): the ask freezes at a random
  early round, so two big moves beat ten small steps. A sheet above their value x (1 - tol) is accepted at
  our price, so we only go above it in the message at moves_left == 2 (A - tick); at moves_left <= 1 we close.
- Sheets: the lowest-C bundle, the lowest-C bundle with payment <= their standard (suppliers that refuse
  long terms), their own terms re-priced (pure price move). Cheapest for us first: they take the first of equal value.
- Closing: a supplier sheet meets us when its C is no more than our cheapest sheet's C.
- A silent thread is skipped after `max_asks` messages; never walk away while a supplier is alive.
"""

import itertools
import math

from ..cost import closing_terms, complete_offer, must_haves_ok, supplier_value, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..play import ENDED, closing_move, latest, live_threads, moves_left
from .reciprocal import (
    ReciprocalAgent,
    _c_alt,
    _live,
    _mine,
    _pinned,
    _sup,
    _tick,
    _valid,
    case_c_open,
    closing_accept,
)
from .reciprocal import _sheets as their_sheets

QUOTE_ASK = "Could you please send us your quote?"
BODY = (
    "Thank you for your offer. Please find our proposal in the attached term sheets; each of them works for us, "
    "please pick the one that suits you best."
)
R_SUP, STD_PD, TOL = 0.074, 30, 0.012  # fitted median supplier rate, its payment days, tolerance
ANCHOR, JUMP = 0.76, 0.55
G_DEFAULT, G_MIN, G_MAX, MIN_STEP = 0.25, 0.1, 0.8, 0.01
MAX_COMBOS, MAX_SHEETS = 3000, 3


def _priced(case, events, std):
    """[(C, sheet)] of the thread's standing sheets, must-haves ignored."""
    return _valid(case, events, std, math.inf, musts=False)


def _std_full(case, events):
    """The supplier's complete standard terms: its quote PDF, its payment days (default 30), gaps from the plan."""
    std = standard_terms(events)
    pd = std.get("payment_days") or STD_PD
    full = closing_terms(case, {"unit_price": None}, std)
    full = {**full, **{k: v for k, v in std.items() if v is not None}, "payment_days": pd}
    return full


def _value(case, std_full, terms):
    return supplier_value(case, terms, {"standard": std_full, "interest_rate": R_SUP})


def _lowest_value(case, std_full, sheets):
    vals = [_value(case, std_full, s["terms"]) for s in sheets if (s.get("terms") or {}).get("unit_price") is not None]
    return min(vals, default=None)


def _target(case, events, std_full, anchor=ANCHOR):
    """The value (to the supplier) we offer this round, or None without a priced sheet of theirs."""
    theirs = [_lowest_value(case, std_full, m["term_sheets"]) for m in _sup(events) if m.get("term_sheets")]
    theirs = [v for v in theirs if v is not None]
    if not theirs:
        return None
    a = theirs[-1]
    mine = [m["term_sheets"][0]["terms"] for m in _mine(events) if m.get("term_sheets")]
    ours = [_value(case, std_full, t) for t in mine if t.get("unit_price")]
    tick = _tick(a)
    if not ours:
        o = anchor * a
    elif len(ours) == 1:
        o = ours[-1] + JUMP * (a - ours[-1])
    else:
        g = G_DEFAULT
        if len(theirs) >= 2 and (fall := theirs[-2] - theirs[-1]) > 0 and (rise := ours[-1] - ours[-2]) > 0:
            g = min(G_MAX, max(G_MIN, fall / rise))
        o_star = (1 - TOL) * (a + g * ours[-1]) / (1 + g * (1 - TOL))
        o = min(a - tick, max(o_star, ours[-1] + max(MIN_STEP * a, tick)))
    if moves_left(case, events) <= 2:
        o = a - tick
    return max(o, ours[-1]) if ours else o


def _pins(events):
    """Pinned fields: the parent's, plus an index clause the supplier repeated twice while we asked otherwise."""
    pins = _pinned(events)
    sup = [m["term_sheets"][0]["terms"] for m in _sup(events) if m.get("term_sheets")]
    mine = [m for m in _mine(events) if m.get("term_sheets")]
    if len(sup) >= 2 and mine and "index_clause" in sup[-1] and sup[-1]["index_clause"] == sup[-2].get("index_clause"):
        if any(s["terms"].get("index_clause") != sup[-1]["index_clause"] for s in mine[-1]["term_sheets"]):
            pins["index_clause"] = sup[-1]["index_clause"]
    return pins


def _reduce(opts, centre, k):
    """At most k options: the one at `centre`, the extremes, then the closest to it."""
    if len(opts) <= k:
        return opts
    nums = all(isinstance(o, int | float) and not isinstance(o, bool) for o in opts)
    if not nums:
        return opts[:k]
    keep = {min(opts), max(opts)} | ({centre} if centre in opts else set())
    rest = sorted((o for o in opts if o not in keep), key=lambda o: (abs(o - (centre if centre is not None else o)), o))
    return sorted(keep | set(rest[: max(0, k - len(keep))]))


def _builder(case, events, std_full, theirs, pins, c_alt, c_open):
    """build(value): our sheets worth exactly `value` to the supplier, cheapest for us first (lowest-C bundle,
    lowest-C bundle with payment <= their standard, their terms re-priced), each below c_alt and c_open."""
    levers = [f for f in case["negotiable"] if f != "unit_price"]
    centre = {f: theirs.get(f, std_full.get(f)) for f in levers}
    options = []
    for f in levers:
        if f in pins:
            options.append([pins[f]])
        else:
            options.append(list((case.get("term_options") or {}).get(f) or [centre[f]]))
    k = 4
    while math.prod(len(x) for x in options) > MAX_COMBOS and k > 1:
        options = [_reduce(x, centre[f], k) for f, x in zip(levers, options, strict=True)]
        k -= 1
    priced = []  # (combo without price, value at price 0, value per euro of price)
    for vals in itertools.product(*options):
        combo = satisfy_must_haves(case, dict(zip(levers, vals, strict=True)), std_full)
        v0 = _value(case, std_full, {**combo, "unit_price": 0.0})
        b = _value(case, std_full, {**combo, "unit_price": 1.0}) - v0
        if b > 0:
            priced.append((combo, v0, b))
    own = {f: std_full[f] for f in case["negotiable"] if f in std_full}
    own.update({k: v for k, v in theirs.items() if v is not None})
    own.update(pins)
    own = complete_offer(case, own)  # the terms actually sent, so the price is computed for them
    v0 = _value(case, std_full, {**own, "unit_price": 0.0})
    own_b = _value(case, std_full, {**own, "unit_price": 1.0}) - v0

    def ok(t):
        if t["unit_price"] <= 0 or not must_haves_ok(case, t, std_full):
            return False
        return (c := total_cost(case, t, std_full)) < c_alt and c < c_open

    def build(value):
        cands = []
        for combo, c0, b in priced:
            t = {**combo, "unit_price": round((value - c0) / b, 2)}
            if ok(t):
                cands.append((total_cost(case, t, std_full), t))
        out = []
        if cands:
            out.append(min(cands, key=lambda x: x[0])[1])
            short = [x for x in cands if (x[1].get("payment_days") or 0) <= std_full["payment_days"]]
            if short:
                out.append(min(short, key=lambda x: x[0])[1])
        if own_b > 0:
            t = satisfy_must_haves(case, {**own, "unit_price": round((value - v0) / own_b, 2)}, std_full)
            if ok(t):
                out.append(t)
        done = []
        for t in out:
            if (c := complete_offer(case, t)) not in done:
                done.append(c)
        return done

    return build


class FinalAgent(ReciprocalAgent):
    def __init__(self, anchor=ANCHOR, max_asks=2):
        self.anchor, self.max_asks = anchor, max_asks

    def _ask(self, case, sid):
        return {"supplier_id": sid, "message": {"subject": case.get("title", "Our enquiry"), "body": QUOTE_ASK}}

    def _unheard(self, threads):
        """A thread that never answered and has had fewer than max_asks of our messages, or None."""
        return next((s for s, ev in threads.items() if not _sup(ev) and len(_mine(ev)) < self.max_asks), None)

    def _close(self, case, quoted):
        """Accept the best acceptable sheet; else rescue a priced sheet that only breaks a must-have by
        sending it with the must-haves fixed; else walk away (only when nothing else can be done)."""
        if not live_threads(quoted):
            return {"supplier_id": next(iter(quoted), None), "message": {"action": {"type": "walk_away"}}}
        move = closing_move(case, quoted)
        if move["message"].get("action", {}).get("type") != "walk_away":
            return move
        c_alt, c_open, best = _c_alt(case), case_c_open(case, quoted), None
        match = self._value_match(case, quoted, c_alt, c_open)
        if match is not None:
            sid, fixed = match
            body = "We can meet your position with the terms below; please confirm."
            message = {"subject": case.get("title", "Our proposal"), "body": body, "term_sheets": [{"terms": fixed}]}
            return {"supplier_id": sid, "message": message}
        # reached only when nothing is acceptable; it may answer a final_offer
        for sid, ev in quoted.items():
            if latest(ev).get("status") in ENDED or moves_left(case, ev) < 1:
                continue
            std = standard_terms(ev)
            base = {k: std[k] for k in case["negotiable"] if k in std}
            sent = [x["terms"] for m in _mine(ev) for x in m.get("term_sheets") or []]
            for _, sh in _priced(case, ev, std):
                fixed = complete_offer(case, satisfy_must_haves(case, {**base, **sh["terms"]}, std))
                if not must_haves_ok(case, fixed, std) or fixed in sent:
                    continue
                if (c := total_cost(case, fixed, std)) < c_alt and c <= c_open:
                    best = min(best or (c, sid, fixed), (c, sid, fixed), key=lambda x: x[0])
        if best is None:
            return move
        _, sid, fixed = best
        body = "We can accept your price with the terms below; please confirm."
        message = {"subject": case.get("title", "Our proposal"), "body": body, "term_sheets": [{"terms": fixed}]}
        return {"supplier_id": sid, "message": message}

    def _value_match(self, case, quoted, c_alt, c_open):
        """(sid, sheet) of the cheapest sheet worth exactly their ask to them (so it is met), on any live thread
        with a message left: their terms at their standard payment days re-priced, or the lowest-C bundle."""
        best = None
        for sid, ev in quoted.items():
            if latest(ev).get("status") in ENDED or moves_left(case, ev) < 1:
                continue
            std_full = _std_full(case, ev)
            priced = [s for s in their_sheets(ev) if (s.get("terms") or {}).get("unit_price") is not None]
            if not priced:
                continue
            a = _lowest_value(case, std_full, priced)
            newest = min(priced, key=lambda s: _value(case, std_full, s["terms"]))["terms"]
            theirs = {**newest, "payment_days": std_full["payment_days"]}
            build = _builder(case, ev, std_full, theirs, _pins(ev), c_alt, c_open)
            sent = [x["terms"] for m in _mine(ev) for x in m.get("term_sheets") or []]
            for t in build(a):
                if t not in sent and must_haves_ok(case, t, std_full):
                    c = total_cost(case, t, std_full)
                    if best is None or c < best[0]:
                        best = (c, sid, t)
        return best and (best[1], best[2])

    def decide(self, case, threads):
        quoted = {s: ev for s, ev in threads.items() if _sup(ev)}
        if not _live(threads):  # nothing to answer: ask a thread that never wrote, else give up
            if (sid := self._unheard(threads)) is not None:
                return self._ask(case, sid)
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        if accept := closing_accept(case, quoted, by_cost=True):
            return accept
        live = [s for s in _live(threads) if moves_left(case, threads[s]) >= 1]
        open_ = [s for s in live if latest(threads[s]).get("status") not in ("final_offer", "agreed")]

        def silent(s):  # no priced sheet and already asked enough: skip it, never walk away from it
            ev = threads[s]
            return not _priced(case, ev, standard_terms(ev)) and len(_mine(ev)) >= self.max_asks

        open_ = [s for s in open_ if not silent(s)]
        if not open_:
            if (sid := self._unheard(threads)) is not None:
                return self._ask(case, sid)
            return self._close(case, quoted)

        def key(s):  # keep every thread moving: fewest messages first, then the cheapest
            ev = threads[s]
            c = min((c for c, _ in _priced(case, ev, standard_terms(ev))), default=math.inf)
            return len(_mine(ev)), c

        sid = min(open_, key=key)
        events = threads[sid]
        if moves_left(case, events) <= 1:  # our last message must never be a counter that can time out
            return self._close(case, quoted)
        std = standard_terms(events)
        # a must-have breach is fixed in our sheet
        valid = _valid(case, events, std, math.inf) or _priced(case, events, std)
        if not valid:  # no priced sheet to answer: ask for one
            return self._ask(case, sid)
        _, best = min(valid, key=lambda v: v[0])
        c_open = case_c_open(case, quoted)  # a deal at or above the opening quote scores 0
        sheets = self._sheets(case, events, std, best["terms"], c_open)
        if not sheets:  # nothing new left to offer: close on the best sheet, or give up
            return self._close(case, quoted)
        return {
            "supplier_id": sid,
            "message": {
                "subject": case.get("title", "Our proposal"),
                "body": BODY,
                "term_sheets": [{"terms": t} for t in sheets],
            },
        }

    def _sheets(self, case, events, std, theirs, c_open=math.inf):
        std_full = _std_full(case, events)
        o = _target(case, events, std_full, self.anchor)
        if o is None:
            return []
        a = _lowest_value(case, std_full, their_sheets(events))
        pins, c_alt, tick = _pins(events), _c_alt(case), _tick(a)
        build = _builder(case, events, std_full, theirs, pins, c_alt, c_open)
        seen = [s["terms"] for m in _mine(events) if m.get("term_sheets") for s in m["term_sheets"]]
        sheets = build(o)
        while sheets and sheets[0] in seen and o < a:
            o += tick
            sheets = build(o)
        o = min(o, a)
        if not sheets or sheets[0] in seen:
            return []
        return [t for i, t in enumerate(sheets) if i == 0 or t not in seen][:MAX_SHEETS]
