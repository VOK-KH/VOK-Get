"""Config: settings store and setup."""

from app.config.store import (
    get_default_settings,
    get_settings_path,
    is_first_run,
    load_settings,
    save_settings,
)

__all__ = [
    "get_default_settings",
    "get_settings_path",
    "is_first_run",
    "load_settings",
    "save_settings",
]
