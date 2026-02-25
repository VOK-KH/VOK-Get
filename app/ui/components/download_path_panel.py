"""Download path panel: shows current download folder and Open folder button."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import BodyLabel, CardWidget, FluentIcon, PushButton

from app.common.paths import get_default_downloads_dir
from app.common.shell import open_path_in_explorer
from app.config import load_settings

from .card_header import CardHeader


class DownloadPathPanel(CardWidget):
    """Card that displays the current download path from settings and an Open folder button."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(CardHeader(FluentIcon.FOLDER, "Download folder", self))

        row = QHBoxLayout()
        self._path_label = BodyLabel(self)
        self._path_label.setWordWrap(True)
        self._path_label.setTextInteractionFlags(Qt.NoTextInteraction)
        row.addWidget(self._path_label, 1)
        self._open_btn = PushButton("Open folder", self)
        self._open_btn.setIcon(FluentIcon.FOLDER)
        self._open_btn.clicked.connect(self._on_open_folder)
        row.addWidget(self._open_btn)
        layout.addLayout(row)

        self.refresh_path()

    def refresh_path(self) -> None:
        """Update displayed path from settings."""
        s = load_settings()
        path = s.get("download_path", str(get_default_downloads_dir())) or str(get_default_downloads_dir())
        self._path_label.setText(path)

    def _on_open_folder(self) -> None:
        s = load_settings()
        path = s.get("download_path", str(get_default_downloads_dir())) or str(get_default_downloads_dir())
        open_path_in_explorer(path)
