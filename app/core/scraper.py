"""Social media scraper analytics helpers.

Formatting utilities (fmt_num, fmt_duration, fmt_date) used across the UI.
All QThread workers have moved to app.common.concurrent.scraper_workers.
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fmt_num(n) -> str:
    """Format a large integer with K / M / B suffix."""
    if n is None:
        return "—"
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def fmt_duration(seconds) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    if not seconds:
        return "—"
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return "—"
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m}:{sec:02d}"


def fmt_date(date_str: str) -> str:
    """Convert YYYYMMDD → YYYY-MM-DD."""
    if not date_str or len(date_str) != 8:
        return date_str or "—"
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

