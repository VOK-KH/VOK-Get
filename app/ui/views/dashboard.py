"""Dashboard view: overview and recent downloads table with actions."""

import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from qfluentwidgets import BodyLabel, LargeTitleLabel, PushButton, SubtitleLabel

from app.common.state import get_recent_downloads
from app.config import load_settings

from .base import BaseView


class DashboardView(BaseView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Dashboard")

        title = LargeTitleLabel(self)
        title.setText("Dashboard")
        self._layout.addWidget(title)
        subtitle = SubtitleLabel(self)
        subtitle.setText("Scail Media video downloader — recent downloads and quick actions.")
        self._layout.addWidget(subtitle)

        # Recent downloads table + actions
        card = QGroupBox("Recent downloads")
        card_main = QVBoxLayout(card)
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["File name", "Date", "Path"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(220)
        card_main.addWidget(self._table)

        btn_layout = QHBoxLayout()
        self._open_btn = PushButton("Open folder")
        self._open_btn.clicked.connect(self._open_download_folder)
        self._refresh_btn = PushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_table)
        btn_layout.addWidget(self._open_btn)
        btn_layout.addWidget(self._refresh_btn)
        btn_layout.addStretch()
        card_main.addLayout(btn_layout)
        self._layout.addWidget(card)

        self._refresh_table()

    def _refresh_table(self):
        rows = get_recent_downloads()
        self._table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(row["name"]))
            self._table.setItem(i, 1, QTableWidgetItem(row["date"]))
            self._table.setItem(i, 2, QTableWidgetItem(row["path"]))
        if not rows:
            self._table.setRowCount(1)
            self._table.setItem(0, 0, QTableWidgetItem("No downloads yet"))
            self._table.setItem(0, 1, QTableWidgetItem(""))
            self._table.setItem(0, 2, QTableWidgetItem(""))

    def _open_download_folder(self):
        path = load_settings().get("download_path", "")
        if path and Path(path).exists():
            os.startfile(path)
        else:
            path = str(Path.home() / "Downloads")
            if Path(path).exists():
                os.startfile(path)
