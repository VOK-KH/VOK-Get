from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtSql import QSqlDatabase
from qfluentwidgets import NavigationItemPosition, MSFluentWindow, FluentIcon, MessageBox

import app
from app.common.paths import PROJECT_ROOT
from app.common.database import DBInitializer, DatabaseThread, sqlSignalBus, SqlResponse
from app.common.signal_bus import signal_bus
from app.config import load_settings
from ..common.icon import Icon
from ..common import resource
from .views import DashboardView, DownloaderView, SettingsView, TaskInterface
from app.ui.components.system_tray_icon import SystemTrayIcon
class MainWindow(MSFluentWindow):
    """Fluent-style window with download and analytics tools."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initDatabase()
        self.initWindow()

        self.dashboard = DashboardView(self)
        self.downloader = DownloaderView(self)
        self.taskInterface = TaskInterface(self)
        self.systemTrayIcon = SystemTrayIcon(self)
        # self.studio = VokStudioView(self)
        # self.logs = LogsView(self)
        self.settings = SettingsView(self)

        self.addSubInterface(self.dashboard, FluentIcon.HOME, "Home")
        self.addSubInterface(self.downloader, FluentIcon.DOWNLOAD, "Download")
        self.addSubInterface(self.taskInterface, Icon.CLOUD_DOWNLOAD, "Tasks")

        self.addSubInterface(
            self.settings,
            FluentIcon.SETTING,
            "Settings",
            position=NavigationItemPosition.BOTTOM,
        )

        default_page = load_settings().get("default_start_page", "Download")
        if default_page == "Dashboard":
            self.switchTo(self.dashboard)
        elif default_page == "Settings":
            self.switchTo(self.settings)
        else:
            self.switchTo(self.downloader)

        self.connectSignalToSlot()

    def initWindow(self):
        """Initialize window size, title, and position."""
        self.resize(1200, 840)
        self.setMinimumSize(900, 840)
        self.setWindowTitle(f"VOK — Download (v{app.__version__})")

        logo_path = PROJECT_ROOT / "resources" / "icon.ico"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def initDatabase(self):
        """Open the SQLite database and start the async DB thread."""
        DBInitializer.init()
        self.databaseThread = DatabaseThread(
            QSqlDatabase.database(DBInitializer.CONNECTION_NAME), self
        )
        sqlSignalBus.dataFetched.connect(self.onDataFetched)

    def connectSignalToSlot(self):
        """Connect application-wide signals to window slots."""
        signal_bus.app_message.connect(self.onAppMessage)
        signal_bus.app_error.connect(self.onAppError)

    # ── Signal handlers ──────────────────────────────────────────────────

    def onDataFetched(self, response: SqlResponse):
        """Route async SQL result to the requesting callback."""
        if response.slot:
            response.slot(response.data)

    def onAppMessage(self, message: str):
        """Raise window on 'show' message (e.g. second instance launched)."""
        if message == "show":
            if self.windowState() & Qt.WindowMinimized:
                self.showNormal()
            else:
                self.show()
                self.raise_()
        else:
            self.switchTo(self.downloader)
            self.show()
            self.raise_()

    def onAppError(self, message: str):
        """Show unhandled-exception dialog and copy error to clipboard."""
        QApplication.clipboard().setText(message)
        w = MessageBox(
            "Unhandled exception occurred",
            "The error has been copied to the clipboard and written to the log.",
            self,
        )
        w.cancelButton.setText("Close")
        w.yesButton.hide()
        w.buttonLayout.insertStretch(0, 1)
        w.exec()

    # ── Window lifecycle ─────────────────────────────────────────────────

    def closeEvent(self, event):
        """Hide to system tray instead of closing."""
        event.ignore()
        self.hide()

    def onExit(self):
        """Clean up: hide tray icon, close DB connection, quit app."""
        self.systemTrayIcon.hide()
        db = QSqlDatabase.database(DBInitializer.CONNECTION_NAME)
        if db.isOpen():
            db.close()
        QSqlDatabase.removeDatabase(DBInitializer.CONNECTION_NAME)
        QApplication.instance().quit()
