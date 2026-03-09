from .entity import Entity
from .task import Task, TaskStatus
from .queue_task import QueueTask, QUEUE_STATUS_PENDING, QUEUE_STATUS_RUNNING, QUEUE_STATUS_DONE, QUEUE_STATUS_ERROR, QUEUE_STATUS_CANCELED

from dataclasses import dataclass


class EntityFactory:
    """ Entity factory """

    @staticmethod
    def create(table: str):
        tables = {
            "tbl_task": Task,
            "tbl_download_queue": QueueTask,
        }
        if table not in tables:
            raise ValueError(f"Table name `{table}` is illegal")

        return tables[table]()
