"""FeatureTile — vertical gallery-style clickable card used in banner components."""

from __future__ import annotations

from PyQt5.QtCore import QPoint, QRect, QRectF, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PyQt5.QtWidgets import (
    QGraphicsBlurEffect,
    QGraphicsScene,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    CaptionLabel,
    FluentIcon,
    IconWidget,
    SubtitleLabel,
)


class FeatureTile(QWidget):
    """Vertical gallery tile: large icon, title, description, link arrow."""

    clicked = pyqtSignal()

    # hover/press overlay alphas (painted, not stylesheet)
    _OVERLAY_NORMAL  = 18
    _OVERLAY_HOVER   = 45
    _OVERLAY_PRESSED = 8
    _BLUR_RADIUS     = 20

    def __init__(
        self,
        icon: FluentIcon,
        title: str,
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setFixedSize(168, 148)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._overlay_alpha = self._OVERLAY_NORMAL
        self._bg_cache: QPixmap | None = None
        self._build(icon, title, subtitle)

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self, icon: FluentIcon, title: str, subtitle: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(6)

        # top row: main icon (left) + link arrow (right)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(0)

        icon_w = IconWidget(icon, self)
        icon_w.setFixedSize(36, 36)
        top_row.addWidget(icon_w)

        top_row.addStretch(1)

        arrow_w = IconWidget(FluentIcon.LINK, self)
        arrow_w.setFixedSize(14, 14)
        top_row.addWidget(arrow_w, 0, Qt.AlignTop)

        root.addLayout(top_row)
        root.addSpacing(8)

        # title
        title_lbl = SubtitleLabel(title, self)
        title_lbl.setStyleSheet(
            "color: white; font-size: 13px; font-weight: 600;"
            " background: transparent; padding: 0;"
        )
        title_lbl.setWordWrap(True)
        root.addWidget(title_lbl)

        # description
        if subtitle:
            desc_lbl = CaptionLabel(subtitle, self)
            desc_lbl.setStyleSheet(
                "color: rgba(255,255,255,0.60); font-size: 11px;"
                " background: transparent; padding: 0;"
            )
            desc_lbl.setWordWrap(True)
            root.addWidget(desc_lbl)

        root.addStretch(1)

    # ── background blur ──────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        # Defer the grab so the parent has fully painted before we sample it.
        QTimer.singleShot(0, self._cache_background)

    def _cache_background(self):
        """Grab and blur the parent region once; called deferred after show."""
        if not self.parent() or not self.isVisible():
            return
        pos = self.mapTo(self.parent(), QPoint(0, 0))
        raw = self.parent().grab(QRect(pos, self.size()))
        self._bg_cache = self._blur_pixmap(raw, self._BLUR_RADIUS)
        self.update()
    @staticmethod
    def _blur_pixmap(pixmap: QPixmap, radius: int) -> QPixmap:
        """Return a blurred copy of *pixmap* using QGraphicsBlurEffect."""
        scene = QGraphicsScene()
        item = scene.addPixmap(pixmap)
        effect = QGraphicsBlurEffect()
        effect.setBlurRadius(radius)
        effect.setBlurHints(QGraphicsBlurEffect.QualityHint)
        item.setGraphicsEffect(effect)

        result = QPixmap(pixmap.size())
        result.fill(Qt.transparent)
        p = QPainter(result)
        scene.render(p, source=QRectF(item.boundingRect()))
        p.end()
        return result

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.setClipPath(path)

        # Draw cached blurred background (never call grab() here)
        if self._bg_cache:
            painter.drawPixmap(0, 0, self._bg_cache)

        # Semi-transparent state overlay
        painter.fillPath(path, QColor(255, 255, 255, self._overlay_alpha))

        painter.end()

    # ── style helpers ──────────────────────────────────────────────────────

    def _set_overlay(self, alpha: int):
        self._overlay_alpha = alpha
        self.update()

    # ── mouse events ──────────────────────────────────────────────────────────

    def enterEvent(self, event):
        self._set_overlay(self._OVERLAY_HOVER)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._set_overlay(self._OVERLAY_NORMAL)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._set_overlay(self._OVERLAY_PRESSED)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._set_overlay(self._OVERLAY_HOVER if self.underMouse() else self._OVERLAY_NORMAL)
            if self.rect().contains(event.pos()):
                self.clicked.emit()
        super().mouseReleaseEvent(event)
