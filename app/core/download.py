"""URL utilities and platform helpers for the download pipeline.

Provides normalization, validation, and platform-detection helpers used by
both the concurrent workers and the rest of the application.
The actual QThread worker lives in app.common.concurrent.download_worker.
"""

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

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
    (
        re.compile(r"douyin\.com/[^?#]*\?.*modal_id=(\d+)", re.I),
        lambda m: f"https://www.douyin.com/video/{m.group(1)}",
    ),
    (
        re.compile(r"iesdouyin\.com/share/video/(\d+)", re.I),
        lambda m: f"https://www.douyin.com/video/{m.group(1)}",
    ),
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


# ---------------------------------------------------------------------------
# Collection URL detection (playlist / channel / profile / group)
# ---------------------------------------------------------------------------

_COLLECTION_PATTERNS: list[re.Pattern] = [
    # YouTube playlist
    re.compile(r"(?:youtube\.com|youtu\.be).*[?&]list=", re.I),
    # YouTube channel / user / handle
    re.compile(r"youtube\.com/(?:channel/|c/|user/|@)[^/?#]+/?$", re.I),
    re.compile(r"youtube\.com/@[^/?#]+(?:/videos|/shorts|/streams|/playlists)?/?$", re.I),
    # TikTok profile  (@username without /video/ segment)
    re.compile(r"tiktok\.com/@[^/?#]+/?$", re.I),
    # TikTok hashtag / discover / tag
    re.compile(r"tiktok\.com/(?:tag|discover|music)/", re.I),
    # Instagram profile, hashtag, highlights
    re.compile(r"instagram\.com/(?!p/|reel/|stories/)[^/?#]+/?$", re.I),
    re.compile(r"instagram\.com/explore/tags/", re.I),
    # Twitter / X list or hashtag-style search
    re.compile(r"(?:twitter|x)\.com/[^/?#]+/lists/", re.I),
    re.compile(r"(?:twitter|x)\.com/i/lists/", re.I),
    # Facebook page, group, reel list
    re.compile(r"facebook\.com/(?:groups?|pages?|profile\.php|[^/?#]+/videos)/?", re.I),
    # Bilibili user space / playlist
    re.compile(r"bilibili\.com/(?:space|playlist)/", re.I),
    # SoundCloud user / sets (album or playlist)
    re.compile(r"soundcloud\.com/[^/?#]+/(?:sets|likes|tracks)/?", re.I),
    re.compile(r"soundcloud\.com/[^/?#]+/?$", re.I),
    # VK community / video list
    re.compile(r"vk\.com/(?:club|public|videos)[^/?#]*", re.I),
    # Twitch channel
    re.compile(r"twitch\.tv/[^/?#]+/?$", re.I),
    # Dailymotion playlist / user
    re.compile(r"dailymotion\.com/(?:playlist/|user/)", re.I),
    # Pinterest board
    re.compile(r"pinterest\.com/[^/?#]+/[^/?#]+/?$", re.I),
    # Reddit subreddit / user (multi-post pages)
    re.compile(r"reddit\.com/(?:r|user)/[^/?#]+/?$", re.I),
]


def detect_collection_url(url: str) -> bool:
    """Return True if the URL points to a playlist, channel, profile or group.

    Uses lightweight regex matching — no network call required.
    """
    for pattern in _COLLECTION_PATTERNS:
        if pattern.search(url):
            return True
    return False


def url_to_single_video(url: str) -> str | None:
    """If the URL is a YouTube watch URL with both v= and list=, return URL with only v= (current video).

    So only the current video is used instead of the full playlist.
    Returns None if the URL cannot be reduced to a single video (e.g. channel, or no v=).
    """
    stripped = url.strip()
    parsed = urlparse(stripped)
    if parsed.netloc and "youtube.com" not in parsed.netloc.lower() and "youtu.be" not in parsed.netloc.lower():
        return None
    # youtube.com/watch?v=ID&list=...
    if "list=" not in stripped and "list=" not in parsed.query:
        return None
    qs = parse_qs(parsed.query, keep_blank_values=False)
    video_id = qs.get("v", [None])[0] if qs.get("v") else None
    if not video_id:
        return None
    new_query = urlencode({"v": video_id})
    new = parsed._replace(query=new_query)
    return urlunparse(new)

