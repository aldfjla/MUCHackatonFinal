# Setup and playing guide (Tacto Negotiation Arena)

How to install the starter kit, play games, and where to change the agent.
Challenge details (rules, scoring, dates) are in [CHALLENGE.md](CHALLENGE.md).
Sources: starter-kit README <https://github.com/tacto-ai/negotiation-arena-kit>, FAQ <https://arena.tacto.ai/faq>, and a local test run on 2026-10-10.

**Never commit `.env`, the arena key or any LLM key.** This repo is public. The root `.gitignore` blocks `.env`.

## 1. Install (once per person, about 5 minutes)

Needs git and [uv](https://docs.astral.sh/uv/) (uv installs Python 3.12 itself).

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh        # installs uv to ~/.local/bin
export PATH="$HOME/.local/bin:$PATH"                   # or open a new terminal
git clone https://github.com/tacto-ai/negotiation-arena-kit.git
cd negotiation-arena-kit/starter-kit
uv sync --all-extras
```

Tested on macOS (Apple silicon): uv 0.13.0, kit cloned and synced without errors.

## 2. Play offline first (no key, no quota, no LLM cost)

The simulator speaks the arena's API with one plain scripted supplier. It teaches the API, **not** how the real suppliers behave.

Terminal 1:

```bash
cd negotiation-arena-kit/starter-kit
uv run arena-sim serve --no-clock        # http://127.0.0.1:8000
```

Terminal 2:

```bash
cd negotiation-arena-kit/starter-kit
export ARENA_URL=http://127.0.0.1:8000
uv run arena register "My Name" sim      # prints a simulator-only api_key
export ARENA_API_KEY=<the api_key>
uv run arena cases                       # list cases (simulator has S01-S03)
uv run arena play case:S01 -v            # naive agent plays one case
```

Output: deal terms, `c_open`, `c_deal`, `c_best`, the score (0 to 1) and a replay link, for example `http://127.0.0.1:8000/replay/sim1`. Our first test run scored **0.52** on `case:S01` (deal at EUR 16.59, 60 days).

## 3. Play the real arena (needs the team key)

1. One person applies at <https://arena.tacto.ai/apply>, shows the match code at the Tacto desk, copies the key (shown once).
2. Create `starter-kit/.env` from `.env.example` and fill in:
   - `ARENA_URL=https://arena.tacto.ai`
   - `ARENA_API_KEY=` the team key
   - `ARENA_DATA=data/package`
   - the LLM settings (section 4)
3. Run:

```bash
uv run arena me                                  # team + practice quota (200 per rolling 24 h)
uv run arena data                                # download the data package (rerun Sun 08:00)
uv run arena play case:P01 -v                    # naive agent, practice case P01
uv run arena play case:P01 --agent llm -v        # LLM agent
uv run arena play case:D01 -v                    # sandbox, does not count against quota
uv run arena run --set practice --agent llm --parallel 8   # all 10 hosted practice cases
uv run arena board                               # practice leaderboard (humans only)
```

Read the replay link after every run: every e-mail plus the supplier's reasons. That is the learning loop. Your **best score per practice case** counts. Practice does not rank; the final does.

## 4. LLM settings (`.env`)

```
LLM_PROVIDER=anthropic          # or openai (any OpenAI-compatible endpoint, even local Ollama)
LLM_MODEL=claude-sonnet-5-5     # the kit's example uses claude-opus-5-5; each message must arrive within 60 s
LLM_EFFORT=low
ANTHROPIC_API_KEY=              # your own key, never committed
```

Each of our messages must arrive within **60 s** of the supplier's reply, so prefer a fast model or low effort, and do heavy research before opening a session. Tacto says a small cheap model is enough; reading the data matters more.

## 5. Where to change the agent

All code is in `starter-kit/arena_kit/`:

| File | What it does | Change it to... |
|---|---|---|
| `agents/llm.py` | The LLM agent. `SYSTEM` prompt, `prepare()` (builds the case brief from the data), `render()` (what the model sees each turn), `guard()` (blocks bad accepts and unknown IDs), `parse()` | **Main place to improve.** Better strategy prompt, richer `prepare()` dossier, smarter term-sheet choices |
| `agents/naive.py` | Baseline: anchors 10% low, splits the difference, accepts early | Reference only; also the fallback when the LLM fails |
| `cost.py` | `total_cost`, `complete_offer`, must-have checks | Use to price every term sheet in code (math in code, words from the model) |
| `data.py` | `DataPackage`: SQL over the data, ID lookup, documents | Add dossier builders (which index series, notes and letters matter for which supplier) |
| `docs.py` | Reads quote PDFs and XLSX; `standard_terms` shows what closes if a field is missing | Check what an unnegotiated field defaults to before accepting |
| `play.py` | `play()`, `play_all()`, `play_waves()` (the Live Final loop) | Rarely; the runner already handles waves, timing and resume |
| `cli.py` | `agent_factory` picks `naive` or `llm` (`--agent` choices) | **Register our own agent here** |
| `mcp_server.py` | Read-only MCP server over the data (6 tools) | Let Claude Code explore the data |

**Our own agent:** any object with `decide(case, threads) -> {"supplier_id": ..., "message": {...}}`. Add it under `agents/`, then add it to `agent_factory` and the `--agent` choices in `cli.py` (two places). Example skeleton is in the starter-kit README.

Ideas the kit and brief point to:
- Mine the notes, letters, news and quote remarks for what moves each supplier.
- Send 2-3 term sheets to learn what a supplier values (for example payment days instead of price).
- Cache one dossier per supplier; the data only changes at the Sunday 08:00 release.
- Never leak urgency, a budget or a missing alternative.
- Read the quote PDF before accepting.
- Do not send ultimatums; the P01 replay shows they cost money.

## 6. Where our code should live

The submission is **our repo plus a commit hash**, and tum.ai runs a code agent over it. Plan: copy our modified `starter-kit` into this repo (for example `agent/`), without `.env`, `.venv`, `data/package` or any key. Decide as a team before editing. A README with run instructions is required.

## 7. Practice quota and rehearsal

- 200 practice sessions per team per rolling 24 h. Use the sandbox (`case:D01`, `case:D02`) and the simulator for plumbing tests.
- Rehearse the final: `uv run arena run --set practice --agent llm --parallel 10` from the machine and network used on Sunday; every case should end well inside 8 minutes.
- Final run command: `uv run arena run --set final --agent llm --parallel 10`. Start before 12:00 and leave it running. A cloud VM is safer than venue Wi-Fi.

## 8. Troubleshooting

- `uv: command not found`: `export PATH="$HOME/.local/bin:$PATH"`.
- Is the arena up? `curl $ARENA_URL/health`.
- HTTP 429 on practice: quota used up; waiting is the only fix.
- `422`: invalid message, no round used. `409`: thread or case ended, or you were late.
- Late messages repeat your last offer; three in a row end the thread.
- Questions: Discord <https://discord.gg/hPwFfbWRV> (one thread per question; never post the key).

## 9. Not verified

- The real-arena commands (`arena me`, `arena data`, LLM agent runs) were not run; no team key yet.
- Only the simulator path was tested.
- `brief/api.md` was not read.
