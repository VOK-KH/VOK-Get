# coding: utf-8
"""FFmpegManager — resolve the ffmpeg binary (system PATH or managed via imageio-ffmpeg).

Usage
-----
from app.core.ffmpeg.manager import ffmpeg_available, ffmpeg_manager

    path = ffmpeg_manager.get()   # str — absolute path to the binary
    ok   = ffmpeg_available()     # bool — True if binary is accessible
"""

import os
import shutil

import imageio_ffmpeg


class FFmpegManager:
    """Lazily resolves the ffmpeg binary, preferring the system install."""

    def __init__(self) -> None:
        self.ffmpeg_path: str | None = None

    def get(self) -> str:
        """Return the absolute path to a usable ffmpeg binary.

        Resolution order:
        1. Cached result from a previous call.
        2. System ffmpeg on PATH  (``shutil.which``).
        3. Managed binary provided by ``imageio-ffmpeg``.
        """
        if self.ffmpeg_path:
            return self.ffmpeg_path

        system = shutil.which("ffmpeg")
        if system:
            self.ffmpeg_path = system
        else:
            self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        os.environ["FFMPEG_BINARY"] = self.ffmpeg_path
        return self.ffmpeg_path

    def reset(self) -> None:
        """Clear the cached path so the next call to ``get()`` re-resolves it."""
        self.ffmpeg_path = None


ffmpeg_manager = FFmpegManager()


def ffmpeg_available() -> bool:
    """Return True if a usable ffmpeg binary can be found."""
    try:
        return bool(ffmpeg_manager.get())
    except Exception:
        return False
