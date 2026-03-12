"""Formatting and text utilities (size, speed, ANSI stripping)."""

import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from console output."""
    return ANSI_RE.sub("", text)


def format_size(size_bytes: int) -> str:
    """Format byte count as human-readable (e.g. 1.5 MB). Returns '—' if size_bytes < 0."""
    if size_bytes < 0:
        return "—"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            if unit == "B":
                return f"{int(size_bytes)} B"
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def format_speed(bytes_per_sec: float) -> str:
    """Format bytes per second as human-readable speed (e.g. 1.2 MB/s)."""
    if bytes_per_sec <= 0 or not isinstance(bytes_per_sec, (int, float)):
        return "—"
    n = float(bytes_per_sec)
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if n < 1024:
            if unit == "B/s":
                return f"{int(n)} B/s"
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB/s"
