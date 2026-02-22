"""First-run setup wizard: theme and download path."""

from PyQt5.QtWidgets import QDialog, QFileDialog, QFormLayout, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    TitleLabel,
)

from app.common.paths import get_default_downloads_dir
from app.config import save_settings

_THEME_OPTIONS = ["Auto", "Light", "Dark"]


class SetupWizardDialog(QDialog):
    """First-run setup: choose theme and download folder, then save and continue."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to VOK")
        self.setFixedSize(440, 300)
        self._build_ui()

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.addWidget(TitleLabel("Setup", self))
        lay.addWidget(BodyLabel("Set your preferences before you start.", self))
        lay.addSpacing(12)

        form = QWidget()
        form_lay = QFormLayout(form)
        form_lay.addRow(BodyLabel("Theme", self))
        self._theme_combo = ComboBox(self)
        self._theme_combo.addItems(_THEME_OPTIONS)
        self._theme_combo.setCurrentText("Dark")
        self._theme_combo.setFixedWidth(140)
        form_lay.addRow(self._theme_combo)

        form_lay.addRow(BodyLabel("Download folder", self))
        path_row = QHBoxLayout()
        self._path_edit = LineEdit(self)
        self._path_edit.setPlaceholderText(str(get_default_downloads_dir()))
        self._path_edit.setText(str(get_default_downloads_dir()))
        browse = PushButton("Browse…", self)
        browse.clicked.connect(self._browse)
        path_row.addWidget(self._path_edit)
        path_row.addWidget(browse)
        form_lay.addRow(path_row)
        lay.addWidget(form)

        lay.addStretch(1)
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        skip_btn = PushButton("Skip", self)
        skip_btn.clicked.connect(self._on_skip)
        finish_btn = PrimaryPushButton("Finish", self)
        finish_btn.clicked.connect(self._on_finish)
        btn_row.addWidget(skip_btn)
        btn_row.addWidget(finish_btn)
        lay.addLayout(btn_row)

    def _browse(self):
        start = self._path_edit.text() or str(get_default_downloads_dir())
        path = QFileDialog.getExistingDirectory(self, "Download folder", start)
        if path:
            self._path_edit.setText(path)

    def _save_and_close(self, path: str, theme: str):
        save_settings({
            "download_path": path,
            "theme": theme,
            "single_video_default": True,
            "theme_color": "#0078D4",
            "concurrent_downloads": 2,
            "concurrent_fragments": 4,
            "cookies_file": "",
        })

    def _on_skip(self):
        self._save_and_close(str(get_default_downloads_dir()), "Dark")
        self.accept()

    def _on_finish(self):
        path = self._path_edit.text().strip() or str(get_default_downloads_dir())
        self._save_and_close(path, self._theme_combo.currentText())
        self.accept()
