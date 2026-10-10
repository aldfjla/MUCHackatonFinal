#!/usr/bin/env bash
# Single entry point: re-verify backlog.csv against the LOCAL simulator only.
cd "$(dirname "$0")/.." || exit 1
export PATH="$HOME/.local/bin:$PATH" UV_PROJECT_ENVIRONMENT="$HOME/.venvs/arena-agent"
case "${ARENA_URL:-http://127.0.0.1:8000}" in
  http://127.0.0.1:*|http://localhost:*) ;;
  *) echo "Refusing to run: ARENA_URL=$ARENA_URL is not local (never the real arena)."; exit 1;;
esac
unset ARENA_URL ARENA_API_KEY
if ! curl -sf http://127.0.0.1:8000/health >/dev/null; then
  echo "Simulator down; starting it (log: /tmp/arena-sim-verify.log)"
  (cd agent && nohup uv run arena-sim serve --no-clock >/tmp/arena-sim-verify.log 2>&1 &)
  for _ in $(seq 20); do curl -sf http://127.0.0.1:8000/health >/dev/null && break; sleep 1; done
  curl -sf http://127.0.0.1:8000/health >/dev/null || { echo "Simulator did not start; see /tmp/arena-sim-verify.log"; exit 1; }
fi
KEY=$(cd agent && uv run arena register "VerifyBot$$" sim 2>/dev/null | python3 -c 'import sys,json;t=sys.stdin.read();print(json.loads(t[t.index("{"):t.rindex("}")+1])["api_key"])')
[ -n "$KEY" ] || { echo "Could not get a simulator key"; exit 1; }
ARENA_URL=http://127.0.0.1:8000 ARENA_API_KEY="$KEY" python3 verification/verify_backlog.py --rerun
echo "Report: $PWD/verification/report.md"
read -r -p "Press Enter to close..."
