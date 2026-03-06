# coding: utf-8
"""FFmpeg package — binary management and availability.

Usage
-----
from app.core.ffmpeg import ffmpeg_available, ffmpeg_manager
"""

from app.core.ffmpeg.manager import FFmpegManager, ffmpeg_available, ffmpeg_manager

__all__ = ["FFmpegManager", "ffmpeg_available", "ffmpeg_manager"]
