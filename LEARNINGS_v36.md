# Learnings from 100 real sessions (v36 - niko, Sun 11 Oct 2026, 10:45-11:00)

Agent: `better` at tag `better-verified-v35` (005862b). Ten passes over the ten hosted practice cases.
Transcripts: `agent/arena_kit/sim_cases/real_runs_v36_100/b01..b10/`. Rows in `backlog.csv` (`v36 - niko`).

## 1. The arena is deterministic given our moves

All 100 sessions reproduced the same deal per case, to the cent, including P01 which had been a coin flip
before the effective-date lever. Supplier bots do not sample. Consequences for the next two upgrades:

- **One session per experiment is a perfect measurement.** Repeats are wasted quota. Use the quota for
  breadth (many variants, many cases), not repeats.
- A case can be searched: vary one thing in our first message, read the supplier's deterministic reply.

| case | score (10/10 identical) | final_offer at supplier msg # | who set the final price |
|---|---|---|---|
| P01 | 0.884 | 6 | supplier final |
| P02 | 0.672 | never | **we did: supplier agreed to our FIRST sheet at once** |
| P03 | 0.923 | never | supplier's own 90-day sheet (cheapest of its three by C) |
| P04 | 0.860 | 4 | supplier final |
| P05 | 0.772 | never | supplier 70210's own 28.5 |
| P07 | 0.678 | 3 | supplier final |
| P08 | 0.564 | 4 | supplier final |
| P10 | 0.671 | 3 | supplier final |
| P11 | 0.710 | never | supplier's 45.5 |
| P18 | 0.509 | 5 | supplier final |

## 2. Our supplier-health estimate is 3x to 22x too high (biggest lever left)

In the four health cases we price every sheet against our own estimate of the supplier-health charge
(`better_agent._health`, band centre). The arena's actual charge on the same deals:

| case | deal | arena relationship | our estimate | ratio |
|---|---|---|---|---|
| P01 | 135.8 @ 30 d | 3,675 | 12,529 | 3.4x |
| P02 | 364.65 @ 90 d | 18,852 | 51,449 | 2.7x |
| P03 | 432.15 @ 90 d | 965 | 21,116 | 21.9x |
| P10 | 31.6 @ 30 d | 0 | 0 | - |

Effect: in P02 we opened at 364.65 (1.7 % under the ask) because the model said anything lower would hurt
the supplier more than it saves us; the supplier agreed instantly and we sent nine more sheets to a thread
that was already closed. P02 sits 33 % of its span above the best cost. The same inflated term made the
effective-date lever invisible until we excluded health from that choice (v29: +0.19 on P01).

**Upgrade candidate A (highest expected value):** calibrate the health term. Either fit a scale factor
against the arena's own breakdowns (we now have 100+ logged deals with `relationship` values) or replace
the band centre by the arena's formula fitted earlier (P01 130.04 @ 9.6 %, P02 367.60 @ 6.6 % full cost /
interest rate). Then re-run P02 with lower first offers, one session each (deterministic): 360, 355, 350.
Expected: P02 up to +0.3, P01/P03 small gains, P10 unchanged.

## 3. What the suppliers say, and what moves them

Phrase counts over 100 sessions (supplier messages):

- "no further / final" at a fixed message index per supplier (table above); timing never varies.
- Cited data acknowledged in every case ("we checked ... it holds"); P10 adds "but do not affect our
  calculation": evidence does nothing against that supplier's floor.
- Cited data rejected only in P01 and P05 ("we did not know that - a fair point", then a concession): our
  notice-period and energy-index claims are the ones that produce movement. Labour-cost-index claims are
  acknowledged but never named as a reason to move.
- P18 complains about "minor adjustment" (our 0.01-0.06 steps late in the thread) and then holds. Small
  late steps buy nothing there.
- Payment days are mentioned in 100 % of P02 messages and 60 % of P01/P03: the health-case suppliers price
  payment terms explicitly ("30 days requires 135.80").
- The index clause is named in 100 % of P02 and 50 % of P18 messages: those suppliers want the clause;
  without it P02 does not move (v32: 0.30 vs 0.67).

**Upgrade candidate B:** step sizing before the known final-offer index. The final arrives at a fixed
supplier message; our last concession before it is what their final scales from (observed since v14).
Test on P18/P08/P07 (floors reached by small steps): one larger step right before the final message
instead of three small ones, one session per variant. Mock cannot judge this; the arena can, cheaply.

## 4. Things we verified are NOT the problem

- P03: the supplier's 90-day sheet we accepted is the cheapest of its three by full C (14 d: 3,957,745;
  60 d: 3,947,029; 90 d: 3,934,105). No payment-ladder loss there.
- P05 / P11: the supplier's own floor sets the price; our first offers (28.8 / 37.6) are far below it.
- Payment mirror (v24), one sheet per message (v25), no clause sheet in health cases (v32), lead-time lever
  (v32): all lost on the arena, all kept as default-off flags.

## 5. Quota and time

316 sessions used before this batch, 416 after; 184 left before the 14:36 UTC reset. Freeze 12:00.
