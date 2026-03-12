"""Command bar for the task download interface: Download Settings, Clipboard, Enhance, Add Link, Clear, Start Download."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import Action, CommandBar, PrimaryPushButton, ToolButton, ToolTipFilter, themeColor
from qfluentwidgets import FluentIcon as FIF


class TaskCommandBar(QWidget):
    """Command bar widget with actions and Start Download button. Emits signals for parent handling."""

    download_settings_clicked = pyqtSignal()
    clipboard_observer_clicked = pyqtSignal()
    clipboard_settings_clicked = pyqtSignal()
    enhance_enabled_changed = pyqtSignal(bool)
    enhance_settings_clicked = pyqtSignal()
    add_link_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    start_download_clicked = pyqtSignal()
    open_save_folder_clicked = pyqtSignal()

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

        try:
            _btn_accent = themeColor().name()
        except Exception:
            _btn_accent = "#0078d4"

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
        _clip_ss = f"""
            QToolButton {{
                border-radius: 4px;
                padding: 6px 10px;
                background-color: rgba(128, 128, 128, 0.2);
            }}
            QToolButton:hover {{
                background-color: rgba(128, 128, 128, 0.35);
            }}
            QToolButton:checked {{
                background-color: {_btn_accent};
            }}
            QToolButton:checked:hover {{
                background-color: {_btn_accent};
            }}
        """
        self.clipboard_observer_btn.setStyleSheet(_clip_ss)
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
        self.clipboard_settings_btn.setStyleSheet("""
            QToolButton {
                border-radius: 4px;
                padding: 6px 10px;
                background-color: rgba(128, 128, 128, 0.2);
            }
            QToolButton:hover {
                background-color: rgba(128, 128, 128, 0.35);
            }
        """)
        self.command_bar.addWidget(self.clipboard_settings_btn)
        self.command_bar.addSeparator()

        # Enhance (checkable) — download then run enhance post-process
        self.enhance_btn = ToolButton(FIF.ZOOM_IN, self)
        self.enhance_btn.setCheckable(True)
        self.enhance_btn.clicked.connect(
            lambda: self.enhance_enabled_changed.emit(self.enhance_btn.isChecked())
        )
        self.enhance_btn.setToolTip(self.tr("Download with Enhance — apply logo, flip, color, speed after download"))
        self.enhance_btn.setToolTipDuration(3000)
        self.enhance_btn.installEventFilter(ToolTipFilter(self.enhance_btn))
        # Background when unchecked; theme color when checked (enabled)
        self.enhance_btn.setStyleSheet(f"""
            QToolButton {{
                border-radius: 4px;
                padding: 6px 10px;
                background-color: rgba(128, 128, 128, 0.2);
            }}
            QToolButton:hover {{
                background-color: rgba(128, 128, 128, 0.35);
            }}
            QToolButton:checked {{
                background-color: {_btn_accent};
            }}
            QToolButton:checked:hover {{
                background-color: {_btn_accent};
            }}
        """)
        self.command_bar.addWidget(self.enhance_btn)

        # Enhance Settings
        enhance_settings_action = Action(
            FIF.EDIT,
            self.tr("Enhance Settings"),
            triggered=self.enhance_settings_clicked.emit,
        )
        enhance_settings_action.setToolTip(self.tr("Configure enhance options (logo, flip, color, speed)"))
        self.command_bar.addAction(enhance_settings_action)

        self.command_bar.addSeparator()

        # Open save folder
        open_folder_action = Action(
            FIF.FOLDER,
            self.tr("Open Save Folder"),
            triggered=self.open_save_folder_clicked.emit,
        )
        open_folder_action.setToolTip(self.tr("Open configured download folder in file manager"))
        self.command_bar.addAction(open_folder_action)

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
