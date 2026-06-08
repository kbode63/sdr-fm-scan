#!/usr/bin/env python3
"""
main.py — Unified entry point for the RTL-SDR scanner.

Subcommands
-----------
  scan      Run rtl_power capture + analysis in one step (wraps scan.sh).
  analyze   (Re-)analyse an existing CSV without the dongle (wraps analyze.py).
  gui       Launch the Streamlit web interface (wraps launch-gui.sh).
  heatmap   Generate a standalone heatmap PNG from a CSV (wraps rtl_heatmap.py).

Examples
--------
  python3 scripts/main.py gui
  python3 scripts/main.py scan --band fm --duration 60
  python3 scripts/main.py analyze data/output.csv --threshold 6
  python3 scripts/main.py heatmap data/output.csv charts/heatmap.png
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


# ── Helpers ───────────────────────────────────────────────────────────────────


def run(cmd: list, **kwargs) -> int:
    """Run *cmd* and return its exit code."""
    try:
        result = subprocess.run(cmd, **kwargs)
        return result.returncode
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


# ── Subcommand handlers ───────────────────────────────────────────────────────


def cmd_scan(args: argparse.Namespace) -> int:
    cmd = ["bash", str(SCRIPTS / "scan.sh")]
    if args.band:
        cmd += ["--band", args.band]
    if args.freq:
        cmd += ["--freq", args.freq]
    if args.step:
        cmd += ["--step", args.step]
    cmd += [
        "--duration",
        str(args.duration),
        "--gain",
        str(args.gain),
        "--threshold",
        str(args.threshold),
    ]
    return run(cmd, cwd=str(REPO))


def cmd_analyze(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(SCRIPTS / "analyze.py"),
        args.csv,
        "--outdir",
        args.outdir,
        "--threshold",
        str(args.threshold),
    ]
    if args.prefix:
        cmd += ["--prefix", args.prefix]
    if args.json_out:
        cmd += ["--json-out", args.json_out]
    return run(cmd, cwd=str(REPO))


def cmd_gui(args: argparse.Namespace) -> int:
    # Prefer the venv streamlit, fall back to whatever is on PATH
    venv_streamlit = REPO / ".venv" / "bin" / "streamlit"
    streamlit_bin = str(venv_streamlit) if venv_streamlit.exists() else "streamlit"
    cmd = [
        streamlit_bin,
        "run",
        str(SCRIPTS / "gui.py"),
        "--server.port",
        str(args.port),
        "--browser.gatherUsageStats",
        "false",
    ]
    print(f"Starting RTL-SDR Scanner GUI → http://localhost:{args.port}")
    return run(cmd, cwd=str(REPO))


def cmd_heatmap(args: argparse.Namespace) -> int:
    cmd = [sys.executable, str(SCRIPTS / "rtl_heatmap.py"), args.csv, args.output]
    return run(cmd, cwd=str(REPO))


# ── Argument parser ───────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdr-scan",
        description="RTL-SDR frequency scanner — capture, analyse, visualise.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # ── scan ──────────────────────────────────────────────────────────────────
    p_scan = sub.add_parser("scan", help="Capture + analyse spectrum (dongle required)")
    freq_grp = p_scan.add_mutually_exclusive_group()
    freq_grp.add_argument(
        "--band",
        "-b",
        choices=["fm", "airband", "weather", "marine", "2m", "70cm", "ism433"],
        help="Named band preset",
    )
    freq_grp.add_argument(
        "--freq",
        "-f",
        metavar="LOW:HIGH",
        help="Custom frequency range, e.g. 156M:174M",
    )
    p_scan.add_argument("--step", "-s", default="", help="Frequency step (e.g. 25k)")
    p_scan.add_argument(
        "--duration", "-d", default=60, type=int, help="Scan duration in seconds (default: 60)"
    )
    p_scan.add_argument(
        "--gain", "-g", default=49.6, type=float, help="Tuner gain in dB (default: 49.6)"
    )
    p_scan.add_argument(
        "--threshold", "-t", default=3.0, type=float, help="SNR threshold in dB (default: 3.0)"
    )

    # ── analyze ───────────────────────────────────────────────────────────────
    p_ana = sub.add_parser("analyze", help="Analyse an existing CSV (no dongle needed)")
    p_ana.add_argument("csv", help="Path to rtl_power output CSV")
    p_ana.add_argument("--outdir", default="charts", help="Output directory (default: charts/)")
    p_ana.add_argument(
        "--threshold", default=3.0, type=float, help="SNR threshold in dB (default: 3.0)"
    )
    p_ana.add_argument("--prefix", default="", help="Filename prefix for output charts")
    p_ana.add_argument(
        "--json-out", default=None, dest="json_out", help="Override JSON output path"
    )

    # ── gui ───────────────────────────────────────────────────────────────────
    p_gui = sub.add_parser("gui", help="Launch the Streamlit web interface")
    p_gui.add_argument("--port", default=8501, type=int, help="Port to serve on (default: 8501)")

    # ── heatmap ───────────────────────────────────────────────────────────────
    p_hm = sub.add_parser("heatmap", help="Generate a standalone heatmap PNG")
    p_hm.add_argument("csv", help="Path to rtl_power output CSV")
    p_hm.add_argument(
        "output",
        nargs="?",
        default="charts/heatmap.png",
        help="Output PNG path (default: charts/heatmap.png)",
    )

    return parser


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "scan": cmd_scan,
        "analyze": cmd_analyze,
        "gui": cmd_gui,
        "heatmap": cmd_heatmap,
    }
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
