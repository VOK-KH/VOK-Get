# coding: utf-8
from PyQt5.QtWidgets import QStackedWidget


class TaskStackedWidget(QStackedWidget):
    """Delegates size hints to the visible page so the parent scroll area sizes correctly."""

    def sizeHint(self):
        return self.currentWidget().sizeHint()

    def minimumSizeHint(self):
        return self.currentWidget().minimumSizeHint()
