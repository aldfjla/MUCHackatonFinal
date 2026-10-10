"""Confident Turtle: Boulware Bot (computational school) with the confidence index. The index (without its
rounds multiplier, Boulware already models time) bends the clock: t_eff = 1 - (1 - t) * conf, so a supplier
near its floor makes us concede toward the final target now. Low confidence also accepts a safe standing
sheet early, and the message tone follows the index. Knobs: Boulware's, plus accept_below.
"""

import logging
import math

from ..confidence import confidence_report
from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..play import closing_move, latest, live_threads, moves_left, standing
from .boulware import BoulwareAgent, _first_priced, target_cost
from .confident import TONE_HIGH, TONE_LOW, TONE_MID
from .rational import _message

log = logging.getLogger("arena")


def effective_time(t, conf):
    """conf 1 keeps the curve, conf 0 jumps to the final target."""
    return 1.0 - (1.0 - t) * conf


class ConfidentBoulwareAgent(BoulwareAgent):
    def __init__(self, beta=3.0, tft=0.10, start=0.88, end=0.97, ask_payment_days=True, accept_below=0.25):
        super().__init__(beta, tft, start, end, ask_payment_days)
        self.accept_below = accept_below

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
            self._costs[s] = [
                cost(s, m["term_sheets"][0]["terms"])
                for m in threads[s]
                if m.get("from") != "buyer" and m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")
            ]
        ok = [s for s in quoting if must_haves_ok(case, standing(threads[s])[1], std[s])]
        sid = min(ok or quoting, key=lambda s: cost(s, standing(threads[s])[1]))
        events = threads[sid]
        rep = confidence_report(case, events, std[sid], include_rounds=False)
        conf = rep["score"]
        log.info("%s confidence %.2f %s", sid, conf, rep["notes"])
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
        t_eff = effective_time(t, conf)  # confidence bends time: low confidence jumps toward the final target
        target = target_cost(c0, reservation, has_alt, t_eff, self.beta, self.start, self.end)
        hist = self._costs[sid]
        if len(hist) >= 3 and hist[-2] - hist[-1] > hist[-3] - hist[-2] and hist[-2] > hist[-1]:
            target += self.tft * (c_hi - target)  # tit-for-tat: they moved more, so do we
        target = min(target, c_hi)

        price = p_hi if c_hi == c_lo else p_hi + (target - c_hi) * (p_lo - p_hi) / (c_lo - c_hi)
        if not math.isfinite(price):
            return closing_move(case, threads)
        offer = at(round(min(max(price, p_lo), p_hi), 2))

        if status in {"agreed", "final_offer"} or left <= 0:
            if (
                status == "final_offer"
                and left > 0
                and final_ok
                and c_hi < c_now
                and must_haves_ok(case, at(p_hi), std[sid])
            ):
                return _message(case, sid, at(p_hi), "We accept your price; please confirm the terms below.")
            return accept if final_ok else {"supplier_id": sid, "message": {"action": {"type": "walk_away"}}}
        early = conf <= self.accept_below and final_ok and c_now <= c0
        log.info("%s t %.2f t_eff %.2f early accept %s", sid, t, t_eff, early)
        if early:
            return accept
        if final_ok and c_now <= cost(sid, offer):  # AC_next
            return accept
        if left <= 1 and final_ok:  # AC_time
            return accept
        tone = TONE_HIGH if conf >= 0.6 else TONE_MID if conf >= 0.3 else TONE_LOW
        return _message(case, sid, offer, tone)

