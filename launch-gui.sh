#!/usr/bin/env bash
# Launch the RTL-SDR Scanner GUI.
# Usage: ./launch-gui.sh [--port PORT]
set -euo pipefail

PORT="${1:-8501}"
REPO="$(cd "$(dirname "$0")" && pwd)"
STREAMLIT="/Users/karlbode/Library/Python/3.9/bin/streamlit"
PYTHONPATH_EXTRA="/Users/karlbode/Library/Python/3.9/lib/python/site-packages"

if [[ ! -x "$STREAMLIT" ]]; then
  echo "Streamlit not found. Install it with: pip3 install streamlit" >&2
  exit 1
fi

export PYTHONPATH="${PYTHONPATH_EXTRA}:${PYTHONPATH:-}"

echo "Starting RTL-SDR Scanner GUI → http://localhost:${PORT}"
exec "$STREAMLIT" run "$REPO/scripts/gui.py" \
  --server.port "$PORT" \
  --browser.gatherUsageStats false
