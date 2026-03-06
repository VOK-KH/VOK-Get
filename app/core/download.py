"""URL utilities and platform helpers for the download pipeline.

Provides normalization, validation, and platform-detection helpers used by
both the concurrent workers and the rest of the application.
The actual QThread worker lives in app.common.concurrent.download_worker.
"""

import re

from app.core.ffmpeg.manager import ffmpeg_available as _ffmpeg_available  # noqa: F401


def _impersonate_available() -> bool:
    """True if curl_cffi is available so yt-dlp can use impersonation (e.g. for TikTok)."""
    try:
        import curl_cffi  # noqa: F401
        return True
    except ImportError:
        return False


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Domains whose extractors are confirmed working with yt-dlp
SUPPORTED_DOMAINS = (
    "youtube.com", "youtu.be",
    "tiktok.com",
    "douyin.com",
    "kuaishou.com", "kwai.com",
    "instagram.com",
    "facebook.com",
    "pinterest.com", "pin.it",
    "twitter.com", "x.com",
    "ok.ru",
    "vk.com", "vkvideo.ru",
    "twitch.tv",
    "vimeo.com",
    "dailymotion.com",
    "soundcloud.com",
    "bilibili.com",
    "reddit.com",
)

# ---------------------------------------------------------------------------
# Unsupported URL patterns (fail fast with a clear message instead of timeout)
# ---------------------------------------------------------------------------
_UNSUPPORTED_URL_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Kuaishou profile / user pages — no yt-dlp extractor (see yt-dlp/yt-dlp#14010)
    (re.compile(r"kuaishou\.com/profile/[^/?#]+", re.I), "Kuaishou profile pages are not supported. Paste a direct video link (e.g. https://www.kuaishou.com/f/...) when available."),
    (re.compile(r"live\.kuaishou\.com/u/[^/?#]+", re.I), "Kuaishou live user pages are not supported. Use a direct video or livestream URL when available."),
]


def check_unsupported_url(url: str) -> str | None:
    """If the URL is known to be unsupported, return a short error message; else None."""
    url_lower = url.strip().lower()
    for pattern, message in _UNSUPPORTED_URL_PATTERNS:
        if pattern.search(url_lower):
            return message
    return None


# ---------------------------------------------------------------------------
# URL normalizers
# Each entry is (pattern, replacement_fn).  The first match wins.
# These fix embed/modal/share URLs that yt-dlp's extractors don't accept.
# ---------------------------------------------------------------------------
_URL_RULES: list[tuple[re.Pattern, "Callable[[re.Match], str]"]] = [
    # Douyin jingxuan/featured page with modal_id query param
    #   https://www.douyin.com/jingxuan?modal_id=7602920755290033448
    #   → https://www.douyin.com/video/7602920755290033448
    (
        re.compile(r"douyin\.com/[^?#]*\?.*modal_id=(\d+)", re.I),
        lambda m: f"https://www.douyin.com/video/{m.group(1)}",
    ),
    # Douyin share short-links  iesdouyin.com/share/video/ID/
    (
        re.compile(r"iesdouyin\.com/share/video/(\d+)", re.I),
        lambda m: f"https://www.douyin.com/video/{m.group(1)}",
    ),
    # TikTok share/embed  vm.tiktok.com or vt.tiktok.com (short links — keep as-is,
    # yt-dlp follows redirects; only the modal pattern needs rewriting)
    # VK clip embed  vk.com/clip-OWNER_ID  → vk.com/video-OWNER_ID  (same content)
    (
        re.compile(r"(https?://(?:www\.)?vk\.com/)clip(-\d+_\d+)", re.I),
        lambda m: f"{m.group(1)}video{m.group(2)}",
    ),
]


def normalize_url(url: str) -> tuple[str, str | None]:
    """Rewrite known embed/modal URLs to their canonical yt-dlp-compatible form.

    Returns
    -------
    (canonical_url, note)
        note is a human-readable explanation when a rewrite happened, else None.
    """
    stripped = url.strip()
    for pattern, rewrite in _URL_RULES:
        m = pattern.search(stripped)
        if m:
            canonical = rewrite(m)
            return canonical, f"URL rewritten → {canonical}"
    return stripped, None


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


_DOMAIN_LABELS: dict[str, str] = {
    "youtu.be": "YouTube",
    "youtube.com": "YouTube",
    "tiktok.com": "TikTok",
    "kwai.com": "Kuaishou",
    "kuaishou.com": "Kuaishou",
    "pin.it": "Pinterest",
    "pinterest.com": "Pinterest",
    "twitter.com": "Twitter/X",
    "x.com": "Twitter/X",
    "vkvideo.ru": "VK",
    "vk.com": "VK",
}


def detect_platform(url: str) -> str:
    """Return a short platform name from the URL, or 'Unknown'."""
    url_lower = url.lower()
    for domain in SUPPORTED_DOMAINS:
        if domain in url_lower:
            if domain in _DOMAIN_LABELS:
                return _DOMAIN_LABELS[domain]
            return domain.split(".")[0].capitalize()
    return "Unknown"
