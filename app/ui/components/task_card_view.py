# coding: utf-8
from typing import Dict, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from qfluentwidgets import FluentIcon

from app.common.database import sqlRequest
from app.common.database.entity import Task, TaskStatus
from .empty_status_widget import EmptyStatusWidget
from .task_card import FailedTaskCard, SuccessTaskCard


_EMPTY_CONFIGS = {
    "downloading": (FluentIcon.DOWNLOAD,   "No active downloads"),
    "enhancing":   (FluentIcon.SPEED_HIGH, "No active enhance tasks"),
    "finished":    (FluentIcon.COMPLETED,  "Nothing finished yet"),
    "failed":      (FluentIcon.INFO,       "No failed tasks"),
}


class TaskCardView(QWidget):
    """Vertically stacked list of task cards with a per-tab empty-state widget."""

    cardCountChanged = pyqtSignal(int)

    def __init__(self, tab_key: str = "", parent=None):
        super().__init__(parent)
        icon, text = _EMPTY_CONFIGS.get(tab_key, (FluentIcon.INFO, "No tasks"))
        self._empty = EmptyStatusWidget(icon, text, self)
        self._empty.setMinimumWidth(200)

        self._vbox = QVBoxLayout(self)
        self._vbox.setSpacing(8)
        self._vbox.setContentsMargins(30, 0, 30, 0)
        self._vbox.setAlignment(Qt.AlignTop)
        self._vbox.addWidget(self._empty, 0, Qt.AlignHCenter)

        self._cards: list = []
        self._card_map: Dict[str, object] = {}  # card_id → card (O(1) lookup)

    def add_card(self, card, card_id: str) -> None:
        if not self._cards:
            self._empty.hide()
        self._vbox.insertWidget(0, card, 0, Qt.AlignTop)
        card.show()
        self._cards.insert(0, card)
        self._card_map[card_id] = card
        self.cardCountChanged.emit(len(self._cards))

    def find_card(self, card_id: str):
        return self._card_map.get(card_id)

    def remove_card_by_id(self, card_id: str) -> None:
        card = self._card_map.pop(card_id, None)
        if card is None:
            return
        if card in self._cards:
            self._cards.remove(card)
        self._vbox.removeWidget(card)
        card.hide()
        card.deleteLater()
        if not self._cards:
            self._empty.show()
        self.cardCountChanged.emit(len(self._cards))

    def take_card(self, card_id: str):
        """Remove without destroying — used to move a card between views."""
        card = self._card_map.pop(card_id, None)
        if card is None:
            return None
        self._cards.remove(card)
        self._vbox.removeWidget(card)
        if not self._cards:
            self._empty.show()
        self.cardCountChanged.emit(len(self._cards))
        return card

    def count(self) -> int:
        return len(self._cards)


class DownloadingTaskView(TaskCardView):
    def __init__(self, parent=None):
        super().__init__("downloading", parent)
        self.setObjectName("downloading")


class EnhancingTaskView(TaskCardView):
    def __init__(self, parent=None):
        super().__init__("enhancing", parent)
        self.setObjectName("enhancing")


class SuccessTaskView(TaskCardView):
    def __init__(self, parent=None):
        super().__init__("finished", parent)
        self.setObjectName("finished")
        sqlRequest(
            "taskService", "listBy", self._load_tasks,
            status=TaskStatus.SUCCESS, orderBy="createTime", asc=True,
        )

    def _load_tasks(self, tasks: List[Task]) -> None:
        if not tasks:
            return
        for task in tasks:
            card = SuccessTaskCard(task, self)
            card.deleted.connect(lambda t: self.remove_card_by_id(t.id))
            self.add_card(card, task.id)


class FailedTaskView(TaskCardView):
    def __init__(self, parent=None):
        super().__init__("failed", parent)
        self.setObjectName("failed")
        sqlRequest(
            "taskService", "listBy", self._load_tasks,
            status=TaskStatus.FAILED, orderBy="createTime", asc=True,
        )

    def _load_tasks(self, tasks: List[Task]) -> None:
        if not tasks:
            return
        for task in tasks:
            card = FailedTaskCard(task, self)
            card.deleted.connect(lambda t: self.remove_card_by_id(t.id))
            self.add_card(card, task.id)
