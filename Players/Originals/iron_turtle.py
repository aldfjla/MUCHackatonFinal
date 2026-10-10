"""Iron Turtle
School of thought: computational (Boulware time-dependent)
Backlog version: v6 - niko
Copied from: agent/arena_kit/agents/boulware.py
Date: 2026-10-10
ORIGINAL SNAPSHOT: do not edit; copy to Players/ for experiments.
Run: see Players/Originals/README.md
"""

"""Boulware Bot: the computational / automated-negotiation school. A time-dependent tactic in TOTAL-COST
space (hold firm, concede late), blended with tit-for-tat, AC_next / AC_time acceptance and a simple
opponent model (the supplier's standing total costs per case and supplier).

Knobs: beta (>1 = Boulware, concede late), tft (extra share of the remaining gap when the supplier
conceded more than last round), start (first target vs the opening cost), end (final target vs the opening cost without an
alternative), ask_payment_days (ask for the longest payment option when it is negotiable).
"""

import math

from arena_kit.cost import complete_offer, must_haves_ok, total_cost
from arena_kit.docs import standard_terms
from arena_kit.play import closing_move, latest, live_threads, moves_left, standing
from patient_hawk import _message


def target_cost(c0, c_res, has_alt, t, beta=3.0, start=0.88, end=0.97):
    """Our target total cost at time t in [0, 1]: c_start + (c_end - c_start) * t**beta.
    With an alternative the target never sits above 0.98 * its cost."""
    if has_alt:
        c_start, c_end = min(start * c0, 0.98 * c_res), 0.98 * c_res
    else:
        c_start, c_end = start * c0, end * c0
    return c_start + (c_end - c_start) * min(max(t, 0.0), 1.0) ** beta


class BoulwareAgent:
    def __init__(self, beta=3.0, tft=0.10, start=0.88, end=0.97, ask_payment_days=True):
        self.beta, self.tft, self.start, self.end, self.ask_payment_days = beta, tft, start, end, ask_payment_days
        self._case_id, self._costs = None, {}

    def supplier_costs(self, sid):
        """Opponent model: the supplier's standing total costs, oldest first."""
        return list(self._costs.get(sid, []))

    def concession_rate(self, sid):
        """Mean cost drop per supplier move (0 with fewer than two quotes)."""
        c = self.supplier_costs(sid)
        return (c[0] - c[-1]) / (len(c) - 1) if len(c) > 1 else 0.0

    def decide(self, case, threads):
        try:
            return self._decide(case, threads)
        except Exception:  # never crash a case: close safely (must-haves + alternative), else walk away
            try:
                return closing_move(case, threads)
            except Exception:
                live = live_threads(threads) or list(threads)
                return {"supplier_id": live[0] if live else None, "message": {"action": {"type": "walk_away"}}}

    def _decide(self, case, threads):
        live = live_threads(threads)
        if not live:
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        if case.get("case_id") != self._case_id:
            self._case_id, self._costs = case.get("case_id"), {}
        std = {s: standard_terms(threads[s]) for s in live}
        cost = lambda s, t: total_cost(case, t, std[s])  # noqa: E731
        quoting = [s for s in live if standing(threads[s])[1].get("unit_price") is not None]
        if not quoting:
            return {"supplier_id": live[0], "message": {"action": {"type": "walk_away"}}}
        for s in quoting:  # opponent model: every sheet the supplier has put on the table
            self._costs[s] = [cost(s, m["term_sheets"][0]["terms"]) for m in threads[s]
                              if m.get("from") != "buyer" and m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")]
        ok = [s for s in quoting if must_haves_ok(case, standing(threads[s])[1], std[s])]
        sid = min(ok or quoting, key=lambda s: cost(s, standing(threads[s])[1]))
        events = threads[sid]
        sheet_id, terms = standing(events)
        c_now = cost(sid, terms)
        opening = [cost(s, f) for s in quoting if (f := _first_priced(threads[s]))]
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        has_alt = bool(alt.get("unit_price"))
        reservation = total_cost(case, alt) if has_alt else math.inf
        compliant = must_haves_ok(case, terms, std[sid])
        final_ok = compliant and (c_now < reservation if has_alt else True)
        status, left = latest(events).get("status"), moves_left(case, events)
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}

        ask = {}
        options = case.get("term_options", {}).get("payment_days")
        if self.ask_payment_days and "payment_days" in case["negotiable"] and "payment_days" in terms:
            ask["payment_days"] = max(options) if options else terms["payment_days"] + 30

        def at(p):
            return complete_offer(case, {**terms, **ask, "unit_price": p})

        p_hi, p_lo = terms["unit_price"], terms["unit_price"] * 0.5
        c_hi, c_lo = cost(sid, at(p_hi)), cost(sid, at(p_lo))  # c_hi: the sheet we would actually send
        c0 = min(opening, default=c_hi)  # the same base for every supplier, so switching threads keeps the curve
        if not math.isfinite(c0):
            c0 = c_hi
        rounds = case.get("round_limit", 10)
        sent = max(sum(m.get("from") == "buyer" for m in ev) for ev in threads.values())
        t = min(sent / max(rounds - 1, 1), 1.0)  # reaches 1 at the last move
        target = target_cost(c0, reservation, has_alt, t, self.beta, self.start, self.end)
        hist = self._costs[sid]
        if len(hist) >= 3 and hist[-2] - hist[-1] > hist[-3] - hist[-2] and hist[-2] > hist[-1]:
            target += self.tft * (c_hi - target)  # tit-for-tat: they moved more, so do we
        target = min(target, c_hi)

        price = p_hi if c_hi == c_lo else p_hi + (target - c_hi) * (p_lo - p_hi) / (c_lo - c_hi)
        if not math.isfinite(price):
            return closing_move(case, threads)
        offer = at(round(min(max(price, p_lo), p_hi), 2))

        if status in {"agreed", "final_offer"} or left <= 0:
            if status == "final_offer" and left > 0 and final_ok and c_hi < c_now and must_haves_ok(case, at(p_hi), std[sid]):
                return _message(case, sid, at(p_hi), "We accept your price; please confirm the terms below.")
            return accept if final_ok else {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
        if final_ok and c_now <= cost(sid, offer):  # AC_next
            return accept
        if left <= 1 and final_ok:  # AC_time
            return accept
        return _message(case, sid, offer, "Thank you for your offer. Based on our analysis we can offer the terms below.")


def _first_priced(events):
    """The supplier's first sheet that carries a unit price, else {}."""
    return next((m["term_sheets"][0]["terms"] for m in events if m.get("from") != "buyer" and m.get("term_sheets")
                 and m["term_sheets"][0]["terms"].get("unit_price")), {})


if __name__ == "__main__":
    from _runner import main

    main(BoulwareAgent)
