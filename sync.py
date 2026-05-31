#!/usr/bin/env python3

import json
import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent
STATE_FILE = PROJECT_ROOT / "logs" / "upload_state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def mark_week_uploaded(slug: str, week_name: str) -> None:
    state = load_state()
    state.setdefault(slug, {})[week_name] = True
    save_state(state)


def is_week_uploaded(slug: str, week_name: str) -> bool:
    return load_state().get(slug, {}).get(week_name, False)


def clear_course_state(slug: str) -> None:
    state = load_state()
    state.pop(slug, None)
    save_state(state)


def mark_download_done(slug: str) -> None:
    state = load_state()
    state.setdefault(slug, {})["_downloaded"] = True
    save_state(state)


def is_download_done(slug: str) -> bool:
    return load_state().get(slug, {}).get("_downloaded", False)


def _nested_get(d: dict, dotted_key: str):
    """Resolve 'section.subsection.key' against a nested dict."""
    node = d
    for part in dotted_key.split("."):
        if not isinstance(node, dict):
            raise KeyError(dotted_key)
        node = node[part]
    return node


def load_config(config_path: Path) -> dict:
    raw = yaml.safe_load(config_path.read_text())
    env_keys = [
        ("auth", "coursera_cauth"),
        ("auth", "baidu_bduss"),
        ("auth", "baidu_stoken"),
    ]
    for section, key in env_keys:
        try:
            raw[section][key] = os.path.expandvars(raw[section][key])
        except KeyError:
            pass
    try:
        raw["download"]["tmp_dir"] = os.path.expandvars(raw["download"]["tmp_dir"])
    except KeyError:
        pass
    return raw


def resolve_path(config: dict, dotted_key: str) -> Path:
    p = Path(_nested_get(config, dotted_key))
    return p if p.is_absolute() else PROJECT_ROOT / p


def _run(cmd: list[str], cwd: Optional[Path] = None, timeout: int = 3600) -> subprocess.CompletedProcess:
    logging.debug("RUN: %s", " ".join(cmd))
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


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


def login_baidu(baidu_bin: Path, config: dict) -> None:
    bduss = config["auth"]["baidu_bduss"]
    stoken = config["auth"]["baidu_stoken"]

    if not bduss or not stoken:
        logging.error(
            "BAIDU_BDUSS and BAIDU_STOKEN must be set as environment variables.\n"
            "Note: credentials will appear in the process list (ps aux) while running."
        )
        sys.exit(1)

    result = _run(
        [str(baidu_bin), "login", f"-bduss={bduss}", f"-stoken={stoken}"]
    )
    if result.returncode != 0:
        logging.error("Baidu login failed:\n%s", result.stderr)
        sys.exit(1)
    logging.info("Baidu login OK")

    baidu_cfg = config["baidu"]
    concurrency = {
        "max_parallel": str(baidu_cfg.get("max_parallel", 10)),
        "max_download_load": str(baidu_cfg.get("max_download_load", 2)),
        "max_upload_parallel": str(baidu_cfg.get("max_upload_parallel", 8)),
        "max_upload_load": str(baidu_cfg.get("max_upload_load", 4)),
    }
    for key, val in concurrency.items():
        r = _run([str(baidu_bin), "config", "set", f"-{key}", val])
        if r.returncode != 0:
            logging.warning("Failed to set %s=%s: %s", key, val, r.stderr.strip())
    logging.info("Baidu concurrency: download=%s/%s upload=%s/%s",
                 concurrency["max_parallel"], concurrency["max_download_load"],
                 concurrency["max_upload_parallel"], concurrency["max_upload_load"])

    result = _run([str(baidu_bin), "quota"])
    logging.info("Baidu quota:\n%s", result.stdout.strip())


def verify_upload(baidu_bin: Path, remote_path: str, local_dir: Path) -> bool:
    local_entries = sum(1 for _ in local_dir.rglob("*"))
    result = _run([str(baidu_bin), "ls", remote_path])
    if result.returncode != 0:
        logging.warning("Verification failed: cannot list %s", remote_path)
        return False
    remote_entries = 0
    for line in result.stdout.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("-") or stripped.startswith("总") or stripped.startswith("当前") or "文件总数" in stripped or "文件(目录)" in stripped:
            continue
        remote_entries += 1
    if remote_entries >= local_entries:
        logging.info("Verified: %s (%d remote >= %d local)", remote_path, remote_entries, local_entries)
        return True
    logging.warning("Verification mismatch: %s local=%d remote=%d", remote_path, local_entries, remote_entries)
    return False


def ensure_remote_dir(baidu_bin: Path, path: str) -> bool:
    parts = [p for p in path.strip("/").split("/") if p]
    current = ""
    for part in parts:
        current = f"{current}/{part}"
        check = _run([str(baidu_bin), "ls", current])
        if check.returncode != 0:
            mkdir_result = _run([str(baidu_bin), "mkdir", current])
            if mkdir_result.returncode != 0:
                logging.warning("Could not create remote dir: %s", current)
                return False
    return True


def download_course(coursera_cmd: list[str], config: dict, course: dict) -> Optional[Path]:
    slug = course["slug"]
    tmp_dir = resolve_path(config, "download.tmp_dir")
    course_dir = tmp_dir / slug
    cauth = config["auth"]["coursera_cauth"]

    if not cauth:
        logging.error("CAUTH must be set as environment variable.")
        return None

    if config["behavior"].get("force_redownload") and course_dir.exists():
        shutil.rmtree(course_dir)
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

    if config["download"]["download_quizzes"]:
        cmd.append("--download-quizzes")
    if config["download"]["download_notebooks"]:
        cmd.append("--download-notebooks")

    subtitle_langs = config["download"]["subtitle_languages"]
    if subtitle_langs:
        cmd.extend(["--subtitle-language", subtitle_langs])

    cmd.append(slug)

    logging.info("Downloading: %s", slug)
    result = _run(cmd)

    if result.returncode != 0:
        logging.error("Download failed for %s:\n%s", slug, result.stderr)
        return None

    mark_download_done(slug)
    logging.info("Download complete: %s", slug)
    return course_dir


def upload_course(baidu_bin: Path, config: dict, course: dict, local_dir: Path) -> bool:
    slug = course["slug"]
    name = course["name"]
    category = course["category"]
    remote_root = config["baidu"]["remote_root"]
    policy = config["baidu"]["upload_policy"]

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
                logging.error("Verification failed for: %s", week_name)
                failed = True
                break

        logging.info("Uploaded: %s (%d/%d)", week_name, uploaded, len(weeks))

    if skipped > 0:
        logging.info("Skipped %d already-uploaded weeks for %s", skipped, name)

    if failed:
        logging.warning("Upload interrupted — run again to resume from checkpoint")
        return False

    return True


def process_course(coursera_cmd: list[str], baidu_bin: Path, config: dict, course: dict) -> bool:
    slug = course["slug"]
    retries = config["behavior"]["max_retries"]

    for attempt in range(1, retries + 1):
        logging.info("=== [%s] Attempt %d/%d ===", slug, attempt, retries)

        course_dir = download_course(coursera_cmd, config, course)
        if course_dir is None:
            logging.warning("Download failed for %s (attempt %d)", slug, attempt)
            continue

        if upload_course(baidu_bin, config, course, course_dir):
            if config["behavior"]["cleanup_after_upload"]:
                shutil.rmtree(course_dir)
                clear_course_state(slug)
                logging.info("Cleaned up: %s", course_dir)
            return True

        logging.warning("Upload interrupted for %s (attempt %d) — checkpoint saved", slug, attempt)

    logging.error("All %d attempts failed for %s", retries, slug)
    return False


def main():
    config_path = PROJECT_ROOT / "config.yaml"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not config_path.exists():
        logging.error("config.yaml not found at %s", config_path)
        sys.exit(1)

    config = load_config(config_path)

    log_level = config["behavior"].get("log_level", "INFO")
    logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))

    coursera_cmd, baidu_bin = check_tools(config)
    login_baidu(baidu_bin, config)

    enabled = [c for c in config["courses"] if c.get("enabled", True)]
    if not enabled:
        logging.warning("No enabled courses found in config.")
        return

    logging.info("Courses to process: %d", len(enabled))
    results = {"ok": [], "fail": []}

    for i, course in enumerate(enabled):
        if not isinstance(course, dict) or "slug" not in course:
            logging.warning("Skipping invalid course entry: %s", course)
            continue

        if i > 0:
            delay = config["download"]["course_delay"]
            logging.info("Waiting %ds before next course...", delay)
            time.sleep(delay)

        if process_course(coursera_cmd, baidu_bin, config, course):
            results["ok"].append(course["slug"])
        else:
            results["fail"].append(course["slug"])

    logging.info("=== Summary ===")
    logging.info("OK:    %s", ", ".join(results["ok"]) if results["ok"] else "(none)")
    logging.info("FAIL:  %s", ", ".join(results["fail"]) if results["fail"] else "(none)")


if __name__ == "__main__":
    main()
