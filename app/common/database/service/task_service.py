# coding:utf-8
from typing import List

from PyQt5.QtSql import QSqlDatabase

from ..dao import TaskDao
from ..entity import Task

from .service_base import ServiceBase


class TaskService(ServiceBase):
    """ Task service """

    def __init__(self, db: QSqlDatabase = None):
        super().__init__()
        self.taskDao = TaskDao(db)

    def createTable(self) -> bool:
        return self.taskDao.createTable()

    def findBy(self, **condition) -> Task:
        return self.taskDao.selectBy(**condition)

    def listBy(self, **condition) -> List[Task]:
        return self.taskDao.listBy(**condition)

    def listAll(self) -> List[Task]:
        return self.taskDao.listAll()

    def listByIds(self, ids: List[str]) -> List[Task]:
        return self.taskDao.listByIds(ids)

    def modify(self, id: str, field: str, value) -> bool:
        return self.taskDao.update(id, field, value)

    def modifyById(self, task: Task) -> bool:
        return self.taskDao.updateById(task)

    def modifyByIds(self, users: List[Task]) -> bool:
        return self.taskDao.updateByIds(users)

    def add(self, task: Task) -> bool:
        return self.taskDao.insert(task)

    def addBatch(self, users: List[Task]) -> bool:
        return self.taskDao.insertBatch(users)

    def removeById(self, id: str) -> bool:
        return self.taskDao.deleteById(id)

    def removeByIds(self, ids: List[str]) -> bool:
        return self.taskDao.deleteByIds(ids)

    def clearTable(self) -> bool:
        return self.taskDao.clearTable()

    def setDatabase(self, db: QSqlDatabase):
        self.taskDao.setDatabase(db)

    def listLike(self, **condition) -> List[Task]:
        return self.taskDao.listLike(**condition)

    def count(self) -> int:
        return self.taskDao.count()
