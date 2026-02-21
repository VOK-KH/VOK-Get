"""In-memory state: log buffer for UI. Settings live in app.config."""

from datetime import datetime
from pathlib import Path

from app.config import load_settings
from app.common.paths import DOWNLOADS_DIR

_log_buffer: list[dict] = []
_max_log_entries = 500


def add_log_entry(level: str, message: str) -> None:
    """Append a log entry for the Logs view."""
    global _log_buffer
    _log_buffer.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "message": message,
    })
    _log_buffer = _log_buffer[-_max_log_entries:]


def get_log_entries() -> list[dict]:
    """Return current log buffer (copy)."""
    return list(_log_buffer)


def clear_log_entries() -> None:
    """Clear the log buffer."""
    global _log_buffer
    _log_buffer.clear()


def get_recent_downloads(limit: int = 50) -> list[dict]:
    """Scan downloads folder from config and return recent files."""
    out = []
    path = Path(load_settings().get("download_path", str(DOWNLOADS_DIR)))
    if not path.exists():
        return out
    for f in path.iterdir():
        if f.is_file():
            try:
                mtime = f.stat().st_mtime
                out.append({
                    "name": f.name,
                    "path": str(f),
                    "date": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
                })
            except OSError:
                continue
    out.sort(key=lambda x: x["date"], reverse=True)
    return out[:limit]
