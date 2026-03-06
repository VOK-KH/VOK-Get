"""Post-download stream edit: ffmpeg overlay (logo), flip, color, speed."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtCore import QThread, pyqtSignal

if TYPE_CHECKING:
    from app.ui.components.download_enhance_feature import EnhanceOptions


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _build_video_filters(opts: "EnhanceOptions", has_logo: bool) -> str:
    """Build -filter_complex video part. Returns the filter string for [0:v] (and optionally [1:v] for logo)."""
    parts: list[str] = []
    # Optional flip
    if opts.flip == "horizontal":
        parts.append("hflip")
    elif opts.flip == "vertical":
        parts.append("vflip")
    elif opts.flip == "both":
        parts.append("hflip,vflip")
    # Color: map -100..100 to eq. brightness -0.5..0.5, contrast 0.5..1.5, saturation 0.5..1.5
    b = opts.brightness / 200.0
    c = 1.0 + opts.contrast / 200.0
    s = 1.0 + opts.saturation / 200.0
    if b != 0 or c != 1.0 or s != 1.0:
        parts.append(f"eq=brightness={b}:contrast={c}:saturation={s}")
    # Speed
    if opts.speed != 1.0:
        parts.append(f"setpts={1.0 / opts.speed}*PTS")
    base_vf = ",".join(parts) if parts else "copy"

    if not has_logo:
        return f"[0:v]{base_vf}[vout]" if base_vf != "copy" else "[0:v]copy[vout]"

    # With logo: scale logo (max height 120px), overlay at position, then apply rest
    pos = opts.logo_position
    if pos == "left":
        overlay_xy = "10:10"
    elif pos == "right":
        overlay_xy = "main_w-overlay_w-10:10"
    elif pos == "top":
        overlay_xy = "(main_w-overlay_w)/2:10"
    else:
        overlay_xy = "(main_w-overlay_w)/2:(main_h-overlay_h)/2"
    logo_scale = "[1:v]scale=-1:120[logo]"
    overlay = f"[0:v][logo]overlay={overlay_xy}[v1]"
    if base_vf and base_vf != "copy":
        rest = f"[v1]{base_vf}[vout]"
        return f"{logo_scale};{overlay};{rest}"
    return f"{logo_scale};{overlay};[v1]copy[vout]"


def run_enhance(
    input_path: str,
    output_path: str,
    opts: "EnhanceOptions",
) -> tuple[bool, str, int]:
    """Run ffmpeg to apply logo, flip, color, speed. Returns (success, message, output_size_bytes)."""
    if not ffmpeg_available():
        return False, "ffmpeg is not installed. Install ffmpeg for stream edit.", -1
    if not input_path or not os.path.isfile(input_path):
        return False, "Input file not found.", -1
    has_logo = bool(opts.logo_path and os.path.isfile(opts.logo_path))
    video_filters = _build_video_filters(opts, has_logo)
    # Audio: speed change
    audio_filter = f"atempo={opts.speed}" if opts.speed != 1.0 else "copy"
    # Build command
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
    ]
    if has_logo:
        cmd.extend(["-i", opts.logo_path])
    cmd.extend([
        "-filter_complex", video_filters,
        "-map", "[vout]",
        "-map", "0:a?",
    ])
    if opts.speed != 1.0:
        cmd.extend(["-filter:a", audio_filter])
    else:
        cmd.extend(["-c:a", "copy"])
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-movflags", "+faststart",
        output_path,
    ])
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "")[-800:]
            return False, f"ffmpeg failed: {err}", -1
        size = os.path.getsize(output_path) if os.path.isfile(output_path) else -1
        return True, "Enhance completed.", size
    except subprocess.TimeoutExpired:
        return False, "ffmpeg timed out.", -1
    except Exception as e:
        return False, str(e), -1


class EnhancePostProcessWorker(QThread):
    """Runs run_enhance in a background thread. Emits log_line and finished_signal."""

    log_line = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, str, int)  # success, message, output_path, size_bytes

    def __init__(
        self,
        input_path: str,
        output_path: str,
        opts: "EnhanceOptions",
        job_id: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._input_path = input_path
        self._output_path = output_path
        self._opts = opts
        self._job_id = job_id
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        self.log_line.emit("[info] Enhance: applying logo, flip, color, speed…")
        success, message, size = run_enhance(
            self._input_path,
            self._output_path,
            self._opts,
        )
        if self._cancelled:
            self.finished_signal.emit(False, "Enhance cancelled.", "", -1)
            return
        self.log_line.emit(f"[info] {message}")
        self.finished_signal.emit(success, message, self._output_path if success else "", size)
