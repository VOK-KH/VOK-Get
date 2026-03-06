# coding: utf-8
"""Task cards (PyQt5): job-based cards for task interface + legacy Task-entity cards."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QFileInfo, QSize
from PyQt5.QtGui import QPainter, QFont, QColor, QPen
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFileIconProvider, QLabel, QSizePolicy

from qfluentwidgets import (
    CardWidget,
    IconWidget,
    ToolButton,
    FluentIcon,
    BodyLabel,
    CaptionLabel,
    ProgressBar,
    IndeterminateProgressBar,
    ImageLabel,
    setFont,
    MessageBoxBase,
    SubtitleLabel,
    CheckBox,
    InfoBar,
    ToolTipFilter,
    InfoLevel,
    DotInfoBadge,
    MessageBox,
    isDarkTheme,
    themeColor,
)

from app.common.utils import showInFolder, openUrl
from app.common.signal_bus import signal_bus
from app.common.speed_badge import SpeedBadge
from app.ui.utils import format_size, format_speed

# Optional: database entity and download task service (no m3u8)
try:
    from app.common.database.entity import Task
except ImportError:
    Task = Any  # type: ignore

try:
    from app.service.download_task_service import downloadTaskService
except ImportError:
    downloadTaskService = None

# Local progress info types (no m3u8dl_service)
class VODDownloadProgressInfo:
    def __init__(self, speed="0MB/s", remainTime="00:00:00", currentSize="0MB", totalSize="0MB", currentChunk=0, totalChunks=0):
        self.speed = speed
        self.remainTime = remainTime
        self.currentSize = currentSize
        self.totalSize = totalSize
        self.currentChunk = currentChunk
        self.totalChunks = totalChunks


class LiveDownloadStatus:
    RECORDING = "recording"
    WAITING = "waiting"


class LiveDownloadProgressInfo:
    def __init__(self, speed="0MB/s", currentTime="00m00s", totalTime="00m00s", percent=0, status=None):
        self.speed = speed
        self.currentTime = currentTime
        self.totalTime = totalTime
        self.percent = percent
        self.status = status or LiveDownloadStatus.RECORDING


def _task_service_show_in_folder(task) -> bool:
    if downloadTaskService is not None:
        return downloadTaskService.showInFolder(task)
    path = Path(getattr(task, "saveFolder", "")) / getattr(task, "fileName", "")
    if path.exists():
        showInFolder(path)
        return True
    return False


def _task_service_remove_downloading(task, delete_file: bool) -> None:
    if downloadTaskService is not None:
        downloadTaskService.removeDownloadingTask(task, delete_file)


def _task_service_removed_success(task, delete_file: bool) -> None:
    if downloadTaskService is not None:
        downloadTaskService.removedSuccessTask(task, delete_file)


def _task_service_remove_failed(task, delete_file: bool) -> None:
    if downloadTaskService is not None:
        downloadTaskService.removeFailedTask(task, delete_file)


def _task_service_finish_live(task) -> None:
    if downloadTaskService is not None:
        downloadTaskService.finishLiveRecordingTask(task)


class TaskCardBase(CardWidget):
    """Task card base class."""

    deleted = pyqtSignal(object)  # Task or any
    checkedChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.checkBox = CheckBox()
        self.checkBox.setFixedSize(23, 23)
        self.setSelectionMode(False)
        self.checkBox.stateChanged.connect(self._onCheckedChanged)

    def setSelectionMode(self, enter: bool):
        self.isSelectionMode = enter
        self.checkBox.setVisible(enter)
        if not enter:
            self.checkBox.setChecked(False)
        self.update()

    def isChecked(self):
        return self.checkBox.isChecked()

    def setChecked(self, checked):
        if checked == self.isChecked():
            return
        self.checkBox.setChecked(checked)
        self.update()

    def removeTask(self, deleteFile=False):
        raise NotImplementedError

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        if self.isSelectionMode:
            self.setChecked(not self.isChecked())
        else:
            self.setSelectionMode(True)
            self.setChecked(True)

    def _onDeleteButtonClicked(self):
        w = DeleteTaskDialog(self.window(), deleteOnClose=False)
        w.deleteFileCheckBox.setChecked(False)
        if w.exec_():
            self.removeTask(w.deleteFileCheckBox.isChecked())
        w.deleteLater()

    def _onCheckedChanged(self):
        self.setChecked(self.checkBox.isChecked())
        self.checkedChanged.emit(self.checkBox.isChecked())
        self.update()

    def paintEvent(self, e):
        if not (self.isSelectionMode and self.isChecked()):
            return super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        r = self.borderRadius
        painter.setPen(QPen(themeColor(), 2))
        painter.setBrush(QColor(255, 255, 255, 15) if isDarkTheme() else QColor(0, 0, 0, 8))
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), r, r)


class VODDownloadingTaskCard(TaskCardBase):
    """VOD downloading task card."""

    def __init__(self, task, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()
        self.task = task
        self.imageLabel = ImageLabel()
        self.fileNameLabel = BodyLabel(getattr(task, "fileName", ""))
        self.progressBar = ProgressBar()
        self.speedIcon = IconWidget(FluentIcon.SPEED_HIGH)
        self.speedLabel = CaptionLabel("0MB/s")
        self.remainTimeIcon = IconWidget(FluentIcon.STOP_WATCH)
        self.remainTimeLabel = CaptionLabel("00:00:00")
        self.sizeIcon = IconWidget(FluentIcon.BOOK_SHELF)
        self.sizeLabel = CaptionLabel("0MB/0MB")
        self.openFolderButton = ToolButton(FluentIcon.FOLDER)
        self.deleteButton = ToolButton(FluentIcon.DELETE)
        self._initWidget()

    def _initWidget(self):
        video_path = getattr(self.task, "videoPath", "")
        self.imageLabel.setImage(QFileIconProvider().icon(QFileInfo(str(video_path))).pixmap(32, 32))
        self.speedIcon.setFixedSize(16, 16)
        self.remainTimeIcon.setFixedSize(16, 16)
        self.sizeIcon.setFixedSize(16, 16)
        self.openFolderButton.setToolTip(self.tr("Show in folder"))
        self.openFolderButton.setToolTipDuration(3000)
        self.openFolderButton.installEventFilter(ToolTipFilter(self.openFolderButton))
        self.deleteButton.setToolTip(self.tr("Remove task"))
        self.deleteButton.setToolTipDuration(3000)
        self.deleteButton.installEventFilter(ToolTipFilter(self.deleteButton))
        setFont(self.fileNameLabel, 18, QFont.Bold)
        self.fileNameLabel.setWordWrap(True)
        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.addWidget(self.checkBox)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.imageLabel)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addSpacing(20)
        self.hBoxLayout.addWidget(self.openFolderButton)
        self.hBoxLayout.addWidget(self.deleteButton)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.fileNameLabel)
        self.vBoxLayout.addLayout(self.infoLayout)
        self.vBoxLayout.addWidget(self.progressBar)
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(3)
        self.infoLayout.addWidget(self.speedIcon)
        self.infoLayout.addWidget(self.speedLabel, 0, Qt.AlignLeft)
        self.infoLayout.addSpacing(5)
        self.infoLayout.addWidget(self.remainTimeIcon)
        self.infoLayout.addWidget(self.remainTimeLabel, 0, Qt.AlignLeft)
        self.infoLayout.addSpacing(5)
        self.infoLayout.addWidget(self.sizeIcon)
        self.infoLayout.addWidget(self.sizeLabel, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)

    def _connectSignalToSlot(self):
        self.openFolderButton.clicked.connect(self._onOpenButtonClicked)
        self.deleteButton.clicked.connect(self._onDeleteButtonClicked)

    def _onOpenButtonClicked(self):
        path = Path(getattr(self.task, "saveFolder", "")) / getattr(self.task, "fileName", "")
        showInFolder(path)

    def removeTask(self, deleteFile=False):
        if not getattr(self.task, "isRunning", lambda: False)():
            return
        _task_service_remove_downloading(self.task, deleteFile)
        self.deleted.emit(self.task)

    def setInfo(self, info: VODDownloadProgressInfo):
        self.speedLabel.setText(info.speed)
        self.remainTimeLabel.setText(info.remainTime)
        self.sizeLabel.setText(f"{info.currentSize}/{info.totalSize}")
        self.progressBar.setRange(0, info.totalChunks)
        self.progressBar.setValue(info.currentChunk)


class SuccessTaskCard(TaskCardBase):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()
        self.task = task
        self.imageLabel = ImageLabel(":/app/images/DefaultCover.jpg")
        self.fileNameLabel = BodyLabel(getattr(task, "fileName", ""))
        create_time = getattr(task, "createTime", None)
        time_str = create_time.toString("yyyy-MM-dd hh:mm:ss") if create_time else "—"
        self.createTimeIcon = IconWidget(FluentIcon.DATE_TIME)
        self.createTimeLabel = CaptionLabel(time_str)
        self.sizeIcon = IconWidget(FluentIcon.BOOK_SHELF)
        self.sizeLabel = CaptionLabel(getattr(task, "size", "—"))
        self.redownloadButton = ToolButton(FluentIcon.UPDATE)
        self.openFolderButton = ToolButton(FluentIcon.FOLDER)
        self.deleteButton = ToolButton(FluentIcon.DELETE)
        self._initWidget()

    def _initWidget(self):
        self.imageLabel.setScaledSize(QSize(112, 63))
        self.imageLabel.setBorderRadius(4, 4, 4, 4)
        self.createTimeIcon.setFixedSize(16, 16)
        self.sizeIcon.setFixedSize(16, 16)
        self.redownloadButton.setToolTip(self.tr("Restart"))
        self.redownloadButton.setToolTipDuration(3000)
        self.redownloadButton.installEventFilter(ToolTipFilter(self.redownloadButton))
        self.openFolderButton.setToolTip(self.tr("Show in folder"))
        self.openFolderButton.setToolTipDuration(3000)
        self.openFolderButton.installEventFilter(ToolTipFilter(self.openFolderButton))
        self.deleteButton.setToolTip(self.tr("Remove task"))
        self.deleteButton.setToolTipDuration(3000)
        self.deleteButton.installEventFilter(ToolTipFilter(self.deleteButton))
        setFont(self.fileNameLabel, 18, QFont.Bold)
        self.fileNameLabel.setWordWrap(True)
        cover_path = getattr(self.task, "coverPath", None)
        if cover_path is not None and getattr(cover_path, "exists", lambda: False)():
            self.updateCover()
        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.addWidget(self.checkBox)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.imageLabel)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addSpacing(20)
        self.hBoxLayout.addWidget(self.redownloadButton)
        self.hBoxLayout.addWidget(self.openFolderButton)
        self.hBoxLayout.addWidget(self.deleteButton)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.fileNameLabel)
        self.vBoxLayout.addLayout(self.infoLayout)
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(3)
        self.infoLayout.addWidget(self.createTimeIcon)
        self.infoLayout.addWidget(self.createTimeLabel, 0, Qt.AlignLeft)
        self.infoLayout.addSpacing(8)
        self.infoLayout.addWidget(self.sizeIcon)
        self.infoLayout.addWidget(self.sizeLabel, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)
        if getattr(self.task, "isLive", False):
            self.sizeIcon.hide()
            self.sizeLabel.hide()

    def updateCover(self):
        cover_path = getattr(self.task, "coverPath", None)
        if cover_path is not None:
            self.imageLabel.setImage(str(cover_path))
        self.imageLabel.setScaledSize(QSize(112, 63))

    def _onOpenButtonClicked(self):
        exist = _task_service_show_in_folder(self.task)
        if not exist:
            win = self.window()
            task_iface = getattr(win, "taskInterface", None)
            InfoBar.error(
                title=self.tr("Open failed"),
                content=self.tr("Video file have been deleted"),
                duration=2000,
                parent=task_iface or self,
            )

    def removeTask(self, deleteFile=False):
        _task_service_removed_success(self.task, deleteFile)
        self.deleted.emit(self.task)

    def redownload(self):
        signal_bus.redownload_task.emit(self.task)

    def _connectSignalToSlot(self):
        self.openFolderButton.clicked.connect(self._onOpenButtonClicked)
        self.deleteButton.clicked.connect(self._onDeleteButtonClicked)
        self.redownloadButton.clicked.connect(self.redownload)


class FailedTaskCard(TaskCardBase):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()
        self.task = task
        self.imageLabel = ImageLabel()
        self.fileNameLabel = BodyLabel(getattr(task, "fileName", ""))
        create_time = getattr(task, "createTime", None)
        time_str = create_time.toString("yyyy-MM-dd hh:mm:ss") if create_time else "—"
        self.createTimeIcon = IconWidget(FluentIcon.DATE_TIME)
        self.createTimeLabel = CaptionLabel(time_str)
        self.sizeIcon = IconWidget(FluentIcon.BOOK_SHELF)
        self.sizeLabel = CaptionLabel(getattr(task, "size", "—"))
        self.redownloadButton = ToolButton(FluentIcon.UPDATE)
        self.logButton = ToolButton(FluentIcon.COMMAND_PROMPT)
        self.deleteButton = ToolButton(FluentIcon.DELETE)
        self._initWidget()

    def _initWidget(self):
        video_path = getattr(self.task, "videoPath", "")
        self.imageLabel.setImage(QFileIconProvider().icon(QFileInfo(str(video_path))).pixmap(32, 32))
        self.createTimeIcon.setFixedSize(16, 16)
        self.sizeIcon.setFixedSize(16, 16)
        self.redownloadButton.setToolTip(self.tr("Restart"))
        self.redownloadButton.setToolTipDuration(3000)
        self.redownloadButton.installEventFilter(ToolTipFilter(self.redownloadButton))
        self.logButton.setToolTip(self.tr("View log"))
        self.logButton.setToolTipDuration(3000)
        self.logButton.installEventFilter(ToolTipFilter(self.logButton))
        setFont(self.fileNameLabel, 18, QFont.Bold)
        self.fileNameLabel.setWordWrap(True)
        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.addWidget(self.checkBox)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.imageLabel)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addSpacing(20)
        self.hBoxLayout.addWidget(self.redownloadButton)
        self.hBoxLayout.addWidget(self.logButton)
        self.hBoxLayout.addWidget(self.deleteButton)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.fileNameLabel)
        self.vBoxLayout.addLayout(self.infoLayout)
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(3)
        self.infoLayout.addWidget(self.createTimeIcon)
        self.infoLayout.addWidget(self.createTimeLabel, 0, Qt.AlignLeft)
        self.infoLayout.addSpacing(8)
        self.infoLayout.addWidget(self.sizeIcon)
        self.infoLayout.addWidget(self.sizeLabel, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)
        if getattr(self.task, "isLive", False):
            self.sizeIcon.hide()
            self.sizeLabel.hide()

    def _onLogButtonClicked(self):
        log_file = getattr(self.task, "logFile", None)
        if log_file:
            openUrl(log_file)

    def removeTask(self, deleteFile=False):
        _task_service_remove_failed(self.task, deleteFile)
        self.deleted.emit(self.task)

    def redownload(self):
        signal_bus.redownload_task.emit(self.task)

    def _connectSignalToSlot(self):
        self.logButton.clicked.connect(self._onLogButtonClicked)
        self.deleteButton.clicked.connect(self._onDeleteButtonClicked)
        self.redownloadButton.clicked.connect(self.redownload)


class DeleteTaskDialog(MessageBoxBase):
    def __init__(self, parent=None, showCheckBox=True, deleteOnClose=True):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(self.tr("Delete task"), self)
        self.contentLabel = BodyLabel(self.tr("Are you sure to delete this task?"), self)
        self.deleteFileCheckBox = CheckBox(self.tr("Remove file"), self)
        self.deleteFileCheckBox.setVisible(showCheckBox)
        if deleteOnClose:
            self.setAttribute(Qt.WA_DeleteOnClose, True)
        self._initWidgets()

    def _initWidgets(self):
        self.deleteFileCheckBox.setChecked(True)
        self.widget.setMinimumWidth(330)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.titleLabel)
        layout.addSpacing(12)
        layout.addWidget(self.contentLabel)
        layout.addSpacing(10)
        layout.addWidget(self.deleteFileCheckBox)
        self.viewLayout.addLayout(layout)


class LiveDownloadingTaskCard(TaskCardBase):
    """Live downloading task card."""

    def __init__(self, task, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.infoLayout = QHBoxLayout()
        self.task = task
        self.imageLabel = ImageLabel()
        self.fileNameLabel = BodyLabel(getattr(task, "fileName", ""))
        self.progressBar = ProgressBar()
        self.speedIcon = IconWidget(FluentIcon.SPEED_HIGH)
        self.speedLabel = CaptionLabel("0MB/s")
        self.timeIcon = IconWidget(FluentIcon.STOP_WATCH)
        self.timeLabel = CaptionLabel("00m00s/00m00s")
        self.statusIcon = DotInfoBadge(self, InfoLevel.SUCCESS)
        self.statusLabel = CaptionLabel(self.tr("Recording"))
        self.openFolderButton = ToolButton(FluentIcon.FOLDER)
        self.deleteButton = ToolButton(FluentIcon.DELETE)
        self.stopButton = ToolButton(FluentIcon.ACCEPT)
        self._initWidget()

    def _initWidget(self):
        video_path = getattr(self.task, "videoPath", "")
        self.imageLabel.setImage(QFileIconProvider().icon(QFileInfo(str(video_path))).pixmap(32, 32))
        self.speedIcon.setFixedSize(16, 16)
        self.timeIcon.setFixedSize(16, 16)
        self.statusIcon.setFixedSize(10, 10)
        self.openFolderButton.setToolTip(self.tr("Show in folder"))
        self.openFolderButton.setToolTipDuration(3000)
        self.openFolderButton.installEventFilter(ToolTipFilter(self.openFolderButton))
        self.stopButton.setToolTip(self.tr("Stop recording"))
        self.stopButton.setToolTipDuration(3000)
        self.stopButton.installEventFilter(ToolTipFilter(self.stopButton))
        self.deleteButton.setToolTip(self.tr("Remove task"))
        self.deleteButton.setToolTipDuration(3000)
        self.deleteButton.installEventFilter(ToolTipFilter(self.deleteButton))
        setFont(self.fileNameLabel, 18, QFont.Bold)
        self.fileNameLabel.setWordWrap(True)
        self._initLayout()
        self._connectSignalToSlot()

    def _initLayout(self):
        self.hBoxLayout.setContentsMargins(20, 11, 20, 11)
        self.hBoxLayout.addWidget(self.checkBox)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addWidget(self.imageLabel)
        self.hBoxLayout.addSpacing(5)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.hBoxLayout.addSpacing(20)
        self.hBoxLayout.addWidget(self.openFolderButton)
        self.hBoxLayout.addWidget(self.stopButton)
        self.hBoxLayout.addWidget(self.deleteButton)
        self.vBoxLayout.setSpacing(5)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addWidget(self.fileNameLabel)
        self.vBoxLayout.addLayout(self.infoLayout)
        self.vBoxLayout.addWidget(self.progressBar)
        self.infoLayout.setContentsMargins(0, 0, 0, 0)
        self.infoLayout.setSpacing(3)
        self.infoLayout.addWidget(self.statusIcon, 0, Qt.AlignVCenter)
        self.infoLayout.addWidget(self.statusLabel, 0, Qt.AlignLeft)
        self.infoLayout.addSpacing(5)
        self.infoLayout.addWidget(self.speedIcon, 0, Qt.AlignVCenter)
        self.infoLayout.addWidget(self.speedLabel, 0, Qt.AlignLeft)
        self.infoLayout.addSpacing(5)
        self.infoLayout.addWidget(self.timeIcon, 0, Qt.AlignVCenter)
        self.infoLayout.addWidget(self.timeLabel, 0, Qt.AlignLeft)
        self.infoLayout.addStretch(1)

    def _connectSignalToSlot(self):
        self.openFolderButton.clicked.connect(self._onOpenButtonClicked)
        self.deleteButton.clicked.connect(self._onDeleteButtonClicked)
        self.stopButton.clicked.connect(self._onStopButtonClicked)

    def _onOpenButtonClicked(self):
        path = Path(getattr(self.task, "saveFolder", "")) / getattr(self.task, "fileName", "")
        showInFolder(path)

    def _onStopButtonClicked(self):
        w = MessageBox(
            self.tr("Stop recording"),
            self.tr("Are you sure to stop recording the live stream?"),
            self.window(),
        )
        w.setAttribute(Qt.WA_DeleteOnClose, True)
        if w.exec_():
            self.deleted.emit(self.task)
            _task_service_finish_live(self.task)

    def removeTask(self, deleteFile=False):
        self.deleted.emit(self.task)
        _task_service_remove_downloading(self.task, deleteFile)

    def setInfo(self, info: LiveDownloadProgressInfo):
        self.speedLabel.setText(info.speed)
        self.timeLabel.setText(f"{info.currentTime}/{info.totalTime}")
        self.progressBar.setValue(info.percent)
        if info.status == LiveDownloadStatus.RECORDING:
            self.statusLabel.setText(self.tr("Recording"))
            self.statusIcon.setLevel(InfoLevel.SUCCESS)
            self.progressBar.resume()
        else:
            self.statusLabel.setText(self.tr("Waiting"))
            self.statusIcon.setLevel(InfoLevel.WARNING)
            self.progressBar.pause()


# ── Job-based cards for TaskInterface (import and use in task_interface) ─────

_STATUS_STYLES = {
    "Downloading": ("rgba(33,150,243,0.14)", "#64B5F6"),
    "Enhancing": ("rgba(255,190,0,0.14)", "#FFD54F"),
    "Finished": ("rgba(0,200,120,0.14)", "#4DB6AC"),
    "Failed": ("rgba(255,80,80,0.14)", "#EF9A9A"),
}


def _job_sub_text(size_bytes: int) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    if size_bytes <= 0:
        return ts
    return f"{ts}  ·  {format_size(size_bytes)}"


def _job_status_style(status: str) -> str:
    bg, fg = _STATUS_STYLES.get(status, ("rgba(150,150,150,0.12)", "#999"))
    return (
        f"QLabel {{ background: {bg}; color: {fg}; border-radius: 8px; "
        f"font-size: 10px; font-weight: 700; letter-spacing: 0.3px; "
        f"padding: 3px 10px; }}"
    )


class TaskJobCardBase(CardWidget):
    """Base for job-based cards: icon | name+sub | status badge | open folder."""

    def __init__(
        self,
        job_id: str,
        title: str,
        task_type: str = "download",
        output_path: str = "",
        size_bytes: int = -1,
        status: str = "Downloading",
        parent=None,
        icon=None,
    ):
        super().__init__(parent)
        self.job_id = job_id
        self.task_type = task_type
        self.output_path = output_path or ""

        self.setFixedHeight(72)
        self._icon = IconWidget(icon or FluentIcon.VIDEO, self)
        self._icon.setFixedSize(32, 32)

        self._name_label = BodyLabel(title or "—")
        self._name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._name_label.setMaximumWidth(9999)

        self._sub_label = CaptionLabel(_job_sub_text(size_bytes))
        self._sub_label.setTextColor("#888", "#666")

        self._text_col = QVBoxLayout()
        self._text_col.setSpacing(2)
        self._text_col.setContentsMargins(0, 0, 0, 0)
        self._text_col.addWidget(self._name_label)
        self._text_col.addWidget(self._sub_label)

        self._status_label = QLabel(status)
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._status_label.setStyleSheet(_job_status_style(status))
        self._status_label.adjustSize()

        self._open_btn = ToolButton(FluentIcon.FOLDER)
        self._open_btn.setToolTip("Open folder")
        self._open_btn.setFixedSize(32, 32)
        self._open_btn.clicked.connect(self._open_folder)

        h = QHBoxLayout(self)
        h.setContentsMargins(16, 0, 16, 0)
        h.setSpacing(12)
        h.addWidget(self._icon)
        h.addLayout(self._text_col, 1)
        h.addWidget(self._status_label)
        h.addWidget(self._open_btn)

    def _open_folder(self) -> None:
        path = self.output_path
        if path and os.path.isfile(path):
            showInFolder(path)
        elif path and os.path.isdir(path):
            showInFolder(path)

    def set_status(self, status: str) -> None:
        self._status_label.setText(status)
        self._status_label.setStyleSheet(_job_status_style(status))
        self._status_label.adjustSize()


class DownloadJobCard(TaskJobCardBase):
    """Download task card with progress bar and optional speed badge."""

    def __init__(
        self,
        job_id: str,
        url: str,
        output_path: str = "",
        size_bytes: int = -1,
        status: str = "Downloading",
        parent=None,
        speed_badge: Optional[SpeedBadge] = None,
    ):
        name = self._name_from_url(url)
        super().__init__(
            job_id, name,
            task_type="download",
            output_path=output_path,
            size_bytes=size_bytes,
            status=status,
            parent=parent,
            icon=FluentIcon.DOWNLOAD,
        )
        self._url = url
        self._speed_badge = speed_badge
        self._is_active = status == "Downloading"

        self._progress = ProgressBar(self)
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(3)
        self._progress.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._progress.setVisible(self._is_active)
        self._text_col.addWidget(self._progress)

        self._speed_label = CaptionLabel("—")
        self._speed_label.setTextColor("#888", "#666")
        self._speed_label.setVisible(self._is_active)
        self._text_col.addWidget(self._speed_label)

        if self._is_active:
            self.setFixedHeight(88)

    @staticmethod
    def _name_from_url(url: str) -> str:
        if not url:
            return "—"
        seg = url.rstrip("/").split("/")
        return (seg[-1] or url)[:80]

    def set_progress(self, value: float) -> None:
        self._progress.setValue(int(max(0.0, min(1.0, value)) * 100))

    def set_speed(self, bytes_per_sec: float) -> None:
        """Update speed label and optional system speed badge."""
        text = format_speed(bytes_per_sec)
        self._speed_label.setText(text)
        self._speed_label.setVisible(True)
        if self._speed_badge is not None:
            self._speed_badge.setSpeed(text)

    def mark_finished(self, success: bool, filepath: str, size_bytes: int) -> None:
        if self._speed_badge is not None:
            self._speed_badge.hide()
        self.output_path = filepath
        self._is_active = False
        self.set_status("Finished" if success else "Failed")
        self._progress.setVisible(False)
        self._speed_label.setVisible(False)
        self.setFixedHeight(72)
        if filepath:
            self._name_label.setText(os.path.basename(filepath))
        self._sub_label.setText(_job_sub_text(size_bytes))


class EnhanceJobCard(TaskJobCardBase):
    """Enhance task card with indeterminate progress."""

    def __init__(
        self,
        job_id: str,
        filename: str,
        output_path: str = "",
        size_bytes: int = -1,
        status: str = "Enhancing",
        parent=None,
    ):
        super().__init__(
            job_id, filename or "—",
            task_type="enhance",
            output_path=output_path,
            size_bytes=size_bytes,
            status=status,
            parent=parent,
            icon=FluentIcon.SPEED_HIGH,
        )
        self._spinner = IndeterminateProgressBar(self)
        self._spinner.setFixedHeight(3)
        self._spinner.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._spinner.setVisible(status == "Enhancing")
        self._text_col.addWidget(self._spinner)

        if status == "Enhancing":
            self.setFixedHeight(80)

    def mark_finished(self, success: bool, output_path: str, size_bytes: int) -> None:
        self.output_path = output_path
        self.set_status("Finished" if success else "Failed")
        self._spinner.setVisible(False)
        self.setFixedHeight(72)
        if output_path:
            self._name_label.setText(os.path.basename(output_path))
        self._sub_label.setText(_job_sub_text(size_bytes))
