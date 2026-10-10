"""The Listener ("Patient Hawk 3.0"): listen first, then offer. Keeps Patient Hawk's slow, reciprocal price
concessions, the must-have guard and the evidence layer (compose as EvidenceAgent(GuardedAgent(ListenerAgent()))),
and adds a supplier model (arena_kit/listener.py) that steers every move:
- frozen fields (hard constraints, or refused twice) stay at the supplier's value and are never asked again;
- each other field is chosen by our value (total_cost) minus what the supplier charges for it;
- 2-3 packages per message trade the supplier's currency (payment, capacity, duration ...) for price;
- "no further concessions" on price switches to non-price packages instead of repeating an offer;
- "your adjustment was minimal" makes our next price step larger (the bots mirror our steps);
- a final offer is closed if it is valid and beats the alternative, after one try at their price with
  better non-price terms; a cheaper package in their e-mail is sent back as ours so it becomes standing.
Rules only, no language model. `focus` (currency, frozen fields, dismissed evidence) is exposed for the
evidence layer."""

import math

from ..cost import complete_offer, must_haves_ok, total_cost
from ..docs import standard_terms
from ..guard import satisfy_must_haves
from ..listener import TOPIC, focus, supplier_model
from ..play import closing_move, latest, live_threads, moves_left, standing
from .rational import estimate_floor

ASK_QUOTE = "Could you please send us your quote?"
BODY = "Thank you for your offer. Please find our proposals in the term sheets; which of them works best for you?"
BODY_THEIR_PRICE = "We accept your price; please confirm the terms below."
PAY_MARGIN = 0.003  # paying faster than they offered must save at least this share of total cost


def _sheets(m):
    return [s.get("terms") or {} for s in m.get("term_sheets") or []]


class ListenerAgent:
    def __init__(self, anchor=0.12, target=0.03, exponent=2.0, margin=0.02, close_gap=0.01, mirror=0.8, give=0.015):
        self.anchor, self.target, self.exponent, self.margin, self.close_gap = (
            anchor,
            target,
            exponent,
            margin,
            close_gap,
        )
        self.mirror, self.give = mirror, give  # share of their last step we match; default price of a non-price favour
        self.focus = None  # read by the evidence layer
        self.model = None

    def decide(self, case, threads):
        try:
            return self._decide(case, threads)
        except Exception:  # never crash a case: close safely, else walk away
            try:
                return closing_move(case, threads)
            except Exception:
                live = live_threads(threads) or list(threads)
                return {"supplier_id": live[0] if live else None, "message": {"action": {"type": "walk_away"}}}

    def _decide(self, case, threads):
        live = live_threads(threads)
        if not live:
            return {"supplier_id": next(iter(threads), None), "message": {"action": {"type": "walk_away"}}}
        std = {s: standard_terms(threads[s]) for s in live}
        quoting = [s for s in live if standing(threads[s])[1].get("unit_price") is not None]
        if not quoting:
            return {"supplier_id": live[0], "message": {"subject": case["title"], "body": ASK_QUOTE}}
        alt = (case["buyer"].get("alternative") or {}).get("terms") or {}
        c_alt = total_cost(case, alt) if alt.get("unit_price") else math.inf
        firsts = [f for s in quoting if (f := _first(threads[s]))]
        c_open = min((total_cost(case, f, std[s]) for s in quoting if (f := _first(threads[s]))), default=math.inf)
        upper = min(c_alt, c_open) if firsts else c_alt  # never offer worse than the opening or the alternative

        def cost(s, t):
            return total_cost(case, t, std[s])

        def final_ok(s, t):  # a deal worse than the opening scores 0, so check both
            return must_haves_ok(case, t, std[s]) and cost(s, t) < c_alt and cost(s, t) <= c_open

        def best_sheet(s):  # their cheapest package in the latest reply (valid ones first)
            sheets = [t for t in _sheets(latest(threads[s])) if t.get("unit_price") is not None]
            return min(sheets, key=lambda t: (not final_ok(s, t), cost(s, t))) if sheets else standing(threads[s])[1]

        talkable = [s for s in quoting if moves_left(case, threads[s]) > 0]  # a spent thread cannot take a move
        if not talkable:
            return closing_move(case, threads)
        sid = min(talkable, key=lambda s: (not must_haves_ok(case, best_sheet(s), std[s]), cost(s, best_sheet(s))))
        events = threads[sid]
        model = self.model = supplier_model(case, events)
        self.focus = {**focus(model, case), "supplier_id": sid}
        sheet_id, terms = standing(events)
        status, left = latest(events).get("status"), moves_left(case, events)
        accept = {"supplier_id": sid, "message": {"action": {"type": "accept", "term_sheet_id": sheet_id}}}
        best = best_sheet(sid)
        mine = [_sheets(m)[0] for m in events if m.get("from") == "buyer" and m.get("term_sheets")]
        mine_prices = [t["unit_price"] for t in mine if t.get("unit_price") is not None]

        if status == "agreed":  # it offers exactly our terms: take them if they are safe
            return accept if final_ok(sid, terms) else closing_move(case, threads)
        if left <= 0:
            return closing_move(case, threads)

        price = self._price(case, model, best, mine_prices)

        def usable(packages):  # must-haves first (they beat a frozen field), then safe, new, valid, no volunteered fast pay
            fixed = [satisfy_must_haves(case, p, std[sid]) for p in packages]
            ok = [
                p
                for i, p in enumerate(fixed)
                if p not in fixed[:i] and p not in mine and must_haves_ok(case, p, std[sid]) and cost(sid, p) <= upper
            ]
            return self._pay_filter(model, ok, lambda t: cost(sid, t))

        fresh = usable(self._packages(case, model, best, price, lambda t: cost(sid, t), upper))

        if status == "final_offer" or left <= 1:
            if _tried_after_final(events):  # one non-price try per thread after a final offer, then close
                return accept if final_ok(sid, terms) else closing_move(case, threads)
            # one last try: their price with the non-price terms that cost us least (not sent before). Terms the
            # supplier tied to its price (P10: 31.90 only with 54 days) and its effective date stay as it sent them.
            hold = self._held(model, best)
            at_theirs = satisfy_must_haves(
                case,
                self._best_terms(case, model, dict(best), lambda t: cost(sid, t), strict=True, hold=hold),
                std[sid],
            )
            if (
                (left > 1 or status == "final_offer")
                and at_theirs not in mine
                and self._pay_filter(model, [at_theirs], lambda t: cost(sid, t), ref=best)
                and final_ok(sid, at_theirs)
                and cost(sid, at_theirs) < cost(sid, best) * 0.995
                and left >= 1
            ):
                return _message(case, sid, [at_theirs], BODY_THEIR_PRICE)
            theirs_full = complete_offer(case, best)  # what we would actually send
            if (
                best != terms
                and final_ok(sid, best)
                and theirs_full not in mine
                and left >= 1
                and cost(sid, best) < cost(sid, terms)
            ):
                return _message(case, sid, [theirs_full], BODY_THEIR_PRICE)  # make their cheaper package standing
            if final_ok(sid, terms):
                return accept
            return closing_move(case, threads)

        if (
            final_ok(sid, terms)
            and fresh
            and cost(sid, terms) <= min(cost(sid, p) for p in fresh) * (1 + self.close_gap)
        ):
            return accept  # their sheet is as good as anything we would ask for
        if not fresh:  # nothing new to ask: never repeat an offer
            if final_ok(sid, terms) and (model["price_frozen"] or left <= 2):
                return accept
            nudged = price + 0.25 * (best["unit_price"] - price)
            fresh = usable(self._packages(case, model, best, nudged, lambda t: cost(sid, t), upper))
            if not fresh:
                return accept if final_ok(sid, terms) else closing_move(case, threads)
        return _message(case, sid, fresh[:3], BODY)

    def _price(self, case, model, best, mine):
        """Patient Hawk's curve, plus reciprocity: match most of their last step, step up when told we moved too
        little, hold when they declare the price frozen without moving."""
        theirs = model["prices"] or [best["unit_price"]]
        first, their = theirs[0], best["unit_price"]
        start = first * (1 - self.anchor)
        if not mine:
            return round(min(start, their), 2)
        last = mine[-1]
        progress = len(mine) / max(case.get("round_limit", 10) - 1, 1)
        curve = start + (first * (1 - self.target) - start) * min(progress, 1) ** self.exponent
        step = max(curve - last, 0.0)
        their_step = theirs[-2] - theirs[-1] if len(theirs) >= 2 else 0.0
        if their_step > 0:
            step = max(step, self.mirror * their_step)
        step = min(step, 0.5 * (their - last))  # matching a big first drop must not hand over the whole gap
        if model["small_moves"]:
            step = max(step, 0.25 * (their - last))
        if model["price_frozen"] and their_step <= 0:
            step = 0.0  # hold the price; the packages change instead
        price = last + step
        if (floor := estimate_floor(theirs)) is not None:
            price = min(price, max(floor * (1 + self.margin), last))
        return round(min(max(price, last), their), 2)

    def _value(self, case, model, t, cost):
        """What a sheet really costs us: total_cost plus what the supplier will charge for each field we push
        away from its preferred value where it resists (its currency, a refusal, or a price it put on it)."""
        c = cost(t)
        for f, pref in model["preferred"].items():
            if t.get(f) == pref or f not in t:
                continue
            resists = model["flex"].get(f, 0) < 0 or TOPIC.get(f) == model["currency"] or f in model["priced"]
            if resists and t.get("unit_price") is not None:
                charge = model["priced"].get(f) or self.give * t["unit_price"]
                c += cost({**t, "unit_price": t["unit_price"] + charge}) - c if math.isfinite(c) else 0
        return c

    def _options(self, case, model, f, base):
        if f in model["frozen"]:
            return [model["preferred"].get(f, base.get(f))]
        opts = [o for o in (case.get("term_options") or {}).get(f) or []]
        if base.get(f) not in opts:
            opts.append(base.get(f))
        return opts

    @staticmethod
    def _held(model, best):
        """Fields we may not change when we answer with the supplier's own price: the ones it tied to that price
        (they differ between its packages, or it charged for them) and its effective date, unless it moved on it."""
        hold = set(model.get("tied", set())) | set(model.get("priced", {})) | set(model.get("frozen", set()))
        if model.get("flex", {}).get("effective_date", 0) <= 0:
            hold.add("effective_date")
        return {f for f in hold if f in best}

    @staticmethod
    def _pay_filter(model, packages, cost, ref=None, margin=PAY_MARGIN):
        """Drop packages that pay faster than the supplier ever offered, unless it asked for faster payment itself
        and the package beats our best other one (or `ref`, their sheet) by a real margin."""
        floor = model.get("min_pay")
        if floor is None:
            return packages
        slow = [p for p in packages if (p.get("payment_days") or floor) >= floor]
        base = min((cost(p) for p in slow + ([ref] if ref else [])), default=math.inf)
        return [
            p
            for p in packages
            if p in slow or (model.get("asks_faster_pay") and cost(p) < base * (1 - margin))
        ]

    def _best_terms(self, case, model, base, cost, strict=False, hold=()):
        """Greedy, field by field: the option of each non-frozen, non-held field with the lowest value for us."""
        t = complete_offer(case, base)
        price = t.get("unit_price")
        fields = [f for f in case["negotiable"] if f != "unit_price" and f not in hold]
        for _ in range(2):
            for f in fields:
                options = self._options(case, model, f, t)
                scored = []
                for o in options:
                    cand = complete_offer(case, {**t, f: o, "unit_price": price})
                    keep = o != t.get(f)  # on a tie, keep the value already on the table
                    scored.append(
                        (
                            self._value(case, model, cand, cost) if not strict else cost(cand),
                            keep,
                            o is None,
                            str(o),
                            cand,
                        )
                    )
                t = min(scored, key=lambda x: x[:4])[4]
        return t

    def _packages(self, case, model, best, price, cost, upper):
        """2-3 term sheets: our best terms at our price; the supplier's currency given for a lower price; a middle one."""
        a = self._best_terms(case, model, {**best, "unit_price": price}, cost)
        out = [a]
        fc = next((f for f in case["negotiable"] if f != "unit_price" and TOPIC.get(f) == model["currency"]), None)
        if fc and (fc not in model["frozen"] or fc == "payment_days"):  # frozen stops asks, not favours
            give = model["priced"].get(fc) or self.give * price
            pref = model["preferred"].get(fc, best.get(fc))
            opts = sorted([o for o in (case.get("term_options") or {}).get(fc) or [] if isinstance(o, int | float)])
            if fc == "payment_days" and opts:  # cash-short: pay at their terms; faster still only if they asked
                faster = [o for o in opts if pref is not None and o < pref]
                out.append(complete_offer(case, {**a, fc: pref, "unit_price": round(price - give, 2)}))
                if faster and model.get("asks_faster_pay"):  # the nearest faster option, never the shortest by default
                    out.append(complete_offer(case, {**a, fc: faster[-1], "unit_price": round(price - 1.5 * give, 2)}))
            elif opts:  # duration, lead time ...: the value it prefers, at our price
                out.append(
                    complete_offer(case, {**a, fc: pref if pref in opts else opts[-1], "unit_price": round(price, 2)})
                )
        elif (
            model["currency"] == "capacity"
        ):  # capacity is full: offer what could free it (longer term, longer lead time)
            more = {
                f: v
                for f in ("contract_months", "lead_time_days")
                if f in case["negotiable"] and f not in model["frozen"]
                and (v := max((o for o in (case.get("term_options") or {}).get(f) or [] if isinstance(o, int | float)), default=None))
            }
            if more:
                out.append(
                    complete_offer(case, {**a, **more, "unit_price": round(max(price, best["unit_price"] * 0.99), 2)})
                )
        traded = out[1] if len(out) > 1 else None  # the package that pays in the supplier's currency
        if len(out) < 3:  # a second price point on our best terms shows where we can move
            mid = round(price + 0.3 * (best["unit_price"] - price), 2)
            if mid != price:
                out.append(complete_offer(case, {**a, "unit_price": mid}))
        seen, keep = [], []
        for p in out:
            if p not in seen and cost(p) <= upper:
                seen.append(p)
                keep.append(p)
        return ([traded] + [p for p in keep if p != traded]) if traded in keep else keep  # lead with their currency


def _tried_after_final(events):
    """We already sent a sheet after the supplier's first final offer in this thread."""
    i = next((i for i, m in enumerate(events) if m.get("from") != "buyer" and m.get("status") == "final_offer"), None)
    return i is not None and any(m.get("from") == "buyer" and m.get("term_sheets") for m in events[i + 1 :])


def _first(events):
    return next(
        (t for m in events if m.get("from") != "buyer" for t in _sheets(m)[:1] if t.get("unit_price") is not None), None
    )


def _message(case, sid, sheets, body):
    return {
        "supplier_id": sid,
        "message": {"subject": case["title"], "body": body, "term_sheets": [{"terms": t} for t in sheets]},
    }
