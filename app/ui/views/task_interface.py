# coding: utf-8
"""TaskInterface — recent downloads viewer."""

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon,
    LargeTitleLabel,
    PushButton,
    TableWidget,
    ToolButton,
)

from app.common.state import get_recent_downloads
from .base import BaseView


class TaskInterface(BaseView):
    """Displays recently downloaded files from the configured download folder."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TaskInterface")
        self._build_ui()
        self._load()

    # ── UI construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Header row
        header_row = QWidget()
        header_row.setStyleSheet("background: transparent;")
        h = QHBoxLayout(header_row)
        h.setContentsMargins(0, 0, 0, 0)

        title = LargeTitleLabel("Recent Downloads")
        self._count_label = QLabel("")
        self._count_label.setStyleSheet("color: grey; font-size: 13px;")

        refresh_btn = ToolButton(FluentIcon.SYNC)
        refresh_btn.setToolTip("Refresh")
        refresh_btn.clicked.connect(self._load)

        h.addWidget(title)
        h.addSpacing(12)
        h.addWidget(self._count_label, 1, Qt.AlignVCenter)
        h.addWidget(refresh_btn)

        # Table
        self._table = TableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["File Name", "Date", "Size", ""])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self._table.verticalHeader().hide()
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)

        self._layout.addWidget(header_row)
        self._layout.addWidget(self._table)

    # ── Data loading ─────────────────────────────────────────────────────

    def _load(self) -> None:
        files = get_recent_downloads()
        self._table.setRowCount(0)

        for row, entry in enumerate(files):
            self._table.insertRow(row)

            name_item = QTableWidgetItem(entry["name"])
            name_item.setData(Qt.UserRole, entry["path"])
            name_item.setToolTip(entry["path"])

            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, QTableWidgetItem(entry["date"]))
            self._table.setItem(row, 2, QTableWidgetItem(entry["size"]))

            open_btn = PushButton(FluentIcon.FOLDER, "Open")
            open_btn.setFixedWidth(90)
            open_btn.clicked.connect(lambda _, p=entry["path"]: self._open_file(p))

            cell = QWidget()
            cell.setStyleSheet("background: transparent;")
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(4, 2, 4, 2)
            cl.addWidget(open_btn)
            self._table.setCellWidget(row, 3, cell)

        count = len(files)
        self._count_label.setText(f"{count} file{'s' if count != 1 else ''}")

    # ── Actions ───────────────────────────────────────────────────────────

    @staticmethod
    def _open_file(path: str) -> None:
        """Open the file's containing folder."""
        if os.path.isfile(path):
            os.startfile(os.path.dirname(path))
        elif os.path.isdir(path):
            os.startfile(path)
