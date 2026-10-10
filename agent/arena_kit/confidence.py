"""Confidence index: how much room is left to push a supplier before it walks (1.0 plenty, 0.0 close now).
Stateless: recomputed from the thread every turn, so it survives a crash and resume."""

import math

from .cost import total_cost
from .play import latest, moves_left

TINY_MOVE = 0.002  # a supplier move of at most this share of the opening cost is "tiny"
TINY_PENALTY = 0.45  # last concession tiny: the supplier is near its floor
SHRINK_PENALTY = 0.2  # last concession under half the previous one
PHRASE_PENALTY, PHRASE_CAP = 0.15, 0.45  # per floor phrase in the latest body, and the cap for all
TRUST_PENALTY, TRUST_CAP = 0.15, 0.3  # per contradicted claim, and the cap
TIMEOUT_PENALTY, TIMEOUT_CAP = 0.1, 0.3  # per timeout of ours: our fault, not a floor signal; and the cap
VALIDITY_PENALTY = 0.1  # the offer's validity shrank since the opening
DELAY_PENALTY = 0.05  # the supplier's reply delay grew since the opening
FLOOR_PHRASES = [
    "final offer", "last offer", "our last", "can't go", "no further", "no room", "below cost", "cost floor",
    "take it or leave", "end here", "last word", "letztes angebot", "nicht möglich", "endgültig",
    "unter unseren kosten", "keinen spielraum",
]  # fmt: skip


def _sheets(case, events, standard):
    """(message, cost) of each supplier message that carries a priced term sheet."""
    out, prev = [], None
    for m in events:
        sheets = m.get("term_sheets") or []
        if m.get("from") in ("buyer", "arena") or not sheets or sheets[0]["terms"].get("unit_price") is None:
            continue
        sheet = sheets[0]
        same = prev is not None and (
            sheet.get("term_sheet_id") == prev.get("term_sheet_id")
            if sheet.get("term_sheet_id") and prev.get("term_sheet_id")
            else sheet["terms"] == prev["terms"]
        )
        if not same:  # a re-sent standing sheet is not a move
            out.append((m, total_cost(case, sheet["terms"], standard)))
            prev = sheet
    return out


def confidence_report(case, events, standard=None):
    """{"score": 0..1, "parts": {name: value}, "notes": [str]}; each part is what it added to 1.0."""
    standard = standard or {}
    last = latest(events)
    status = last.get("status")
    parts, notes = {}, []
    if status in ("final_offer", "agreed", "walked_away", "no_bid"):
        notes.append(f"supplier status {status}: no room" if status != "agreed" else "supplier agreed: close it")
        return {"score": 0.0, "parts": {"status": -1.0}, "notes": notes}
    parts["status"] = 0.0

    sheets = _sheets(case, events, standard)
    parts["concession"] = 0.0
    if len(sheets) >= 2:
        costs = [c for _, c in sheets]
        ref = costs[0]
        moves = [(a - b) / ref for a, b in zip(costs, costs[1:], strict=False)] if 0 < ref < math.inf else []
        if not moves:
            pass
        elif moves[-1] <= TINY_MOVE:
            parts["concession"] = -TINY_PENALTY
            notes.append(f"last concession {moves[-1] * 100:.1f}% of opening: near its floor")
        elif len(moves) >= 2 and moves[-1] < moves[-2] / 2:
            parts["concession"] = -SHRINK_PENALTY
            notes.append("concessions shrinking")

    body = (last.get("body") or "").lower()
    hits = [p for p in FLOOR_PHRASES if p in body]
    parts["wording"] = -min(PHRASE_CAP, PHRASE_PENALTY * len(hits))
    notes += [f"wording: '{p}'" for p in hits]

    bad = sum(r.get("result") == "contradicted" for m in events for r in m.get("claim_results") or [])
    parts["trust"] = -min(TRUST_CAP, TRUST_PENALTY * bad)
    if bad:
        notes.append(f"{bad} contradicted claim(s)")

    timeouts = sum(m.get("from") == "arena" for m in events)
    parts["timeouts"] = -min(TIMEOUT_CAP, TIMEOUT_PENALTY * timeouts)
    if timeouts:
        notes.append(f"{timeouts} timeout(s)")

    parts["signals"] = 0.0
    first = next((m for m in events if m.get("from") != "buyer"), last)
    now, then = last.get("signals") or {}, first.get("signals") or {}
    if now.get("validity_days") is not None and then.get("validity_days") is not None:
        if now["validity_days"] < then["validity_days"]:
            parts["signals"] -= VALIDITY_PENALTY
            notes.append("validity shrinking")
    if now.get("reply_delay_days") is not None and then.get("reply_delay_days") is not None:
        if now["reply_delay_days"] > then["reply_delay_days"]:
            parts["signals"] -= DELAY_PENALTY
            notes.append("replies slowing")

    score = max(0.0, min(1.0, 1.0 + sum(parts.values())))
    limit = case.get("round_limit", 10)
    factor = min(1.0, 0.5 + 0.5 * moves_left(case, events) / limit) if limit > 0 else 1.0
    parts["rounds"] = factor
    if factor < 1.0:
        notes.append(f"rounds factor {factor:.2f}")
    return {"score": max(0.0, min(1.0, score * factor)), "parts": parts, "notes": notes}


def confidence(case, events, standard=None):
    return confidence_report(case, events, standard)["score"]
