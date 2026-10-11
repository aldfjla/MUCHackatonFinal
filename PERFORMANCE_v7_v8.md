# Performance analysis: v7-petra vs v8-petra (2026-10-11, overnight run)

20 real practice sessions in total (quota 154 -> 174), 10 per version, one run per case, full data package (evidence on in every run).

| Version | Branch | Agent | What it is |
|---|---|---|---|
| v7-petra | `v7-petra` | `combined` | Alex's final agent + Petra's listener, index clause only when `total_cost` says it is cheaper |
| v8-petra | `v8-petra` | `combined2` | Router: `combined` for cases with a negotiable index clause and no supplier-health stake, Niko's `better` agent for everything else; merges `v1-niko` and `v7-petra` |

Run: `cd agent && uv run arena play case:P01 --agent combined2 --data <folder with world.sqlite>`.

## Results

| Case | Type / goal | v6 combined | **v7** | **v8** | Route (v8) | Niko `better` v21 |
|---|---|---|---|---|---|---|
| P01 | price increase / stabilise | 0.87 | 0.87 | 0.87 | better | 0.84 |
| P02 | price increase / stabilise | 0.20 | 0.19 | **0.00** | better | 0.67 |
| P03 | renewal / stabilise | 0.85 | 0.85 | 0.85 | better | 0.92 |
| P04 | renewal / routine | 0.77 | 0.77 | **0.86** | better | 0.86 |
| P05 | RFQ / leverage | 0.72 | 0.72 | **0.77** | better | 0.77 |
| P07 | bundling / routine | 0.73 | 0.73 | 0.68 | better | 0.68 |
| P08 | raw material / leverage | 0.54 | **0.63** | **0.63** | combined | 0.45 |
| P10 | capacity / secure supply | 0.64 | 0.64 | **0.67** | better | 0.67 |
| P11 | quality / quality first | 0.15 | 0.15 | **0.71** | better | 0.71 |
| P18 | raw material / leverage | 0.42 | **0.52** | **0.52** | combined | 0.40 |
| **Mean** | | 0.59 | **0.61** | **0.66** | | 0.70 |
| Deals | | 10/10 | 10/10 | 10/10 (P02 scores 0) | | |

Excluding P02, v8 averages 0.73, the best result the team has on these cases.

## What changed and what it did

**v7 (index rule).** Our sheets only carry an index clause when it lowers `total_cost`. P08 +0.09 and P18 +0.10 (the suppliers accepted lower prices, with their own index clause). Everything else unchanged. Mean 0.59 -> 0.61.

**v8 (router).** Porting `better`'s health estimate directly into `combined` made it worse in the mock (0.39), so v8 routes whole cases instead. Gains came where `better` is strong: P11 0.15 -> 0.71 (no longer pays extra for quality terms), P04 +0.09, P05 +0.05, P10 +0.03. P08 and P18 kept the v7 gains via the combined route. Mean 0.61 -> 0.66.

## The P02 failure (the main open problem)

`better` accepted the supplier's final offer at 345.51, 30 days, **with a copper index clause (3 % deadband)**. The arena priced that deal at 2,291,903, which is **9,035 more than the opening quote** (2,282,867), so the score is 0. Our local `total_cost` judged it acceptable.

Cause: our local cost model undervalues the index clause in P02 compared with the arena. Earlier the same case showed a gap of about EUR 125k between our calculation and the arena's for an index deal. Copper rose 47.7 % in the supplier's cited index, so the arena's index path and risk make the clause expensive. Niko's code has an `INDEX_PREMIUM` switch, off by default.

Suggested fix (not applied, needs testing): never accept or offer a sheet with an index clause unless a version **without** the clause is also within the opening cost, or price index clauses with a risk margin (turn on `INDEX_PREMIUM` for rising indices). This alone would have kept P02 near 0.2–0.67.

## Remaining gaps (EUR left to best, v8)

P10 is still the largest in money (capacity case, about EUR 200k). P02 (index valuation), P18 and P08 (raw material, about 8–16 % above the best price) are next. All of them are mainly price, not package mix.

## Caveats

- One run per case. Differences under about 0.05 can be chance; the routed cases repeated their earlier real scores almost exactly, which suggests the suppliers are fairly deterministic.
- The router rule (index negotiable and no health stake -> combined) is fitted on 10 cases. Unseen case types default to `better`.
- The local mock arena ranks agents differently from the real arena, so decisions here rest on real runs.

## Recommendation for the final

Use `combined2` from `v8-petra`, after fixing the P02 index-clause accept (and re-testing P02 once). Without that fix, `combined2` still has the highest mean on the other 9 cases.
