# check_last_run.py
"""Inspect the most recent pipeline run in the log file and report its health."""

from __future__ import annotations

from pathlib import Path

# Default location used by Chapter 10 / cron setup.
# Change this if your log lives elsewhere.
LOG_PATH = Path(__file__).resolve().parent / "logs" / "pipeline.log"

# Fallback for the simple redirect style from Chapter 10:
#   ... >> /home/pi/grounded-pipeline/logs/run.log 2>&1
FALLBACK_LOG_PATH = Path(__file__).resolve().parent / "logs" / "run.log"


def _read_log() -> list[str]:
    for path in (LOG_PATH, FALLBACK_LOG_PATH):
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    return []


def check_last_run() -> str:
    """
    Return a short human-readable status of the most recent run.

    Looks for stage lines containing SUCCESS / FAILED / REJECTED / APPROVED
    and for the structured "=== run start ===" markers emitted by the
    logging setup in run_pipeline.py.
    Compatible with both plain print-style logs and timestamped logging output.
    """
    lines = _read_log()

    if not lines:
        return "NO LOG FOUND — pipeline may never have run"

    # Prefer an explicit run marker if present; otherwise use the tail.
    start_idx = 0
    for i, line in enumerate(lines):
        if "=== run start ===" in line.lower() or "run start" in line.lower():
            start_idx = i

    recent = lines[start_idx:]

    # Keep only lines that look like stage outcomes or errors
    stage_lines = [
        line
        for line in recent
        if any(
            token in line.upper()
            for token in ("STAGE", "SUCCESS", "FAILED", "REJECTED", "APPROVED", "ERROR", "CRITICAL")
        )
    ]

    if not stage_lines:
        # Last resort: show the final few lines of the log
        tail = recent[-8:] if len(recent) >= 8 else recent
        return "LAST RUN — no clear stage markers found. Tail:\n" + "\n".join(tail)

    failures = [
        line
        for line in stage_lines
        if any(token in line.upper() for token in ("FAILED", "REJECTED", "ERROR", "CRITICAL"))
    ]

    if failures:
        return "LAST RUN HAD ISSUES:\n" + "\n".join(failures)

    return "LAST RUN OK\n" + "\n".join(stage_lines[-6:])


if __name__ == "__main__":
    print(check_last_run())
