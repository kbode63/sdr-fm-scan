#!/usr/bin/env bash
# scan.sh — capture an RTL-SDR power scan and generate analysis charts.
#
# Usage:
#   ./scripts/scan.sh [options]
#
# Options:
#   -b, --band BAND      Named frequency band preset (see list below)
#   -f, --freq LOW:HIGH  Custom frequency range, e.g. 156M:174M
#   -s, --step STEP      Frequency step size (default: band preset or 125k)
#   -d, --duration SECS  Scan duration in seconds (default: 60)
#   -g, --gain DB        Tuner gain in dB (default: 49.6)
#   -t, --threshold DB   SNR detection threshold (default: 3.0)
#   -h, --help           Show this help message
#
# Named bands:
#   fm          FM broadcast       87.5–108 MHz   step 125k
#   airband     Aviation VHF      118–137 MHz    step 25k
#   weather     NOAA weather      162.4–162.55 MHz step 2.5k
#   marine      Marine VHF        156–174 MHz    step 25k
#   2m          2m amateur        144–148 MHz    step 12.5k
#   70cm        70cm amateur      430–440 MHz    step 12.5k
#   ism433      ISM / LoRa 433    433.05–434.79 MHz step 5k
#
# Examples:
#   ./scripts/scan.sh --band marine
#   ./scripts/scan.sh --band fm --duration 120
#   ./scripts/scan.sh --freq 156M:174M --step 25k
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
BAND=""
FREQ_LOW=""
FREQ_HIGH=""
STEP=""
DURATION=60
GAIN=49.6
THRESHOLD=3.0

# ── Argument parsing ──────────────────────────────────────────────────────────
usage() {
  sed -n '3,29p' "$0"
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--band)      BAND="$2";      shift 2 ;;
    -f|--freq)      FREQ_RANGE="$2"; shift 2 ;;
    -s|--step)      STEP="$2";      shift 2 ;;
    -d|--duration)  DURATION="$2";  shift 2 ;;
    -g|--gain)      GAIN="$2";      shift 2 ;;
    -t|--threshold) THRESHOLD="$2"; shift 2 ;;
    -h|--help)      usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done

# ── Resolve band preset ───────────────────────────────────────────────────────
if [[ -n "${BAND}" ]]; then
  case "${BAND}" in
    fm)       FREQ_LOW=87.5M; FREQ_HIGH=108M;     STEP=${STEP:-125k}  ;;
    airband)  FREQ_LOW=118M;  FREQ_HIGH=137M;     STEP=${STEP:-25k}   ;;
    weather)  FREQ_LOW=162.4M; FREQ_HIGH=162.55M; STEP=${STEP:-2.5k}  ;;
    marine)   FREQ_LOW=156M;  FREQ_HIGH=174M;     STEP=${STEP:-25k}   ;;
    2m)       FREQ_LOW=144M;  FREQ_HIGH=148M;     STEP=${STEP:-12.5k} ;;
    70cm)     FREQ_LOW=430M;  FREQ_HIGH=440M;     STEP=${STEP:-12.5k} ;;
    ism433)   FREQ_LOW=433.05M; FREQ_HIGH=434.79M; STEP=${STEP:-5k}   ;;
    *)
      echo "Unknown band '${BAND}'. Valid: fm airband weather marine 2m 70cm ism433" >&2
      exit 1
      ;;
  esac
elif [[ -n "${FREQ_RANGE:-}" ]]; then
  FREQ_LOW="${FREQ_RANGE%%:*}"
  FREQ_HIGH="${FREQ_RANGE##*:}"
  STEP=${STEP:-125k}
else
  # Legacy positional-arg fallback
  FREQ_LOW="${1:-85M}"
  FREQ_HIGH="${2:-110M}"
  STEP=${STEP:-125k}
fi

# ── Derive band label for filenames ──────────────────────────────────────────
BAND_LABEL=${BAND:-custom}

# ── Run scan ──────────────────────────────────────────────────────────────────
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
DATA_DIR="$(cd "$(dirname "$0")/../data" && pwd)"
CHARTS_DIR="$(cd "$(dirname "$0")/../charts" && pwd)"
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"

CSV="${DATA_DIR}/scan_${BAND_LABEL}_${TIMESTAMP}.csv"

echo "==> Band     : ${BAND_LABEL}"
echo "==> Range    : ${FREQ_LOW}–${FREQ_HIGH}  step ${STEP}"
echo "==> Duration : ${DURATION}s  gain ${GAIN} dB"
echo ""
rtl_power -f "${FREQ_LOW}:${FREQ_HIGH}:${STEP}" -g "${GAIN}" -i 1 -e "${DURATION}" "${CSV}"

echo ""
echo "==> Analysing → ${CHARTS_DIR}/"
python3 "${SCRIPTS_DIR}/analyze.py" \
  "${CSV}" \
  --outdir "${CHARTS_DIR}" \
  --threshold "${THRESHOLD}" \
  --prefix "${BAND_LABEL}"

echo ""
echo "==> Done."
echo "    Data   : ${CSV}"
