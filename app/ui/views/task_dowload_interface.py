"""Task Download Interface: subtitle table editor with command bar toolbar."""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, QTime, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QColor, QDragEnterEvent, QDropEvent, QKeyEvent
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    Action,
    BodyLabel,
    CommandBar,
    InfoBar,
    InfoBarPosition,
    MessageBoxBase,
    PrimaryPushButton,
    ProgressBar,
    PushButton,
    RoundMenu,
    TableView,
    TextEdit,
    TransparentDropDownPushButton,
)
from qfluentwidgets import FluentIcon as FIF

# ── Local constants (replace broken app.core.constant) ────────────────────────
INFOBAR_MS_SUCCESS = 3000
INFOBAR_MS_ERROR = 5000
INFOBAR_MS_WARNING = 4000
INFOBAR_MS_INFO = 3000

# ── Local enums / format lists (replace broken app.core.entities) ─────────────
OUTPUT_SUBTITLE_FORMATS = ["srt", "vtt", "ass", "txt", "lrc"]
SUBTITLE_LAYOUTS = ["译文在上", "原文在上", "仅译文", "仅原文"]
SUPPORTED_SUBTITLE_EXTENSIONS = {"srt", "vtt", "ass", "txt", "lrc", "ssa"}
TARGET_LANGUAGES = [
    "中文", "英语", "日语", "韩语", "法语", "德语", "西班牙语", "俄语",
    "葡萄牙语", "意大利语", "阿拉伯语", "泰语", "越南语", "印尼语",
]

DEFAULT_LAYOUT = "仅原文"
DEFAULT_LANGUAGE = "中文"


def _open_folder(path: str) -> None:
    """Open a folder in the OS file manager."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


# ── Subtitle table model ───────────────────────────────────────────────────────

class SubtitleTableModel(QAbstractTableModel):
    def __init__(self, data: Union[str, Dict[str, Any]] = ""):
        super().__init__()
        self._data: Dict[str, Any] = {}
        self._need_translate: bool = False
        if isinstance(data, str):
            self.load_data(data)
        else:
            self._data = data

    def load_data(self, data: str):
        try:
            self._data = json.loads(data)
            self.layoutChanged.emit()
        except json.JSONDecodeError:
            pass

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore
        if not index.isValid() or not self._data:
            return None
        row = index.row()
        col = index.column()
        segment = self._data.get(str(row + 1))
        if not segment:
            return None
        if role in (Qt.DisplayRole, Qt.EditRole):  # type: ignore
            if col == 0:
                return QTime(0, 0).addMSecs(segment["start_time"]).toString("hh:mm:ss.zzz")[:-2]
            elif col == 1:
                return QTime(0, 0).addMSecs(segment["end_time"]).toString("hh:mm:ss.zzz")[:-2]
            elif col == 2:
                return segment.get("original_subtitle", "")
            elif col == 3:
                return segment.get("translated_subtitle", "")
        elif role == Qt.TextAlignmentRole:  # type: ignore
            if col in (0, 1):
                return Qt.AlignCenter  # type: ignore
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:  # type: ignore
        if not index.isValid() or not self._data:
            return False
        if role == Qt.EditRole:  # type: ignore
            segment = self._data.get(str(index.row() + 1))
            if not segment:
                return False
            if index.column() == 2:
                segment["original_subtitle"] = value
            elif index.column() == 3:
                segment["translated_subtitle"] = value
            else:
                return False
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])  # type: ignore
            return True
        return False

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.DisplayRole) -> Any:  # type: ignore
        if role == Qt.DisplayRole:  # type: ignore
            if orientation == Qt.Horizontal:  # type: ignore
                labels = [
                    self.tr("开始时间"), self.tr("结束时间"),
                    self.tr("字幕内容"),
                    self.tr("翻译字幕") if self._need_translate else self.tr("优化字幕"),
                ]
                return labels[section] if section < len(labels) else None
            elif orientation == Qt.Vertical:  # type: ignore
                return str(section + 1)
        elif role == Qt.TextAlignmentRole:  # type: ignore
            return Qt.AlignCenter  # type: ignore
        return None

    def rowCount(self, parent: Optional[QModelIndex] = None) -> int:
        return len(self._data)

    def columnCount(self, parent: Optional[QModelIndex] = None) -> int:
        return 4

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags  # type: ignore
        if index.column() in (2, 3):
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable  # type: ignore
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable  # type: ignore

    def update_data(self, new_data: Dict[str, str]) -> None:
        updated_rows = set()
        for key, value in new_data.items():
            if key in self._data:
                self._data[key]["translated_subtitle"] = value
                row = list(self._data.keys()).index(key)
                updated_rows.add(row)
        if updated_rows:
            min_row, max_row = min(updated_rows), max(updated_rows)
            self.dataChanged.emit(
                self.index(min_row, 2), self.index(max_row, 3),
                [Qt.DisplayRole, Qt.EditRole],  # type: ignore
            )

    def update_all(self, data: Dict[str, Any]) -> None:
        self._data = data
        self.layoutChanged.emit()


# ── Main widget ────────────────────────────────────────────────────────────────

class TaskDownloadInterface(QWidget):
    """Subtitle table editor: command bar + TableView + progress bar."""

    finished = pyqtSignal(str, str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.task: Optional[dict] = None
        self.subtitle_path: Optional[str] = None
        self.setAttribute(Qt.WA_DeleteOnClose)  # type: ignore

        # UI state (replaces cfg.xxx)
        self._need_translate: bool = False
        self._need_optimize: bool = False
        self._subtitle_layout: str = DEFAULT_LAYOUT
        self._target_language: str = DEFAULT_LANGUAGE
        self._custom_prompt: str = ""

        self._init_ui()
        self._set_initial_values()

    # ── UI setup ───────────────────────────────────────────────────────────────

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self._setup_top_layout()
        self._setup_subtitle_table()
        self._setup_bottom_layout()

    def _set_initial_values(self):
        self.layout_button.setText(self._subtitle_layout)
        self.translate_button.setChecked(self._need_translate)
        self.optimize_button.setChecked(self._need_optimize)
        self.target_language_button.setText(self._target_language)
        self.target_language_button.setEnabled(self._need_translate)

    def _setup_top_layout(self):
        top_layout = QHBoxLayout()

        self.command_bar = CommandBar(self)
        self.command_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # type: ignore
        top_layout.addWidget(self.command_bar, 1)

        # Save drop-down
        save_menu = RoundMenu(parent=self)
        save_menu.view.setMaxVisibleItems(8)
        for fmt in OUTPUT_SUBTITLE_FORMATS:
            action = Action(text=fmt.upper())
            action.triggered.connect(
                lambda checked, f=fmt: self.on_save_format_clicked(f)
            )
            save_menu.addAction(action)
        save_button = TransparentDropDownPushButton(self.tr("保存"), self, FIF.SAVE)
        save_button.setMenu(save_menu)
        save_button.setFixedHeight(34)
        self.command_bar.addWidget(save_button)

        # Subtitle layout drop-down
        self.layout_button = TransparentDropDownPushButton(
            self.tr("字幕排布"), self, FIF.LAYOUT
        )
        self.layout_button.setFixedHeight(34)
        self.layout_button.setMinimumWidth(125)
        self.layout_menu = RoundMenu(parent=self)
        for layout in SUBTITLE_LAYOUTS:
            action = Action(text=layout)
            action.triggered.connect(
                lambda checked, lv=layout: self._on_layout_changed(lv)
            )
            self.layout_menu.addAction(action)
        self.layout_button.setMenu(self.layout_menu)
        self.command_bar.addWidget(self.layout_button)

        self.command_bar.addSeparator()

        # Optimize toggle
        self.optimize_button = Action(
            FIF.EDIT, self.tr("字幕校正"),
            triggered=self._on_optimize_toggled,
            checkable=True,
        )
        self.command_bar.addAction(self.optimize_button)

        # Translate toggle
        self.translate_button = Action(
            FIF.LANGUAGE, self.tr("字幕翻译"),
            triggered=self._on_translate_toggled,
            checkable=True,
        )
        self.command_bar.addAction(self.translate_button)

        # Target language drop-down
        self.target_language_button = TransparentDropDownPushButton(
            self.tr("翻译语言"), self, FIF.LANGUAGE
        )
        self.target_language_button.setFixedHeight(34)
        self.target_language_button.setMinimumWidth(125)
        lang_menu = RoundMenu(parent=self)
        lang_menu.setMaxVisibleItems(10)
        for lang in TARGET_LANGUAGES:
            action = Action(text=lang)
            action.triggered.connect(
                lambda checked, lv=lang: self._on_language_changed(lv)
            )
            lang_menu.addAction(action)
        self.target_language_button.setMenu(lang_menu)
        self.command_bar.addWidget(self.target_language_button)

        self.command_bar.addSeparator()

        # Prompt button
        self.prompt_button = Action(
            FIF.DOCUMENT, self.tr("Prompt"),
            triggered=self._show_prompt_dialog,
        )
        self.command_bar.addAction(self.prompt_button)

        # Settings (stub)
        self.command_bar.addAction(
            Action(FIF.SETTING, "", triggered=self._show_subtitle_settings)
        )

        # Open folder
        self.command_bar.addAction(
            Action(FIF.FOLDER, "", triggered=self._on_open_folder)
        )

        self.command_bar.addSeparator()

        # File select
        self.command_bar.addAction(
            Action(FIF.FOLDER_ADD, "", triggered=self._on_file_select)
        )

        # Start button
        self.start_button = PrimaryPushButton(self.tr("开始"), self, icon=FIF.PLAY)
        self.start_button.setFixedHeight(34)
        self.start_button.clicked.connect(self._on_start_clicked)
        top_layout.addWidget(self.start_button)

        self.main_layout.addLayout(top_layout)

    def _setup_subtitle_table(self):
        self.subtitle_table = TableView(self)
        self.model = SubtitleTableModel("")
        self.subtitle_table.setModel(self.model)
        self.subtitle_table.setBorderVisible(True)
        self.subtitle_table.setBorderRadius(8)
        self.subtitle_table.setWordWrap(True)
        hdr = self.subtitle_table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.Stretch)
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        hdr.setSectionResizeMode(1, QHeaderView.Fixed)
        self.subtitle_table.setColumnWidth(0, 120)
        self.subtitle_table.setColumnWidth(1, 120)
        v_hdr = self.subtitle_table.verticalHeader()
        v_hdr.setVisible(True)
        v_hdr.setDefaultAlignment(Qt.AlignCenter)  # type: ignore
        v_hdr.setDefaultSectionSize(50)
        v_hdr.setMinimumWidth(20)
        self.subtitle_table.setEditTriggers(
            QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed  # type: ignore
        )
        self.subtitle_table.setContextMenuPolicy(Qt.CustomContextMenu)  # type: ignore
        self.subtitle_table.customContextMenuRequested.connect(self._show_context_menu)
        self.main_layout.addWidget(self.subtitle_table)

    def _setup_bottom_layout(self):
        bottom_layout = QHBoxLayout()

        self.progress_bar = ProgressBar(self)
        self.status_label = BodyLabel(self.tr("请拖入字幕文件"), self)
        self.status_label.setMinimumWidth(100)
        self.status_label.setAlignment(Qt.AlignCenter)  # type: ignore

        self.cancel_button = PushButton(self.tr("取消"), self, icon=FIF.CANCEL)
        self.cancel_button.hide()
        self.cancel_button.clicked.connect(self._on_cancel)

        bottom_layout.addWidget(self.progress_bar, 1)
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(bottom_layout)

    # ── Toolbar slot handlers ──────────────────────────────────────────────────

    def _on_layout_changed(self, layout: str) -> None:
        self._subtitle_layout = layout
        self.layout_button.setText(layout)

    def _on_optimize_toggled(self, checked: bool) -> None:
        self._need_optimize = checked
        self.optimize_button.setChecked(checked)

    def _on_translate_toggled(self, checked: bool) -> None:
        self._need_translate = checked
        self.translate_button.setChecked(checked)
        self.target_language_button.setEnabled(checked)
        self.model._need_translate = checked
        self.model.headerDataChanged.emit(Qt.Horizontal, 3, 3)  # type: ignore

    def _on_language_changed(self, lang: str) -> None:
        self._target_language = lang
        self.target_language_button.setText(lang)

    def _on_open_folder(self) -> None:
        if self.subtitle_path:
            _open_folder(str(Path(self.subtitle_path).parent))
        else:
            InfoBar.warning(
                self.tr("Warning"), self.tr("No subtitle file loaded."),
                duration=INFOBAR_MS_WARNING, parent=self,
            )

    def _on_file_select(self) -> None:
        exts = " ".join(f"*.{e}" for e in sorted(SUPPORTED_SUBTITLE_EXTENSIONS))
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Select subtitle file"), "",
            f"{self.tr('Subtitle files')} ({exts})"
        )
        if path:
            self.subtitle_path = path
            self._load_subtitle_file(path)

    def _show_prompt_dialog(self) -> None:
        dialog = _PromptDialog(self._custom_prompt, self)
        if dialog.exec_():
            self._custom_prompt = dialog.get_prompt()
            self._refresh_prompt_icon()

    def _refresh_prompt_icon(self) -> None:
        if self._custom_prompt.strip():
            self.prompt_button.setIcon(
                FIF.DOCUMENT.colored(QColor(76, 255, 165), QColor(76, 255, 165))
            )
        else:
            self.prompt_button.setIcon(FIF.DOCUMENT)

    def _show_subtitle_settings(self) -> None:
        InfoBar.info(
            self.tr("Settings"),
            self.tr("Subtitle settings coming soon."),
            duration=INFOBAR_MS_INFO, parent=self,
        )

    # ── Start / cancel ─────────────────────────────────────────────────────────

    def _on_start_clicked(self) -> None:
        if not self.subtitle_path:
            InfoBar.warning(
                self.tr("Warning"), self.tr("Please load a subtitle file first."),
                duration=INFOBAR_MS_WARNING, parent=self,
            )
            return
        InfoBar.info(
            self.tr("Started"),
            self.tr("Processing subtitle…"),
            duration=INFOBAR_MS_INFO, parent=self,
        )
        self.start_button.setEnabled(False)
        self.cancel_button.show()
        self.progress_bar.setValue(0)

    def _on_cancel(self) -> None:
        self.start_button.setEnabled(True)
        self.cancel_button.hide()
        self.progress_bar.setValue(0)
        self.status_label.setText(self.tr("已取消"))
        InfoBar.warning(
            self.tr("Cancelled"), self.tr("Operation cancelled."),
            duration=INFOBAR_MS_WARNING, parent=self,
        )

    # ── Progress feedback (for external wiring) ────────────────────────────────

    def set_progress(self, value: int, status: str = "") -> None:
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)

    def on_finished(self, video_path: str = "", output_path: str = "") -> None:
        self.start_button.setEnabled(True)
        self.cancel_button.hide()
        self.progress_bar.setValue(100)
        if video_path or output_path:
            self.finished.emit(video_path, output_path)
        InfoBar.success(
            self.tr("Done"), self.tr("Subtitle processing complete."),
            duration=INFOBAR_MS_SUCCESS,
            position=InfoBarPosition.BOTTOM,
            parent=self.parent() or self,
        )

    def on_error(self, error: str) -> None:
        self.start_button.setEnabled(True)
        self.cancel_button.hide()
        self.progress_bar.error()
        InfoBar.error(
            self.tr("Error"), self.tr(error),
            duration=INFOBAR_MS_ERROR, parent=self,
        )

    # ── Save ───────────────────────────────────────────────────────────────────

    def on_save_format_clicked(self, fmt: str) -> None:
        if not self.subtitle_path:
            InfoBar.warning(
                self.tr("Warning"), self.tr("No subtitle file loaded."),
                duration=INFOBAR_MS_WARNING, parent=self,
            )
            return
        default_name = Path(self.subtitle_path).stem
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save subtitle file"), default_name,
            f"{self.tr('Subtitle files')} (*.{fmt})"
        )
        if not path:
            return
        try:
            rows = []
            for key in sorted(self.model._data.keys(), key=lambda k: int(k)):
                seg = self.model._data[key]
                start = seg.get("original_subtitle", "")
                rows.append(start)
            Path(path).write_text("\n".join(rows), encoding="utf-8")
            InfoBar.success(
                self.tr("Saved"), self.tr(f"Saved to: {path}"),
                duration=INFOBAR_MS_SUCCESS, parent=self,
            )
        except Exception as exc:
            InfoBar.error(
                self.tr("Save failed"), str(exc),
                duration=INFOBAR_MS_ERROR, parent=self,
            )

    # ── Data loading (stub — wire real parser when available) ──────────────────

    def _load_subtitle_file(self, file_path: str) -> None:
        """Load subtitle rows from a plain SRT/VTT/TXT file into the table."""
        self.subtitle_path = file_path
        try:
            text = Path(file_path).read_text(encoding="utf-8", errors="replace")
            self._parse_and_load(text)
            self.status_label.setText(self.tr("已加载文件"))
            InfoBar.success(
                self.tr("Loaded"), os.path.basename(file_path),
                duration=INFOBAR_MS_SUCCESS,
                position=InfoBarPosition.BOTTOM, parent=self,
            )
        except Exception as exc:
            InfoBar.error(
                self.tr("Load error"), str(exc),
                duration=INFOBAR_MS_ERROR, parent=self,
            )

    def _parse_and_load(self, text: str) -> None:
        """Build a minimal subtitle dict from raw text (best-effort, no deps)."""
        import re
        # Try SRT blocks: index \n start --> end \n text...
        srt_block = re.compile(
            r"(\d+)\s*\n(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*\n([\s\S]*?)(?=\n\d+\n|\Z)",
            re.MULTILINE,
        )
        data: Dict[str, Any] = {}

        def ms(ts: str) -> int:
            ts = ts.replace(",", ".")
            h, m, rest = ts.split(":")
            s, ms_ = rest.split(".")
            return int(h) * 3600000 + int(m) * 60000 + int(s) * 1000 + int(ms_[:3])

        for m in srt_block.finditer(text):
            idx = m.group(1)
            data[idx] = {
                "start_time": ms(m.group(2)),
                "end_time": ms(m.group(3)),
                "original_subtitle": m.group(4).strip(),
                "translated_subtitle": "",
            }
        if not data:
            # Fallback: one entry per non-empty line
            for i, line in enumerate(text.splitlines(), 1):
                if line.strip():
                    data[str(i)] = {
                        "start_time": 0,
                        "end_time": 0,
                        "original_subtitle": line.strip(),
                        "translated_subtitle": "",
                    }
        self.model.update_all(data)

    # ── Public API (called from HomeInterface or DownloaderView) ───────────────

    def set_task(self, task: dict) -> None:
        self.task = task
        path = task.get("subtitle_path") or task.get("file_path", "")
        if path and os.path.isfile(path):
            self.subtitle_path = path
            self._load_subtitle_file(path)

    # ── Drag & drop ────────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.accept() if event.mimeData().hasUrls() else event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not os.path.isfile(path):
                continue
            ext = os.path.splitext(path)[1][1:].lower()
            if ext in SUPPORTED_SUBTITLE_EXTENSIONS:
                self._load_subtitle_file(path)
            else:
                InfoBar.error(
                    self.tr(f"Unsupported format: .{ext}"),
                    self.tr("Supported: ") + ", ".join(sorted(SUPPORTED_SUBTITLE_EXTENSIONS)),
                    duration=INFOBAR_MS_ERROR, parent=self,
                )
            break
        event.accept()

    # ── Context menu ───────────────────────────────────────────────────────────

    def _show_context_menu(self, pos) -> None:
        indexes = self.subtitle_table.selectedIndexes()
        if not indexes:
            return
        rows = sorted({idx.row() for idx in indexes})
        menu = RoundMenu(parent=self)
        merge_action = Action(FIF.LINK, self.tr("合并"))
        merge_action.setShortcut("Ctrl+M")
        merge_action.setEnabled(len(rows) > 1)
        merge_action.triggered.connect(lambda: self._merge_rows(rows))
        menu.addAction(merge_action)
        menu.exec(self.subtitle_table.viewport().mapToGlobal(pos))

    def _merge_rows(self, rows: List[int]) -> None:
        if len(rows) < 2:
            return
        data = self.model._data
        data_list = list(data.values())
        first, last = data_list[rows[0]], data_list[rows[-1]]
        merged = {
            "start_time": first["start_time"],
            "end_time": last["end_time"],
            "original_subtitle": " ".join(data_list[r]["original_subtitle"] for r in rows),
            "translated_subtitle": " ".join(data_list[r]["translated_subtitle"] for r in rows),
        }
        keys = list(data.keys())
        preserved = keys[: rows[0]] + keys[rows[-1] + 1:]
        new_data: Dict[str, Any] = {}
        inserted = False
        for i, key in enumerate(preserved):
            if i == rows[0] and not inserted:
                new_data[str(len(new_data) + 1)] = merged
                inserted = True
            new_data[str(len(new_data) + 1)] = data[key]
        if not inserted:
            new_data[str(len(new_data) + 1)] = merged
        self.model.update_all(new_data)
        InfoBar.success(
            self.tr("Merged"), self.tr(f"Merged {len(rows)} rows."),
            duration=INFOBAR_MS_SUCCESS, parent=self,
        )

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_M:  # type: ignore
            indexes = self.subtitle_table.selectedIndexes()
            if indexes:
                rows = sorted({idx.row() for idx in indexes})
                if len(rows) > 1:
                    self._merge_rows(rows)
            event.accept()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)


# ── Prompt dialog ──────────────────────────────────────────────────────────────

class _PromptDialog(MessageBoxBase):
    def __init__(self, current_prompt: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._current_prompt = current_prompt
        self._setup_ui()
        self.yesButton.clicked.connect(self._save)

    def _setup_ui(self) -> None:
        self.viewLayout.addWidget(BodyLabel(self.tr("文稿提示"), self))
        self.text_edit = TextEdit(self)
        self.text_edit.setPlaceholderText(
            self.tr(
                "Enter prompt to assist subtitle correction and translation.\n\n"
                "Examples:\n"
                "• Glossary: Machine Learning -> 机器学习\n"
                "• Style instructions: use formal language\n"
                "• Corrections: unify pronouns"
            )
        )
        self.text_edit.setText(self._current_prompt)
        self.text_edit.setMinimumWidth(420)
        self.text_edit.setMinimumHeight(380)
        self.viewLayout.addWidget(self.text_edit)
        self.viewLayout.setSpacing(10)
        self.yesButton.setText(self.tr("确定"))
        self.cancelButton.setText(self.tr("取消"))

    def get_prompt(self) -> str:
        return self.text_edit.toPlainText()

    def _save(self) -> None:
        self._current_prompt = self.text_edit.toPlainText()
