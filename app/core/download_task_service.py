# coding:utf-8
from pathlib import Path
import shutil
from PyQt5.QtCore import Qt, Signal, Property, QObject
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from ..common.database import sqlRequest
from ..common.database.entity import Task
from ..common.utils import removeFile, showInFolder


class DownloadTaskService(QObject):
    """ Download task service """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def removedSuccessTask(self, task: Task, deleteFile=True):
        """ remove success task """
        sqlRequest("taskService", "removeById", id=task.id)

        if deleteFile:
            removeFile(task.availableVideoPath())

    def removeFailedTask(self, task: Task, deleteFile=True):
        """ remove failed task """
        sqlRequest("taskService", "removeById", id=task.id)

        if deleteFile:
            self._removeTmpFolder(task)

    def _removeTmpFolder(self, task: Task):
        folder = task.videoPath.parent / task.fileName
        shutil.rmtree(folder, ignore_errors=True)


downloadTaskService = DownloadTaskService()