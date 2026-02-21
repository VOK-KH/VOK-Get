"""Single-download worker: yt-dlp in a thread with progress and log signals."""

import os
import re
from typing import Callable

from PyQt5.QtCore import QThread, pyqtSignal

from app.common.paths import DOWNLOADS_DIR

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


class DownloadWorker(QThread):
    """Runs yt-dlp in a thread. Emits log_line, progress, finished_signal."""

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
        job_id: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.url = url.strip()
        self.output_dir = output_dir or str(DOWNLOADS_DIR)
        self.format_key = format_key
        self.single_video = single_video
        self.concurrent_fragments = max(1, min(16, int(concurrent_fragments)))
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
            self.finished_signal.emit(False, "yt-dlp not installed.")
            return

        os.makedirs(self.output_dir, exist_ok=True)
        out_tmpl = os.path.join(self.output_dir, "%(title)s.%(ext)s")

        format_map = {
            "Best (video+audio)": "best",
            "Best video": "bestvideo",
            "Best audio": "bestaudio",
            "Video (mp4)": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "Audio (mp3)": "bestaudio[ext=m4a]/bestaudio/best",
        }
        fkey = format_map.get(self.format_key, "best")
        is_audio_only = "audio" in self.format_key.lower() or "mp3" in self.format_key.lower()

        def progress_hook(d):
            if self._cancelled:
                raise yt_dlp.utils.DownloadCancelled()
            if d.get("status") == "downloading" and "total_bytes" in d:
                total = d.get("total_bytes") or 1
                done = d.get("downloaded_bytes", 0)
                self.progress.emit(done / total if total else 0.0)
            elif d.get("status") == "finished":
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

        opts = {
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
            "js_runtimes": {"deno": {}, "node": {}},
        }

        if is_audio_only and "Audio (mp3)" == self.format_key:
            opts["postprocessors"] = [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([self.url])
            if self._cancelled:
                self.finished_signal.emit(False, "Cancelled.")
            else:
                self.finished_signal.emit(True, "Download completed.")
        except yt_dlp.utils.DownloadCancelled:
            self.finished_signal.emit(False, "Cancelled.")
        except Exception as e:
            log_emit(str(e))
            self.finished_signal.emit(False, str(e))
