#!/usr/bin/env bash
# Usage: ./scripts/scan.sh [freq_low] [freq_high] [step] [duration_s]
# Example: ./scripts/scan.sh 85M 110M 125k 60
set -euo pipefail

FREQ_LOW="${1:-85M}"
FREQ_HIGH="${2:-110M}"
STEP="${3:-125k}"
DURATION="${4:-60}"
GAIN=49.6

TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
DATA_DIR="$(cd "$(dirname "$0")/../data" && pwd)"
CHARTS_DIR="$(cd "$(dirname "$0")/../charts" && pwd)"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

CSV="${DATA_DIR}/scan_${TIMESTAMP}.csv"
HEATMAP="${CHARTS_DIR}/heatmap_${TIMESTAMP}.png"

echo "==> Scanning ${FREQ_LOW}–${FREQ_HIGH} step ${STEP} for ${DURATION}s ..."
rtl_power -f "${FREQ_LOW}:${FREQ_HIGH}:${STEP}" -g "${GAIN}" -i 1 -e "${DURATION}" "${CSV}"

echo "==> Generating heatmap → ${HEATMAP}"
python3 "${SCRIPTS_DIR}/rtl_heatmap.py" "${CSV}" "${HEATMAP}"

echo "==> Done. Output files:"
echo "    Data   : ${CSV}"
echo "    Chart  : ${HEATMAP}"
