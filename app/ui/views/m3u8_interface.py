"""M3U8 / HLS Download interface — Coming Soon"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CardWidget,
    FluentIcon,
    LargeTitleLabel,
    StrongBodyLabel,
    TitleLabel,
)

from app.ui.components import CardHeader

from .base import BaseView


class M3u8Interface(BaseView):
    """Coming-soon page for the M3U8 / HLS download feature."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("M3U8 Download")
        self._layout.setContentsMargins(24, 20, 24, 24)
    