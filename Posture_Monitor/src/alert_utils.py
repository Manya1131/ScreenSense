"""
alert_utils.py
--------------
Manages on-screen alert logic and CSV-based activity logging.

Alert priority (highest → lowest):
  1. "break_in_progress" – looking away during a break
  2. "break_needed"      – work timer expired
  3. "too_close"         – distance < min_safe
  4. "too_far"           – distance > max_safe
  5. "good"              – all clear

CSV log schema
--------------
timestamp, distance_cm, work_elapsed_mins, distance_status, break_status, alert
"""

import csv
import os
from datetime import datetime
from pathlib import Path

# ── Log file location ─────────────────────────────────────────────────────────
LOG_DIR  = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "activity_log_v2.csv"

# Column headers written on first run
_CSV_HEADERS = [
    "timestamp",
    "distance_cm",
    "work_elapsed_mins",
    "distance_status",
    "break_status",
    "alert",
]

# ── Alert metadata ────────────────────────────────────────────────────────────
ALERT_CONFIG = {
    "good": {
        "emoji":   "🟢",
        "label":   "All Good!",
        "colour":  "#1e8c2a",       # dark green
        "bg":      "#d4edda",
        "border":  "#28a745",
    },
    "too_close": {
        "emoji":   "🟠",
        "label":   "Too Close – Move Back",
        "colour":  "#7d4e00",
        "bg":      "#fff3cd",
        "border":  "#fd7e14",
    },
    "break_needed": {
        "emoji":   "🟣",
        "label":   "Time for an Eye Break! Look away for 20s.",
        "colour":  "#4a1c40",
        "bg":      "#e8d8e6",
        "border":  "#800080",
    },
    "break_in_progress": {
        "emoji":   "⏳",
        "label":   "Break in progress... Keep looking away!",
        "colour":  "#856404",
        "bg":      "#fff3cd",
        "border":  "#ffeeba",
    },
    "too_far": {
        "emoji":   "🔵",
        "label":   "Move Closer to Screen",
        "colour":  "#004085",
        "bg":      "#cce5ff",
        "border":  "#007bff",
    },
    "unknown": {
        "emoji":   "⚪",
        "label":   "No Face Detected",
        "colour":  "#383d41",
        "bg":      "#e2e3e5",
        "border":  "#6c757d",
    },
}


def determine_alert(distance_status: str, break_status: str) -> str:
    """
    Return the highest-priority alert key given distance and break status.
    """
    if break_status == "break_in_progress":
        return "break_in_progress"
    if break_status == "break_needed":
        return "break_needed"
    
    if distance_status == "unknown":
        return "unknown"
    if distance_status == "too_close":
        return "too_close"
    if distance_status == "too_far":
        return "too_far"
    
    return "good"


def get_alert_info(alert_key: str) -> dict:
    """Return display metadata dict for the given alert key."""
    return ALERT_CONFIG.get(alert_key, ALERT_CONFIG["unknown"])


def ensure_log_file() -> None:
    """Create the log directory and CSV file (with headers) if missing."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(_CSV_HEADERS)


def log_event(
    distance_cm: float,
    work_elapsed_mins: float,
    distance_status: str,
    break_status: str,
    alert: str,
) -> None:
    """
    Append one monitoring event to the CSV log.
    Only warning/alert events (non-"good") are written to keep the log lean.
    """
    if alert == "good":
        return

    ensure_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [timestamp, distance_cm, work_elapsed_mins, distance_status, break_status, alert]
        )


def load_today_log():
    """Load today's log entries as a list of dicts."""
    ensure_log_file()
    today = datetime.now().strftime("%Y-%m-%d")
    rows = []

    with open(LOG_FILE, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("timestamp", "").startswith(today):
                rows.append(row)

    return rows


def count_today_warnings() -> dict:
    """Count today's warnings broken down by alert type."""
    rows = load_today_log()
    counts: dict = {}
    for row in rows:
        key = row.get("alert", "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts
