"""Shared subprocess runner and path utilities."""

import logging
import re
import subprocess
from pathlib import Path
from typing import Optional


def run(cmd: list[str], cwd: Optional[Path] = None, timeout: int = 3600) -> subprocess.CompletedProcess:
    logging.debug("RUN: %s", " ".join(cmd))
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


_BAIDU_UNSAFE_CHARS = re.compile(r"[&#?]")

def sanitize_baidu_path(segment: str) -> str:
    """Replace characters that break BaiduPCS-Go path handling.

    ``&``, ``#``, ``?`` are treated as shell/URL special characters by
    the Baidu API and cause silent upload failures or ``ls`` errors.
    """
    segment = segment.replace("&", "and")
    segment = _BAIDU_UNSAFE_CHARS.sub("", segment)
    return segment


def has_baidu_unsafe_chars(segment: str) -> bool:
    return bool(_BAIDU_UNSAFE_CHARS.search(segment)) or "&" in segment
