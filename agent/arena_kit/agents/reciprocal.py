"""The Reciprocal Bargainer: moves a visible step every round, in step with the supplier, and closes.

Why (30 real practice runs): suppliers answer visible moves with moves and send `final_offer` when
we idle (anchors ~20% below their price that then crept 0.01-0.03 a round scored 0.03-0.1), while an
agent that moved +2-3 EUR every round scored 0.94. And one run lost a 28.00 / 30 d / lead 35 deal
(best, must-have met) by re-asking for 90 days until the supplier walked: score 0.

- `closing_accept` (reusable; `ClosingAgent(delegate)` adds it to any agent): evaluate EVERY sheet of
  every live thread (alternatives `offer:..-a` too) with total_cost; take the cheapest that keeps the
  must-haves, beats the case alternative and is no worse than the thread's opening quote; accept it
  when the supplier says final_offer/agreed, or met our last price, or repeated itself (after >= 3 of
  our messages), or it is our last allowed message.
- `ReciprocalAgent`: anchor at 0.80 x their best standing price (0.75 floor, never above our current
  price when they ask for more), then every round close 25% (rising by 5 points a round, cap 50%) of the
  gap to their best standing price, at least 1% of price (while they move: at most 0.25 x their last
  move, at least 0.2%: the local simulator pays for patience, real suppliers for visible steps), but not closer than 3% to it before the last
  two messages (the supplier then ends with final_offer and we accept); never the same sheet twice; two sheets per
  message (main: the best contract length, payment and index option we may ask; variant: their own
  payment / index terms at the same price).
"""

import logging
import math
import re

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..play import ENDED, closing_move, latest, moves_left, standing

log = logging.getLogger("arena")

ANCHOR, ANCHOR_FLOOR = 0.80, 0.75  # first offer: x their best standing price (0.90 was met at once in 3 real runs)
FRAC0, FRAC_STEP, FRAC_MAX, MIN_STEP = 0.25, 0.05, 0.50, 0.01
KEEP = 0.05  # stay this far below their price until the last two messages (they end with final_offer, we accept)
MOVING_MIN = 0.002  # smallest step (x price) while they move; MIN_STEP when they hold still
MATCH = 0.25  # while they move, our step is at most this x their last move
REPEAT_AFTER = 3  # our messages before "the supplier repeated its sheet twice" means it has stalled
LIMIT = re.compile(r"(?:limit|stick to|only with|stay at|must stay|have to)[^.\n]{0,40}?(\d+)\s*days", re.I)
PAYMENT = re.compile(r"\b(?:payment|net|zahlungsziel)\b", re.I)
SENTENCE = re.compile(r"[.!?\n](?!\d)")  # not the point of 28.00
PINNABLE = ("payment_days", "lead_time_days", "contract_months")


def _tick(price):
    """The smallest visible price step: a cent, or 0.1% of the price when prices are large (per 100 / 1000 pieces)."""
    return max(0.01, 0.001 * price)


def _sup(events):
    return [m for m in events if m.get("from") != "buyer"]


def _mine(events):
    return [m for m in events if m.get("from") == "buyer"]


def _sheets(events):
    """Sheets of the supplier's newest message that has any (look back past question-only replies)."""
    return next((m["term_sheets"] for m in reversed(_sup(events)) if m.get("term_sheets")), [])


def _live(threads):
    """Threads with a supplier message that have not ended."""
    return [s for s, ev in threads.items() if _sup(ev) and latest(ev).get("status") not in ENDED]


def _c_alt(case):
    alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
    return total_cost(case, alt) if alt.get("unit_price") else math.inf


def case_c_open(case, threads):
    """C of the best opening: the cheapest first-message sheet (alternatives too) of ANY thread, ended
    ones included, that keeps the must-haves. A deal must beat it: a deal worse than the opening scores 0."""
    out = math.inf
    for ev in threads.values():
        first = next((m["term_sheets"] for m in _sup(ev) if m.get("term_sheets")), [])
        std = standard_terms(ev)
        for s in first:
            t = s.get("terms") or {}
            if t.get("unit_price") is not None and must_haves_ok(case, t, std):
                out = min(out, total_cost(case, t, std))
    return out


def cheapest_index(case, t, std):
    """Our sheet carries an index clause only when total_cost says it is strictly cheaper than every other
    option, None included (P02/P08/P18: a 5 % deadband clause cost 2-17k more than none at the same price)."""
    if not t.get("index_clause") or "index_clause" not in case["negotiable"]:
        return t
    opts = [None] + [c for c in (case.get("term_options") or {}).get("index_clause", []) if c]
    opts = [c for c in opts if must_haves_ok(case, {**t, "index_clause": c}, std)]  # a required clause stays
    if not opts:
        return t
    best = min(opts, key=lambda c: (total_cost(case, {**t, "index_clause": c}, std), c is not None))
    return {**t, "index_clause": best}


def _valid(case, events, std, c_alt, musts=True):
    """[(C, sheet)] of the thread's standing sheets that keep the must-haves (unless musts=False), beat the alternative."""
    out = []
    for s in _sheets(events):
        t = s.get("terms") or {}
        if t.get("unit_price") is not None and s.get("term_sheet_id") and (not musts or must_haves_ok(case, t, std)):
            if (c := total_cost(case, t, std)) < c_alt:
                out.append((c, s))
    return out


def _ready(case, events, sheet):
    if latest(events).get("status") in ("final_offer", "agreed") or moves_left(case, events) <= 1:
        return True
    mine = [m for m in _mine(events) if m.get("term_sheets")]
    if not mine:
        return False
    price = sheet["terms"]["unit_price"]
    if price <= max(s["terms"].get("unit_price") or 0 for s in mine[-1]["term_sheets"]):
        return True  # they met us
    sup = [[s["terms"] for s in m["term_sheets"]] for m in _sup(events) if m.get("term_sheets")]
    return len(mine) >= REPEAT_AFTER and len(sup) >= 2 and sup[-1] == sup[-2]  # every sheet repeated, alternatives too


def _copy_sheet(case, events, std, sheet):
    """Our own term sheet with exactly the terms of one of theirs (to make it the standing sheet)."""
    base = {k: std[k] for k in case["negotiable"] if k in std}
    return complete_offer(case, {**base, **sheet["terms"]})


def _all_heard(case, threads):
    """Several live suppliers: each has had 2 of our messages, or is final / agreed, or is nearly out of messages."""
    live = _live(threads)
    return len(live) < 2 or all(
        len(_mine(threads[s])) >= 2 or latest(threads[s]).get("status") in ("final_offer", "agreed") or moves_left(case, threads[s]) <= 1
        for s in live
    )


def closing_accept(case, threads, c_open=None):
    """The decision that closes on the cheapest acceptable sheet when the rule says so, else None: an accept of
    the thread's standing sheet, or, when the best sheet is another one (an alternative `-a`, or one before a
    question-only reply), our term sheet with its exact terms - the supplier then agrees on a standing sheet."""
    c_alt, best, order = _c_alt(case), None, {s: i for i, s in enumerate(threads)}
    if not _all_heard(case, threads):
        return None
    c_open = case_c_open(case, threads) if c_open is None else c_open
    for sid in _live(threads):
        ev = threads[sid]
        for c, s in _valid(case, ev, standard_terms(ev), c_alt):
            if s["term_sheet_id"] != standing(ev)[0] and moves_left(case, ev) <= 1:
                continue  # our last message: only a standing sheet can still be accepted (a copy would be swapped away)
            if c < c_open:
                cand = (c, order[sid], sid, s["term_sheet_id"])  # ties: the thread that arrived first
                best = min(best or cand, cand)
    if best is None:
        return None
    _, _, sid, sheet_id = best
    events = threads[sid]
    sheet = next(s for s in _sheets(events) if s["term_sheet_id"] == sheet_id)
    if not _ready(case, events, sheet):
        return None
    if sheet_id == standing(events)[0]:
        return {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
    copy = _copy_sheet(case, events, standard_terms(events), sheet)
    if any(s["terms"] == copy for m in _mine(events) for s in m.get("term_sheets") or []):
        return None  # sent already and not agreed: let the agent carry on
    return {"supplier_id": sid, "message": {"subject": case.get("title", "Our proposal"), "body": "We accept these terms; please confirm.", "term_sheets": [{"terms": copy}]}}


class ClosingAgent:
    """Adds only the accept rule to any agent."""

    def __init__(self, delegate):
        self.delegate = delegate

    def __getattr__(self, name):
        if name == "delegate":
            raise AttributeError(name)
        return getattr(self.delegate, name)

    def decide(self, case, threads):
        try:
            if accept := closing_accept(case, threads):
                return accept
        except Exception:
            log.exception("%s closing rule failed", case.get("case_id"))
        return self.delegate.decide(case, threads)


def _pinned(events):
    """Terms the supplier will not move: repeated by it twice while we asked otherwise, or stated as a limit."""
    pins = {}
    sup = [m["term_sheets"][0]["terms"] for m in _sup(events) if m.get("term_sheets")]
    mine = [m for m in _mine(events) if m.get("term_sheets")]
    if len(sup) >= 2 and mine:
        for f in PINNABLE:
            asked = {s["terms"].get(f) for s in mine[-1]["term_sheets"]} - {None, sup[-1].get(f)}
            if sup[-1].get(f) is not None and sup[-1].get(f) == sup[-2].get(f) and asked:
                pins[f] = sup[-1][f]
    for m in _sup(events)[-2:]:
        for sentence in SENTENCE.split(m.get("body") or ""):
            if (hit := LIMIT.search(sentence)) and PAYMENT.search(sentence):
                pins["payment_days"] = int(hit.group(1))
    return pins


class ReciprocalAgent:
    def decide(self, case, threads):
        if not _live(threads):  # nothing to answer
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        if accept := closing_accept(case, threads):
            return accept
        live = [s for s in _live(threads) if moves_left(case, threads[s]) >= 1]
        open_ = [s for s in live if latest(threads[s]).get("status") not in ("final_offer", "agreed")]
        if not open_:
            return closing_move(case, threads)

        def key(s):  # keep every thread moving: fewest messages first, then the cheapest
            ev = threads[s]
            c = min((c for c, _ in _valid(case, ev, standard_terms(ev), math.inf, musts=False)), default=math.inf)
            return len(_mine(ev)), c

        sid = min(open_, key=key)
        events = threads[sid]
        std = standard_terms(events)
        valid = _valid(case, events, std, math.inf) or _valid(case, events, std, math.inf, musts=False)  # a must-have breach is fixed in our sheet
        if not valid:  # no priced sheet to answer: ask for one, give up after 3 asks
            if len(_mine(events)) >= 3:
                return {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
            return {"supplier_id": sid, "message": {"subject": case.get("title", "Our enquiry"), "body": "Could you please send us your quote?"}}
        _, best = min(valid, key=lambda v: v[0])
        sheets = self._sheets(case, events, std, best["terms"])
        if not sheets:  # nothing new left to offer: close on the best sheet, or give up
            return closing_move(case, threads)
        return {
            "supplier_id": sid,
            "message": {
                "subject": case.get("title", "Our proposal"),
                "body": "Thank you for your offer. We have moved on our side; please see our updated terms.",
                "term_sheets": [{"terms": t} for t in sheets],
            },
        }

    @staticmethod
    def _their_move(events):
        """How far the supplier's best price fell in its last message (0 if it did not)."""
        ps = [min(s["terms"]["unit_price"] for s in m["term_sheets"] if s["terms"].get("unit_price") is not None)
              for m in _sup(events) if any(s["terms"].get("unit_price") is not None for s in m["term_sheets"])]
        return max(0.0, ps[-2] - ps[-1]) if len(ps) >= 2 else 0.0

    def _price(self, case, events, p):
        mine = [m["term_sheets"][0]["terms"]["unit_price"] for m in _mine(events) if m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")]
        if not mine:
            cur = case["buyer"].get("current_unit_price") or p
            return max(ANCHOR_FLOOR * p, min(ANCHOR * p, cur))  # anchor; never pay more than now unless forced
        frac = min(FRAC_MAX, FRAC0 + FRAC_STEP * len(mine))
        move = self._their_move(events)
        step = max(frac * (p - mine[-1]), MIN_STEP * p, _tick(p))
        if move > 0:  # they moved: answer in step, not beyond (a supplier that holds still gets the full step)
            step = max(MOVING_MIN * p, _tick(p), min(step, MATCH * move))
        top = p if moves_left(case, events) <= 2 else p * (1 - KEEP)
        return max(mine[-1], min(top, mine[-1] + step))

    @staticmethod
    def _index_variant(case, main, p, opts, pins, make, cost, cap, seen):
        """An index clause is security for the supplier, not cash: offer it for the price at which our C is just
        below the main sheet's C (the clause's expected cost per unit taken off the price). None if not negotiable."""
        if "index_clause" not in case["negotiable"] or "index_clause" in pins:
            return None
        best = None
        for clause in (c for c in opts.get("index_clause", []) if c):
            t = make(main["unit_price"], index_clause=clause, **{f: main[f] for f in ("payment_days", "contract_months") if f in main})
            if t["index_clause"] != clause or t["index_clause"] == main.get("index_clause"):
                continue
            slope = cost({**t, "unit_price": t["unit_price"] + 1}) - cost(t)
            if slope <= 0:
                continue
            price = round(max(0.75 * p, min(p, t["unit_price"] - (cost(t) - cost(main)) / slope - 0.01)), 2)  # no lowball
            v = cap({**t, "unit_price": price})
            if (
                0 < price
                and v not in seen
                and cost(v) < cost(main)
                and cost(v) < cost({**v, "index_clause": None})  # the clause itself must save us money
                and (best is None or v["unit_price"] > best["unit_price"])
            ):
                best = v
        return best

    def _sheets(self, case, events, std, theirs):
        p, pins = theirs["unit_price"], _pinned(events)
        base = {k: v for k, v in {**{f: std[f] for f in case["negotiable"] if f in std}, **theirs}.items() if v is not None}
        opts = case.get("term_options") or {}
        c_alt = _c_alt(case)
        sent = [m["term_sheets"] for m in _mine(events) if m.get("term_sheets")]
        seen = [s["terms"] for ss in sent for s in ss]

        def make(price, **over):
            over = {k: v for k, v in over.items() if k not in pins}
            return satisfy_must_haves(case, {**base, "unit_price": round(price, 2), **over}, std)

        def cost(t):
            return total_cost(case, t, std)

        def cap(t):  # hard floor: never offer a sheet that costs more than the alternative
            if (c := cost(t)) >= c_alt:
                slope = cost({**t, "unit_price": t["unit_price"] + 1}) - c
                if slope > 0:
                    t = {**t, "unit_price": round(t["unit_price"] - (c - c_alt) / slope - 0.01, 2)}
            return t

        def best_months(price, **over):
            months = [m for m in opts.get("contract_months", []) if m and "contract_months" in case["negotiable"]] or [None]
            return min(months, key=lambda m: (cost(make(price, **over, **({"contract_months": m} if m else {}))), m or 0))

        fields = [f for f in ("payment_days", "index_clause") if f in case["negotiable"] and f not in pins and opts.get(f)]
        combos = [{}]
        for f in fields:
            combos = [{**v, f: o} for v in combos for o in opts[f]]

        def pair(price):
            """(main, variant): main asks for the cheapest payment/index option, variant keeps their own."""
            months = best_months(price)
            mk = lambda v: cap(make(price, **({"contract_months": months} if months else {}), **v))  # noqa: E731
            theirs, asks = mk({}), [mk(v) for v in combos]
            main = min(asks, key=cost)
            return main, theirs

        price = self._price(case, events, p)
        main, theirs = pair(price)
        floor = max((x["terms"]["unit_price"] for ss in sent for x in ss[:1] if x["terms"].get("unit_price")), default=0.0)
        while (main in seen or main["unit_price"] <= floor) and price < p:  # always a visible step, never a repeat, never above theirs
            price = min(p, price + _tick(p))
            new, theirs = pair(price)
            if new == main:  # capped: the price cannot move
                break
            main = new
        if main in seen:
            return []
        out = [main] + ([theirs] if theirs != main and theirs not in seen else [])
        if (extra := self._index_variant(case, main, p, opts, pins, make, cost, cap, seen)) and extra not in out:
            out.append(extra)
        done = []
        for t in out:
            t = complete_offer(case, t if "index_clause" in pins else cheapest_index(case, t, std))
            if t not in done and t not in seen:
                done.append(t)
        return done
