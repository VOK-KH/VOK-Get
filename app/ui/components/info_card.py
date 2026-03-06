# coding: utf-8
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    BodyLabel,
    TransparentToolButton,
    FluentIcon,
    ImageLabel,
    SimpleCardWidget,
    HyperlinkLabel,
    VerticalSeparator,
    PrimaryPushButton,
    TitleLabel,
    PillPushButton,
    setFont,
)

from .statistic_widget import StatisticsWidget


class AppInfoCard(SimpleCardWidget):
    """App information card (generic, no m3u8 branding)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)
        try:
            icon = QIcon(":/app/images/ico/M3U8DL.ico").pixmap(120, 120)
        except Exception:
            icon = QIcon().pixmap(120, 120)
        self.iconLabel = ImageLabel(icon, self)
        self.nameLabel = TitleLabel(self.tr("VOK Download"), self)
        self.updateButton = PrimaryPushButton(self.tr("Update"), self)
        self.companyLabel = HyperlinkLabel(
            QUrl("https://github.com"), self.tr("VOK"), self
        )

        self.versionWidget = StatisticsWidget(self.tr("Version"), "v0.1.0", self)
        self.fileSizeWidget = StatisticsWidget(self.tr("File Size"), "—", self)
        self.updateTimeWidget = StatisticsWidget(self.tr("Update Time"), "—", self)

        self.descriptionLabel = BodyLabel(
            self.tr("Download and enhance tools."), self
        )
        self.tagButton = PillPushButton(self.tr("App"), self)
        self.shareButton = TransparentToolButton(FluentIcon.SHARE, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.__initWidgets()

    def __initWidgets(self):
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(120)
        self.updateButton.setFixedWidth(160)
        self.descriptionLabel.setWordWrap(True)
        self.tagButton.setCheckable(False)
        setFont(self.tagButton, 12)
        self.tagButton.setFixedSize(80, 32)
        self.shareButton.setFixedSize(32, 32)
        self.shareButton.setIconSize(QSize(14, 14))
        self.nameLabel.setObjectName("nameLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")
        self.initLayout()

    def initLayout(self):
        self.hBoxLayout.setSpacing(30)
        self.hBoxLayout.setContentsMargins(34, 24, 24, 24)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.updateButton, 0, Qt.AlignRight)
        self.vBoxLayout.addSpacing(3)
        self.vBoxLayout.addWidget(self.companyLabel)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addLayout(self.statisticsLayout)
        self.statisticsLayout.setContentsMargins(0, 0, 0, 0)
        self.statisticsLayout.setSpacing(10)
        self.statisticsLayout.addWidget(self.versionWidget)
        self.statisticsLayout.addWidget(VerticalSeparator())
        self.statisticsLayout.addWidget(self.fileSizeWidget)
        self.statisticsLayout.addWidget(VerticalSeparator())
        self.statisticsLayout.addWidget(self.updateTimeWidget)
        self.statisticsLayout.setAlignment(Qt.AlignLeft)
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)
        self.vBoxLayout.addSpacing(12)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.buttonLayout.addWidget(self.tagButton, 0, Qt.AlignLeft)
        self.buttonLayout.addWidget(self.shareButton, 0, Qt.AlignRight)

    def setVersion(self, version: str):
        text = version or "0.1.0"
        self.versionWidget.valueLabel.setText(text)
        self.versionWidget.valueLabel.setTextColor(
            QColor(0, 0, 0), QColor(255, 255, 255)
        )


# Backward compatibility
M3U8DLInfoCard = AppInfoCard
