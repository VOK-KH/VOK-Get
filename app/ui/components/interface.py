# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QVBoxLayout

from qfluentwidgets import ScrollArea, setFont, TitleLabel


class Interface(ScrollArea):
    """Scrollable page with title."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.titleLabel = TitleLabel(self.view)
        self.vBoxLayout = QVBoxLayout(self)
        self.viewLayout = QVBoxLayout(self.view)
        self.__initWidgets()

    def __initWidgets(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.vBoxLayout.setContentsMargins(30, 33, 30, 10)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        setFont(self.titleLabel, 23, QFont.DemiBold)
        self.enableTransparentBackground()

    def setTitle(self, title: str):
        self.titleLabel.setText(title)
        self.setObjectName(title)
