# Combined agent (v6-petra)

Rules-only buyer agent (no language model, zero token cost). It combines Alex's final agent (visible, reciprocal price steps) with Petra's listener (reads what the supplier can and cannot move). Branch `v6-petra`, code in `agent/arena_kit/agents/combined.py`.

Run:
```bash
cd agent
uv run arena play case:P01 --agent combined --data <data folder with world.sqlite> -v
```
The data folder must contain `world.sqlite`, otherwise the evidence layer is off (the agent warns at start).

## What it does

It negotiates a supplier's term sheet down to the lowest total cost it can get, closes a valid deal in every case it can, and never accepts a deal that breaks a must-have or is worse than the alternative or the opening quote.

## How it works

Layers, from the outside in:

| Layer | File | Job |
|---|---|---|
| Game loop | `play.py` | Talks to the arena; answers all supplier threads at once (RFQ cases) |
| Evidence | `agents/evidence.py`, `evidence.py` | Rewrites the e-mail: up to 3 facts checked against the data package, one question aimed at the supplier's main interest |
| Guard | `guard.py` | Every sheet meets the must-haves; no resent sheets; a crash or walk-away becomes a safe counter |
| Strategy | `agents/combined.py` | Decides price, terms and when to close (below) |
| Supplier model | `listener.py` | Reads the thread: hard limits, frozen terms, the supplier's "currency" (what it cares about most), offers written only in the e-mail text, refused asks |
| Cost | `cost.py` | `total_cost` prices every sheet with the arena's scoring formula |

Each turn:
1. **Listen.** Update the supplier model from its latest e-mail and term sheet.
2. **Choose the mode.**
   - Supplier still moving, no hard price limit: Alex's visible step. Open at 80 % of their price (never under 75 %), then close 25 % to 50 % of the gap each round, at least 1 % of price, staying 3 % away until the last two messages.
   - Real limit ("no further concessions", same price twice, capacity full, payment fixed): hold our price and switch to non-price packages that trade the supplier's currency (payment, contract length, volume, lead time, index clause).
3. **Build 2 sheets** (main + variant or currency package) and clean them: frozen terms stay at the supplier's value; no faster payment than the supplier offered (unless it asked and it saves at least 0.3 %); a price stays paired with the terms the supplier tied it to; the supplier's effective date is kept; never a sheet sent before; never worse than the opening quote or the alternative.
4. **Close.** Take the cheapest valid sheet across all live suppliers. An acceptable final offer is accepted at once (suppliers walk after a push). An unacceptable final offer gets one try at their price with cheaper non-price terms (for example P07: same price, 24 months). Never walks away while a supplier is still in the case.
5. **Guard, then evidence**, then send.

## Last 10 real practice runs (2026-10-11, v6-petra)

| Case | Type / goal | Score | Saved vs opening (EUR) | Gap to best (EUR) | Deal |
|---|---|---|---|---|---|
| P01 | price increase / stabilise | 0.87 | 49,369 | 7,595 | 133.30, 30 d, 12 m |
| P02 | price increase / stabilise | 0.20 | 9,377 | 37,977 | 350.85, 90 d, 12 m |
| P03 | renewal / stabilise | 0.85 | 286,394 | 50,877 | 429.22, 30 d, 24 m |
| P04 | renewal / routine | 0.77 | 1,775 | 542 | 4.88, 30 d, 24 m |
| P05 | RFQ, 3 suppliers / leverage | 0.72 | 59,446 | 22,675 | 28.97, 30 d, 24 m, lead 28 d |
| P07 | bundling / routine | 0.73 | 67,255 | 24,531 | 5.36, 30 d, 24 m |
| P08 | raw material / leverage | 0.54 | 94,455 | 81,123 | 5.48, 90 d, 24 m |
| P10 | capacity / secure supply | 0.64 | 385,973 | 217,592 | 32.00, 24 m, 23,400 pc, lead 56 d |
| P11 | quality / quality first | 0.15 | 13,992 | 81,086 | 49.00, 60 d, 12 m, 300 ppm |
| P18 | raw material / leverage | 0.42 | 30,389 | 42,133 | 5.50, 30 d, 24 m |
| **Total** | | **mean 0.59** | **998,423** | **566,131** | 10 of 10 deals |

Comparison on the same 10 cases (one run each): listener v5-petra 0.61, Alex's final v17 0.58, Evidence Router v13 0.27.

### Findings
- **Reliable closing.** 10 of 10 deals and no must-have breaks; it saved about EUR 1.0 M against the opening quotes.
- **Strong where suppliers keep moving:** P01, P03, P04, P05, P07 score 0.72 to 0.87. The RFQ case P05 (0.72) gained most from answering all three suppliers at once (listener alone: 0.48).
- **Weak spots (gap to best):**
  - **P10** (EUR 218k): the supplier only gives the needed volume on 24 months with a longer lead time; the agent closed near their price.
  - **P11** (EUR 81k): accepted 49.00 with 300 ppm; the listener reached 45.50 on the same case. The quality trade (ppm) is probably over-valued or accepted too early. Needs a replay check.
  - **P08, P18, P02** (raw material / price increase, EUR 38k to 81k): the index clause is not yet used as a lever; P02 and P08 still end on 90-day payment.
- **Noise:** one run per case; differences under about 0.05 between agents may be chance.

### Next steps
1. Check the P11 replay and fix the early accept (expected mean about 0.64 if P11 returns to about 0.6).
2. Use the index clause in raw-material and price-increase cases.
3. Re-run each case 2 to 3 times before the final to separate skill from luck.
