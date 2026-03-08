# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel


class ActiveBadge(QLabel):
    """Small pill showing active (downloading + enhancing) job count."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(22, 22)
        self.hide()

    def set_count(self, n: int) -> None:
        if n > 0:
            self.setText(str(n))
            self.setStyleSheet(
                "QLabel { background: #FF5252; color: white; border-radius: 11px;"
                " font-size: 10px; font-weight: 700; }"
            )
            self.show()
        else:
            self.hide()
