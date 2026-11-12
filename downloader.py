"""coursera-helper download and tool detection."""

import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from config import resolve_path
from courses import is_download_done, mark_download_done, mark_download_status, clear_course_state
from utils import run as _run

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def check_tools(config: dict) -> tuple[list[str], Path]:
    python311 = shutil.which("python3.11")
    if python311:
        coursera_cmd = [python311, "-m", "coursera_helper.coursera_dl"]
    else:
        coursera_bin = shutil.which("coursera-helper") or shutil.which("coursera-dl")
        if not coursera_bin:
            logging.error(
                "coursera-helper not found. Install with:\n"
                "  pip3.11 install coursera-helper"
            )
            sys.exit(1)
        coursera_cmd = [coursera_bin]
    logging.info("coursera cmd: %s", " ".join(coursera_cmd))

    baidu_bin_val = resolve_path(config, "baidu.binary_path")
    if not baidu_bin_val.exists():
        logging.error(
            "BaiduPCS-Go not found at %s. Run:\n"
            "  bash setup_baidu.sh",
            baidu_bin_val
        )
        sys.exit(1)
    logging.info("BaiduPCS-Go:   %s", baidu_bin_val)
    return coursera_cmd, baidu_bin_val


def download_course(coursera_cmd: list[str], config: dict, course: dict) -> Optional[Path]:
    slug = course["slug"]

    if not _SLUG_RE.match(slug):
        logging.error("Invalid course slug (must be kebab-case): %r", slug)
        return None

    tmp_dir = resolve_path(config, "download.tmp_dir")
    course_dir = tmp_dir / slug
    cauth = config["auth"]["coursera_cauth"]

    if not cauth:
        logging.error("CAUTH must be set as environment variable.")
        return None

    if config["behavior"].get("force_redownload") and course_dir.exists():
        shutil.rmtree(str(course_dir))
        clear_course_state(slug)
        logging.info("Force redownload: removed %s", course_dir)

    if course_dir.exists() and is_download_done(slug):
        logging.info("Course already downloaded: %s", course_dir)
        return course_dir

    tmp_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        *coursera_cmd,
        "--cauth", cauth,
        "--video-resolution", str(config["download"]["resolution"]),
        "--path", str(tmp_dir),
        "--resume",
    ]

    if config["download"].get("download_quizzes"):
        cmd.append("--download-quizzes")
    if config["download"].get("download_notebooks"):
        cmd.append("--download-notebooks")

    subtitle_langs = config["download"].get("subtitle_languages", "")
    if subtitle_langs:
        cmd.extend(["--subtitle-language", subtitle_langs])

    cmd.append(slug)

    logging.info("Downloading: %s", slug)
    result = subprocess.run(
        cmd, text=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=3600,
    )

    if result.stdout:
        logging.debug("coursera-helper stdout:\n%s", result.stdout)

    if result.returncode != 0:
        logging.error("Download failed for %s:\n%s", slug, result.stderr)
        return None

    if not course_dir.exists() or not any(
        d.is_dir() and any(d.iterdir()) for d in course_dir.iterdir()
    ):
        logging.error(
            "Download produced empty or missing course directory: %s (exit code was 0)",
            course_dir,
        )
        return None

    mark_download_status(slug)
    mark_download_done(slug)
    logging.info("Download complete: %s", slug)
    return course_dir
