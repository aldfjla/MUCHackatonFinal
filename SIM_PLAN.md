# Plan: a varied mock of the arena (no credits used)

Goal: test our players on many different cases, so they cannot memorise the 10 hosted practice cases and still do well on the hidden final cases. Status: **plan only, nothing built yet.**

## What is verified (sources: `negotiation-arena-kit/brief/api.md`, the data package, our `arena_kit/sim.py`)

- `GET /v1/cases?set=practice` returns every practice case file in full, including the `buyer` block (need, fallback price, interest rate, goal, must-haves, alternative). `?set=sandbox` returns D01 and D02. These calls open no session and use none of the 200 practice sessions. Only `POST /v1/sessions` counts.
- Sandbox sessions (D01, D02) do not count against the quota and have no leaderboard.
- Each case lists `refs` and `facts` that point into the data package, so cases can be tied to real rows.
- Data package (`negotiation-arena-kit/data/`, 8.2 MB, fictional company Hollerau Pumpenwerke, real public market indices): 447 suppliers (46 detailed), 60 parts, 108 quotes in 47 RFQs, 300 past price events (`negotiation_history`: asked % vs settled %), 414 scorecards, 46 contracts, 208 letters/notes, index series.
- Our local simulator (`agent/arena_kit/sim.py`, `sim_cases/S01-S03`) speaks the real API but its supplier is one fixed script (opens 10% above, concedes 2% per sheet to 90%, price-only final offer from round 5). The scoring code in `arena_kit/cost.py` is the arena's own.

## What cannot be recovered

- The real suppliers' hidden floors and exact behaviour. Replays hide their figures (shown as an ellipsis).
- The hidden final cases and the Sunday 08:00 data release.
- So mock results only partly predict the final. Treat them as a robustness test, not a score forecast.

## Steps

1. **Fetch** the practice and sandbox case files (read-only, 0 sessions) and save them under `agent/arena_kit/sim_cases/real/`. Never commit the API key.
2. **Compare** each case's fields and refs with the data package; note which buyer fields are not in the data (fallback price, rates, goal), because those must be copied or varied from real case files, never invented.
3. **Generator:** build new cases from real supplier/part pairs in the data. Vary need, fallback price, rates, goal, must-haves, alternative, quote values and case type (price_increase, renewal, rfq, bundling, raw_material, capacity, quality). The existing scoring recomputes `c_open` and `c_best`.
4. **Supplier model:** replace the fixed script with parameters (opening premium, concession rate, floor, final-offer round), with ranges taken from `negotiation_history` (asked vs settled) and from the replays. Randomise per seed.
5. **Split** the generated cases into a development set (tune on it) and a held-out test set (each agent scored on it once, never tuned on).
6. **Evaluate** all eight players (`Players/Originals/`) over many seeds; rank by the mean across seeds and by the worst case, not by one case.
7. **Guard against hard-coding:** agents must read case fields, never case IDs; a test greps the agents for case-ID strings.
8. Log results in `backlog.csv` (version format `v<N> - <name>`).

## Optional real-API use (needs the owner's approval each time)

- Sandbox runs (D01, D02): free, suggested 5-10 to see real supplier reactions.
- Practice replays: suggested 20 sessions in total (10 with the naive agent, one per hosted case; 10 with Patient Hawk). Gain is steep for the first 10, smaller for the next 10, and flat after that, because only 10 cases are hosted. Not verified: whether suppliers are random; if a rerun differs, extra runs only measure that noise.
- 3 of 200 sessions are used so far (real practice P01, P03, P07). The quota resets on a rolling 24 h.

## Workflow

Follow `CLAUDE.md`: plan first, `coder` writes code, `reviewer` checks every change, tests in `agent/tests/`.
