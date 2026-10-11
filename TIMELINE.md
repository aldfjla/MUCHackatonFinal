# Timeline: Tacto Negotiation Arena (Sat 10 Oct 2026)

> **CURRENT CANDIDATE: `better`** (`arena_kit/agents/better_agent.py`, run with `--agent better`).
> Last proven result: **v21 - niko, real practice arena, 10/10 deals, mean 0.70** (P01 0.84, P02 0.67, P03 0.92, P04 0.86, P05 0.77, P07 0.68, P08 0.45, P10 0.67, P11 0.71, P18 0.40), code commit 0a53f83 = tag `better-baseline-v21` (frozen baseline); tag `v21-better-0.70` marks the logged runs.
> **VERIFIED REVISION: bf4fc95 = tag `better-verified-v22`** (v22 - niko regression checks on P02/P03/P08/P10/P11/P18: 0.67/0.92/0.53/0.67/0.71/0.51, none worse than v21; P08 +0.08, P18 +0.11). Submit this one; `better-baseline-v21` is the fallback.
> **DATA RELEASE (Sun 11 Oct, checked 09:15):** package v1.0.0 unchanged (sqlite dump identical); `release-sunday` adds 11 citable IDs (6 news, 4 supplier letters, 1 memo; facts.json sha256 a6fbee11…). Installed at `<ARENA_DATA>/release-sunday`, loader picks it up. v23 - niko: `better` (bf4fc95, unchanged) on the five affected hosted cases P02/P03/P05/P07/P11 = 0.67/0.92/0.77/0.68/0.71, mean 0.75, identical to v21; the agent cited none of the new IDs. No new hosted cases.
> **MERGED origin/v8-petra (Sun 11 Oct ~09:50):** Petra's `combined2` (router better/combined), `combined`, `final`, `listener` and release-aware evidence are in. Her two behaviour changes to shared code (guard no-resend rule, better's wider health band on release distress news) are gated behind `GuardedAgent.RESEND_CHECK` / `BetterAgent.RELEASE_DISTRESS`, default off, switched on only in her chains; `better`/`simplify` are unchanged (mock 0.507/0.466 before and after, evidence claims identical on all 19 practice cases).
> Baseline `simplify`: 0.57 (v14/v16). Mock scores are in-sample and do not prove generalisation; the real runs do.

Use: presentation material and handover if we switch AI agents. Times are commit times. Scores are mean score on real practice cases (0..1) unless noted.

## Goal and rules (short)
- Buyer agent e-mails supplier bots. Score = (C_open - C_deal) / (C_open - C_best), clipped 0..1. Deal worse than opening quote or broken must-have = 0.
- Code freeze and live final: Sunday 12:00. Submit repo + commit hash on ehl.gg. Sunday 08:00 data release: rerun `arena data`.
- Practice quota 450 sessions (about 40 used on probes today). Every run is logged in `backlog.csv` as `v<N> - niko`.

## Timeline
| Time | Step | Result |
|---|---|---|
| 11:42-12:39 | Team setup: Entire tracking, README, shared subagents (`coder`, `reviewer`, `teacher`), manager rules | Workflow: plan, coder, reviewer |
| 14:31-14:56 | Challenge notes (CHALLENGE.md), SETUP.md | Rules and run commands documented |
| 15:26-16:18 | `backlog.csv` created; v0 naive baseline on simulator S01-S03 and real P01, P03, P07 | Baseline: naive closes near opening cost, about 0 |
| 16:07-17:16 | RESOURCES.md tips, Petra's `v1-petra` (SmartAgent), merge | "Always make a deal" rule; research-based tips |
| 17:44-18:00 | Research: 9 more sources, one RESEARCH.md | Evidence base for rules |
| 18:10-18:37 | Agents: Alex's ConfidentAgent; Niko's Patient Hawk (`rational`), SCHOOLS.md, five strategy agents; `Players/Originals/` frozen snapshots | 8+ player agents |
| 19:01-20:08 | Alex merges v1-niko, adds Confident Turtle/Owl and a must-have guard; first 20 real runs logged | `GuardedAgent` around every agent |
| 20:17-20:18 | Niko merges into local `local-alex-niko` (Alex's code as base), SIM_PLAN.md | Combined branch |
| 20:45 | Fetch 19 real practice case files; 20 probe runs (guarded_rational, confident_router) | Real means 0.18 / 0.29 (v11, v12) |
| 21:48 | Diagnosis from replays, then evidence layer (cites only verified data-package facts) | 46+ claims verified, 0 contradicted; mean 0.27 (v13) |
| 22:11 | `reciprocal` agent: steady concessions, closing rule, RFQ rule, index-clause variant, anchor 0.80 | Mean 0.57 (v14); best case 0.67 (P07, P10) |
| 22:23 | Mock arena (fitted to real runs), case generator (30 dev + 30 test), evaluator; 274 tests pass | Free tests, no credits |

## Findings (what the replays showed)
- Suppliers ask for the data behind our claims; cited, checked data helps.
- They match our visible concessions, send `final_offer` after 2-7 rounds (median 4), and walk if pushed past it.
- A soft first anchor (0.90x) is accepted at once: open lower.
- Horizon-2 cases need contract_months >= 12 x horizon; RFQ cases need every supplier worked.
- Longer contract plus an index clause moved some suppliers 6.10 to 5.50.

## Score progression (real practice, 10 cases)
guarded_rational 0.18 -> confident_router 0.29 -> evidence_router 0.27 -> reciprocal_evidence 0.57

Weak cases: P02 (0.18), P18 (0.34), P05 (0.37), P08 (0.42). Mock weak types: raw_material about 0.20, rfq about 0.24.

## Mock arena (honest limits)
- Supplier profile fitted on 40 real runs. Matches our means (0.57 real vs 0.56 mock) but in-sample only: not proof of final performance.
- Anchor 0.80 vs 0.90 in mock: 0.584 vs 0.568 (real set), 0.485 vs 0.466 (dev). Small gap, may be noise.
- Never tune on `gen_test`; use `gen_dev`.

## State and next steps
- Pushed to `v1-niko`: up to e153b9e (evidence layer, v13).
- Local only on `local-alex-niko`: b5537c0 (reciprocal, v14) and a504e3b (mock arena). Not yet pushed.
- Unverified on the real arena: anchor 0.80, RFQ rule, index variant.
- Next: push for Alex; tune raw_material/RFQ on `gen_dev`; 10 more real sessions to confirm; final agent into submission repo.

## Reproduce
- `uv` with `UV_PROJECT_ENVIRONMENT=$HOME/.venvs/arena-agent`; data via `ARENA_DATA`.
- Mock: `python -m arena_kit.evaluate --agents reciprocal_evidence --set dev --seeds 4`.
- Real keys only in `negotiation-arena-kit/starter-kit/.env` (never commit).
