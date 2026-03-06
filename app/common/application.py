# coding: utf-8
"""Singleton application: single instance via QSharedMemory + QLocalServer."""

import sys
import traceback
from typing import List

from PyQt5.QtCore import QIODevice, QSharedMemory, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import QApplication

from .logger import Logger
from .signal_bus import signal_bus


class SingletonApplication(QApplication):
    """Single-instance application: second launch sends message to first and exits."""

    messageSig = pyqtSignal(object)
    logger = Logger("application")

    def __init__(self, argv: List[str], key: str):
        super().__init__(argv)
        self.key = key
        self.timeout = 1000
        self.server = QLocalServer(self)

        QSharedMemory(key).attach()
        self.memory = QSharedMemory(self)
        self.memory.setKey(key)

        if self.memory.attach():
            self.isRunning = True
            self.sendMessage(" ".join(argv[1:]) if len(argv) > 1 else "show")
            sys.exit()

        self.isRunning = False
        if not self.memory.create(1):
            self.logger.error(self.memory.errorString())
            raise RuntimeError(self.memory.errorString())

        self.server.newConnection.connect(self._on_new_connection)
        QLocalServer.removeServer(key)
        self.server.listen(key)

    def _on_new_connection(self):
        socket = self.server.nextPendingConnection()
        if socket.waitForReadyRead(self.timeout):
            msg = socket.readAll().data().decode("utf-8", errors="replace")
            signal_bus.app_message.emit(msg)
        socket.disconnectFromServer()

    def sendMessage(self, message: str):
        """Send message to the already-running instance."""
        if not self.isRunning:
            return
        socket = QLocalSocket(self)
        socket.connectToServer(self.key, QIODevice.WriteOnly)
        if not socket.waitForConnected(self.timeout):
            self.logger.error(socket.errorString())
            return
        socket.write(message.encode("utf-8"))
        if not socket.waitForBytesWritten(self.timeout):
            self.logger.error(socket.errorString())
            return
        socket.disconnectFromServer()


def exception_hook(exception: BaseException, value, tb):
    """Global exception callback: log and emit app_error."""
    SingletonApplication.logger.error("Unhandled exception", (exception, value, tb))
    message = "\n".join(
        ["".join(traceback.format_tb(tb)), f"{type(exception).__name__}: {value}"]
    )
    signal_bus.app_error.emit(message)


sys.excepthook = exception_hook
