# coding:utf-8
from .dao_base import DaoBase


class TaskDao(DaoBase):
    """ Task DAO """

    table = 'tbl_task'
    fields = [
        'id', 'url', 'isLive', 'fileName', "saveFolder", 'size', 'isBinaryMerge',
        'isLiveRealTimeMerge', 'command', 'status', 'logFile', 'createTime'
    ]

    def createTable(self):
        success = self.query.exec(f"""
            CREATE TABLE IF NOT EXISTS {self.table}(
                id CHAR(32) PRIMARY KEY,
                url TEXT,
                isLive INTEGER,
                fileName TEXT,
                saveFolder TEXT,
                size TEXT,
                isBinaryMerge INTEGER,
                isLiveRealTimeMerge INTEGER,
                command TEXT,
                status INTEGER,
                logFile TEXT,
                createTime TEXT
            )
        """)
        return success
