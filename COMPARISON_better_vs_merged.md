# Better vs the merged agents on identical real practice cases (Sun 11 Oct 2026)

All rows are real practice-arena sessions from `backlog.csv` (first row per version and case). Data release
column: `v1.0.0` = package only; `+rel` = package plus `release-sunday` (11 Oct). The release changed no
supplier behaviour: v23 (better) and v9-petra (combined2) reproduced v21/v22 and v8 deal for deal.

| case | final v17-alex (v1.0.0) | listener v5 (v1.0.0) | combined v7 (v1.0.0) | combined2 v8 (v1.0.0) | combined2 v9 (+rel) | better v21 (0a53f83) | better v22 (bf4fc95) | better v23 (bf4fc95, +rel) |
|---|---|---|---|---|---|---|---|---|
| P01 | 0.61 | **0.89** | 0.87 | 0.87 | 0.87 | 0.84 | | |
| P02 | 0.14 | 0.28 | 0.19 | 0.00 | 0.00 | **0.67** | 0.67 | 0.67 |
| P03 | 0.82 | 0.92 | 0.85 | 0.85 | 0.85 | **0.92** | 0.92 | 0.92 |
| P04 | 0.77 | 0.86 | 0.77 | 0.86 | 0.86 | 0.86 | | |
| P05 | 0.46 | 0.48 | 0.72 | 0.77 | 0.77 | 0.77 | | 0.77 |
| P07 | **0.74** | 0.65 | 0.73 | 0.68 | 0.68 | 0.68 | | 0.68 |
| P08 | 0.58 | 0.42 | **0.63** | 0.63 | 0.63 | 0.45 | 0.53 | |
| P10 | 0.63 | 0.66 | 0.64 | 0.67 | 0.67 | 0.67 | 0.67 | |
| P11 | 0.62 | 0.66 | 0.15 | 0.71 | 0.71 | 0.71 | 0.71 | 0.71 |
| P18 | 0.42 | 0.32 | 0.52 | 0.52 | 0.52 | 0.40 | 0.51 | |
| mean (10) | 0.58 | 0.61 | 0.61 | 0.66 | 0.66 | **0.70** | | |

combined2 = better on every case except P08/P18 (routed to combined) and P02 (0.00: deal above the
opening cost once the health term is counted; combined ignores supplier health) and P03 (0.85 vs 0.92,
same reason).

## Where each side wins, and the decision behind it

- **P08 (+0.10 to +0.18 for combined / final)**. Transcripts (sessions fetched by replay id): the supplier
  (70710) answered better's 90/60-day sheets with 5.69@90 / 5.63@30, then 5.61@90 / 5.58@60, final 5.56@90
  (v21) or 5.45@60 (v22). It answered combined's 30-day sheets with 5.40@30, 5.29, 5.24, final 5.21@30. Our
  own steps were the same size. The supplier prices payment days far above our cost model: 30 extra days
  are worth 0.3–0.6 % of C to us, but the supplier's ladder moved 1–3 %.
- **P07 (+0.06 for final v17-alex)**: same pattern. Supplier (70610) 5.60@90 / 5.56@60, final 5.48@60 to
  better; 5.53@30, 5.42, final 5.35@30 to the agent that kept 30 days.
- **P01 (+0.05 for listener)**: 138.1@90 d vs better's 133.6@30 d; the listener kept the tied terms and
  took 90 days. Single run, within noise of the supplier bot.
- **P02, P03 (better +0.67, +0.07)**: supplier-health term. combined/combined2 price packages without it
  and either accept a deal that costs more than the opening (P02 = 0) or stop short (P03).
- **P11 (better +0.56 vs combined v7)**: combined asked for ppm/chargeback that the supplier priced at
  +3.50 a unit; combined2 fixed this by routing P11 to better.

## One transferable improvement to test alone: mirror the supplier's payment term

Observable, not case-specific: the supplier's first term sheet states its payment days. In cases where
supplier health is not at stake, keep that value in every sheet instead of asking for 60/90 days.
Implemented as `BetterAgent.PAY_MIRROR` (default off); agent name `better_pay` = `better` with the flag on.

Expected from the v21 transcripts: gains on P07/P08 (suppliers that price payment days), neutral on
P01/P05/P10/P11 (30 days anyway or not negotiable), unchanged on P02/P03 (health cases keep the C-minimising
payment lever), small possible losses on P04/P18 (suppliers that gave 90 days at almost no premium).
The mock simulator has no payment-day price ladder (only a hard 30-day limit for some suppliers), so it
can only show the downside; the real arena decides.

Caveats: the pattern was found on P07/P08 and every hosted practice case has been played before, so a
real-arena test is a same-case A/B against better v21/v22, not unseen validation.

## Result of the A/B (v24 - niko, 10 real sessions, 11 Oct ~10:40)

| case | better (best v21/v22) | better_pay v24 | deal v24 |
|---|---|---|---|
| P01 | 0.84 | 0.69 | 133.3 @ 14 d |
| P02 | 0.67 | 0.67 | unchanged (health case) |
| P03 | 0.92 | 0.92 | unchanged (health case) |
| P04 | 0.86 | 0.77 | 4.88 @ 30 d |
| P05 | 0.77 | 0.77 | same |
| P07 | 0.68 | 0.69 | 5.42 @ 30 d |
| P08 | 0.53 | 0.49 | 5.45 @ 30 d |
| P10 | 0.67 | 0.67 | same |
| P11 | 0.71 | 0.71 | same |
| P18 | 0.51 | 0.42 | 5.50 @ 30 d |
| mean | 0.72 | 0.68 | 10/10 deals |

**Not promoted.** Mock said +0.03 (real set), neutral on dev and on the reserved-supplier split; the real
arena says −0.035. P08 did not reproduce combined's 5.21: the supplier's final was 5.45 at 30 days, the
same price it gave better at 60 days, so the payment term was not what moved its ladder. P04/P18 lost the
value of the longer payment without any price gain, as predicted. P07 gained 0.01. P01 ended at 14 days
(the supplier's second sheet term) and lost 0.15.

What differed in combined's P08 run besides payment days: one sheet per message (better sends two or
three), no index clause in the first offer, and tiny visible steps (5.04, 5.05, 5.06) after the first anchor.
Which of these moved the supplier is untested; it is the next single-change experiment, not for today.

`PAY_MIRROR` stays in the code, default off, as the record of this test. `better` is unchanged.

## even_better (belief layer + one purposeful move), v25 - niko, 11 Oct ~09:55

`even_better` = better + a per-supplier belief dict (values / refuses / uncertain / resistance, from Petra's
deterministic supplier model) logged with every decision, plus two rules behind flags: ONE_SHEET (one
sheet per message, a conditional trade when the supplier has a currency) and HOLD_ON_RESIST (no price cut
on a repeated price while more than two moves remain). No language model.

Mock ablation (3 seeds): belief-only = better exactly (0.701 dev / 0.507 real); ONE_SHEET −0.03 dev /
−0.06 real; HOLD_ON_RESIST −0.05 dev / −0.03 real; both −0.08 / −0.08; reserved split 0.443 vs 0.526.

Real arena, same ten cases, vs better's best v21/v22 (mean 0.72):

| variant | P01 | P02 | P03 | P04 | P05 | P07 | P08 | P10 | P11 | P18 | mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| belief-only (`even_better_b`) | 0.64 | 0.67 | 0.92 | 0.86 | crash | 0.67 | 0.53 | 0.68 | 0.63 | 0.40 | 0.67 (9) |
| one sheet (`even_better_s`) | 0.64 | 0.21 | 0.92 | 0.81 | 0.77 | 0.70 | 0.53 | 0.69 | 0.63 | n/a (429 rate limit) | 0.66 (9) |

Belief-only changes only the evidence layer's one question and its frozen fields, yet P01 (−0.20), P11
(−0.08) and P18 (−0.11) got worse: the supplier bots answered the clarifying question with a harder
line. P05 crashed with "not a standing offer" (an accept of an offer the arena no longer held, in the
three-supplier RFQ); better has never done that in 50 sessions. One-sheet lost P02 (−0.46: without the
index-clause sheet the health case closed above the C-minimising package).

**Verdict: interpreting replies, as implemented, does not improve outcomes; neither rule does. Not
promoted. `better` unchanged.** Kept in the repo as experimental agents (`even_better`, `_b`, `_s`, `_h`).
