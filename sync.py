#!/usr/bin/env python3
"""Coursera Sync — download courses and upload to Baidu Netdisk."""

import logging
import sys
import time

from constants import PROJECT_ROOT
from config import load_config
from courses import load_courses, print_status, resolve_all_courses, sync_status_from_baidu
from downloader import check_tools
from baidu import login_baidu
from pipeline import process_course


def main():
    if "--status" in sys.argv:
        print_status()
        return
    if "--resolve" in sys.argv:
        resolve_all_courses()
        return
    if "--sync-status" in sys.argv:
        sync_status_from_baidu()
        return

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

    courses = load_courses()
    enabled = [c for c in courses if c.get("enabled", True)]
    if not enabled:
        logging.warning("No enabled courses found in course-data/courses.jsonl.")
        return

    logging.info("Courses loaded: %d total, %d enabled", len(courses), len(enabled))
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
