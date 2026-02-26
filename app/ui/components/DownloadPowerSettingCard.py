from qfluentwidgets import (
    ComboBox,
    ExpandGroupSettingCard,
    FluentIcon,
    IndicatorPosition,
    SwitchButton,
)

from app.config import load_settings
from app.ui.helpers import DOWNLOAD_FORMATS


class DownloadConfigCard(ExpandGroupSettingCard):
    """Expandable card grouping download format and single-video toggle.

    Attributes
    ----------
    format_combo : ComboBox
        Currently selected download format.
    single_switch : SwitchButton
        Mirrors the "single video only" setting.
    """

    def __init__(self, parent=None):
        super().__init__(
            FluentIcon.DOWNLOAD,
            "Download config",
            "Format and per-job options",
            parent,
        )
        s = load_settings()

        # Format group
        self.format_combo = ComboBox()
        self.format_combo.addItems(DOWNLOAD_FORMATS)
        default_fmt = s.get("download_format", DOWNLOAD_FORMATS[0])
        if default_fmt in DOWNLOAD_FORMATS:
            self.format_combo.setCurrentText(default_fmt)
        self.format_combo.setFixedWidth(175)

        # Single video only group
        self.single_switch = SwitchButton("Off", self, IndicatorPosition.RIGHT)
        self.single_switch.setOnText("On")
        self.single_switch.setChecked(s.get("single_video_default", True))

        # Layout tweaks
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        self.addGroup(
            FluentIcon.MEDIA,
            "Format",
            "Video/audio quality and container",
            self.format_combo,
        )
        self.addGroup(
            FluentIcon.VIDEO,
            "Single video only",
            "Download only the current video; skip playlists",
            self.single_switch,
        )
