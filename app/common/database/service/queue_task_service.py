# coding: utf-8
from typing import List

from PyQt5.QtSql import QSqlDatabase

from ..dao import QueueTaskDao
from ..entity import QueueTask

from .service_base import ServiceBase


class QueueTaskService(ServiceBase):
    """Persist and retrieve download queue tasks."""

    def __init__(self, db: QSqlDatabase = None):
        super().__init__()
        self.queueTaskDao = QueueTaskDao(db)

    def createTable(self) -> bool:
        return self.queueTaskDao.createTable()

    def clearTable(self) -> bool:
        return self.queueTaskDao.clearTable()

    def add(self, task: QueueTask) -> bool:
        return self.queueTaskDao.insert(task)

    def update_status(self, task_id: str, status: str) -> bool:
        return self.queueTaskDao.update(task_id, "status", status)

    def update_job_id(self, task_id: str, job_id: str) -> bool:
        return self.queueTaskDao.update(task_id, "job_id", job_id)

    def remove(self, task_id: str) -> bool:
        return self.queueTaskDao.deleteById(task_id)

    def remove_batch(self, ids: List[str]) -> bool:
        return self.queueTaskDao.deleteByIds(ids)

    def list_recoverable(self) -> List[QueueTask]:
        """Return rows that should be re-queued on next launch (Pending/Downloading)."""
        return self.queueTaskDao.list_recoverable()

    def listAll(self) -> List[QueueTask]:
        return self.queueTaskDao.listAll()

    def setDatabase(self, db: QSqlDatabase):
        self.queueTaskDao.setDatabase(db)

    # ServiceBase stubs
    def findBy(self, **condition) -> QueueTask:
        return self.queueTaskDao.selectBy(**condition)
