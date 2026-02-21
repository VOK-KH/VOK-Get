"""Downloader view: multi-job download queue with progress and process log."""

import re
from datetime import datetime

from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    ElevatedCardWidget,
    FluentIcon,
    IndeterminateProgressBar,
    LineEdit,
    ProgressBar,
    PrimaryPushButton,
    PushButton,
    SwitchButton,
)

from app.common.paths import DOWNLOADS_DIR
from app.common.state import add_log_entry
from app.config import load_settings
from app.core.manager import DownloadJob, DownloadManager
from app.ui.components import CardHeader, StatusTable

from .base import BaseView

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


class DownloaderView(BaseView):
    """Multi-job downloader: queues jobs via DownloadManager, shows live progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloader")

        self._manager = DownloadManager(parent=self)
        self._manager.log_line.connect(lambda _jid, msg: self._log_append(msg))
        self._manager.progress.connect(self._on_progress)
        self._manager.job_finished.connect(self._on_job_finished)
        self._active_jobs: set[str] = set()

        # ── URL & output card ─────────────────────────────────────────────
        url_card = ElevatedCardWidget(self)
        url_layout = QVBoxLayout(url_card)
        url_layout.setSpacing(10)
        url_layout.addWidget(CardHeader(FluentIcon.LINK, "Video URL & output", url_card))

        url_row = QHBoxLayout()
        url_row.addWidget(BodyLabel("URL", url_card))
        self._url_edit = LineEdit(url_card)
        self._url_edit.setPlaceholderText("https://…")
        self._url_edit.setClearButtonEnabled(True)
        url_row.addWidget(self._url_edit, 1)
        url_layout.addLayout(url_row)

        path_row = QHBoxLayout()
        path_row.addWidget(BodyLabel("Output folder", url_card))
        self._path_edit = LineEdit(url_card)
        self._path_edit.setPlaceholderText(str(DOWNLOADS_DIR))
        self._path_edit.setText(load_settings().get("download_path", str(DOWNLOADS_DIR)))
        browse_btn = PushButton("Browse…", url_card)
        browse_btn.clicked.connect(self._browse_output)
        path_row.addWidget(self._path_edit, 1)
        path_row.addWidget(browse_btn)
        url_layout.addLayout(path_row)

        single_row = QHBoxLayout()
        single_row.addWidget(BodyLabel("Single video only (no playlist)", url_card))
        single_row.addStretch(1)
        self._single_switch = SwitchButton(url_card)
        self._single_switch.setChecked(load_settings().get("single_video_default", True))
        single_row.addWidget(self._single_switch)
        url_layout.addLayout(single_row)

        self._layout.addWidget(url_card)

        # ── Format & actions card ─────────────────────────────────────────
        fmt_card = CardWidget(self)
        fmt_layout = QVBoxLayout(fmt_card)
        fmt_layout.setSpacing(10)
        fmt_layout.addWidget(CardHeader(FluentIcon.MEDIA, "Format & actions", fmt_card))

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(BodyLabel("Format", fmt_card))
        self._format_combo = ComboBox(fmt_card)
        self._format_combo.addItems([
            "Best (video+audio)",
            "Best video",
            "Best audio",
            "Video (mp4)",
            "Audio (mp3)",
        ])
        fmt_row.addWidget(self._format_combo)
        fmt_row.addStretch(1)
        self._jobs_label = BodyLabel("", fmt_card)
        fmt_row.addWidget(self._jobs_label)
        self._start_btn = PrimaryPushButton("Download", fmt_card)
        self._start_btn.setIcon(FluentIcon.DOWNLOAD)
        self._start_btn.clicked.connect(self._start_download)
        self._stop_btn = PushButton("Stop all", fmt_card)
        self._stop_btn.setIcon(FluentIcon.CANCEL)
        self._stop_btn.clicked.connect(self._stop_all)
        self._stop_btn.setEnabled(False)
        fmt_row.addWidget(self._start_btn)
        fmt_row.addWidget(self._stop_btn)
        fmt_layout.addLayout(fmt_row)
        self._layout.addWidget(fmt_card)

        # ── Progress ──────────────────────────────────────────────────────
        self._progress_indet = IndeterminateProgressBar(self)
        self._progress_indet.setVisible(False)
        self._layout.addWidget(self._progress_indet)

        self._progress = ProgressBar(self)
        self._progress.setVisible(False)
        self._layout.addWidget(self._progress)

        # ── Download process log card ─────────────────────────────────────
        proc_card = CardWidget(self)
        proc_layout = QVBoxLayout(proc_card)
        proc_layout.setSpacing(10)

        proc_hdr = QHBoxLayout()
        proc_hdr.addWidget(CardHeader(FluentIcon.HISTORY, "Download log", proc_card))
        clear_btn = PushButton("Clear", proc_card)
        clear_btn.setIcon(FluentIcon.DELETE)
        clear_btn.clicked.connect(lambda: self._process_table.setRowCount(0))
        proc_hdr.addWidget(clear_btn)
        proc_layout.addLayout(proc_hdr)

        self._process_table = StatusTable(proc_card)
        self._process_table.setMinimumHeight(220)
        proc_layout.addWidget(self._process_table)
        self._layout.addWidget(proc_card)

        self._layout.addStretch(1)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Output folder", self._path_edit.text())
        if path:
            self._path_edit.setText(path)

    def _log_append(self, text: str):
        clean = _strip_ansi(text.strip())
        if not clean:
            return
        if clean.lower().startswith("[error]") or "error:" in clean.lower():
            status = "error"
        elif "[download]" in clean.lower():
            status = "download"
        elif "[warning]" in clean.lower():
            status = "warning"
        else:
            status = "info"
        time_str = datetime.now().strftime("%H:%M:%S")
        self._process_table.append_row(time_str, status, clean)
        add_log_entry(status, clean)

    def _update_controls(self):
        count = len(self._active_jobs)
        self._stop_btn.setEnabled(count > 0)
        self._jobs_label.setText(f"{count} active" if count else "")

    # ── Download control ──────────────────────────────────────────────────

    def _start_download(self):
        url = self._url_edit.text().strip()
        if not url:
            self._log_append("Enter a URL first.")
            return

        job = DownloadJob(
            url=url,
            output_dir=self._path_edit.text().strip() or str(DOWNLOADS_DIR),
            format_key=self._format_combo.currentText(),
            single_video=self._single_switch.isChecked(),
        )
        self._active_jobs.add(job.job_id)
        self._log_append(f"Queued: {url}")
        self._manager.enqueue(job)
        self._progress_indet.setVisible(True)
        self._progress.setVisible(False)
        self._update_controls()

    def _on_progress(self, job_id: str, value: float):
        self._progress_indet.setVisible(False)
        self._progress.setVisible(True)
        if value < 0:
            self._progress.setRange(0, 0)
        else:
            self._progress.setRange(0, 100)
            self._progress.setValue(int(value * 100))

    def _stop_all(self):
        self._manager.cancel_all()
        self._log_append("Cancelling all active downloads…")

    def _on_job_finished(self, job_id: str, success: bool, message: str):
        self._active_jobs.discard(job_id)
        self._log_append(message)
        if not self._active_jobs:
            self._progress_indet.setVisible(False)
            self._progress.setVisible(False)
        self._update_controls()
