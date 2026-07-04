"""Small, dependency-free helpers: phone normalization, folders, JSON, timestamps.

Kept intentionally tiny (PRD §9.9). No business logic here.
"""
import json
import os
from pathlib import Path
from typing import Any, Union

PathLike = Union[str, os.PathLike]

# Characters stripped when normalizing a phone number (PRD §9.1).
_PHONE_STRIP = set(" -()." )


def normalize_phone(raw: str) -> str:
    """Remove spaces, dashes, parentheses, and dots; preserve a leading '+'.

    "+1-805-439-8008" -> "+18054398008". Does not add a country code.
    """
    if not raw:
        return ""
    return "".join(ch for ch in raw if ch not in _PHONE_STRIP)


def ensure_dir(path: PathLike) -> Path:
    """Create a directory (and parents) if missing; return it. Idempotent."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path: PathLike, data: Any) -> Path:
    """Write ``data`` as pretty JSON, creating parent directories as needed."""
    p = Path(path)
    ensure_dir(p.parent)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return p


def read_json(path: PathLike) -> Any:
    """Load JSON from ``path``."""
    return json.loads(Path(path).read_text())


def format_timestamp(seconds: Union[int, float]) -> str:
    """Format a number of seconds as MM:SS (e.g. 154 -> '02:34')."""
    total = int(seconds)
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"
