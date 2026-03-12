"""Command bar for the task download interface: Download Settings, Clipboard, Enhance, Add Link, Clear, Start Download."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import Action, CommandBar, PrimaryPushButton, ToolButton, ToolTipFilter
from qfluentwidgets import FluentIcon as FIF


class TaskCommandBar(QWidget):
    """Command bar widget with actions and Start Download button. Emits signals for parent handling."""

    download_settings_clicked = pyqtSignal()
    clipboard_observer_clicked = pyqtSignal()
    clipboard_settings_clicked = pyqtSignal()
    subtitle_optimization_changed = pyqtSignal(bool)
    enhance_configure_clicked = pyqtSignal()
    add_link_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    start_download_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 8, 0, 0)

        self.command_bar = CommandBar(self)
        self.command_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # type: ignore
        layout.addWidget(self.command_bar, 1)

        # Download Settings
        download_settings_action = Action(
            FIF.SETTING,
            self.tr("Download Settings"),
            triggered=self.download_settings_clicked.emit,
        )
        download_settings_action.setToolTip(self.tr("Configure download options"))
        self.command_bar.addAction(download_settings_action)
        self.command_bar.addSeparator()

        # Clipboard Observer (checkable)
        self.clipboard_observer_btn = ToolButton(FIF.PASTE, self)
        self.clipboard_observer_btn.setCheckable(True)
        self.clipboard_observer_btn.clicked.connect(self.clipboard_observer_clicked.emit)
        self.clipboard_observer_btn.setToolTip(self.tr("Enable or Disable Clipboard Monitor"))
        self.clipboard_observer_btn.setToolTipDuration(3000)
        self.clipboard_observer_btn.installEventFilter(ToolTipFilter(self.clipboard_observer_btn))
        self.command_bar.addWidget(self.clipboard_observer_btn)

        # Clipboard Settings
        self.clipboard_settings_btn = ToolButton(FIF.FILTER, self)
        self.clipboard_settings_btn.clicked.connect(self.clipboard_settings_clicked.emit)
        self.clipboard_settings_btn.setToolTip(
            self.tr("Configure Clipboard Monitor (interval, filters)")
        )
        self.clipboard_settings_btn.setToolTipDuration(3000)
        self.clipboard_settings_btn.installEventFilter(ToolTipFilter(self.clipboard_settings_btn))
        self.clipboard_settings_btn.setEnabled(False)
        self.command_bar.addWidget(self.clipboard_settings_btn)

        self.command_bar.addSeparator()

        # Enhance (checkable)
        self.optimize_button = Action(
            FIF.ZOOM_IN,
            self.tr(""),
            triggered=lambda: self.subtitle_optimization_changed.emit(self.optimize_button.isChecked()),
            checkable=True,
        )
        self.optimize_button.setToolTip(self.tr("Enable or Disable Enhance"))
        self.command_bar.addAction(self.optimize_button)

        # Enhance Settings
        self.enhance_settings_action = Action(
            FIF.BUS,
            self.tr(""),
            triggered=self.enhance_configure_clicked.emit,
        )
        self.enhance_settings_action.setToolTip(self.tr("Configure Enhance"))
        self.command_bar.addAction(self.enhance_settings_action)

        self.command_bar.addSeparator()

        # Add Link
        add_link_action = Action(
            FIF.ADD,
            self.tr("Add Link"),
            triggered=self.add_link_clicked.emit,
        )
        add_link_action.setToolTip(self.tr("Add a video URL and analyze its info (Ctrl+V)"))
        self.command_bar.addAction(add_link_action)

        # Clear
        self.command_bar.addAction(
            Action(FIF.DELETE, self.tr("Clear"), triggered=self.clear_clicked.emit)
        )

        # Start Download
        self.start_button = PrimaryPushButton(self.tr("Start Download"), self, icon=FIF.DOWNLOAD)
        self.start_button.setFixedHeight(34)
        self.start_button.clicked.connect(self.start_download_clicked.emit)
        layout.addWidget(self.start_button)
