"""Single-download worker: yt-dlp in a thread with progress and log signals.

Supported platforms include (but are not limited to):
  YouTube, ok.ru, VK, Twitter/X, TikTok, Instagram, Twitch, Vimeo,
  Dailymotion, SoundCloud, Bilibili, Reddit, Facebook, and 1 000+ more
  via yt-dlp's extractor library.

For platforms that require authentication (e.g. ok.ru private videos,
Instagram stories) pass a Netscape-format cookies file via `cookies_file`.
"""

import os
import re
from typing import Callable

from PyQt5.QtCore import QThread, pyqtSignal

from app.common.paths import DOWNLOADS_DIR

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Domains whose extractors are confirmed working with yt-dlp
SUPPORTED_DOMAINS = (
    "youtube.com", "youtu.be",
    "ok.ru",
    "vk.com", "vkvideo.ru",
    "twitter.com", "x.com",
    "tiktok.com",
    "instagram.com",
    "twitch.tv",
    "vimeo.com",
    "dailymotion.com",
    "soundcloud.com",
    "bilibili.com",
    "reddit.com",
    "facebook.com",
)


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def detect_platform(url: str) -> str:
    """Return a short platform name from the URL, or 'Unknown'."""
    url_lower = url.lower()
    for domain in SUPPORTED_DOMAINS:
        if domain in url_lower:
            return domain.split(".")[0].capitalize()
    return "Unknown"


class DownloadWorker(QThread):
    """Runs yt-dlp in a background thread.

    Signals
    -------
    log_line      str          — one line of console output
    progress      float        — 0.0 – 1.0 download progress
    finished_signal (bool, str) — (success, message)
    """

    log_line = pyqtSignal(str)
    progress = pyqtSignal(float)
    finished_signal = pyqtSignal(bool, str)

    def __init__(
        self,
        url: str,
        output_dir: str,
        format_key: str,
        single_video: bool = True,
        concurrent_fragments: int = 4,
        cookies_file: str = "",
        job_id: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.url = url.strip()
        self.output_dir = output_dir or str(DOWNLOADS_DIR)
        self.format_key = format_key
        self.single_video = single_video
        self.concurrent_fragments = max(1, min(16, int(concurrent_fragments)))
        self.cookies_file = cookies_file.strip() if cookies_file else ""
        self.job_id = job_id or url[:80]
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        if not self.url:
            self.finished_signal.emit(False, "No URL provided.")
            return
        try:
            import yt_dlp
        except ImportError:
            self.finished_signal.emit(False, "yt-dlp not installed. Run: pip install yt-dlp")
            return

        os.makedirs(self.output_dir, exist_ok=True)
        out_tmpl = os.path.join(self.output_dir, "%(title)s.%(ext)s")

        format_map = {
            "Best (video+audio)": "bv*+ba/b",
            "Best video": "bv",
            "Best audio": "ba",
            "Video (mp4)": "bv[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
            "Audio (mp3)": "ba[ext=m4a]/ba/b",
        }
        fkey = format_map.get(self.format_key, "bv*+ba/b")
        is_mp3 = self.format_key == "Audio (mp3)"

        def progress_hook(d: dict):
            if self._cancelled:
                raise yt_dlp.utils.DownloadCancelled()
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes", 0)
                if total:
                    self.progress.emit(done / total)
            elif status == "finished":
                self.progress.emit(1.0)

        def log_emit(msg: str):
            self.log_line.emit(_strip_ansi(msg))

        class LogLogger:
            def __init__(self, emit: Callable[[str], None]):
                self._emit = emit

            def debug(self, msg): self._emit(msg)
            def info(self, msg): self._emit(msg)
            def warning(self, msg): self._emit(f"[warning] {msg}")
            def error(self, msg): self._emit(f"[error] {msg}")

        opts: dict = {
            "outtmpl": out_tmpl,
            "format": fkey,
            "progress_hooks": [progress_hook],
            "logger": LogLogger(log_emit),
            "noprogress": False,
            "noplaylist": self.single_video,
            "socket_timeout": 120,
            "retries": 5,
            "fragment_retries": 5,
            "concurrent_fragment_downloads": self.concurrent_fragments,
        }

        if self.cookies_file and os.path.isfile(self.cookies_file):
            opts["cookiefile"] = self.cookies_file
            log_emit(f"[info] Using cookies: {self.cookies_file}")

        if is_mp3:
            opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ]

        platform = detect_platform(self.url)
        log_emit(f"[info] Platform detected: {platform}")

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            if self._cancelled:
                self.finished_signal.emit(False, "Cancelled.")
            else:
                self.finished_signal.emit(True, "Download completed.")
        except yt_dlp.utils.DownloadCancelled:
            self.finished_signal.emit(False, "Cancelled.")
        except Exception as exc:
            log_emit(str(exc))
            self.finished_signal.emit(False, str(exc))
