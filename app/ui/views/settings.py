"""Settings view: data table and Save / Reset actions."""

from pathlib import Path

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, LargeTitleLabel, LineEdit, CheckBox, PushButton, PrimaryPushButton, SpinBox

from app.common.paths import DOWNLOADS_DIR
from app.common.state import add_log_entry
from app.config import load_settings, save_settings

from .base import BaseView


class SettingsView(BaseView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")

        title = LargeTitleLabel(self)
        title.setText("Settings")
        self._layout.addWidget(title)
        body = BodyLabel(self)
        body.setText("Application settings. Edit in the table and use Save or Reset.")
        self._layout.addWidget(body)

        # Settings table: Name | Value (we use delegates or embedded widgets for value)
        card = QGroupBox("Settings data")
        card_layout = QVBoxLayout(card)
        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Setting", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(180)
        card_layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        self._save_btn = PrimaryPushButton("Save")
        self._save_btn.clicked.connect(self._save)
        self._reset_btn = PushButton("Reset")
        self._reset_btn.clicked.connect(self._reset)
        btn_layout.addWidget(self._save_btn)
        btn_layout.addWidget(self._reset_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)
        self._layout.addWidget(card)

        self._path_edit = None
        self._single_video_cb = None
        self._concurrent_downloads_spin = None
        self._concurrent_fragments_spin = None
        self._reset()

    def _reset(self):
        s = load_settings()
        self._table.setRowCount(4)

        self._table.setItem(0, 0, QTableWidgetItem("Download path"))
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        self._path_edit = LineEdit()
        self._path_edit.setText(s.get("download_path", str(DOWNLOADS_DIR)))
        self._path_edit.setPlaceholderText(str(DOWNLOADS_DIR))
        browse_btn = PushButton("Browse...")
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(self._path_edit)
        path_layout.addWidget(browse_btn)
        self._table.setCellWidget(0, 1, path_widget)

        self._table.setItem(1, 0, QTableWidgetItem("Single video only (default)"))
        self._single_video_cb = CheckBox()
        self._single_video_cb.setChecked(s.get("single_video_default", True))
        self._table.setCellWidget(1, 1, self._single_video_cb)

        self._table.setItem(2, 0, QTableWidgetItem("Concurrent downloads (parallel jobs)"))
        self._concurrent_downloads_spin = SpinBox()
        self._concurrent_downloads_spin.setRange(1, 4)
        self._concurrent_downloads_spin.setValue(int(s.get("concurrent_downloads", 2)))
        self._table.setCellWidget(2, 1, self._concurrent_downloads_spin)

        self._table.setItem(3, 0, QTableWidgetItem("Concurrent fragments per download"))
        self._concurrent_fragments_spin = SpinBox()
        self._concurrent_fragments_spin.setRange(1, 16)
        self._concurrent_fragments_spin.setValue(int(s.get("concurrent_fragments", 4)))
        self._table.setCellWidget(3, 1, self._concurrent_fragments_spin)

    def _save(self):
        path = self._path_edit.text().strip() or str(DOWNLOADS_DIR)
        single = self._single_video_cb.isChecked()
        s = load_settings()
        s["download_path"] = path
        s["single_video_default"] = single
        s["concurrent_downloads"] = self._concurrent_downloads_spin.value()
        s["concurrent_fragments"] = self._concurrent_fragments_spin.value()
        save_settings(s)
        add_log_entry("info", "Settings saved.")

    def _browse_path(self):
        start = self._path_edit.text() or str(DOWNLOADS_DIR)
        path = QFileDialog.getExistingDirectory(self, "Download folder", start)
        if path:
            self._path_edit.setText(path)
