"""Settings store: load/save from JSON file."""

import json
from pathlib import Path

from app.common.paths import PROJECT_ROOT, DOWNLOADS_DIR

CONFIG_DIR = PROJECT_ROOT
SETTINGS_PATH = CONFIG_DIR / "vok_settings.json"

_DEFAULTS = {
    "download_path": str(DOWNLOADS_DIR),
    "single_video_default": True,
    "theme_color": "#0078D4",
    "concurrent_downloads": 2,
    "concurrent_fragments": 4,
}


def load_settings() -> dict:
    """Load settings from config file."""
    if not SETTINGS_PATH.exists():
        return _DEFAULTS.copy()
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        out = _DEFAULTS.copy()
        out.update(data)
        return out
    except (json.JSONDecodeError, OSError):
        return _DEFAULTS.copy()


def save_settings(settings: dict) -> None:
    """Persist settings to config file."""
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError:
        pass
