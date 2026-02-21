"""Downloader view: full UI for video/download using core.DownloadWorker."""

import re

from PyQt5.QtWidgets import QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    LineEdit,
    PlainTextEdit,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    SubtitleLabel,
)

from app.common.paths import DOWNLOADS_DIR
from app.common.state import add_log_entry
from app.config import load_settings
from app.core.download import DownloadWorker

from .base import BaseView

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


class DownloaderView(BaseView):
    """Full download tools: URL, path, format, start/stop, progress, log."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloader")
        self._worker: DownloadWorker | None = None

        card_input = QGroupBox("Video URL & output")
        layout_input = QGridLayout(card_input)
        self._url_edit = LineEdit(self)
        self._url_edit.setPlaceholderText("https://...")
        self._url_edit.setClearButtonEnabled(True)
        self._path_edit = LineEdit(self)
        self._path_edit.setPlaceholderText(str(DOWNLOADS_DIR))
        self._path_edit.setText(load_settings().get("download_path", str(DOWNLOADS_DIR)))
        browse_btn = PushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output)
        layout_input.addWidget(BodyLabel("URL"), 0, 0)
        layout_input.addWidget(self._url_edit, 0, 1, 1, 2)
        layout_input.addWidget(BodyLabel("Output folder"), 1, 0)
        layout_input.addWidget(self._path_edit, 1, 1)
        layout_input.addWidget(browse_btn, 1, 2)
        self._single_video_cb = CheckBox("Single video only (no playlist)")
        self._single_video_cb.setChecked(load_settings().get("single_video_default", True))
        layout_input.addWidget(self._single_video_cb, 2, 0, 1, 3)
        self._layout.addWidget(card_input)

        card_format = QGroupBox("Format & actions")
        layout_fmt = QHBoxLayout(card_format)
        self._format_combo = ComboBox(self)
        self._format_combo.addItems([
            "Best (video+audio)",
            "Best video",
            "Best audio",
            "Video (mp4)",
            "Audio (mp3)",
        ])
        layout_fmt.addWidget(SubtitleLabel("Format"))
        layout_fmt.addWidget(self._format_combo)
        layout_fmt.addStretch(1)
        self._start_btn = PrimaryPushButton("Start download")
        self._start_btn.clicked.connect(self._start_download)
        self._stop_btn = PushButton("Stop")
        self._stop_btn.clicked.connect(self._stop_download)
        self._stop_btn.setEnabled(False)
        layout_fmt.addWidget(self._start_btn)
        layout_fmt.addWidget(self._stop_btn)
        self._layout.addWidget(card_format)

        self._progress = ProgressBar(self)
        self._progress.setVisible(False)
        self._layout.addWidget(self._progress)

        card_log = QGroupBox("Log")
        log_layout = QVBoxLayout(card_log)
        self._log = PlainTextEdit(self)
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(200)
        log_layout.addWidget(self._log)
        self._layout.addWidget(card_log)

        self._layout.addStretch(1)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Output folder", self._path_edit.text())
        if path:
            self._path_edit.setText(path)

    def _log_append(self, text: str):
        clean = _strip_ansi(text.strip())
        self._log.appendPlainText(clean)
        scrollbar = self._log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        level = "error" if clean.lower().startswith("[error]") or "error:" in clean.lower() else "info"
        add_log_entry(level, clean)

    def _start_download(self):
        url = self._url_edit.text().strip()
        if not url:
            self._log_append("Enter a URL first.")
            return
        self._log.clear()
        self._log_append(f"Starting: {url}")
        self._progress.setVisible(True)
        self._progress.setRange(0, 0)
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

        s = load_settings()
        self._worker = DownloadWorker(
            url,
            self._path_edit.text().strip() or str(DOWNLOADS_DIR),
            self._format_combo.currentText(),
            single_video=self._single_video_cb.isChecked(),
            concurrent_fragments=max(1, min(16, int(s.get("concurrent_fragments", 4)))),
        )
        self._worker.log_line.connect(self._log_append)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, value: float):
        if value < 0:
            self._progress.setRange(0, 0)
        else:
            self._progress.setRange(0, 100)
            self._progress.setValue(int(value * 100))

    def _stop_download(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._log_append("Cancelling...")

    def _on_finished(self, success: bool, message: str):
        self._progress.setVisible(False)
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._worker = None
        self._log_append(message)
