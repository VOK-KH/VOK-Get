
"""About page — app identity, feature overview, and quick links."""

from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon as FIF,
    HyperlinkButton,
    IconWidget,
    LargeTitleLabel,
    StrongBodyLabel,
    TitleLabel,
)

import app as _app
from app.common.paths import RESOURCES_DIR
from .base import BaseView


# ── Helpers ───────────────────────────────────────────────────────────────────

class _FeatureRow(CardWidget):
    """Single feature row: icon + title stacked on description."""

    def __init__(self, icon, title: str, description: str, parent=None):
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(14, 8, 14, 8)
        row.setSpacing(12)

        icon_w = IconWidget(icon, self)
        icon_w.setFixedSize(20, 20)
        row.addWidget(icon_w, 0, Qt.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(1)
        title_lbl = StrongBodyLabel(title, self)
        desc_lbl  = CaptionLabel(description, self)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: gray;")
        text_col.addWidget(title_lbl)
        text_col.addWidget(desc_lbl)
        row.addLayout(text_col, 1)


class _SectionTitle(TitleLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setContentsMargins(0, 8, 0, 4)


# ── About view ────────────────────────────────────────────────────────────────

class AboutInterface(BaseView):
    """About — app identity, features, links."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About")
        self._layout.setContentsMargins(32, 32, 32, 32)
        self._layout.setSpacing(16)
        self._build_ui()

    def _build_ui(self) -> None:
        # ── Header ────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setSpacing(20)

        logo = QLabel(self)
        pix = QPixmap(str(RESOURCES_DIR / "logo.png"))
        if not pix.isNull():
            pix = pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo.setPixmap(pix)
        logo.setFixedSize(72, 72)
        header.addWidget(logo, 0, Qt.AlignTop)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        name_lbl = LargeTitleLabel("VOK Get", self)
        title_col.addWidget(name_lbl)

        tagline = BodyLabel(
            "Video Downloader & Batch Enhancer — download from 1 000+ platforms "
            "and post-process your videos in a few clicks.",
            self,
        )
        tagline.setWordWrap(True)
        title_col.addWidget(tagline)

        ver_lbl = CaptionLabel(f"Version {_app.__version__}", self)
        ver_lbl.setStyleSheet("color: gray;")
        title_col.addWidget(ver_lbl)
        header.addLayout(title_col, 1)

        self._layout.addLayout(header)

        # ── Download features ─────────────────────────────────────────────
        self._layout.addWidget(_SectionTitle("Download", self))

        _DOWNLOAD_FEATURES = [
            (FIF.DOWNLOAD,   "HD Video",          "4K, 1080p, 720p, Best — pick the quality that suits you."),
            (FIF.MUSIC,      "Audio (MP3)",        "Extract audio tracks as MP3 with a single toggle."),
            (FIF.PHOTO,      "Photos & Images",   "Save image posts and thumbnails automatically."),
            (FIF.COPY,       "Bulk Download",     "Paste one URL per line — all jobs run in parallel."),
            (FIF.CHECKBOX,   "Selective Download","Preview a playlist, tick the items, download only those."),
            (FIF.SPEED_HIGH, "Parallel Jobs",     "Up to 4 concurrent downloads and 16 fragment threads."),
            (FIF.WIFI,       "1 000+ Sites",      "Powered by yt-dlp: YouTube, TikTok, Pinterest, Vimeo, and more."),
            (FIF.FINGERPRINT,"Cookie Auth",       "Authenticated downloads — point to a Netscape cookies file."),
        ]
        for icon, title, desc in _DOWNLOAD_FEATURES:
            self._layout.addWidget(_FeatureRow(icon, title, desc, self))

        # ── Enhance features ──────────────────────────────────────────────
        self._layout.addWidget(_SectionTitle("Batch Enhance", self))

        _ENHANCE_FEATURES = [
            (FIF.ZOOM_IN,    "Batch Processing",  "Add files or drop a folder — process dozens of videos in one run."),
            (FIF.PHOTO,      "Logo Overlay",      "Watermark with a PNG/JPG logo: position, size, and offset controls."),
            (FIF.ROTATE,     "Flip",              "Mirror horizontally, vertically, or both."),
            (FIF.SPEED_HIGH, "Playback Speed",    "Output at 0.5×, 0.75×, 1×, 1.25×, 1.5×, 1.75×, or 2×."),
            (FIF.PALETTE,    "Color Adjustment",  "Tune brightness, contrast, and saturation per job."),
            (FIF.FIT_PAGE,   "Aspect Ratio",      "Reframe to 16:9, 9:16, 4:3, or 1:1 with blur/color/stretch fill."),
            (FIF.SAVE,       "Keep Original",     "Optionally preserve the source file alongside the enhanced output."),
            (FIF.TILES,      "Concurrent Tasks",  "Run 1–4 enhancement workers simultaneously — configurable in Settings."),
        ]
        for icon, title, desc in _ENHANCE_FEATURES:
            self._layout.addWidget(_FeatureRow(icon, title, desc, self))

        # ── Tech stack note ───────────────────────────────────────────────
        self._layout.addWidget(_SectionTitle("Built With", self))
        tech_card = CardWidget(self)
        tech_lay  = QVBoxLayout(tech_card)
        tech_lay.setContentsMargins(16, 12, 16, 12)
        tech_lay.setSpacing(4)
        for line in (
            "Python 3.12+ · PyQt5 · PyQt-Fluent-Widgets (Fluent Design UI)",
            "yt-dlp — video extraction engine (1 000+ sites)",
            "FFmpeg — media encoding, stream editing, audio extraction",
            "Playwright / aiohttp / BeautifulSoup4 — scraping pipeline",
        ):
            lbl = BodyLabel(line, tech_card)
            lbl.setWordWrap(True)
            tech_lay.addWidget(lbl)
        self._layout.addWidget(tech_card)

        # ── Links ─────────────────────────────────────────────────────────
        links_row = QHBoxLayout()
        links_row.setSpacing(12)
        links_row.addWidget(
            HyperlinkButton("https://github.com/k10978311-ai/VOK-Get", "GitHub", self)
        )
        links_row.addWidget(
            HyperlinkButton("https://github.com/k10978311-ai/VOK-Get/releases", "Releases", self)
        )
        links_row.addWidget(
            HyperlinkButton("https://github.com/k10978311-ai/VOK-Get/issues", "Report a Bug", self)
        )
        links_row.addStretch()
        self._layout.addLayout(links_row)

        self._layout.addStretch()
