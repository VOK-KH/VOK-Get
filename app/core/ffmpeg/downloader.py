# coding: utf-8
"""Binary downloader helper for ffmpeg.

When ffmpeg is not on the system PATH, ``imageio-ffmpeg`` can supply a
pre-built static binary.  This module exposes a convenience function to
trigger the download/resolution and return the path.

Usage
-----
from app.core.ffmpeg.downloader import ensure_ffmpeg

    path = ensure_ffmpeg()   # downloads if needed, returns absolute path
"""

from app.core.ffmpeg.manager import ffmpeg_manager


def ensure_ffmpeg() -> str:
    """Ensure a usable ffmpeg binary exists and return its absolute path.

    Uses the system binary when available; falls back to downloading
    a managed binary via ``imageio-ffmpeg``.
    """
    return ffmpeg_manager.get()
