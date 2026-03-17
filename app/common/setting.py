# coding: utf-8
"""Re-export config paths for database/entity (backward-compat with VOK-Get style imports)."""

from pathlib import Path

from app.config.store import COVER_FOLDER, DB_PATH, LOG_FOLDER

DEBUG = "__compiled__" not in globals()

# Single source of truth: pyproject.toml [project].version (works in CI and when not installed)
def _get_version() -> str:
    try:
        from importlib.metadata import version
        return version("vok-get")
    except Exception:
        pass
    path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("version") and "=" in line:
                return line.split("=", 1)[1].strip().strip('"\'')
    return "0.0.0"

VERSION = _get_version()

__all__ = ["DB_PATH", "LOG_FOLDER", "COVER_FOLDER", "VERSION"]
