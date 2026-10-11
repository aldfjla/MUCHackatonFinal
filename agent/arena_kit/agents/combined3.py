"""Combined3Agent (v11-petra, EXPERIMENT): combined2 plus a supplier-floor estimate. Rules only, no language model.

Offline analysis (scratchpad floor/, 145 real sessions): the price behind C_best is 6-14 % below any price a supplier
ever offered us in the price cases, and opening x a goal factor predicts it with ~7 % leave-one-out error. Here that
estimate only shapes OUR side, in cases without supplier health at stake (the health route is left exactly as combined2):
- first offer: no higher than the floor estimate (never under ANCHOR_FLOOR x their price, Alex's walk-away guard);
- target = floor x (1 + TARGET_MARGIN): while >= 3 messages remain our counter stays at or under the target, rising by
  one tick a round at most, but never more than MAX_HOLDS such rounds in a row (suppliers walk when we stop moving);
- an accept above the target with >= 3 messages left and no final_offer becomes a counter at the target instead;
  a final_offer is accepted as before when valid (suppliers walk after a push).
If the opening is already within MIN_GAP of the estimate (P04-like), the case behaves exactly like combined2.
"""

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..guard import GuardedAgent, satisfy_must_haves
from ..play import latest, moves_left, standing
from .better_agent import BetterAgent, HealthScope
from .combined2 import Combined2Agent, CombinedCore, route
from .evidence import EvidenceAgent
from .reciprocal import ANCHOR_FLOOR, _c_alt, _mine, _sup, _tick, case_c_open
from .simplify_agent import _health_at_stake

# implied-best price / supplier opening, real practice runs (floor/analyze.py): leverage P05 .73 P08 .81 P18 .74;
# routine P07 .86 P04 .99 (0.93 is the safe middle); quality_first P11 .93; secure_supply P10 .85; stabilise P01-P03 ~.97
FLOOR_FACTOR = {"leverage": 0.76, "routine": 0.93, "quality_first": 0.93, "secure_supply": 0.85, "stabilise": 0.97}
TARGET_MARGIN = 0.03  # aim this far above the floor estimate (its error is ~7 %)
MIN_GAP = 0.02  # opening within this share of the estimate: nothing to gain, act like combined2
MAX_HOLDS = 2  # at most this many tick-sized (near-zero) moves of ours in a row


def floor_estimate(case, events):
    """The supplier's likely floor price (Predictor A), or None (health case, unknown goal, no quote, small gap)."""
    try:
        if _health_at_stake(case):
            return None
        f = FLOOR_FACTOR.get((case.get("buyer") or {}).get("category_goal"))
        opening = next((s["terms"]["unit_price"] for m in _sup(events) for s in m.get("term_sheets") or []
                        if (s.get("terms") or {}).get("unit_price")), None)
        if not f or not opening:
            return None
        floor = opening * f
        return floor if (opening - floor) / opening >= MIN_GAP else None
    except Exception:
        return None


def _holds(mine, p):
    """Our tick-sized moves at the end of the thread, in a row."""
    n = 0
    for a, b in zip(reversed(mine[:-1]), reversed(mine)):
        if b - a > 2 * _tick(p) + 1e-9:
            break
        n += 1
    return n


class FloorPrice:
    """Mixin over a chain's `_price(case, events, p)` (p = their standing price)."""

    def _price(self, case, events, p):
        price = super()._price(case, events, p)
        fl = floor_estimate(case, events)
        if fl is None:
            return price
        mine = [m["term_sheets"][0]["terms"]["unit_price"] for m in _mine(events)
                if m.get("term_sheets") and m["term_sheets"][0]["terms"].get("unit_price")]
        if not mine:
            return max(ANCHOR_FLOOR * p, min(price, fl))
        target = fl * (1 + TARGET_MARGIN)
        if moves_left(case, events) > 2 and price > target and _holds(mine, p) < MAX_HOLDS:
            return min(price, max(target, mine[-1] + _tick(p)))  # up to the target, else one visible tick
        return price


class FloorBetter(FloorPrice, BetterAgent):
    pass


class FloorCore(FloorPrice, CombinedCore):
    pass


class Combined3Agent(Combined2Agent):
    def __init__(self, data=None):
        super().__init__(data)
        self.chains = {
            "better": lambda: EvidenceAgent(HealthScope(GuardedAgent(FloorBetter())), data),
            "combined": lambda: EvidenceAgent(GuardedAgent(FloorCore()), data, questions=False),
        }

    def decide(self, case, threads):
        d = super().decide(case, threads)
        try:
            return self._gate(case, threads, d)
        except Exception:  # never let the experiment break a decision
            return d

    @staticmethod
    def _gate(case, threads, d):
        """An accept above the target, early and without final_offer, becomes a counter at the target."""
        action = ((d or {}).get("message") or {}).get("action") or {}
        sid = (d or {}).get("supplier_id")
        if action.get("type") != "accept" or sid not in threads:
            return d
        ev = threads[sid]
        fl = floor_estimate(case, ev)
        if fl is None or latest(ev).get("status") in ("final_offer", "agreed") or moves_left(case, ev) < 3:
            return d
        sheet_id, terms = standing(ev)
        p = terms.get("unit_price")
        target = fl * (1 + TARGET_MARGIN)
        if p is None or p <= target:
            return d
        std = standard_terms(ev)
        mine = [m["term_sheets"][0]["terms"].get("unit_price") or 0 for m in _mine(ev) if m.get("term_sheets")]
        price = round(min(p - _tick(p), max(target, (mine[-1] if mine else 0) + _tick(p))), 2)
        t = complete_offer(case, satisfy_must_haves(case, {**terms, "unit_price": price}, std))
        sent = [x["terms"] for m in _mine(ev) for x in m.get("term_sheets") or []]
        c = total_cost(case, t, std)
        if not must_haves_ok(case, t, std) or c > min(_c_alt(case), case_c_open(case, threads)) or t in sent:
            return d
        return {"supplier_id": sid, "message": {"subject": case.get("title", "Our proposal"),
                "body": "Thank you for your offer. We are close; please see our terms.", "term_sheets": [{"terms": t}]}}


__all__ = ["Combined3Agent", "floor_estimate", "route"]
