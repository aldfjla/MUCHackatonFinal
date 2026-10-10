"""Guard layer: wraps any delegate agent so a must-have is always ASKED for in the term sheet and an
open thread is never abandoned while something sensible is left to try.

Why: practice runs lost cases with no deal because sheets were snapped (by `complete_offer`) onto
an option that breaks a must-have, and the agents then walked away. `satisfy_must_haves` fixes the
sheets; `GuardedAgent` turns a delegate's walk-away (or crash) into an accept of a safe standing
sheet, or into one more counter at the supplier's own price with the must-haves satisfied.
"""

import logging

from .cost import OPS, complete_offer, must_haves_ok, snap, total_cost
from .docs import standard_terms
from .play import ENDED, closing_move, latest, live_threads, moves_left, standing

log = logging.getLogger("arena")

MAX_COUNTERS = 2  # guard counters per thread and case
EARLY_ACCEPT = 0.97  # accept a safe sheet before the last move only once the supplier has moved this far
ASK_QUOTE = "Could you please send us your quote?"
ASK_BODY = "We can proceed at your price if the terms below work for you; please confirm."


def _fits(m, value):
    try:
        return value is not None and OPS[m["op"]](value, m["value"])
    except TypeError:
        return False


def _must_have_value(case, m, current):
    """A value for the must-have's field that satisfies it, or `current` when none can."""
    op, bound = m["op"], m["value"]
    options = [o for o in (case.get("term_options") or {}).get(m["field"]) or [] if o is not None]
    if options:
        ok = [o for o in options if _fits(m, o)]
        if not ok:
            return current
        if op in ("<=", "<"):
            return max(ok)
        if op in (">=", ">"):
            return min(ok)
        if op == "!=":
            return current if _fits(m, current) else ok[0]
        return bound
    if op in ("<=", ">=", "=="):
        return bound
    if op == "!=":
        return current if _fits(m, current) else (bound + 1 if isinstance(bound, int | float) else current)
    step = 1 if isinstance(bound, int) else 0.01
    return bound - step if op == "<" else bound + step


def satisfy_must_haves(case, terms, standard=None):
    """A copy of `terms` with every must-have on a negotiable field satisfied, completed to a valid
    sheet. Must-haves on fields we cannot negotiate are left alone."""
    must = [m for m in case["buyer"].get("must_haves", []) if m["field"] in case["negotiable"]]
    result = dict(terms)
    for m in must:
        cur = result.get(m["field"])
        cur = snap(case, m["field"], cur) if cur is not None else cur  # complete_offer snaps it later
        result[m["field"]] = cur if _fits(m, cur) else _must_have_value(case, m, cur)
    result = complete_offer(case, result)
    for m in must:  # a gap filled from the plan, or a snap, may have broken it again
        if not _fits(m, result.get(m["field"])):
            result[m["field"]] = _must_have_value(case, m, result.get(m["field"]))
    if not must_haves_ok(case, result, standard):
        log.debug("guard: must-haves still fail after fixing %s", result)
    return result


def fix_sheets(case, sheets, standard=None):
    """(sheets, changes): `satisfy_must_haves` on each sheet (other keys kept); exact duplicates
    dropped; at most 3 kept. `changes`: what was changed, per input sheet, as readable text."""
    out, changes = [], []
    for s in sheets:
        old = s.get("terms") or {}
        fixed = {**s, "terms": satisfy_must_haves(case, old, standard)}
        if c := ", ".join(f"{k} {old.get(k)} -> {v}" for k, v in fixed["terms"].items() if old.get(k) != v):
            changes.append(c)
        if fixed not in out:
            out.append(fixed)
    return out[:3], changes


def _text(sid, body, sheets=None):
    msg = {"subject": "Our proposal", "body": body}
    if sheets:
        msg["term_sheets"] = sheets
    return {"supplier_id": sid, "message": msg}


def _walk(sid):
    return {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}


class GuardedAgent:
    def __init__(self, delegate, log_name="arena"):
        self.delegate = delegate
        self.log = logging.getLogger(log_name)
        self._case_id = None
        self._tried = {}

    def __getattr__(self, name):  # e.g. `.chosen` of a wrapped router
        if name in ("delegate", "log", "_case_id", "_tried"):
            raise AttributeError(name)
        return getattr(self.delegate, name)

    def decide(self, case, threads):
        """Never raises: any failure here falls back to the guard's own continuation, then closing_move."""
        if not any(threads.values()):  # nothing to look at: nothing to continue
            return _walk(next(iter(threads), None))
        try:
            return self._decide(case, threads)
        except Exception:
            log.exception("%s guard: failed", self._case_id)
        try:
            return self._keep_going(case, threads, None, "guard failed")
        except Exception:
            log.exception("%s guard: fallback failed", self._case_id)
        try:
            return closing_move(case, threads)
        except Exception:
            return _walk(next(iter(threads), None))

    def _decide(self, case, threads):
        if case.get("case_id") != self._case_id:
            self._case_id, self._tried = case.get("case_id"), {}
        error = False
        try:
            decision = self.delegate.decide(case, threads)
        except Exception:
            log.exception("%s guard: delegate crashed", self._case_id)
            decision, error = None, True
        msg = (decision or {}).get("message") or {}
        action = msg.get("action") or {}
        sid = (decision or {}).get("supplier_id")
        if decision and action.get("type") == "accept":
            if self._accept_ok(case, threads, decision):
                events = threads[sid]
                if (not any(m.get("from") == "buyer" for m in events) and moves_left(case, events) > 1
                        and not self._supplier_moved(case, threads, sid)):
                    self.log.info("%s guard: deferred round-1 accept on %s (unmoved opening offer)",
                                  self._case_id, sid)
                    return self._counter(case, threads, sid)
                return decision
            return self._keep_going(case, threads, sid, "delegate accept is not safe")
        if decision and msg.get("term_sheets"):
            sheets = self._fix(case, threads, sid, msg["term_sheets"])
            if sheets:
                return self._last_move(case, threads, {**decision, "message": {**msg, "term_sheets": sheets}})
        elif decision and not action:
            return self._last_move(case, threads, decision)  # a text-only message
        reason = (
            "delegate crashed" if error
            else "delegate wanted to walk" if action.get("type") == "walk_away"
            else f"unknown action {action.get('type')}" if action
            else "no usable sheet"
        )
        return self._keep_going(case, threads, sid, reason)

    @staticmethod
    def _accept_ok(case, threads, decision):
        """The accept names the standing sheet, keeps the must-haves and beats the alternative."""
        sid, action = decision.get("supplier_id"), decision["message"]["action"]
        if sid not in threads or latest(threads[sid]).get("status") in ENDED:
            return False
        sheet_id, terms = standing(threads[sid])  # only the standing id: an `-a` id is not verified to be accepted
        if sheet_id is None or sheet_id != action.get("term_sheet_id"):
            return False
        std = standard_terms(threads[sid])
        if not must_haves_ok(case, terms, std):
            return False
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        return not alt.get("unit_price") or total_cost(case, terms, std) < total_cost(case, alt)

    def _fix(self, case, threads, sid, sheets):
        std = standard_terms(threads[sid]) if sid in threads else {}
        fixed, changes = fix_sheets(case, sheets, std)
        for c in changes:
            self.log.info("%s guard: fixed sheet (must-have): %s", self._case_id, c)
        return fixed

    def _last_move(self, case, threads, decision):
        """Rule e: on our last allowed message, a price push the supplier will refuse is replaced."""
        sid = decision["supplier_id"]
        if sid not in threads:
            return decision
        left = moves_left(case, threads[sid])
        if left > 1:
            return decision
        if left < 1:
            self.log.info("%s guard: closing move (no messages left on %s)", self._case_id, sid)
            return closing_move(case, threads)
        sheets = decision["message"].get("term_sheets") or []
        theirs = standing(threads[sid])[1].get("unit_price")
        prices = [p for p in (s["terms"].get("unit_price") for s in sheets) if p is not None]
        if theirs is None or not prices or min(prices) >= theirs:
            return decision
        close = closing_move(case, threads)
        if close["message"]["action"]["type"] == "accept":
            self.log.info("%s guard: accept on last move (a lower counter would be refused)", self._case_id)
            return close
        if self._resend(case, threads[sid]):  # that counter was sent and refused: keep the agent's own new sheet
            return decision
        self.log.info("%s guard: must-have counter at their price on last move", self._case_id)
        return self._counter(case, threads, sid)

    @staticmethod
    def _resend(case, events):
        """True when the must-have counter at their standing price was already sent by us."""
        _, terms = standing(events)
        if terms.get("unit_price") is None:
            return False
        sheet = satisfy_must_haves(case, dict(terms), standard_terms(events))
        sent = [x["terms"] for m in events if m.get("from") == "buyer" for x in m.get("term_sheets") or []]
        return sheet in sent or complete_offer(case, sheet) in sent

    def _counter(self, case, threads, sid):
        events = threads[sid]
        _, terms = standing(events)
        if terms.get("unit_price") is None:
            body = _text(sid, ASK_QUOTE)
        else:
            sheet = satisfy_must_haves(case, dict(terms), standard_terms(events))
            body = _text(sid, ASK_BODY, [{"terms": sheet}])
        key = (self._case_id, sid)
        self._tried[key] = self._tried.get(key, 0) + 1
        return body

    def _eligible(self, case, threads, sid):
        events = threads[sid]
        status, left = latest(events).get("status"), moves_left(case, events)
        cap = 1 if status == "final_offer" else MAX_COUNTERS
        if status in ENDED | {"agreed"} or left < 1 or self._tried.get((self._case_id, sid), 0) >= cap:
            return False
        return not self._resend(case, events)  # a counter we already sent was refused: sending it again only burns a move

    def _supplier_moved(self, case, threads, sid):
        """The standing sheet costs at most EARLY_ACCEPT x the thread's opening sheet."""
        events = threads[sid]
        std = standard_terms(events)
        _, terms = standing(events)
        opening = next((t for m in events if m.get("from") != "buyer"
                        for sh in m.get("term_sheets") or [] for t in [sh.get("terms") or {}]
                        if t.get("unit_price") is not None), None)
        if opening is None:
            return True
        return total_cost(case, terms, std) <= EARLY_ACCEPT * total_cost(case, opening, std)

    @staticmethod
    def _hopeless(case, threads):
        """Every live thread is at its final offer (or out of messages) and even its must-have-fixed sheet costs
        no less than the alternative: a counter could only end above the alternative's C."""
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        if not alt.get("unit_price"):
            return False
        c_alt = total_cost(case, alt)
        for sid in live_threads(threads):
            ev = threads[sid]
            if latest(ev).get("status") != "final_offer" and moves_left(case, ev) >= 1:
                return False
            terms = standing(ev)[1]
            if terms.get("unit_price") is not None:
                std = standard_terms(ev)
                if total_cost(case, satisfy_must_haves(case, dict(terms), std), std) < c_alt:
                    return False
        return True

    def _keep_going(self, case, threads, preferred, reason):
        """Rule d: never walk while something sensible is left."""
        close = closing_move(case, threads)
        if close["message"]["action"]["type"] == "walk_away" and reason == "delegate wanted to walk" and self._hopeless(case, threads):
            self.log.info("%s guard: walk away stands (every thread is final, no counter beats the alternative)", self._case_id)
            return close
        if close["message"]["action"]["type"] == "accept":
            asid = close["supplier_id"]
            if (moves_left(case, threads[asid]) <= 1 or not self._eligible(case, threads, asid)
                    or self._supplier_moved(case, threads, asid)):
                self.log.info("%s guard: accept a safe standing sheet (%s)", self._case_id, reason)
                return close
        live = [s for s in live_threads(threads) if self._eligible(case, threads, s)]

        def cost(s):
            terms = standing(threads[s])[1]
            try:
                return total_cost(case, terms, standard_terms(threads[s])) if terms.get("unit_price") else float("inf")
            except Exception:
                return float("inf")

        order = ([preferred] if preferred in live else []) + sorted((s for s in live if s != preferred), key=cost)
        if not order:
            self.log.info("%s guard: closing move, no thread left to continue (%s)", self._case_id, reason)
            return close
        sid = order[0]
        self.log.info("%s guard: counter at their price on %s (%s)", self._case_id, sid, reason)
        return self._counter(case, threads, sid)
