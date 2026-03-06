# coding: utf-8
"""Common utilities: file names, JSON, URLs, explorer, process execution, proxy."""

import os
import re
import sys
from json import loads
from pathlib import Path
from typing import Union

from PyQt5.QtCore import QDir, QFile, QFileInfo, QProcess, QStandardPaths, QUrl
from PyQt5.QtGui import QDesktopServices


def adjustFileName(name: str) -> str:
    """Normalize a file name for safe use on disk."""
    name = re.sub(r'[\\/:*?"<>|\r\n\s]+', "_", name.strip()).strip()
    return name.rstrip(".")


def readFile(filePath: str) -> str:
    """Read file contents as UTF-8 string."""
    f = QFile(filePath)
    if not f.open(QFile.ReadOnly):
        return ""
    data = f.readAll().data().decode("utf-8", errors="replace")
    f.close()
    return data


def loadJsonData(filePath: str):
    """Load JSON from file."""
    return loads(readFile(filePath))


def removeFile(filePath: Union[str, Path]) -> None:
    """Remove file if it exists; ignore errors."""
    try:
        os.remove(filePath)
    except OSError:
        pass


def openUrl(url: str) -> bool:
    """Open URL in default app (browser or local file)."""
    if not url.startswith("http"):
        if not os.path.exists(url):
            return False
        QDesktopServices.openUrl(QUrl.fromLocalFile(url))
    else:
        QDesktopServices.openUrl(QUrl(url))
    return True


def showInFolder(path: Union[str, Path]) -> bool:
    """Reveal file or folder in system file explorer."""
    if not os.path.exists(path):
        return False
    if isinstance(path, Path):
        path = str(path.absolute())
    if not path or path.lower().startswith("http"):
        return False

    info = QFileInfo(path)
    if sys.platform == "win32":
        args = [QDir.toNativeSeparators(path)]
        if not info.isDir():
            args.insert(0, "/select,")
        QProcess.startDetached("explorer", args)
    elif sys.platform == "darwin":
        args = [
            "-e", "tell application \"Finder\"",
            "-e", "activate",
            "-e", f'select POSIX file "{path}"',
            "-e", "end tell",
            "-e", "return",
        ]
        QProcess.execute("/usr/bin/osascript", args)
    else:
        url = QUrl.fromLocalFile(path if info.isDir() else info.path())
        QDesktopServices.openUrl(url)
    return True


def runProcess(
    executable: Union[str, Path],
    args=None,
    timeout: int = 5000,
    cwd: Union[str, Path, None] = None,
) -> str:
    """Run process and return stdout as UTF-8 string."""
    process = QProcess()
    if cwd:
        process.setWorkingDirectory(str(cwd))
    process.start(str(executable).replace("\\", "/"), args or [])
    process.waitForFinished(timeout)
    out = process.readAllStandardOutput()
    return out.data().decode("utf-8", errors="replace")


def runDetachedProcess(
    executable: Union[str, Path],
    args=None,
    cwd: Union[str, Path, None] = None,
) -> None:
    """Start process detached (no wait)."""
    process = QProcess()
    if cwd:
        process.setWorkingDirectory(str(cwd))
    process.startDetached(str(executable).replace("\\", "/"), args or [])


def getSystemProxy() -> str:
    """Return system HTTP proxy URL if set; otherwise empty string or env proxy."""
    if sys.platform == "win32":
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
                if enabled:
                    return "http://" + winreg.QueryValueEx(key, "ProxyServer")[0]
        except (OSError, ValueError):
            pass
    elif sys.platform == "darwin":
        try:
            s = os.popen("scutil --proxy").read()
            info = dict(re.findall(r"(?m)^\s+([A-Z]\w+)\s+:\s+(\S+)", s))
            if info.get("HTTPEnable") == "1":
                return f"http://{info.get('HTTPProxy', '')}:{info.get('HTTPPort', '')}"
            if info.get("ProxyAutoConfigEnable") == "1":
                return info.get("ProxyAutoConfigURLString", "")
        except (OSError, KeyError):
            pass
    return os.environ.get("http_proxy", "") or os.environ.get("HTTP_PROXY", "")
