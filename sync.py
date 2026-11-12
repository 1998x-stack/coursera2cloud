#!/usr/bin/env python3
"""Coursera Sync — download courses and upload to Baidu Netdisk."""

import argparse
import logging
import sys
import time

from constants import PROJECT_ROOT
from config import load_config
from courses import load_courses, load_status, print_status, resolve_all_courses, sync_status_from_baidu
from downloader import check_tools
from baidu import login_baidu
from pipeline import process_course


def cmd_status() -> None:
    print_status()


def cmd_resolve() -> None:
    resolve_all_courses()


def cmd_sync_status() -> None:
    sync_status_from_baidu()


def cmd_stats() -> None:
    courses = load_courses()
    status = load_status()
    total = len(courses)
    enabled = [c for c in courses if c.get("enabled", True)]
    completed = [c for c in enabled if status.get(c["slug"], {}).get("downloaded")
                 and status.get(c["slug"], {}).get("uploaded")]
    downloaded = [c for c in enabled if status.get(c["slug"], {}).get("downloaded")
                  and not status.get(c["slug"], {}).get("uploaded")]
    pending = [c for c in enabled if c["slug"] not in
               {x["slug"] for x in completed + downloaded}]

    pct = (len(completed) / len(enabled) * 100) if enabled else 0
    print(f"Total courses:     {total}")
    print(f"Enabled:           {len(enabled)}")
    print(f"Completed:         {len(completed)} ({pct:.1f}%)")
    print(f"Downloaded only:   {len(downloaded)}")
    print(f"Pending:           {len(pending)}")
    if pending:
        print(f"\nNext 5 pending:")
        for c in pending[:5]:
            print(f"  - {c['slug']}  ({c.get('category', '?')})")


def cmd_default(config, args) -> None:
    coursera_cmd, baidu_bin = check_tools(config)
    login_baidu(baidu_bin, config)

    courses = load_courses()
    enabled = [c for c in courses if c.get("enabled", True)]

    if args.course:
        enabled = [c for c in enabled if c["slug"] == args.course]
        if not enabled:
            logging.error("Course not found or not enabled: %s", args.course)
            sys.exit(1)

    if not enabled:
        logging.warning("No enabled courses found.")
        return

    if args.dry_run:
        logging.info("[DRY RUN] Would process %d course(s):", len(enabled))
        for c in enabled:
            logging.info("  - %s  (%s)", c["slug"], c.get("category", "?"))
        logging.info("[DRY RUN] No changes made.")
        return

    logging.info("Courses loaded: %d total, %d enabled, %d selected",
                 len(courses), len([c for c in courses if c.get("enabled", True)]),
                 len(enabled))
    results = {"ok": [], "fail": []}
    consecutive_failures = 0
    circuit_breaker_limit = 3

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
            consecutive_failures = 0
        else:
            results["fail"].append(course["slug"])
            consecutive_failures += 1
            if consecutive_failures >= circuit_breaker_limit:
                logging.error(
                    "Circuit breaker: %d consecutive failures. "
                    "Check tokens (CAUTH, BDUSS, STOKEN) and network. Aborting.",
                    consecutive_failures,
                )
                break

    logging.info("=== Summary ===")
    logging.info("OK:    %s", ", ".join(results["ok"]) if results["ok"] else "(none)")
    logging.info("FAIL:  %s", ", ".join(results["fail"]) if results["fail"] else "(none)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Coursera Sync — download courses and upload to Baidu Netdisk.",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Print per-course completion table",
    )
    parser.add_argument(
        "--resolve", action="store_true",
        help="Refresh course names from Coursera.org",
    )
    parser.add_argument(
        "--sync-status", action="store_true",
        help="Sync status.json from Baidu directory listing",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Print aggregate statistics",
    )
    parser.add_argument(
        "--course", type=str, metavar="SLUG",
        help="Process a single course by slug",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would happen without downloading or uploading",
    )
    args = parser.parse_args()

    # Commands that don't need config or logging
    if args.status:
        return cmd_status()
    if args.resolve:
        return cmd_resolve()
    if args.sync_status:
        return cmd_sync_status()
    if args.stats:
        return cmd_stats()

    # Default pipeline — needs config and logging
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

    cmd_default(config, args)


if __name__ == "__main__":
    main()
