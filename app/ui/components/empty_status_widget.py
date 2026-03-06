# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import IconWidget, CaptionLabel, SimpleCardWidget, isDarkTheme


class EmptyStatusWidget(SimpleCardWidget):
    """Empty-state card with icon and message."""

    def __init__(self, icon, text, parent=None):
        super().__init__(parent=parent)
        self.iconWidget = IconWidget(icon)
        self.label = CaptionLabel(text)
        self.vBoxLayout = QVBoxLayout(self)
        self._init_widget()

    def _init_widget(self):
        self.setBorderRadius(10)
        self.iconWidget.setFixedSize(80, 80)
        self.label.setTextColor(QColor(96, 96, 96), QColor(216, 216, 216))
        self.label.setAlignment(Qt.AlignCenter)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(16, 20, 16, 20)
        self.vBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignHCenter)
        self.vBoxLayout.addWidget(self.label, 0, Qt.AlignHCenter)

    def setIcon(self, icon):
        self.iconWidget.setIcon(icon)

    def setText(self, text):
        self.label.setText(text)

    def _normalBackgroundColor(self):
        return QColor(255, 255, 255, 13 if isDarkTheme() else 200)

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setBrush(self.backgroundColor)
        painter.setPen(Qt.NoPen)
        r = self.borderRadius
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), r, r)
