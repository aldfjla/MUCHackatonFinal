# Live Final runbook (Sun 11 Oct 2026, 12:00)

Machine: this laptop (or a cloud VM with the same checkout). Power on, sleep off, wired or stable Wi-Fi.

```bash
cd ~/Documents/Codex/MUCHackatonFinal
git fetch origin && git checkout submission          # the submitted commit (tag)
cd agent
set -a; source ~/Documents/Codex/negotiation-arena-kit/starter-kit/.env; set +a   # ARENA_URL, ARENA_API_KEY
export ARENA_DATA=$HOME/Documents/Codex/negotiation-arena-kit/data               # package; release-sunday sits inside it
export UV_PROJECT_ENVIRONMENT=$HOME/.venvs/arena-agent
uv run arena me                                       # must print the team and quota
mkdir -p ../final_logs
nohup uv run arena run --set final --agent better --parallel 10 --waves 5 -v \
  > ../final_logs/final_$(date +%H%M).log 2>&1 &
tail -f ../final_logs/final_*.log
```

- Start before 11:55. The runner polls for waves, plays each wave's cases in parallel, closes 90 s before
  the cap, and resumes after a crash (just rerun the same command).
- Do not touch the leaderboard, events or results from the agent machine during the final.
- Do not push to the repo after 12:00.
- If the runner dies: rerun the same `uv run arena run ...` line; it resumes open sessions.
- After the last wave: the log ends with `waves: {...} points so far: N`.
