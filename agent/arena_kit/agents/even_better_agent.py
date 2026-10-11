"""EvenBetterAgent: BetterAgent plus a per-supplier belief (listener.supplier_model) and one purposeful move per message.

Belief: values (its currency), refuses (hard / frozen fields, price), uncertain (negotiable fields not yet tested), resistance (repeated prices).
Move: one sheet per message (the cheapest for us, or the one in the currency the supplier values); a supplier that repeated its price while
> 2 moves are left gets our last price again with ONE changed non-price lever, not a lower price. The last two moves are better's own."""

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..listener import TOPIC, focus, supplier_model
from ..play import moves_left
from .better_agent import BetterAgent, HealthScope, _with_health
from .reciprocal import _mine, _pinned


class EvenHealthScope(HealthScope):
    """HealthScope rebuilds `why` from scratch: put the belief back so acceptance reasons and beliefs are logged together."""

    def decide(self, case, threads):
        d = super().decide(case, threads)
        belief = getattr(self.delegate, "beliefs", {}).get(d.get("supplier_id")) if isinstance(d, dict) else None
        return {**d, "why": {**d["why"], "belief": belief}} if belief and isinstance(d.get("why"), dict) else d


class EvenBetterAgent(BetterAgent):
    ONE_SHEET = HOLD_ON_RESIST = True  # both False: belief and focus only, better's decision unchanged

    def __init__(self):
        self.beliefs, self.focus = {}, None

    def decide(self, case, threads):
        d = super().decide(case, threads)
        sid, ev = d.get("supplier_id"), threads.get(d.get("supplier_id"))
        if not ev or not any(m.get("from") != "buyer" for m in ev):
            return d
        model = supplier_model(case, ev)
        ps = model["prices"]
        refuses = sorted(model["hard"] | model["frozen"]) + (["price"] if model["price_frozen"] else [])
        belief = {"values": model["currency"], "refuses": refuses,
                  "uncertain": sorted(f for f in case["negotiable"] if f != "unit_price" and model["flex"].get(f, 0) == 0 and f not in refuses),
                  "resistance": sum(a == b for a, b in zip(ps, ps[1:]))}
        self.beliefs[sid] = belief
        self.focus = {**focus(model, case), "supplier_id": sid}
        try:
            with _with_health(case, self.HEALTH_ESTIMATE, self.RELEASE_DISTRESS):
                d = self._one_move(case, ev, d, model, belief)
        except Exception:  # the extra layer is optional: better's own decision stands
            pass
        return {**d, "why": {**(d.get("why") or {}), "belief": belief}}

    def _one_move(self, case, ev, d, model, belief):
        msg = d.get("message") or {}
        if msg.get("action") or not msg.get("term_sheets"):
            return d  # accept / walk / question: a purposeful move already
        std = standard_terms(ev)
        sheets = [s["terms"] for s in msg["term_sheets"]]
        blocked = {*model["hard"], *model["frozen"], *_pinned(ev)}
        opts = case.get("term_options") or {}
        fields = [f for f in case["negotiable"] if f != "unit_price" and f not in blocked]
        valued = [f for f in fields if model["currency"] != "price" and TOPIC.get(f) == model["currency"]]
        cost = lambda t: total_cost(case, t, std)  # noqa: E731
        mine = [m["term_sheets"][0]["terms"] for m in _mine(ev) if m.get("term_sheets")]
        seen = [s["terms"] for m in _mine(ev) for s in m.get("term_sheets") or []]
        if self.HOLD_ON_RESIST and mine and belief["resistance"] >= 1 and self._their_move(ev) <= 0 and moves_left(case, ev) > 2:
            fits, cands = self._fits(case, {"t": ev}), []
            for f in fields:  # our last price again, one lever changed
                for o in (o for o in opts.get(f, []) if o and o != mine[-1].get(f)):
                    t = complete_offer(case, satisfy_must_haves(case, {**mine[-1], f: o}, std))
                    if t.get(f) == o and t not in seen and must_haves_ok(case, t, std) and fits(ev, t, std):
                        cands.append((f not in valued, cost(t), f, t))
            if cands:
                _, _, f, t = min(cands, key=lambda c: c[:2])
                return {**d, "message": {**msg, "body": f"We can meet you on {f} if the price moves to {t['unit_price']}.", "term_sheets": [{"terms": t}]}}
            return d
        if not self.ONE_SHEET:
            return d
        pref = [t for t in sheets if valued and any(t.get(f) == model["preferred"].get(f) for f in valued)]
        pick = min(pref or sheets, key=cost)
        return {**d, "message": {**msg, "term_sheets": [{"terms": pick}]}}
