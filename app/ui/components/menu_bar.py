# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QAction, QKeySequence
from PyQt5.QtWidgets import QMenuBar


class MenuBar(QMenuBar):
    """Application menu bar."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.fileMenu = self.addMenu(self.tr("File") + "(&R)")
        self.openFileAct = QAction(self.tr("Open File"), self)
        self.openFileAct.setShortcut("Ctrl+O")
        self.settingsAct = QAction(self.tr("Preferences"), self)
        self.settingsAct.setShortcuts(QKeySequence.Preferences)
        self.closeWindowAct = QAction(self.tr("Close Window"), self)
        self.closeWindowAct.setShortcut("Ctrl+W")
        self.fileMenu.addActions([self.openFileAct, self.settingsAct])
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.closeWindowAct)

        self.helpMenu = self.addMenu(self.tr("Help") + "(&H)")
        self.docAct = QAction(self.tr("Documentation"), self)
        self.docAct.setShortcuts(QKeySequence.HelpContents)
        self.videoTutorialAct = QAction(self.tr("Video Tutorials"), self)
        self.feedbackAct = QAction(self.tr("Feedback"), self)
        self.donateAct = QAction(self.tr("Support Us"), self)
        self.helpMenu.addActions([self.docAct, self.videoTutorialAct, self.feedbackAct])
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.donateAct)
