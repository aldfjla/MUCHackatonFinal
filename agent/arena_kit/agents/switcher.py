"""The Adaptive Switcher: the negotiator's-dilemma / dual-concern school (cue-based switching between
integrative and distributive moves, a reciprocity gate, the accept-slightly-worse rule).

Modes, kept per (case, supplier): COLLABORATE (one interest question, two equivalent packages - price vs
payment days - concede only after the supplier's total cost improved), FIRM (after `stall` messages without
improvement, or when the supplier got more demanding: one sheet, position restated, a small concession, no
questions; back to COLLABORATE once the supplier improves), CLOSING (final_offer or few moves left: accept a
compliant sheet that beats the reservation and costs within `accept_within` of the best standing cost seen,
else a last counter at their price on our terms, else accept if it beats the reservation, else walk away).

Knobs: anchor (first cut below their quote), step (share of the gap closed on a reciprocated concession),
firm_step (share closed while FIRM), stall (messages without improvement before FIRM), accept_within,
closing_moves (moves left that start CLOSING).
"""

import copy
import math

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..play import closing_move, latest, live_threads, moves_left, standing
from .rational import _first_terms, _message, _prices

COLLABORATE, FIRM, CLOSING = "collaborate", "firm", "closing"


class SwitcherAgent:
    def __init__(self, anchor=0.08, step=0.25, firm_step=0.10, stall=2, accept_within=0.02, closing_moves=2):
        self.anchor, self.step, self.firm_step, self.stall = anchor, step, firm_step, stall
        self.accept_within, self.closing_moves = accept_within, closing_moves
        self.case_id, self.state = None, {}  # state: supplier -> {mode, prev, best, base, stalls, idle, countered}
        self._last = None  # (key, decision): a repeated call on identical threads changes nothing

    def decide(self, case, threads):
        key = (case["case_id"], tuple((s, len(ev), ev[-1].get("status")) for s, ev in threads.items()))
        if self._last and self._last[0] == key:
            return copy.deepcopy(self._last[1])
        try:
            out = self._decide(case, threads)
            self._last = (key, out)
            return copy.deepcopy(out)
        except Exception:  # never crash a case: close safely (must-haves + alternative), else walk away
            try:
                return closing_move(case, threads)
            except Exception:
                live = live_threads(threads) or list(threads)
                return {"supplier_id": live[0] if live else None, "message": {"action": {"type": "walk_away"}}}

    def _packages(self, case, terms, base, c, ok):
        """A: price `base` on their terms. B: longer payment days, price raised until it costs us the same.
        Packages that break a must-have or cost more than their standing sheet are dropped."""
        a = complete_offer(case, {**terms, "unit_price": base})
        options = case.get("term_options", {}).get("payment_days")
        out = [a]
        if "payment_days" in case["negotiable"] and "payment_days" in terms:
            days = max(options) if options else terms["payment_days"] + 30
            at = lambda p: complete_offer(case, {**terms, "payment_days": days, "unit_price": round(p, 2)})  # noqa: E731
            slope = c(at(base + 1)) - c(at(base))
            if days > terms["payment_days"] and slope > 0:  # shorter days would be a downward solve
                p = base + (c(a) - c(at(base))) / slope
                b = at(min(max(p, 0.5 * base), terms["unit_price"]))
                out += [b] if b != a else []
        return [p for p in out if ok(p) and c(p) <= c(terms)] or [a]

    def _decide(self, case, threads):
        if case["case_id"] != self.case_id:
            self.case_id, self.state = case["case_id"], {}
        live = live_threads(threads)
        if not live:
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        std = {s: standard_terms(threads[s]) for s in live}
        cost = lambda s, t: total_cost(case, t, std[s])  # noqa: E731
        quoting = [s for s in live if standing(threads[s])[1].get("unit_price") is not None]
        if not quoting:
            return {"supplier_id": live[0], "message": {"action": {"type": "walk_away"}}}
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        has_alt = bool(alt.get("unit_price"))
        opening = [cost(s, _first_terms(threads[s])) for s in quoting if _first_terms(threads[s]).get("unit_price")]
        reservation = total_cost(case, alt) if has_alt else min(opening, default=math.inf)
        sid = min(quoting, key=lambda s: cost(s, standing(threads[s])[1]))
        events = threads[sid]
        sheet_id, terms = standing(events)
        c = lambda t: cost(sid, t)  # noqa: E731
        compliant = must_haves_ok(case, terms, std[sid])
        now = c(terms)
        beats = compliant and now < reservation
        final_ok = beats or (compliant and not has_alt)  # no alternative: walking away scores 0
        status, left = latest(events).get("status"), moves_left(case, events)
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        walk = {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}

        sent = sum(m.get("from") == "buyer" for m in events)
        fresh = sid not in self.state
        for s in quoting:  # refresh every live supplier; those not messaged now are idle
            if s not in self.state:
                seen = [cost(s, t["terms"]) for m in threads[s] if m.get("from") != "buyer" for t in m.get("term_sheets") or []]
                self.state[s] = {"mode": COLLABORATE, "prev": min(seen), "best": min(seen), "stalls": 0}
                if _prices(threads[s], True):  # resume after a crash: continue from our last offer
                    self.state[s]["base"] = _prices(threads[s], True)[-1]
            if s != sid:
                o = self.state[s]
                o["idle"], o["prev"] = True, cost(s, standing(threads[s])[1])
                o["best"] = min(o["best"], o["prev"])
        st = self.state[sid]
        first = fresh or st.pop("idle", False)  # no concession for a supplier that has not answered us
        theirs = terms["unit_price"]
        improved, worse = now < st["prev"] and not first, now > st["prev"] and not first
        st["stalls"] = 0 if improved else st["stalls"] + (not first)
        if improved:
            st["mode"] = COLLABORATE
        elif worse or st["stalls"] >= self.stall:
            st["mode"] = FIRM
        st["best"], st["prev"] = min(st["best"], now), now
        if status != "final_offer":
            st["countered"] = False

        ending = status in {"agreed", "final_offer"} or left <= 0
        if ending or left <= self.closing_moves:
            st["mode"] = CLOSING
        base = st.get("base", theirs * (1 - self.anchor))
        gap_share = {COLLABORATE: self.step if improved else 0, FIRM: self.firm_step, CLOSING: self.step}[st["mode"]]
        base = st["base"] = round(min(base + (theirs - base) * gap_share * (not first), theirs), 2)
        packages = self._packages(case, terms, base, c, lambda t: must_haves_ok(case, t, std[sid]))
        if st["mode"] == CLOSING:
            if beats and now <= st["best"] * (1 + self.accept_within) and (sent or ending):  # accept-slightly-worse rule
                return accept
            if ending:
                if status == "final_offer" and left > 0 and final_ok and not st.get("countered"):
                    st["countered"] = True
                    at_theirs = min(({**p, "unit_price": theirs} for p in packages), key=c)  # their price, our terms
                    if c(at_theirs) < now and must_haves_ok(case, at_theirs, std[sid]):
                        return _message(case, sid, at_theirs, "We accept your price; please confirm the terms below.")
                return accept if final_ok else walk
            if left <= 1 and beats:  # a last counter could make them walk
                return accept
            return _message(case, sid, packages[0], "This is our last proposal; the terms are below.")
        if st["mode"] == FIRM:
            return _message(case, sid, packages[0], "Our position is unchanged: the terms below are what we can offer.")
        body = "Thank you for the improvement; we moved our price closer to yours."
        if fresh and not sent:
            body = "Which matters most to you: price or payment timing? These two packages are equivalent for us."
        elif not improved:
            body = "We keep these packages, which are equivalent for us; please choose the one that suits you."
        msg = _message(case, sid, packages[0], body)
        msg["message"]["term_sheets"] = [{"terms": p} for p in packages]
        return msg
