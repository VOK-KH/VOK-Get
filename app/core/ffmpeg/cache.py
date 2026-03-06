# coding: utf-8
"""Path resolution cache for the ffmpeg binary.

Thin helper — wraps FFmpegManager so callers can ask for the resolved
path without holding a reference to the manager themselves.

Usage
-----
from app.core.ffmpeg.cache import get_ffmpeg_path

    cmd = [get_ffmpeg_path(), "-y", "-i", input_path, ...]
"""

from app.core.ffmpeg.manager import ffmpeg_manager


def get_ffmpeg_path() -> str:
    """Return the absolute path to the ffmpeg binary (cached after first call)."""
    return ffmpeg_manager.get()
