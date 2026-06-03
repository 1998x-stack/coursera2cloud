"""BaiduPCS-Go operations: login, upload, directory management, verification."""

import logging
import sys
from pathlib import Path

from utils import run as _run


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
    local_entries = sum(1 for _ in local_dir.glob("*"))
    result = _run([str(baidu_bin), "ls", remote_path])
    if result.returncode != 0:
        if "31062" in result.stderr or "invalid" in result.stderr.lower():
            logging.warning("Verification skipped (BaiduPCS-Go ls cannot handle path with spaces): %s", remote_path)
            return True
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
    parts = [p.strip() for p in path.strip("/").split("/") if p.strip()]
    current = ""
    for part in parts:
        current = f"{current}/{part}"
        check = _run([str(baidu_bin), "ls", current])
        if check.returncode != 0:
            if "31062" in check.stderr or "invalid" in check.stderr.lower():
                logging.debug("ls cannot handle path segment — skipping check: %s", current)
            mkdir_result = _run([str(baidu_bin), "mkdir", current])
            if mkdir_result.returncode != 0:
                logging.warning("Could not create remote dir: %s", current)
                return False
    return True
