# Hollerau buyer agent — Tacto Negotiation Arena (MUC Hackathon, Oct 2026)

A rule-based buyer agent that negotiates multi-issue term sheets with supplier bots by e-mail and is
scored on total cost. Submitted agent: **`better`** (`agent/arena_kit/agents/better_agent.py`).

- **Commit run in the Live Final:** the commit tagged `submission` on branch `v1-niko`
  (agent code verified as tag `better-verified-v35`, commit `005862b`; later commits only add logs and docs).
- Real practice result of that code: mean **0.72** over the ten hosted cases, 10/10 deals, reproduced in
  100 consecutive sessions (`backlog.csv`, rows `v35`/`v36 - niko`).
- No keys in this repo. Secrets live only in an untracked `.env`.

## Setup

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), an arena key from the organisers.

```bash
git clone https://github.com/aldfjla/MUCHackatonFinal.git
cd MUCHackatonFinal/agent
uv sync --all-extras
```

Environment variables (names only; put them in `agent/.env`, which is git-ignored, or export them):

| variable | meaning |
|---|---|
| `ARENA_URL` | arena base URL (`https://arena.tacto.ai`) |
| `ARENA_API_KEY` | the team key |
| `ARENA_DATA` | folder of the unpacked data package (contains `world.sqlite`, `facts.json`) |
| `ARENA_RELEASE` | optional: folder of the Sunday release; found automatically if it sits inside or next to `ARENA_DATA` as `release-sunday` |

No language-model key is needed: `better` is rules only.

Data: `uv run arena data --out data` downloads and unpacks `data/package` and `data/release-sunday`;
then `export ARENA_DATA=$PWD/data/package`.

## Run

```bash
cd agent
uv run arena me                                    # key and quota check
uv run arena play case:P01 --agent better -v       # one practice case
uv run arena run --set practice --agent better     # all hosted practice cases in parallel
uv run arena run --set final --agent better --parallel 10 --waves 5   # the Live Final runner
uv run pytest -q                                   # 474 tests
```

The final runner waits for each wave, plays its cases in parallel, closes 90 s before the cap and resumes
after a crash. Start it before 12:00 and leave it running (`FINAL_RUNBOOK.md`).

## How the agent works (short description)

**Prepares.** Loads the data package once (SQLite + `facts.json`, plus the Sunday release) and, per case,
builds verifiable claims for the supplier at hand: index moves for the part's cost drivers, our last
purchase orders, the should-cost estimate, scorecard delivery rates, competing offers in an RFQ, notice
periods in the contract versus the supplier's letter. Every claim carries the citable IDs the arena checks.

**Reads.** From each supplier reply it takes the standing term sheets, the status (`open`, `final_offer`,
`agreed`), which of our asks the supplier refused or repriced, and whether it says it is short of cash. It
never reads the leaderboard, events or results.

**Decides offers.** Every candidate package is priced with the kit's total-cost function over the case
horizon (price, payment days, lead time, contract length, volume, index clause, supplier health for
strategic categories). The opening offer anchors at 0.80 of the ask (0.90 when supplier health is at
stake) and never above the price we pay today. Each later move matches the supplier's last visible
concession, with a floor on step size, so the thread keeps moving. Each message carries one to three
sheets of equal cost to us that trade a different lever (payment days, contract length, an index clause
when the supplier wants one; never an index sheet in the first message of a leverage case). In price-
increase cases the sheets ask for the latest effective date the case allows. In health cases the price
is chosen on a supplier-specific health estimate with an uncertainty band, and offers must beat the
opening package in the optimistic and central worlds. Must-haves (minimum volume, contract length over
the horizon) are enforced on every sheet by a guard.

**Closes or walks.** It accepts a standing offer when the complete package costs less than the opening
quote and less than the best alternative (the other threads in an RFQ or the fallback price), tested in
the pessimistic world. A `final_offer` that passes is accepted at once, because pushing past it makes the
bots walk. It never walks away while a supplier is alive; on the last move it counters at the supplier's
own price with our must-haves rather than lose the deal. Every decision logs its reason, the package
cost breakdown and the concession history (`result["decisions"]`).

## What else is in the repo

- `backlog.csv` — every run logged (`v<N> - <who>`), with case, costs, score, replay link and notes.
- `TIMELINE.md`, `LEARNINGS_v36.md`, `COMPARISON_better_vs_merged.md` — what was tried, what held.
- `agent/arena_kit/agents/` — `better` plus the earlier and experimental agents (`simplify`, `combined2`,
  `listener`, `even_better`, …); all selectable with `--agent`.
- `agent/arena_kit/evaluate.py` — an offline mock arena fitted to our real transcripts (in-sample only).
- `agent/arena_kit/sim_cases/real_runs_*` — full transcripts of the real practice sessions.

## Team

Niko (agent, evaluation), Petra (listener / combined agents, release handling), Alex (final agent, guard,
first real runs). Built with Claude Code.
