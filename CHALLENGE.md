# Challenge: Tacto Negotiation Arena

Single source of truth for the challenge. Compiled 2026-10-10 from the official kit
(<https://github.com/tacto-ai/negotiation-arena-kit>: `brief/brief.md`, `brief/submission.md`,
`starter-kit/README.md`, `data/README.md`) and the organiser's Discord post.
**Not yet read:** `brief/api.md` (full API) and the contents of `data/`. Check the originals before relying on any detail here.

> **Status: candidate project, not yet chosen.** Never put the arena key, `.env` or any LLM key in this repo (the repo is public).

## 1. The task in one paragraph

Build an **AI buyer agent** for a fictional German pump maker (Hollerau Pumpenwerke, ~45 suppliers). It reads the
company's data, negotiates **by e-mail** against supplier bots, and **accepts one supplier term sheet or walks
away**. Score = **total cost in EUR**, not unit price. Practice all weekend; the **Live Final** (Sun 12:00) runs
on hidden cases against unseen suppliers. Bring your own LLM; Tacto runs the suppliers.

## 2. Key dates and links

| When | What |
|---|---|
| Sat 12:00-13:00 | Deep dive, ground floor. **Challenge selection closes 13:00.** |
| Sat afternoon | Office hours at the Tacto table; Discord until 23:00 |
| Sun 08:00 | **Second data release.** Run `uv run arena data` again; hidden cases may cite it |
| Sun 09:00 | Pre-flight: one practice case through the final setup |
| Sun 11:30 | Checklist (section 8) |
| **Sun 12:00** | **Code freeze + Live Final** (5 waves x 8 min, all teams at once). Submit on **ehl.gg** |
| Sun 13:00-14:30 | Top 10 pitch: 5 min + 2 min questions |
| Sun 14:30 / 15:30 / 16:30 | Winners announced / Grand Final pitches (AudiMax) / Awards |

Links: [arena](https://arena.tacto.ai) · [apply for key](https://arena.tacto.ai/apply) · [practice board](https://arena.tacto.ai/live) · [results](https://arena.tacto.ai/results) · [Discord](https://discord.gg/hPwFfbWRV) · [kit repo](https://github.com/tacto-ai/negotiation-arena-kit)

**Prizes:** 1st place EUR 1,500, medals for top 3, best 2 EHL finalist teams go to the Grand Final.
How the Live Final score and jury score combine is **still undecided** (placeholder in the brief, "decided Sat morning"). Ask on Discord.

## 3. Getting the key (one per team)

1. Apply at `arena.tacto.ai/apply` (team name + contact e-mail; a name starting with one emoji shows on the big screen).
2. Show the match code at the Tacto desk.
3. Copy the key. **It is shown once.** Lost it: organisers reset it at the desk.
4. Put it in `.env` as `ARENA_API_KEY=...`. Never post or commit it.

Only **one person** should hold the team key. Share it privately, not in git, chat threads or Discord.

## 4. How a negotiation works

- A **case** = one negotiation (trigger such as a price-increase letter, expiring contract or RFQ + case file + 1-3 supplier bots).
- Round 0: suppliers send a quote e-mail with a quote PDF.
- Your message: subject, body, **up to 3 term sheets** (only term sheets bind), data IDs you rely on, optional text attachments.
- Supplier replies with a status: `open`, `final_offer` (push further and it may walk), `agreed` (you still have to accept), `walked_away`, `no_bid`.
- **Only you close a deal**, by accepting a supplier's standing term sheet. In RFQ cases 2-3 suppliers run in parallel; accepting one ends the case.
- **Limits:** 10 messages per thread (default), **60 s per message** from the supplier's reply. Late = your last offer repeated and supplier patience drops; 3 in a row ends the thread. Supplier replies can take up to ~1 min (not counted against you).
- **Unstated terms default to the supplier's standard terms** in its quote PDF. Read the PDF before accepting.
- Supplier behaviour: never sells below cost floor; bigger moves need boss approval; cited data is checked by ID; reacts to tone and what you signal; "padding does not buy price". Suppliers differ (family foundry, group with approval ladder, cash-short job shop, near-monopolist).

## 5. Scoring

- Only the accepted term sheet scores: **total cost C** of covering a fixed need over a fixed horizon (price, uncovered need at fallback price + risk, payment-term interest, freight, lead time, quality/PPM, index clause, and supplier-health margin for `stabilise`/`secure_supply` goals).
- **Case score = (C_open - C_deal) / (C_open - C_best)**, clipped to 0..1. `C_open` = best opening quote; `C_best` = best package any supplier would ever accept (hidden) or your alternative.
- No deal scores your alternative (0 if none). **A broken must-have scores 0.** Some cases are best left without a deal.
- Final: each wave 0-100 (mean case score x 100); up to **500 points** over 5 waves.
- Category goals: `stabilise`, `secure_supply`, `quality_first`, `leverage`, `routine`.
- Use `arena_kit.total_cost` to compute C for every term sheet. Formula is in `api.md`.
- Worked example in the brief: asking EUR 43.20/30 days, deal EUR 41.60/60 days, best 40.80/90 days gives score 0.64. A 12-month deal that covers half the need can score 0.

## 6. Data (what the agent mines)

Data package v1: CSV + `world.sqlite` + `facts.json` + contracts + letters/e-mails/notes. Key tables: suppliers (447),
parts (60), price_conditions, negotiation_history, contracts + clauses, po_lines, goods_receipts, invoices,
quality_notifications, scorecards, forecasts, rfqs/quotes, spend_cube, index_series/index_values (real public
market series), cost_drivers, should_cost, news, documents. Company "today" is **2026-09-30**.

- Every citable fact has an ID: `<type>:<id>[@period]`, e.g. `po:4500010001-10`, `idx:PPI-C2451@2026-08`, `sc:70110@2026Q3`, `ctr:4600070110#3.1`.
- Reply marks each cited claim `verified`, `contradicted` (wrong figure/unknown ID, **costs trust**), `irrelevant` or `duplicate`.
- **True data is not automatically rewarded.** Read the supplier's situation (notes, letters, news, quote remarks) and find the trade it wants (a cash-short supplier may value payment days more than price).
- Some notes are noise. Sunday 08:00 release adds news, letters and a memo.
- Download: `uv run arena data` or `https://arena.tacto.ai/v1/data/package.zip`.

## 7. Rules

- **No human in the loop** during the Live Final. Start the agent before 12:00 and leave it running.
- The agent **must not read** `/v1/events`, `/screen`, `/leaderboard`, `/results` (or their JSON) during the Final. `arena board` is for humans only.
- One API key per team. No attacks on the service or other teams.
- One attempt per case in the final. Everything else counts, including weaknesses found in the bots; replays are open to the jury.
- Max 10 open sessions per key. Client limit ~10 calls/s.
- A supplier remembers only within a case.
- Up to **one third of hidden cases combine supplier/case types practice never shows**. Memorising practice suppliers will not work.

## 8. Practice and tooling

- **Quota:** 200 practice sessions per team per rolling 24 h (`uv run arena me` shows usage). Plan runs.
- Needs Python 3.12, [uv](https://docs.astral.sh/uv/), git.

```bash
git clone https://github.com/tacto-ai/negotiation-arena-kit.git
cd negotiation-arena-kit/starter-kit
cp .env.example .env              # add ARENA_API_KEY (and the LLM provider settings)
uv sync --all-extras
uv run arena me                   # team + quota
uv run arena play case:P01 -v     # naive agent, one practice case; prints score + replay link
uv run arena data                 # download data (rerun Sun 08:00)
uv run arena play case:P01 --agent llm -v
uv run arena run --set practice --agent llm --parallel 8
uv run arena board                # practice leaderboard (humans only)
```

- **No key yet:** `arena-sim` runs the API locally (one plain scripted supplier; teaches the API contract, not real supplier behaviour).
- **LLM:** `LLM_PROVIDER=anthropic` (needs `ANTHROPIC_API_KEY`) or `openai` for any OpenAI-compatible endpoint. Must answer within 60 s: use a fast model, do heavy research before opening a session. Tacto says a small cheap model is enough; reading the data matters more.
- **MCP server over the data:** `uv run arena mcp --data <path>` (6 read-only tools) lets Claude Code query the data.
- Own agent = any object with `decide(case, threads) -> {"supplier_id": ..., "message": {...}}`. Kit helpers: `total_cost`, `complete_offer`, `standard_terms`, `play`, `play_waves`.
- Kit's final runner: `uv run arena run --set final --agent llm --parallel 10`. It waits for each wave, closes cases 90 s before the cap, and resumes after a crash.

## 9. Submission (ehl.gg, by Sun 12:00)

1. **Repo** with the agent and a README to run it (setup, env var names without values, command). Include the **commit hash** run in the final. Jury and tum.ai (runs a code agent over submissions) must be able to open it. **No keys in the repo.**
2. **Short description:** how the agent prepares, what it reads, how it decides offers, when it closes or walks.
3. **Slides** for the pitch (top 10 only present).
4. Do not push after the freeze; the top 10 are checked for it.

**Checklist for 11:30:** final machine and network tested at the 09:00 pre-flight; `arena data` rerun after 08:00; `arena me` works; LLM credits and rate limits for ~1 h of parallel play; runner started and logging to a file; laptop on power, sleep disabled.

## 10. Pitch

5 min + 2 min questions. Walk the jury through one replay. Expected questions: Why did your agent write that? Would it work on a real supplier? What did it learn about suppliers, and from where? Draft jury criteria: approach, explainability, craft (not final).

## 11. Strategy notes (from the brief's tips)

- **Numbers come from code, the model writes.** Compute C for every term sheet; LLM picks arguments and wording.
- Read the supplier before arguing; read the quote PDF before accepting.
- Send 2-3 term sheets to learn what a supplier values; ask the roles (engineering, finance, quality) the right questions.
- Don't leak urgency, a budget or a missing alternative. Don't take the first offer.
- The kit's LLM agent is a **starting point, not a winner**. It only sees what the case file points to.
- Refuse bad accepts; fall back to a safe move if the model times out.
- Consider building our own supplier simulator from the public data to test against.
- Rehearse the final: all hosted cases in parallel from the final machine, well inside 8 minutes.

## 12. Open questions / risks

- How final score and jury score combine for places 1-3 (undecided in the brief).
- `api.md` not yet read here; `data/` contents not yet explored.
- Wave themes are revealed on the day. The host may extend a wave cap.
- Practice quota (200/24 h) limits brute-force tuning.
- Key handling in a public repo: use `.env` (listed in the root `.gitignore`) and a secrets check before every push.

## 13. Suggested team split (maps to our subagents)

| Role | Owner | Job |
|---|---|---|
| Manager | main session / team lead | plan, assign, track the freeze deadline |
| `coder` | build agent | strategy module, cost pricing, term-sheet logic |
| `reviewer` | check agent | review diffs, hunt key leaks and unsafe accepts |
| `teacher` | explain | explain data and code to teammates |
| Data analyst (human) | mine the data | which index/clause/note moves which supplier |
| Pitch (human) | slides and replay walkthrough | |

## 14. From the arena website (arena.tacto.ai, snapshot Sat 10 Oct, build phase)

Pages: `/` overview, `/apply` key flow, `/live` practice board, `/results` final standings (empty until wave 1), `/faq`.

**Practice board (22 teams, 12 active in the last hour at snapshot).** Best team mean was 0.68; most teams had met 1 of 10 suppliers. Nobody had beaten Tacto's **house agent** on any of the 10 bots.

| Case | Type | Supplier | House agent | Best team |
|---|---|---|---|---|
| P01 | Price increase | Brandlhuber (family foundry, +9.5% volute casings) | 0.97 | 0.93 |
| P02 | Price increase | Nordmark (copper pass-through, 7.5 kW motor) | 0.74 | none |
| P03 | Renewal | Selvbrunn Drive Systems (frequency converter) | 0.92 | 0.90 |
| P04 | Renewal | Wälzlager-Zentrum Süd (ball bearing 6306) | 0.86 | none |
| P05 | RFQ (3 bidders) | Dralveck / Hrvelec / Fuchsreiter (pump shaft) | 0.56 | 0.36 |
| P07 | Bundling | Schraubenhandel Leitner (fastener kit) | 0.78 | 0.74 |
| P08 | Raw material | Edelstahl-Service Donautal (1.4404 bar) | 0.75 | none |
| P10 | Capacity | Ravensteiner (seal allocation cut) | 0.69 | 0.45 |
| P11 | Quality | Kalwisz (bearing brackets in red) | 0.31 | none |
| P18 | Raw material | Blankstahl Werdenfels (1.4404 bar) | 0.39 | none |

Takeaways: the house agent scores 0.31-0.97, so quality and capacity cases (P11, P18, P10) are hardest. Beating the house agent is a visible goal. Sandbox cases `case:D01`, `case:D02` do **not** count against the 200/day quota.

**FAQ highlights**
- **Ranking is by points, not euros.** Every case weighs the same; "EUR saved" is a side number (mention it in the pitch). Ties: more deals, then fewer rounds.
- **Nothing to deploy.** The agent is an API client; no server or public URL. Real suppliers exist only on arena.tacto.ai. For the final, **a cloud VM is safer than a laptop on venue Wi-Fi.** Tacto does not run our code; we run the submitted commit ourselves.
- **Tokens are cheap.** Math in code (`total_cost`), prepare a cached dossier per supplier, use a strong model for the plan and a small one for writing, any OpenAI-compatible endpoint (even local Ollama) works. Max 10 of our messages per supplier by default.
- **Worked replay (P01, Brandlhuber):** the agent cited a real index (`idx:PPI-D351@2026-08`, electricity -3.7%) and a should-cost (`cost:310010`), offered faster payment as a trade, and closed at EUR 134.50, 30 days, from 1 Jan 2027, **score 0.76**, about EUR 43,500 saved. The same index argument sent as an ultimatum got EUR 136.50 from November: roughly EUR 13,700 a year worse. **Tone and trades beat threats.**
- A deal that covers only part of the need (for example 12 months instead of 24) can score 0 even at a lower unit price.

**Privacy:** contact e-mail on `/apply` is visible only to organisers and deleted after the event.
