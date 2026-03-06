# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import BodyLabel, CaptionLabel, setFont


class StatisticsWidget(QWidget):
    """Title + value statistic row."""

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = CaptionLabel(title, self)
        self.valueLabel = BodyLabel(value, self)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 0, 16, 0)
        self.vBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignTop)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignBottom)
        setFont(self.valueLabel, 18, QFont.DemiBold)
        self.titleLabel.setObjectName("titleLabel")
        self.valueLabel.setObjectName("valueLabel")
