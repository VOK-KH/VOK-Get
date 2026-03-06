# coding: utf-8
from PyQt5.QtWidgets import QWidget, QHBoxLayout

from qfluentwidgets import IconWidget, BodyLabel


class HintWidget(QWidget):
    """Hint row: icon + text."""

    def __init__(self, icon, text, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.iconWidget = IconWidget(icon)
        self.label = BodyLabel(text)
        self.iconWidget.setFixedSize(16, 16)
        self.hBoxLayout.setContentsMargins(24, 24, 24, 24)
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addWidget(self.label)
        self.hBoxLayout.setSpacing(10)
