"""Logs view: log entries table with Clear and Export actions."""

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
)
from qfluentwidgets import BodyLabel, LargeTitleLabel, PushButton

from app.common.state import clear_log_entries, get_log_entries

from .base import BaseView


class LogsView(BaseView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Logs")

        title = LargeTitleLabel(self)
        title.setText("Logs")
        self._layout.addWidget(title)
        body = BodyLabel(self)
        body.setText("Application log entries. Use Clear or Export as needed.")
        self._layout.addWidget(body)

        card = QGroupBox("Log data")
        card_layout = QVBoxLayout(card)
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Time", "Level", "Message"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(220)
        card_layout.addWidget(self._table)

        btn_layout = QHBoxLayout()
        self._refresh_btn = PushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_table)
        self._clear_btn = PushButton("Clear")
        self._clear_btn.clicked.connect(self._clear_logs)
        self._export_btn = PushButton("Export...")
        self._export_btn.clicked.connect(self._export_logs)
        btn_layout.addWidget(self._refresh_btn)
        btn_layout.addWidget(self._clear_btn)
        btn_layout.addWidget(self._export_btn)
        btn_layout.addStretch()
        card_layout.addLayout(btn_layout)
        self._layout.addWidget(card)

        self._refresh_table()

    def _refresh_table(self):
        entries = get_log_entries()
        self._table.setRowCount(len(entries))
        for i, e in enumerate(entries):
            self._table.setItem(i, 0, QTableWidgetItem(e.get("time", "")))
            self._table.setItem(i, 1, QTableWidgetItem(e.get("level", "")))
            self._table.setItem(i, 2, QTableWidgetItem(e.get("message", "")))
        if not entries:
            self._table.setRowCount(1)
            self._table.setItem(0, 0, QTableWidgetItem(""))
            self._table.setItem(0, 1, QTableWidgetItem(""))
            self._table.setItem(0, 2, QTableWidgetItem("No log entries yet."))

    def _clear_logs(self):
        clear_log_entries()
        self._refresh_table()

    def _export_logs(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export logs",
            str(Path.home() / "vok_logs.txt"),
            "Text files (*.txt);;All files (*)",
        )
        if not path:
            return
        entries = get_log_entries()
        try:
            with open(path, "w", encoding="utf-8") as f:
                for e in entries:
                    f.write(f"{e.get('time', '')}\t{e.get('level', '')}\t{e.get('message', '')}\n")
        except OSError:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_table()
