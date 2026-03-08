from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
)
from qfluentwidgets import (
    BodyLabel,
    TitleLabel,
    PushButton,
    ScrollArea,
)

from app.ui.components import DownloadEnhanceFeature


class EnhanceSettingDialog(QDialog):
    """Modal dialog for configuring enhance (stream-edit) options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enhance Settings")
        self.setModal(True)
        self.setMinimumWidth(680)
        self.setMinimumHeight(560)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )
        self._setup_content()

    # ── Build ──────────────────────────────────────────────────────────────

    def _setup_content(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(8)

        # Title
        title = TitleLabel("Enhance Settings", self)
        root.addWidget(title)

        sub = BodyLabel("Changes are saved automatically.", self)
        root.addWidget(sub)

        # Scrollable enhance feature (URL card hidden)
        scroll = ScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(ScrollArea.NoFrame)

        self._feature = DownloadEnhanceFeature()
        # Hide the URL input card (first widget in the feature's layout)
        url_widget = self._feature.layout().itemAt(0).widget()
        if url_widget is not None:
            url_widget.setVisible(False)

        scroll.setWidget(self._feature)
        root.addWidget(scroll, 1)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = PushButton("Close", self)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)