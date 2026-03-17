"""
In-app auto-updater: check GitHub Releases, download installer, run silent install.

Uses GitHub API for latest release; installer is expected to be built with Inno Setup
(supports /VERYSILENT, /SUPPRESSMSGBOXES). AppMutex in the installer allows clean upgrade.
Respects system proxy (e.g. corporate) via getSystemProxy().
"""

import os
import subprocess
import sys
from typing import Tuple

from app.config.store import REPO_URL
from app.common.utils import getSystemProxy
from app.common.exception_handler import exceptionHandler

GITHUB_REPO = REPO_URL.split("/")[-2:]
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
REQUEST_TIMEOUT = 10
DOWNLOAD_CHUNK_SIZE = 8192

# Headers so GitHub doesn't reject the request
_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
}


def _parse_version(version_str: str) -> Tuple[int, ...]:
    s = (version_str or "").strip().lstrip("v")
    parts = []
    for part in s.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts) if parts else (0, 0, 0)


def _version_greater(latest: str, current: str) -> bool:
    """True if latest > current (e.g. 0.1.2 > 0.1.1)."""
    return _parse_version(latest) > _parse_version(current)


def _proxies() -> dict:
    """Proxies dict for requests (uses system proxy if set)."""
    proxy = getSystemProxy()
    if not proxy:
        return {}
    return {"http": proxy, "https": proxy}


@exceptionHandler("version", (None, None))
def check_update(current_version: str) -> Tuple[str | None, str | None]:
    """
    Check GitHub Releases for a version newer than current_version.

    Returns
    -------
    (latest_version, download_url) if update available, else (None, None).
    """
    try:
        import requests
    except ImportError:
        return None, None

    try:
        r = requests.get(
            GITHUB_API_LATEST,
            headers=_REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
            proxies=_proxies(),
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None, None

    tag = (data.get("tag_name") or "").strip().lstrip("v")
    if not tag or not _version_greater(tag, current_version):
        return None, None

    assets = data.get("assets") or []
    for asset in assets:
        name = (asset.get("name") or "").lower()
        if name.endswith(".exe") and "install" in name:
            url = asset.get("browser_download_url")
            if url:
                return tag, url
    if assets:
        url = assets[0].get("browser_download_url")
        if url:
            return tag, url
    return None, None


def download_update(url: str, progress_callback=None) -> str | None:
    """
    Download the installer to TEMP and return its path.

    progress_callback(current_bytes, total_bytes or None) is optional.
    """
    try:
        import requests
    except ImportError:
        return None

    try:
        r = requests.get(
            url,
            stream=True,
            headers=_REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            proxies=_proxies(),
        )
        r.raise_for_status()
        total = int(r.headers.get("content-length") or 0)
    except Exception:
        return None

    temp_dir = os.environ.get("TEMP", os.path.expandvars("%TEMP%"))
    path = os.path.join(temp_dir, "VOK-Update.exe")
    written = 0
    try:
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if not chunk:
                    continue
                f.write(chunk)
                written += len(chunk)
                if progress_callback and callable(progress_callback):
                    progress_callback(written, total if total else None)
        return path
    except Exception:
        try:
            os.remove(path)
        except OSError:
            pass
        return None


def install_update(installer_path: str) -> None:

    if not installer_path or not os.path.isfile(installer_path):
        return
    try:
        subprocess.Popen(
            [installer_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"],
            shell=False,
        )
    except Exception:
        pass
    sys.exit(0)
