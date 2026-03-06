# coding: utf-8
"""Basic and advanced config cards (PyQt5, no m3u8)."""

from typing import List, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFileDialog

from qfluentwidgets import (
    IconWidget,
    BodyLabel,
    FluentIcon,
    InfoBarIcon,
    PrimaryPushButton,
    LineEdit,
    GroupHeaderCardWidget,
    PushButton,
    CompactSpinBox,
    SwitchButton,
    IndicatorPosition,
    PlainTextEdit,
    ToolTipFilter,
)

from ..common.icon import Logo

try:
    from ..common.config import cfg
except ImportError:
    cfg = None


def _cfg_get(option: Any, default: Any = None) -> Any:
    if cfg is None or option is None:
        return default
    try:
        return cfg.get(option)
    except (TypeError, AttributeError):
        return default


def _cfg_set(option: Any, value: Any) -> None:
    if cfg is not None and option is not None and hasattr(cfg, "set"):
        cfg.set(option, value)


class GroupHeaderCardWithSwitch(GroupHeaderCardWidget):
    """Group header card with optional switch rows."""

    def add_switch_option(self, icon, title, content, config_item: Any = None):
        button = SwitchButton(self.tr("Off"), self, IndicatorPosition.RIGHT)
        button.setOnText(self.tr("On"))
        button.setOffText(self.tr("Off"))
        button.setProperty("config", config_item)
        if config_item is not None:
            button.setChecked(_cfg_get(config_item, False))
            button.checkedChanged.connect(lambda c: _cfg_set(config_item, c))
        self.addGroup(icon, title, content, button)
        return button


class BasicConfigCard(GroupHeaderCardWidget):
    """Basic settings card (URL, file name, save folder, threads)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Basic Settings"))

        self.url_line_edit = LineEdit()
        self.file_name_line_edit = LineEdit()
        self.save_folder_button = PushButton(self.tr("Choose"))
        self.thread_count_spin = CompactSpinBox()
        self.hint_icon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hint_label = BodyLabel(self.tr("Click the download button to start downloading") + " 👉")
        self.download_button = PrimaryPushButton(self.tr("Download"), self, FluentIcon.PLAY_SOLID)
        self.tool_bar_layout = QHBoxLayout()

        self._init_widgets()

    def _init_widgets(self):
        self.setBorderRadius(8)
        self.download_button.setEnabled(False)
        self.hint_icon.setFixedSize(16, 16)

        self.url_line_edit.setFixedWidth(300)
        self.file_name_line_edit.setFixedWidth(300)
        self.save_folder_button.setFixedWidth(120)
        self.thread_count_spin.setFixedWidth(120)

        self.url_line_edit.setClearButtonEnabled(True)
        self.file_name_line_edit.setClearButtonEnabled(True)
        self.file_name_line_edit.setPlaceholderText(self.tr("Please enter the name of downloaded file"))
        self.url_line_edit.setPlaceholderText(self.tr("Please enter the URL or path"))
        self.url_line_edit.setToolTip(self.tr("URL or path to resource"))
        self.url_line_edit.setToolTipDuration(3000)
        self.url_line_edit.installEventFilter(ToolTipFilter(self.url_line_edit))

        if cfg is not None and hasattr(cfg, "threadCount") and getattr(cfg, "threadCount", None):
            self.thread_count_spin.setRange(*cfg.threadCount.range)
            self.thread_count_spin.setValue(_cfg_get(cfg.threadCount, 4))

        self._init_layout()
        self._connect_signals()

    def _init_layout(self):
        self.addGroup(
            icon=Logo.GLOBE.icon() if hasattr(Logo, "GLOBE") else FluentIcon.LINK.icon(),
            title=self.tr("Download URL"),
            content=self.tr("URL or file path"),
            widget=self.url_line_edit,
        )
        self.addGroup(
            icon=Logo.FILM.icon() if hasattr(Logo, "FILM") else FluentIcon.EDIT.icon(),
            title=self.tr("File Name"),
            content=self.tr("The name of downloaded file"),
            widget=self.file_name_line_edit,
        )
        self.save_folder_group = self.addGroup(
            icon=Logo.FOLDER.icon() if hasattr(Logo, "FOLDER") else FluentIcon.FOLDER.icon(),
            title=self.tr("Save Folder"),
            content=_cfg_get(getattr(cfg, "saveFolder", None), "") if cfg else "",
            widget=self.save_folder_button,
        )
        group = self.addGroup(
            icon=Logo.KNOT.icon() if hasattr(Logo, "KNOT") else FluentIcon.SYNC.icon(),
            title=self.tr("Download Threads"),
            content=self.tr("Set the number of concurrent download threads"),
            widget=self.thread_count_spin,
        )
        group.setSeparatorVisible(True)

        self.tool_bar_layout.setContentsMargins(24, 15, 24, 20)
        self.tool_bar_layout.setSpacing(10)
        self.tool_bar_layout.addWidget(self.hint_icon, 0, Qt.AlignLeft)
        self.tool_bar_layout.addWidget(self.hint_label, 0, Qt.AlignLeft)
        self.tool_bar_layout.addStretch(1)
        self.tool_bar_layout.addWidget(self.download_button, 0, Qt.AlignRight)
        self.tool_bar_layout.setAlignment(Qt.AlignVCenter)
        self.vBoxLayout.addLayout(self.tool_bar_layout)

    def _on_text_changed(self):
        url = self.url_line_edit.text().strip()
        file_name = self.file_name_line_edit.text()
        self.download_button.setEnabled(bool(url and file_name))

    def _choose_save_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), self.save_folder_group.content()
        )
        if folder:
            folder = folder.replace("\\", "/")
            _cfg_set(getattr(cfg, "saveFolder", None), folder)
            self.save_folder_group.setContent(folder)

    def _connect_signals(self):
        self.url_line_edit.textChanged.connect(self._on_text_changed)
        self.file_name_line_edit.textChanged.connect(self._on_text_changed)
        self.save_folder_button.clicked.connect(self._choose_save_folder)
        if cfg is not None and hasattr(cfg, "threadCount"):
            self.thread_count_spin.valueChanged.connect(
                lambda v: _cfg_set(getattr(cfg, "threadCount", None), v)
            )

    def parse_options(self) -> List[List[str]]:
        """Return options for download (override in subclass if needed)."""
        return []


class AdvanceConfigCard(GroupHeaderCardWithSwitch):
    """Advanced settings card (timeout, headers, retry, etc.)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Advance Settings"))
        self.http_timeout_spin = CompactSpinBox()
        self.http_header_edit = PlainTextEdit()
        self.retry_count_spin = CompactSpinBox()
        self._init_widgets()

    def _init_widgets(self):
        self.setBorderRadius(8)
        self.retry_count_spin.setFixedWidth(120)
        self.http_timeout_spin.setFixedWidth(120)
        if cfg and getattr(cfg, "retryCount", None):
            self.retry_count_spin.setRange(*cfg.retryCount.range)
            self.retry_count_spin.setValue(_cfg_get(cfg.retryCount, 3))
        if cfg and getattr(cfg, "httpRequestTimeout", None):
            self.http_timeout_spin.setRange(*cfg.httpRequestTimeout.range)
            self.http_timeout_spin.setValue(_cfg_get(cfg.httpRequestTimeout, 30))
        if cfg and getattr(cfg, "httpHeader", None):
            self.http_header_edit.setPlainText(_cfg_get(cfg.httpHeader, ""))
        self.http_header_edit.setFixedSize(300, 56)
        self.http_header_edit.setPlaceholderText("User-Agent: iOS\nCookie: mycookie")
        self._init_layout()
        self._connect_signals()

    def _init_layout(self):
        self.addGroup(
            icon=Logo.COOKIE.icon() if hasattr(Logo, "COOKIE") else FluentIcon.LINK.icon(),
            title=self.tr("Header"),
            content=self.tr("Set custom headers for HTTP requests"),
            widget=self.http_header_edit,
        )
        self.addGroup(
            icon=Logo.HOURGLASS.icon() if hasattr(Logo, "HOURGLASS") else FluentIcon.TIME.icon(),
            title=self.tr("Request Timeout"),
            content=self.tr("Set timeout for HTTP requests (in seconds)"),
            widget=self.http_timeout_spin,
        )
        self.addGroup(
            icon=Logo.JOYSTICK.icon() if hasattr(Logo, "JOYSTICK") else FluentIcon.SYNC.icon(),
            title=self.tr("Retry Count"),
            content=self.tr("Set the retry count for each shard download exception"),
            widget=self.retry_count_spin,
        )

    def _connect_signals(self):
        if cfg and getattr(cfg, "httpRequestTimeout", None):
            self.http_timeout_spin.valueChanged.connect(
                lambda v: _cfg_set(cfg.httpRequestTimeout, v)
            )
        if cfg and getattr(cfg, "retryCount", None):
            self.retry_count_spin.valueChanged.connect(
                lambda v: _cfg_set(cfg.retryCount, v)
            )
        if cfg and getattr(cfg, "httpHeader", None):
            self.http_header_edit.textChanged.connect(
                lambda: _cfg_set(cfg.httpHeader, self.http_header_edit.toPlainText())
            )

    def parse_options(self) -> List[str]:
        """Return extra options (override in subclass)."""
        return []
