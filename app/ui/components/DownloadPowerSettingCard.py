from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QWidget

from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    ExpandGroupSettingCard,
    FluentIcon,
    IndicatorPosition,
    PushButton,
    Slider,
    SwitchButton,
)

from app.common.paths import get_default_downloads_dir
from app.config import load_settings
from app.common.downloader_helpers import DOWNLOAD_FORMATS


class DownloadConfigCard(ExpandGroupSettingCard):
    """Expandable card grouping download format, location override, and single-video toggle.

    Attributes
    ----------
    format_combo : ComboBox
        Currently selected download format.
    single_switch : SwitchButton
        Mirrors the "single video only" setting.
    """

    def __init__(self, parent=None):
        super().__init__(
            FluentIcon.DOWNLOAD,
            "Download config",
            "Format and per-job options",
            parent,
        )
        s = load_settings()

        # Format group
        self.format_combo = ComboBox()
        self.format_combo.addItems(DOWNLOAD_FORMATS)
        default_fmt = s.get("download_format", DOWNLOAD_FORMATS[0])
        if default_fmt in DOWNLOAD_FORMATS:
            self.format_combo.setCurrentText(default_fmt)
        self.format_combo.setFixedWidth(175)

        # Download location: current folder text + Choose (no line edit)
        self._override_path: str | None = None  # None = use default from Settings
        default_path = s.get("download_path", str(get_default_downloads_dir()))
        self._path_label = BodyLabel(default_path, self)
        self._path_label.setWordWrap(False)
        choose_btn = PushButton("Choose", self)
        choose_btn.setFixedWidth(80)
        choose_btn.clicked.connect(self._browse_folder)
        path_row = QWidget(self)
        path_lay = QHBoxLayout(path_row)
        path_lay.setContentsMargins(0, 0, 0, 0)
        path_lay.setSpacing(8)
        path_lay.addWidget(self._path_label, 1)
        path_lay.addWidget(choose_btn)

        # Single video only group
        self.single_switch = SwitchButton("Off", self, IndicatorPosition.RIGHT)
        self.single_switch.setOnText("On")
        self.single_switch.setChecked(s.get("single_video_default", True))

        # Performance: concurrent downloads (1–4) and fragments (1–16) via sliders
        conc_val = max(1, min(4, int(s.get("concurrent_downloads", 2))))
        self._conc_slider = Slider(Qt.Horizontal)
        self._conc_slider.setFixedWidth(200)
        self._conc_slider.setRange(1, 4)
        self._conc_slider.setValue(conc_val)
        self._conc_label = BodyLabel(str(conc_val), self)
        self._conc_slider.valueChanged.connect(lambda v: self._conc_label.setText(str(v)))
        conc_row = QWidget(self)
        conc_lay = QHBoxLayout(conc_row)
        conc_lay.setContentsMargins(0, 0, 0, 0)
        conc_lay.setSpacing(8)
        conc_lay.addWidget(self._conc_slider)
        conc_lay.addWidget(self._conc_label)
        conc_lay.addStretch(1)

        frag_val = max(1, min(16, int(s.get("concurrent_fragments", 4))))
        self._frag_slider = Slider(Qt.Horizontal)
        self._frag_slider.setFixedWidth(200)
        self._frag_slider.setRange(1, 16)
        self._frag_slider.setValue(frag_val)
        self._frag_label = BodyLabel(str(frag_val), self)
        self._frag_slider.valueChanged.connect(lambda v: self._frag_label.setText(str(v)))
        frag_row = QWidget(self)
        frag_lay = QHBoxLayout(frag_row)
        frag_lay.setContentsMargins(0, 0, 0, 0)
        frag_lay.setSpacing(8)
        frag_lay.addWidget(self._frag_slider)
        frag_lay.addWidget(self._frag_label)
        frag_lay.addStretch(1)

        # Layout tweaks
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.addGroup(
            FluentIcon.MEDIA,
            "Format",
            "Video/audio quality and container",
            self.format_combo,
        )
        self.addGroup(
            FluentIcon.FOLDER,
            "Download location",
            "",
            path_row,
        )
        self.addGroup(
            FluentIcon.VIDEO,
            "Single video only",
            "Download only the current video; skip playlists",
            self.single_switch,
        )
        self.addGroup(
            FluentIcon.DOWNLOAD,
            "Concurrent downloads",
            "Number of parallel download jobs (1–4)",
            conc_row,
        )
        self.addGroup(
            FluentIcon.SPEED_HIGH,
            "Concurrent fragments",
            "Fragment threads per download job (1–16)",
            frag_row,
        )

    def _browse_folder(self):
        start = self._path_label.text() or str(get_default_downloads_dir())
        path = QFileDialog.getExistingDirectory(self, "Download folder", start)
        if path:
            self._override_path = path
            self._path_label.setText(path)

    def _refresh_path_display(self):
        """Update path label to current override or default from Settings."""
        if self._override_path is not None:
            self._path_label.setText(self._override_path)
        else:
            s = load_settings()
            self._path_label.setText(s.get("download_path", str(get_default_downloads_dir())))

    def _refresh_performance_display(self):
        """Update concurrent downloads/fragments sliders from Settings."""
        s = load_settings()
        self._conc_slider.setValue(max(1, min(4, int(s.get("concurrent_downloads", 2)))))
        self._conc_label.setText(str(self._conc_slider.value()))
        self._frag_slider.setValue(max(1, min(16, int(s.get("concurrent_fragments", 4)))))
        self._frag_label.setText(str(self._frag_slider.value()))

    def output_dir(self) -> str | None:
        """Return override folder if set, else None (caller uses default from Settings)."""
        return self._override_path

    def concurrent_downloads(self) -> int:
        """Number of parallel download jobs (1–4) from card; use for this session."""
        return self._conc_slider.value()

    def concurrent_fragments(self) -> int:
        """Fragment threads per download job (1–16) from card; use for this session."""
        return self._frag_slider.value()
