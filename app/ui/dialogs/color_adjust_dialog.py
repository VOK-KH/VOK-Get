"""Color Adjustment dialog — brightness, contrast, saturation sliders."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    FluentIcon,
    PrimaryPushButton,
    PushButton,
    ScrollArea,
    Slider,
    TitleLabel,
)


class ColorAdjustDialog(QDialog):
    """Modal dialog for brightness / contrast / saturation adjustment."""

    def __init__(self, brightness: int, contrast: int, saturation: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Color Adjustment")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setFixedSize(480, 360)
        self._setup_ui(brightness, contrast, saturation)

    # ── Build ─────────────────────────────────────────────────────────────

    def _setup_ui(self, brightness: int, contrast: int, saturation: int) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(0)

        title = TitleLabel("Color Adjustment", self)
        root.addWidget(title)
        root.addSpacing(4)

        sub = BodyLabel(
            "Fine-tune brightness, contrast and saturation of the output video.", self
        )
        sub.setWordWrap(True)
        root.addWidget(sub)
        root.addSpacing(16)

        card = CardWidget(self)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(20, 16, 20, 16)
        card_lay.setSpacing(14)

        self._brightness_slider = self._add_slider_row(card_lay, "Brightness", brightness)
        self._contrast_slider = self._add_slider_row(card_lay, "Contrast", contrast)
        self._saturation_slider = self._add_slider_row(card_lay, "Saturation", saturation)

        scroll = ScrollArea(self)
        scroll.setWidget(card)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(ScrollArea.NoFrame)
        root.addWidget(scroll, 1)
        root.addSpacing(20)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        reset_btn = PushButton("Reset", self)
        reset_btn.setIcon(FluentIcon.SYNC)
        reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch(1)

        cancel_btn = PushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        ok_btn = PrimaryPushButton("Apply", self)
        ok_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        root.addLayout(btn_row)

    def _add_slider_row(self, layout: QVBoxLayout, label: str, value: int) -> Slider:
        row_lay = QVBoxLayout()
        row_lay.setSpacing(4)

        header_row = QHBoxLayout()
        name_lbl = BodyLabel(label, self)
        val_lbl = BodyLabel(f"{value:+d}" if value != 0 else "0", self)
        val_lbl.setFixedWidth(40)
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_row.addWidget(name_lbl)
        header_row.addStretch(1)
        header_row.addWidget(val_lbl)
        row_lay.addLayout(header_row)

        slider_row = QHBoxLayout()
        min_lbl = BodyLabel("−100", self)
        slider = Slider(Qt.Horizontal, self)
        slider.setRange(-100, 100)
        slider.setValue(value)
        slider.setMinimumWidth(220)
        max_lbl = BodyLabel("+100", self)
        slider.valueChanged.connect(
            lambda v, l=val_lbl: l.setText(f"{v:+d}" if v != 0 else "0")
        )
        slider_row.addWidget(min_lbl)
        slider_row.addWidget(slider, 1)
        slider_row.addWidget(max_lbl)
        row_lay.addLayout(slider_row)

        layout.addLayout(row_lay)
        return slider

    # ── Actions ───────────────────────────────────────────────────────────

    def _reset(self) -> None:
        self._brightness_slider.setValue(0)
        self._contrast_slider.setValue(0)
        self._saturation_slider.setValue(0)

    # ── Properties ────────────────────────────────────────────────────────

    @property
    def brightness(self) -> int:
        return self._brightness_slider.value()

    @property
    def contrast(self) -> int:
        return self._contrast_slider.value()

    @property
    def saturation(self) -> int:
        return self._saturation_slider.value()
