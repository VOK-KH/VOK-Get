# coding: utf-8
"""Re-export config paths for database/entity (backward-compat with VOK-Get style imports)."""

from app.config.store import COVER_FOLDER, DB_PATH, LOG_FOLDER

__all__ = ["DB_PATH", "LOG_FOLDER", "COVER_FOLDER"]
