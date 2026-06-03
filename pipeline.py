"""Course processing pipeline: upload + orchestration (download → upload → cleanup)."""

import logging
import shutil
from pathlib import Path

from baidu import ensure_remote_dir, verify_upload
from courses import (
    is_week_uploaded, mark_week_uploaded, mark_upload_status,
    clear_course_state, is_course_complete,
)
from downloader import download_course
from utils import run as _run


def upload_course(baidu_bin: Path, config: dict, course: dict, local_dir: Path) -> bool:
    from utils import sanitize_baidu_path

    slug = course["slug"]
    name = sanitize_baidu_path(course["name"])
    # Split category path components and strip whitespace around "/"
    # e.g. "Computer Science / AI and Machine Learning" → "Computer Science/AI and Machine Learning"
    category_parts = [p.strip() for p in sanitize_baidu_path(course["category"]).split("/")]
    category = "/".join(category_parts)
    remote_root = config["baidu"]["remote_root"]
    policy = config["baidu"].get("upload_policy", "rsync")

    course_remote = f"{remote_root}/{category}/{name}"

    if not ensure_remote_dir(baidu_bin, course_remote):
        return False

    weeks = sorted([d for d in local_dir.iterdir() if d.is_dir()])
    skipped = sum(1 for w in weeks if is_week_uploaded(slug, w.name))
    uploaded = skipped
    failed = False

    for week_dir in weeks:
        week_name = week_dir.name

        if is_week_uploaded(slug, week_name):
            logging.info("Skip (already uploaded): %s", week_name)
            continue

        cmd = [
            str(baidu_bin), "u",
            str(week_dir), f"{course_remote}/",
            "--policy", policy,
        ]
        result = _run(cmd, timeout=7200)

        if result.returncode != 0:
            logging.error(
                "Upload failed for %s -> %s:\n%s",
                week_name, course_remote, result.stderr
            )
            failed = True
            break

        mark_week_uploaded(slug, week_name)
        uploaded += 1

        if config["baidu"].get("verify_upload", False):
            week_remote = f"{course_remote}/{week_name}"
            if not verify_upload(baidu_bin, week_remote, week_dir):
                logging.warning("Verification mismatch for: %s (upload reported success, continuing)", week_name)

        logging.info("Uploaded: %s (%d/%d)", week_name, uploaded, len(weeks))

    if skipped > 0:
        logging.info("Skipped %d already-uploaded weeks for %s", skipped, name)

    if failed:
        logging.warning("Upload interrupted — run again to resume from checkpoint")
        return False

    return True


def process_course(coursera_cmd: list[str], baidu_bin: Path, config: dict, course: dict) -> bool:
    slug = course["slug"]
    retries = config["behavior"].get("max_retries", 3)

    if is_course_complete(slug):
        logging.info("=== [%s] Already complete (status.json) — skipping ===", slug)
        return True

    for attempt in range(1, retries + 1):
        logging.info("=== [%s] Attempt %d/%d ===", slug, attempt, retries)

        course_dir = download_course(coursera_cmd, config, course)
        if course_dir is None:
            logging.warning("Download failed for %s (attempt %d)", slug, attempt)
            continue

        if upload_course(baidu_bin, config, course, course_dir):
            mark_upload_status(slug)
            if config["behavior"]["cleanup_after_upload"]:
                shutil.rmtree(str(course_dir))
                clear_course_state(slug)
                logging.info("Cleaned up: %s", course_dir)
            return True

        logging.warning("Upload interrupted for %s (attempt %d) — checkpoint saved", slug, attempt)

    logging.error("All %d attempts failed for %s", retries, slug)
    return False
