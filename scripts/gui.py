#!/usr/bin/env python3
"""
gui.py — Streamlit web interface for the RTL-SDR scanner.

Usage:
    streamlit run scripts/gui.py
    # or, from anywhere:
    streamlit run ~/sdr-fm-scan/scripts/gui.py
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import streamlit as st

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
DATA = REPO / "data"
CHARTS = REPO / "charts"

# Make sure user-installed packages (matplotlib, numpy, etc.) are importable
# when scan.sh spawns analyze.py as a subprocess.
_USER_SITE = Path(sys.executable).parent.parent / "lib" / "python" / "site-packages"
if not _USER_SITE.exists():
    import site

    _USER_SITE = Path(site.getusersitepackages())

# ── Band presets (mirror scan.sh) ─────────────────────────────────────────────
BANDS: dict[str, dict] = {
    "fm": {
        "low": "87.5M",
        "high": "108M",
        "step": "125k",
        "label": "FM Broadcast · 87.5–108 MHz",
    },
    "airband": {
        "low": "118M",
        "high": "137M",
        "step": "25k",
        "label": "Aviation VHF · 118–137 MHz",
    },
    "weather": {
        "low": "162.4M",
        "high": "162.55M",
        "step": "2.5k",
        "label": "NOAA Weather · 162.4–162.55 MHz",
    },
    "marine": {
        "low": "156M",
        "high": "174M",
        "step": "25k",
        "label": "Marine VHF · 156–174 MHz",
    },
    "2m": {
        "low": "144M",
        "high": "148M",
        "step": "12.5k",
        "label": "2m Amateur · 144–148 MHz",
    },
    "70cm": {
        "low": "430M",
        "high": "440M",
        "step": "12.5k",
        "label": "70cm Amateur · 430–440 MHz",
    },
    "ism433": {
        "low": "433.05M",
        "high": "434.79M",
        "step": "5k",
        "label": "ISM / LoRa · 433 MHz",
    },
}

# Valid R820T gain values
GAIN_VALUES = [
    0.0,
    0.9,
    1.4,
    2.7,
    3.7,
    7.7,
    8.7,
    12.5,
    14.4,
    15.7,
    16.6,
    19.7,
    20.7,
    22.9,
    25.4,
    28.0,
    29.7,
    32.8,
    33.8,
    36.4,
    37.2,
    38.6,
    40.2,
    42.1,
    43.4,
    43.9,
    44.5,
    48.0,
    49.6,
]

TIER_EMOJI = {"STRONG": "🔴", "MEDIUM": "🟠", "WEAK": "🟢", "MARGINAL": "🔵"}

# ── Voice / data classification by frequency range ────────────────────────────
# Returns (type_label, service_hint)
_FREQ_CLASSES = [
    # (low_mhz, high_mhz, type, service)
    (87.5, 108.0, "🎙 Voice/Music", "FM Broadcast"),
    (108.0, 118.0, "📡 Data", "Aeronautical nav (VOR/ILS)"),
    (118.0, 137.0, "🎙 Voice (AM)", "Aviation"),
    (137.0, 138.0, "📡 Data", "Weather satellites"),
    (144.0, 148.0, "🎙/📡 Mixed", "2m Amateur"),
    (156.525, 156.525, "📡 Data", "DSC Channel 70"),
    (156.0, 174.0, "🎙 Voice", "Marine VHF"),
    (162.400, 162.550, "🎙 Voice", "NOAA Weather Radio"),
    (430.0, 440.0, "🎙/📡 Mixed", "70cm Amateur"),
    (433.050, 434.790, "📡 Data", "ISM / LoRa"),
    (862.0, 870.0, "📡 Data", "LoRa 868"),
    (902.0, 928.0, "📡 Data", "ISM 915"),
]


def classify_signal(freq_mhz: float) -> tuple[str, str]:
    """Return (type_label, service_hint) for a frequency in MHz."""
    best = ("❓ Unknown", "")
    best_width = float("inf")  # prefer narrower (more specific) matching range
    for low, high, label, service in _FREQ_CLASSES:
        if low <= freq_mhz <= high:
            width = high - low
            if width < best_width:
                best = (label, service)
                best_width = width
    return best


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RTL-SDR Scanner",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state init ────────────────────────────────────────────────────────
if "scan_running" not in st.session_state:
    st.session_state.scan_running = False
if "last_json" not in st.session_state:
    st.session_state.last_json = None
if "last_stem" not in st.session_state:
    st.session_state.last_stem = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📡 RTL-SDR Scanner")
    st.caption("Passive spectrum scan · peak detection · analysis")
    st.divider()

    # ── Frequency source
    st.subheader("Frequency")
    mode = st.radio(
        "Source", ["Band preset", "Custom range"], horizontal=True, label_visibility="collapsed"
    )

    band_key = None
    freq_low = freq_high = ""
    step_override = ""

    if mode == "Band preset":
        band_key = st.selectbox(
            "Band",
            options=list(BANDS.keys()),
            format_func=lambda k: BANDS[k]["label"],
            index=3,  # default: marine
        )
        preset = BANDS[band_key]
        st.caption(
            f"Range: **{preset['low']}** – **{preset['high']}** | Default step: **{preset['step']}**"
        )
        step_override = st.text_input(
            "Override step (optional)",
            placeholder=preset["step"],
            help="Leave blank to use the band preset default.",
        )
    else:
        c1, c2 = st.columns(2)
        freq_low = c1.text_input("Low freq", value="156M")
        freq_high = c2.text_input("High freq", value="174M")
        step_override = st.text_input("Step", value="5k")

    st.divider()

    # ── Scan parameters
    st.subheader("Parameters")
    duration = st.slider(
        "Duration (s)",
        min_value=5,
        max_value=1800,
        value=60,
        step=5,
        format="%d s",
        help="Up to 30 minutes. Long scans capture intermittent signals more reliably.",
    )
    gain = st.select_slider(
        "Gain (dB)",
        options=GAIN_VALUES,
        value=49.6,
        help="Valid R820T gain steps.",
    )
    threshold = st.slider(
        "SNR threshold (dB)",
        min_value=1.0,
        max_value=20.0,
        value=3.0,
        step=0.5,
        help="Minimum SNR above noise floor to report a peak.",
    )

    st.divider()
    scan_btn = st.button(
        "▶  Start Scan",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.scan_running,
    )

# ── Helpers ───────────────────────────────────────────────────────────────────


def build_cmd(band_key, freq_low, freq_high, step_override, duration, gain, threshold):
    cmd = ["bash", str(SCRIPTS / "scan.sh")]
    if band_key:
        cmd += ["--band", band_key]
        if step_override.strip():
            cmd += ["--step", step_override.strip()]
    else:
        cmd += ["--freq", f"{freq_low}:{freq_high}", "--step", step_override.strip() or "125k"]
    cmd += [
        "--duration",
        str(int(duration)),
        "--gain",
        str(gain),
        "--threshold",
        str(threshold),
    ]
    return cmd


def find_latest_artifacts(band_label: str):
    """Return (json_path, {chart_name: path}) for the most recent scan."""
    pattern = f"{band_label}_*_summary.json"
    candidates = sorted(CHARTS.glob(pattern), key=lambda p: p.stat().st_mtime)
    if not candidates:
        candidates = sorted(CHARTS.glob("*_summary.json"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        return None, None, {}
    j = candidates[-1]
    stem = j.stem.replace("_summary", "")
    charts = {name: CHARTS / f"{stem}_{name}.png" for name in ("heatmap", "spectrum", "report")}
    return j, stem, {k: v for k, v in charts.items() if v.exists()}


def make_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(_USER_SITE) + ":" + env.get("PYTHONPATH", "")
    return env


def render_signal_table(signals: list):
    rows = [
        "| Freq (MHz) | Type | Service | Mean dBm | Peak dBm | SNR dB | Tier | Stability |",
        "|:----------:|:----:|:-------:|:--------:|:--------:|:------:|:----:|:---------:|",
    ]
    for s in signals:
        emoji = TIER_EMOJI.get(s["tier"], "")
        sig_type, service = classify_signal(s["freq_mhz"])
        rows.append(
            f"| **{s['freq_mhz']:.3f}** "
            f"| {sig_type} "
            f"| {service} "
            f"| {s['mean_dbm']:.1f} "
            f"| {s['peak_dbm']:.1f} "
            f"| {s['snr_db']:.1f} "
            f"| {emoji} {s['tier']} "
            f"| {s['stability']} |"
        )
    st.markdown("\n".join(rows))


def render_results(json_path: Path, charts: dict):
    summary = json.loads(json_path.read_text())
    scan = summary["scan"]
    analysis = summary["analysis"]
    signals = summary["signals"]

    # ── Metadata strip
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Range (MHz)", f"{scan['freq_low_mhz']:.1f} – {scan['freq_high_mhz']:.1f}")
    m2.metric("Duration", f"{scan['duration_s']} s")
    m3.metric("Noise floor", f"{analysis['noise_floor_dbm']} dBm")
    m4.metric("Signals", analysis["total_signals"])
    m5.metric("Time (UTC)", scan["start_utc"][11:16])

    st.divider()

    # ── Charts
    if charts:
        st.subheader("Charts")
        tabs = st.tabs([n.capitalize() for n in charts])
        for tab, (_name, path) in zip(tabs, charts.items()):
            with tab:
                st.image(str(path), width="stretch")
        st.divider()

    # ── Tier summary badges
    st.subheader(f"Detected signals — {len(signals)} total")
    tc = analysis.get("by_tier", {})
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("🔴 Strong", tc.get("STRONG", 0), help="SNR > 20 dB")
    b2.metric("🟠 Medium", tc.get("MEDIUM", 0), help="SNR 14–20 dB")
    b3.metric("🟢 Weak", tc.get("WEAK", 0), help="SNR 6–14 dB")
    b4.metric("🔵 Marginal", tc.get("MARGINAL", 0), help="SNR 3–6 dB")

    # ── Signal table
    render_signal_table(signals)

    st.divider()

    # ── Downloads
    d1, d2 = st.columns(2)
    d1.download_button(
        "⬇ Download JSON summary",
        data=json_path.read_text(),
        file_name=json_path.name,
        mime="application/json",
    )
    if "report" in charts:
        d2.download_button(
            "⬇ Download report PNG",
            data=charts["report"].read_bytes(),
            file_name=charts["report"].name,
            mime="image/png",
        )


# ── Main area ─────────────────────────────────────────────────────────────────
st.header("Scan Results")

# ── Run scan when button pressed
if scan_btn:
    st.session_state.scan_running = True
    cmd = build_cmd(band_key, freq_low, freq_high, step_override, duration, gain, threshold)

    st.subheader("Live output")
    progress_bar = st.progress(0.0, text="Initialising scan…")
    output_box = st.empty()
    lines: list[str] = []
    scan_start = time.monotonic()

    with st.spinner("Scanning… (dongle must be connected)"):
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(REPO),
                env=make_env(),
            )
            for raw_line in proc.stdout:
                elapsed = time.monotonic() - scan_start
                # rtl_power phase: progress fills to 95%; analysis fills the last 5%
                scan_frac = min(elapsed / max(int(duration), 1), 0.95)
                mins, secs = divmod(int(elapsed), 60)
                time_str = f"{mins}m {secs:02d}s" if mins else f"{secs}s"
                progress_bar.progress(
                    scan_frac,
                    text=f"Scanning…  {time_str} elapsed / {int(duration)} s target",
                )
                stripped = raw_line.rstrip()
                lines.append(stripped)
                # Bump to 98% when analysis starts
                if stripped.startswith("==> Analysing"):
                    progress_bar.progress(0.98, text="Analysing…")
                output_box.code("\n".join(lines[-30:]), language="bash")
            proc.wait()
            progress_bar.progress(1.0, text="Complete ✅")
        except FileNotFoundError:
            st.error("scan.sh not found. Run this app from inside the sdr-fm-scan repo.")
            st.session_state.scan_running = False
            st.stop()

    st.session_state.scan_running = False

    if proc.returncode == 0:
        st.success("✅ Scan complete!")
        band_label = band_key if band_key else "custom"
        json_path, stem, charts = find_latest_artifacts(band_label)
        st.session_state.last_json = str(json_path) if json_path else None
        st.session_state.last_stem = stem
    else:
        st.error(
            f"Scan exited with code {proc.returncode}. "
            "Check that the RTL-SDR dongle is connected and rtl_power is installed."
        )

# ── Render previous / current results
json_str = st.session_state.last_json
if json_str:
    json_path = Path(json_str)
    stem = st.session_state.last_stem or ""
    charts = {
        name: CHARTS / f"{stem}_{name}.png"
        for name in ("heatmap", "spectrum", "report")
        if stem and (CHARTS / f"{stem}_{name}.png").exists()
    }
    if json_path.exists():
        render_results(json_path, charts)
else:
    # Auto-load the most recent scan from disk on first run
    _, stem, charts = find_latest_artifacts("")
    candidates = sorted(CHARTS.glob("*_summary.json"), key=lambda p: p.stat().st_mtime)
    if candidates:
        json_path = candidates[-1]
        stem = json_path.stem.replace("_summary", "")
        charts = {
            name: CHARTS / f"{stem}_{name}.png"
            for name in ("heatmap", "spectrum", "report")
            if (CHARTS / f"{stem}_{name}.png").exists()
        }
        st.info(
            f"Showing most recent scan: **{json_path.name}**  — run a new scan using the sidebar."
        )
        render_results(json_path, charts)
    else:
        st.info(
            "No scan results yet. Configure settings in the sidebar and click **▶ Start Scan**.\n\n"
            "Make sure your RTL-SDR dongle is connected before scanning."
        )
        st.image(
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/RTL-SDR_Blog_V3_Dongle.jpg/320px-RTL-SDR_Blog_V3_Dongle.jpg",
            caption="RTL-SDR dongle required",
            width=260,
        )
