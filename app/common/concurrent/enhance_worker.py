# coding: utf-8
"""EnhancePostProcessWorker — runs ffmpeg post-processing in a QThread."""

from typing import TYPE_CHECKING

from PyQt5.QtCore import QThread, pyqtSignal

from app.core.enhance.runner import run_enhance

if TYPE_CHECKING:
    from app.ui.components.download_enhance_feature import EnhanceOptions


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
