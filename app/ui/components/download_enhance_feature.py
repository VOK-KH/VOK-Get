"""Enhance download card: URL + stream-edit options (logo, flip, color, speed, auto)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from app.config import load_settings, save_settings
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    LineEdit,
    PushButton,
    Slider,
    SubtitleLabel,
    SwitchButton,
)

from app.ui.components import CardHeader


@dataclass
class EnhanceOptions:
    """Options for post-download stream edit (logo, flip, color, speed)."""

    logo_path: str = ""
    logo_position: str = "center"  # left, right, center, top
    flip: str = "none"  # none, horizontal, vertical, both
    brightness: int = 0  # -100..100, 0 = no change
    contrast: int = 0
    saturation: int = 0
    speed: float = 1.0  # 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0
    auto: bool = False  # apply recommended defaults
    keep_original: bool = True  # if True, create folder per download and keep original; else one file only

    def has_edits(self) -> bool:
        """True if any edit is requested (so we need post-process)."""
        return (
            bool(self.logo_path and Path(self.logo_path).is_file())
            or self.flip != "none"
            or self.brightness != 0
            or self.contrast != 0
            or self.saturation != 0
            or self.speed != 1.0
        )


LOGO_POSITIONS = ["Left", "Right", "Center", "Top"]
FLIP_OPTIONS = ["None", "Horizontal", "Vertical", "Both"]
SPEED_OPTIONS = ["0.5x", "0.75x", "1x", "1.25x", "1.5x", "1.75x", "2x"]
SPEED_VALUES = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0]


class DownloadEnhanceFeature(CardWidget):
    """Card for enhance-download: URL + logo position, flip, color, speed, auto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DownloadEnhanceFeature")
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.addWidget(CardHeader(FluentIcon.SYNC, "Enhance — Download with stream edit", self))

        # URL row
        url_row = QHBoxLayout()
        url_row.addWidget(BodyLabel("URL", self))
        self._url_edit = LineEdit(self)
        self._url_edit.setPlaceholderText(
            "https://  —  Paste video URL, then set logo, flip, color, speed below …"
        )
        self._url_edit.setClearButtonEnabled(True)
        url_row.addWidget(self._url_edit, 1)
        lay.addLayout(url_row)

        # Logo: path + position
        logo_row = QHBoxLayout()
        logo_row.addWidget(BodyLabel("Logo", self))
        self._logo_edit = LineEdit(self)
        self._logo_edit.setPlaceholderText("No logo")
        self._logo_edit.setClearButtonEnabled(True)
        logo_row.addWidget(self._logo_edit, 1)
        self._logo_browse = PushButton("Browse", self)
        self._logo_browse.setIcon(FluentIcon.FOLDER)
        self._logo_browse.clicked.connect(self._browse_logo)
        logo_row.addWidget(self._logo_browse)
        lay.addLayout(logo_row)

        pos_row = QHBoxLayout()
        pos_row.addWidget(BodyLabel("Logo position", self))
        self._logo_position = ComboBox(self)
        self._logo_position.addItems(LOGO_POSITIONS)
        self._logo_position.setCurrentIndex(2)  # Center
        self._logo_position.setFixedWidth(140)
        pos_row.addWidget(self._logo_position)
        pos_row.addStretch(1)
        lay.addLayout(pos_row)

        # Flip + Speed
        opts_row = QHBoxLayout()
        opts_row.addWidget(BodyLabel("Flip", self))
        self._flip_combo = ComboBox(self)
        self._flip_combo.addItems(FLIP_OPTIONS)
        self._flip_combo.setFixedWidth(120)
        opts_row.addWidget(self._flip_combo)
        opts_row.addSpacing(24)
        opts_row.addWidget(BodyLabel("Speed", self))
        self._speed_combo = ComboBox(self)
        self._speed_combo.addItems(SPEED_OPTIONS)
        self._speed_combo.setCurrentIndex(2)  # 1x
        self._speed_combo.setFixedWidth(100)
        opts_row.addWidget(self._speed_combo)
        opts_row.addStretch(1)
        lay.addLayout(opts_row)

        # Color: brightness, contrast, saturation
        color_label = SubtitleLabel("Color", self)
        color_label.setStyleSheet("margin-top: 8px;")
        lay.addWidget(color_label)
        grid = QGridLayout()
        self._brightness_slider = Slider(Qt.Horizontal)
        self._brightness_slider.setRange(-100, 100)
        self._brightness_slider.setValue(0)
        self._brightness_slider.setFixedWidth(180)
        self._brightness_label = BodyLabel("0", self)
        self._brightness_label.setFixedWidth(32)
        grid.addWidget(BodyLabel("Brightness", self), 0, 0)
        grid.addWidget(self._brightness_slider, 0, 1)
        grid.addWidget(self._brightness_label, 0, 2)
        self._brightness_slider.valueChanged.connect(lambda v: self._brightness_label.setText(str(v)))

        self._contrast_slider = Slider(Qt.Horizontal)
        self._contrast_slider.setRange(-100, 100)
        self._contrast_slider.setValue(0)
        self._contrast_slider.setFixedWidth(180)
        self._contrast_label = BodyLabel("0", self)
        self._contrast_label.setFixedWidth(32)
        grid.addWidget(BodyLabel("Contrast", self), 1, 0)
        grid.addWidget(self._contrast_slider, 1, 1)
        grid.addWidget(self._contrast_label, 1, 2)
        self._contrast_slider.valueChanged.connect(lambda v: self._contrast_label.setText(str(v)))

        self._saturation_slider = Slider(Qt.Horizontal)
        self._saturation_slider.setRange(-100, 100)
        self._saturation_slider.setValue(0)
        self._saturation_slider.setFixedWidth(180)
        self._saturation_label = BodyLabel("0", self)
        self._saturation_label.setFixedWidth(32)
        grid.addWidget(BodyLabel("Saturation", self), 2, 0)
        grid.addWidget(self._saturation_slider, 2, 1)
        grid.addWidget(self._saturation_label, 2, 2)
        self._saturation_slider.valueChanged.connect(lambda v: self._saturation_label.setText(str(v)))
        lay.addLayout(grid)

        # Keep original: create folder per download and keep both files; if off, only enhanced file
        keep_row = QHBoxLayout()
        self._keep_original_switch = SwitchButton(self)
        s = load_settings()
        self._keep_original_switch.setChecked(s.get("enhance_keep_original", True))
        keep_row.addWidget(BodyLabel("Keep original (create folder per download)", self))
        keep_row.addWidget(self._keep_original_switch)
        keep_row.addStretch(1)
        lay.addLayout(keep_row)
        self._keep_original_switch.checkedChanged.connect(self._on_keep_original_changed)

        # Auto: apply recommended defaults
        auto_row = QHBoxLayout()
        self._auto_switch = SwitchButton(self)
        self._auto_switch.setChecked(False)
        auto_row.addWidget(BodyLabel("Auto (recommended defaults)", self))
        auto_row.addWidget(self._auto_switch)
        auto_row.addStretch(1)
        lay.addLayout(auto_row)
        self._auto_switch.checkedChanged.connect(self._on_auto_changed)

    def _browse_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select logo image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All files (*)",
        )
        if path:
            self._logo_edit.setText(path)

    def _on_keep_original_changed(self, checked: bool) -> None:
        s = load_settings()
        s["enhance_keep_original"] = checked
        save_settings(s)

    def _on_auto_changed(self, checked: bool) -> None:
        if checked:
            self._logo_position.setCurrentIndex(2)
            self._flip_combo.setCurrentIndex(0)
            self._speed_combo.setCurrentIndex(2)
            self._brightness_slider.setValue(0)
            self._contrast_slider.setValue(0)
            self._saturation_slider.setValue(0)

    def url(self) -> str:
        return self._url_edit.text().strip()

    def set_url(self, text: str) -> None:
        self._url_edit.setText(text)

    def get_options(self) -> EnhanceOptions:
        logo_path = self._logo_edit.text().strip()
        pos_idx = self._logo_position.currentIndex()
        logo_position = LOGO_POSITIONS[pos_idx].lower() if 0 <= pos_idx < len(LOGO_POSITIONS) else "center"
        flip_idx = self._flip_combo.currentIndex()
        flip = FLIP_OPTIONS[flip_idx].lower() if 0 <= flip_idx < len(FLIP_OPTIONS) else "none"
        speed_idx = self._speed_combo.currentIndex()
        speed = SPEED_VALUES[speed_idx] if 0 <= speed_idx < len(SPEED_VALUES) else 1.0
        return EnhanceOptions(
            logo_path=logo_path,
            logo_position=logo_position,
            flip=flip,
            brightness=self._brightness_slider.value(),
            contrast=self._contrast_slider.value(),
            saturation=self._saturation_slider.value(),
            speed=speed,
            auto=self._auto_switch.isChecked(),
            keep_original=self._keep_original_switch.isChecked(),
        )
