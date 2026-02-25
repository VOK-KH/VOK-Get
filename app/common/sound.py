"""Play sound files for download complete (success) and download error. Uses QtMultimedia if available, else subprocess fallback."""

import os
import subprocess
import sys

from app.common.paths import RESOURCES_DIR

SOUND_SUCCESS = "universfield.mp3"
SOUND_ERROR = "alert-sound.mp3"

# Keep references to active players so they are not garbage-collected during playback
_players: list = []


def _play_via_subprocess(path: str) -> None:
    """Fallback: open with system default handler (may open external app)."""
    path = os.path.normpath(path)
    if not os.path.isfile(path):
        return
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(
                ["xdg-open", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception:
        pass


def _play_file(path) -> None:
    """Play a sound file under resources/sound/. path is Path or filename str."""
    if not path:
        return
    if isinstance(path, str):
        path = RESOURCES_DIR / "sound" / path
    if not path.is_file():
        return
    path_str = str(path.resolve())
    try:
        from PyQt5.QtCore import QUrl
        from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

        player = QMediaPlayer()
        player.setMedia(QMediaContent(QUrl.fromLocalFile(path_str)))

        def on_state_changed(state):
            if state == QMediaPlayer.StoppedState and player in _players:
                _players.remove(player)

        player.stateChanged.connect(on_state_changed)
        _players.append(player)
        player.play()
    except Exception:
        _play_via_subprocess(path_str)


def play_download_sound(success: bool) -> None:
    """Play sound for download result: success → universfield.mp3, error → alert-sound.mp3."""
    filename = SOUND_SUCCESS if success else SOUND_ERROR
    path = RESOURCES_DIR / "sound" / filename
    _play_file(path)
