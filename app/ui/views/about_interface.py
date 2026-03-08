
from .base import BaseView

class AboutInterface(BaseView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)