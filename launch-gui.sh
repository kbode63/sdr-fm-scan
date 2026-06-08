#!/usr/bin/env bash
# Launch the RTL-SDR Scanner GUI.
# Usage: ./launch-gui.sh [--port PORT]
set -euo pipefail

PORT="${1:-8501}"
REPO="$(cd "$(dirname "$0")" && pwd)"

# Prefer the project venv; fall back to whatever streamlit is on PATH
if [[ -x "$REPO/.venv/bin/streamlit" ]]; then
  STREAMLIT="$REPO/.venv/bin/streamlit"
elif command -v streamlit &>/dev/null; then
  STREAMLIT="streamlit"
else
  echo "Streamlit not found. Activate the venv and run: pip install streamlit" >&2
  exit 1
fi

echo "Starting RTL-SDR Scanner GUI → http://localhost:${PORT}"
exec "$STREAMLIT" run "$REPO/scripts/gui.py" \
  --server.port "$PORT" \
  --browser.gatherUsageStats false
