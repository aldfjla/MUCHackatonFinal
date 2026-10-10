"""A real-like supplier for arena-sim: every number is drawn per seed from sim_cases/supplier_profile.json
(fitted by fit_supplier.py from the real practice dumps; what could not be fitted is marked assumed there).

    arena-sim serve --supplier real --seed 7

How it behaves (one draw per seed, case and supplier, so the same seed replays the same supplier):
- opens at a fitted multiple of the buyer's current price (at the announced price in price_increase cases),
  quoting at its standard terms (payment days drawn per supplier: 30, sometimes 45 or 60);
- its ask is a cash value per unit; every sheet is valued with cost.supplier_value at its own money cost;
- it agrees to a sheet worth at least its ask minus a small tolerance, but never below its floor;
- otherwise it concedes: a first-reply drop, then a share (pass-through) of how much our BEST offer so far
  rose (a new maximum only), a small step when we idle;
  it freezes into a final_offer at its drawn round; pushing past it walks away;
- some suppliers refuse payment terms beyond 30 days; a capacity supplier caps the volume unless the
  contract is 24 months or longer;
- its floor (never below) fixes C_best: the cheapest package at which it still gets its floor value.
"""

import itertools
import json
import random
import re
from pathlib import Path

from .cost import must_haves_ok, supplier_value, total_cost
from .sim import Sim, structured

PROFILE = Path(__file__).parent / "sim_cases" / "supplier_profile.json"
STD_PD = 30  # the default standard payment days


def levers(case):
    """The negotiable fields other than the price (it is not always listed first, e.g. P11)."""
    return [f for f in case["negotiable"] if f != "unit_price"]


def load_profile(path=PROFILE):
    return json.loads(Path(path).read_text(encoding="utf-8"))["parameters"]


LIFT_MONTHS = 24  # a volume cap is lifted by a contract of at least this many months (P10, reciprocal_evidence)


def capped(cap, terms):
    """True if the volume is over the supplier's allocation cap and the contract is too short to lift it."""
    return bool(cap and (terms.get("volume_per_year") or 0) > cap and (terms.get("contract_months") or 0) < LIFT_MONTHS)


def package_cost(case, std, rate, floor, pd_limit=None, vol_cap=None):
    """C of the cheapest package a supplier accepts: over every allowed value of the other terms, the
    price at which it receives exactly `floor` (cash per unit at its standard terms). inf if none."""
    names = levers(case)
    sup = {"standard": std, "interest_rate": rate}
    best = float("inf")
    for combo in itertools.product(*[case["term_options"].get(f) or [None] for f in names]):
        c = dict(zip(names, combo, strict=True))
        if (pd_limit and (c.get("payment_days") or 0) > pd_limit) or capped(vol_cap, c):
            continue
        if not must_haves_ok(case, c, std):
            continue
        a = supplier_value(case, {**c, "unit_price": 0.0}, sup)
        b = supplier_value(case, {**c, "unit_price": 1.0}, sup) - a
        best = min(best, total_cost(case, {**c, "unit_price": (floor - a) / b}, std))
    return best


def draw(profile, case, sup, i, nsup, seed):
    """One supplier's parameters from the fitted ranges. Deterministic in (seed, case, supplier)."""
    rng = random.Random(f"{seed}|{case['case_id']}|{sup}")
    P = profile
    hw = P["single_sample_halfwidth"]["value"]
    jit = P["pass_through_jitter"]
    kind = P["opening_vs_current_price"]["by_type"].get(case["type"], {})
    lo, hi = (kind["min"], kind["max"]) if kind.get("n", 0) >= 2 else (  # one sample: +- the assumed half-width
        (kind["median"] - hw, kind["median"] + hw) if kind else P["opening_vs_current_price"]["pooled_excl_rfq"]
    )  # fmt: skip
    ratio = rng.uniform(lo, hi)
    f = P["floor_vs_opening"]
    fk = f["by_type"].get(case["type"], {})
    flo, fhi = (fk["min"], fk["max"]) if fk.get("n", 0) >= 2 else (  # one sample: +- the assumed half-width
        (fk["median"] - hw, fk["median"] + hw) if fk else (f["min"], f["max"])
    )  # fmt: skip
    caps = case["term_options"].get("volume_per_year") or []
    cap = (
        sorted(caps)[1]
        if case["type"] == "capacity" and len(caps) >= 2 and "volume_per_year" in case["negotiable"]
        else None
    )
    r = P["supplier_interest_rate"]
    drops = P["first_reply_drop_multi_supplier" if nsup > 1 else "first_reply_drop_plain"]["samples"]
    verified = P["first_reply_drop_with_verified_claims"]["samples"]
    return {
        "ratio": ratio,
        "r": rng.uniform(r["min"], r["max"]),
        "floor": min(P["floor_cap"]["value"], rng.uniform(flo, fhi)),
        "std_pd": rng.choice(P["standard_payment_days"]["samples"]),
        "final_margin": P["final_at_floor_margin"]["value"],
        "idle_thr": P["idle_threshold"]["value"],
        "g": min(1.0, max(0.0, rng.choice(P["concession_pass_through"]["samples"])))
        * rng.uniform(jit["low"], jit["high"]),
        "idle": rng.choice(P["idle_step"]["samples"]),
        "first": max(0.0, rng.choice(drops)),
        "first_verified": max(0.0, rng.choice(verified)),
        "final_round": rng.choice(P["final_offer_round"]["samples"]),
        "walk_after": rng.choice(P["walk_after_pushes_post_final"]["samples"]),
        "tol": rng.uniform(P["accept_tolerance"]["min"], P["accept_tolerance"]["max"]),
        "pd_limit": 30 if rng.random() < P["payment_days_hard_limit_30"]["share"] else None,
        "vol_cap": cap,
        "omit": {f for f, x in P["opening_omits_field"]["rates"].items() if rng.random() < x["omit"]},
    }


class SimReal(Sim):
    def __init__(self, *args, seed=0, profile=None, **kw):
        super().__init__(*args, **kw)
        self.seed, self.profile, self._p = seed, profile or load_profile(), {}

    # -- hooks of Sim --------------------------------------------------------------------------
    def _params(self, case, sup, i):
        key = (case["case_id"], sup)
        if key not in self._p:
            self._p[key] = draw(self.profile, case, sup, i, len(case["suppliers"]), self.seed)
        return self._p[key]

    def _opening(self, case, i, sup, current):
        ref = current or case["buyer"]["fallback_unit_price"]
        if (
            case["type"] == "price_increase" and current
        ):  # the supplier opens at the price it announced (P01, P02: exact)
            asked = (self.facts.get(case.get("trigger_doc")) or {}).get("asked_price")
            pct = re.search(r"\+(\d+(?:\.\d+)?) ?%", case["title"])
            if asked or pct:
                return round(asked or current * (1 + float(pct[1]) / 100), 2)
        return round(ref * self._params(case, sup, i)["ratio"], 2)

    def _standard(self, case, sup):
        """The supplier's standard terms. Fitted: payment days from the profile (30, 45 or 60), volume = the buyer's
        need and contract 12 months (what the real quotes state, P03/P10). Assumed (profile, standard_terms_gaps):
        the slowest lead time, ppm 2.5x the loosest option."""
        std, p = {}, self._params(case, sup, case["suppliers"].index(sup))
        mult = self.profile["standard_terms_gaps"]["ppm_multiplier"]
        for f in levers(case):
            o = case["term_options"].get(f) or [None]
            if f == "payment_days":
                std[f] = min(o, key=lambda d: (abs(d - p["std_pd"]), d))
            elif f == "volume_per_year":
                std[f] = case["buyer"]["need_per_year"]
            elif f == "lead_time_days":
                std[f] = o[-1]
            elif f == "ppm_commitment" and o[0] is not None:
                std[f] = round(max(o) * mult)
            else:
                std[f] = o[0]
        return std

    def _init_thread(self, s, th, i):
        sup = s["case"]["suppliers"][i]
        p = self._params(s["case"], sup, i)
        th.update(p=p, ask=th["opening"], last_ov=None, pushes=0, floor=round(p["floor"] * th["opening"], 2))
        # the quote states the price and most standard terms; some it leaves out (fitted rates per field)
        th["first"] = {"unit_price": th["opening"], **{f: v for f, v in th["standard"].items() if f not in p["omit"]}}

    def _bounds(self, case, ths):
        c_open = min(total_cost(case, {"unit_price": th["opening"]}, th["standard"]) for th in ths.values())
        c_best = min(
            package_cost(case, th["standard"], th["p"]["r"], th["floor"], th["p"]["pd_limit"], th["p"]["vol_cap"])
            for th in ths.values()
        )
        alt = case["buyer"].get("alternative") or {}
        if alt.get("terms", {}).get("unit_price"):
            c_best = min(c_best, total_cost(case, alt["terms"]))
        return c_open, (c_best if c_best < float("inf") else c_open)

    # -- the supplier --------------------------------------------------------------------------
    def _value(self, s, th, terms):
        return supplier_value(s["case"], terms, {"standard": th["standard"], "interest_rate": th["p"]["r"]})

    def _allowed(self, th, sheet):
        p = th["p"]
        return not (p["pd_limit"] and (sheet.get("payment_days") or 0) > p["pd_limit"]) and not capped(
            p["vol_cap"], sheet
        )

    def _quote(self, s, th, asked, ask):
        """Our terms at its ask: the levers asked for (cut to its limits), the price that pays it `ask`."""
        p, case = th["p"], s["case"]
        t = {f: asked.get(f, th["standard"].get(f)) for f in levers(case)}
        if p["pd_limit"] and (t.get("payment_days") or 0) > p["pd_limit"]:
            t["payment_days"] = p["pd_limit"]
        if capped(p["vol_cap"], t):
            t["volume_per_year"] = max(o for o in case["term_options"]["volume_per_year"] if o <= p["vol_cap"])
        a = self._value(s, th, {**t, "unit_price": 0.0})
        b = self._value(s, th, {**t, "unit_price": 1.0}) - a
        return {"unit_price": round((ask - a) / b, 2), **t}

    def _answer(self, s, th, msg, sheets):
        case, p = s["case"], th["p"]
        results, files = self._claims(s, th, msg)
        n_ver = sum(r["result"] == "verified" for r in results)
        ok = [t for t in sheets if self._allowed(th, t)]
        best = max(ok, key=lambda t: self._value(s, th, t), default=None)
        ov = self._value(s, th, best) if best else None
        open0, k, was_final = th["opening"], th["round"], th["status"] == "final_offer"
        # never below its floor, whatever the tolerance: a deal at C_best is the only way to score 1
        accepted = lambda ask: ov is not None and ov >= max(th["floor"], ask * (1 - p["tol"]))  # noqa: E731
        extra = " Which volume can you commit to?" if "volume_per_year" in case["negotiable"] else ""
        why = []
        if not sheets:
            reply = self._mail(s, th, th["status"], th["stated"], "We keep our offer." + extra, files)
            why.append("No term sheet: it keeps its offer.")
        elif accepted(th["ask"]):
            reply = self._mail(s, th, "agreed", best, "We agree.", [*files, "quote.pdf"])
            why.append(f"Your sheet is worth {ov:.2f} to it, its ask is {th['ask']:.2f}: it agrees.")
        elif was_final:
            th["pushes"] += 1
            if th["pushes"] >= p["walk_after"]:
                th["closed"] = "walked_away"
                reply = self._mail(s, th, "walked_away", th["stated"], "We end here.")
                why.append(f"You pushed {th['pushes']} time(s) past its final offer: it walks away.")
            else:
                terms = self._quote(s, th, best or sheets[0], th["ask"])
                reply = self._mail(s, th, "final_offer", terms, "Final offer, as before.", [*files, "quote.pdf"])
                why.append("Pushed past a final offer: it repeats it, priced for the terms you asked.")
        else:
            if k == 1:
                drop = (p["first_verified"] if n_ver else p["first"]) * open0
            elif ov is not None and th["last_ov"] is not None and ov - th["last_ov"] >= p["idle_thr"] * open0:
                drop = p["g"] * (ov - th["last_ov"])  # a NEW best offer of ours only: H, L, H pays once
            else:
                drop = p["idle"] * open0
            if ov is not None:
                th["last_ov"] = ov if th["last_ov"] is None else max(th["last_ov"], ov)
            th["ask"] = round(max(th["floor"], th["ask"] - drop), 2)
            if accepted(th["ask"]):
                reply = self._mail(s, th, "agreed", best, "We agree.", [*files, "quote.pdf"])
                why.append(f"It conceded to {th['ask']:.2f} and your sheet now meets it: it agrees.")
            else:
                final = k >= p["final_round"] or th["ask"] <= th["floor"] * p["final_margin"]
                terms = self._quote(s, th, best or sheets[0], th["ask"])
                status = "final_offer" if final else "open"
                reply = self._mail(
                    s,
                    th,
                    status,
                    terms,
                    ("Final offer." if final else "Our counter-offer.") + extra,
                    [*files, "quote.pdf"],
                )
                why.append(f"Ask {th['ask']:.2f} (drop {drop:.2f}); {'final' if final else 'open'}.")
        reply["claim_results"] = results
        s["trace"].append(
            {"round": th["round"], "actor": f"sup:{th['key']}", "move": structured(reply, th["round"]), "reasons": why}
        )
        return reply
