"""Clipper interface — Coming Soon placeholder view."""

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

class CliperInterface(BaseView):
    """Coming-soon page for the Clipper feature."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clipper")
        self._layout.setContentsMargins(24, 20, 24, 24)
       