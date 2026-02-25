"""VOK application package."""

import re
from pathlib import Path

def _get_version() -> str:
    try:
        from importlib.metadata import version
        return version("vok")
    except Exception:
        pass
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        m = re.search(r'version\s*=\s*"([^"]+)"', text)
        if m:
            return m.group(1)
    return "0.0.0"

__version__ = _get_version()
