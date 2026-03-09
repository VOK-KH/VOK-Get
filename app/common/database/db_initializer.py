# coding: utf-8
from PyQt5.QtSql import QSqlDatabase
from PyQt5.QtWidgets import QApplication

from ..logger import Logger
from ..paths import get_config_dir

from .service import TaskService, QueueTaskService


class DBInitializer:
    """Initialize SQLite database and create tables."""

    logger = Logger("database")
    CONNECTION_NAME = "main"

    @classmethod
    def init(cls):
        """Open database and create tables if needed."""
        db_path = str(get_config_dir() / "database.db")
        db = QSqlDatabase.addDatabase("QSQLITE", cls.CONNECTION_NAME)
        db.setDatabaseName(db_path)
        if not db.open():
            cls.logger.error("Database connection failed")
            QApplication.instance().quit()
            return
        TaskService(db).createTable()
        QueueTaskService(db).createTable()