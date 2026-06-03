"""Course catalog, status / state persistence, and remote sync."""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

import requests
import yaml

from config import resolve_path
from constants import COURSES_FILE, PROJECT_ROOT, STATE_FILE, STATUS_FILE


# ---------------------------------------------------------------------------
# Course catalog
# ---------------------------------------------------------------------------

def load_courses() -> list[dict]:
    from utils import has_baidu_unsafe_chars

    courses = []
    if COURSES_FILE.exists():
        for line in COURSES_FILE.read_text().strip().split("\n"):
            if line.strip():
                c = json.loads(line)
                for field in ("category", "name"):
                    val = c.get(field, "")
                    if has_baidu_unsafe_chars(val):
                        import logging
                        logging.warning(
                            "Course '%s' has '%s' containing chars that break BaiduPCS-Go (& # ?): %r",
                            c.get("slug", "?"), field, val
                        )
                courses.append(c)
    return courses


def resolve_course_name(slug: str, timeout: int = 10) -> Optional[dict]:
    url = f"https://www.coursera.org/learn/{slug}"
    try:
        resp = requests.get(url, timeout=timeout, allow_redirects=True,
                           headers={"User-Agent": "Mozilla/5.0"})
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    match = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', resp.text)
    if not match:
        match = re.search(r"<title>(.*?)</title>", resp.text)
    name = match.group(1).strip() if match else slug
    return {"slug": slug, "name": name, "url": url, "status": resp.status_code}


def resolve_all_courses() -> None:
    courses = load_courses()
    total = len(courses)
    ok, fail = 0, 0
    for i, c in enumerate(courses):
        slug = c["slug"]
        result = resolve_course_name(slug)
        if result:
            ok += 1
            old_name = c["name"]
            if result["name"] != old_name:
                c["name"] = result["name"]
                print(f"[{i+1:3d}/{total}] ✅ {slug}")
                print(f"            old: {old_name}")
                print(f"            new: {result['name']}")
            else:
                print(f"[{i+1:3d}/{total}] ✅ {slug}")
        else:
            fail += 1
            print(f"[{i+1:3d}/{total}] ❌ {slug} (not found)")
    tmp_path = COURSES_FILE.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        for c in courses:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    tmp_path.replace(COURSES_FILE)
    print(f"\nDone: {ok} valid, {fail} not found")


# ---------------------------------------------------------------------------
# Course-level status (status.json)
# ---------------------------------------------------------------------------

def load_status() -> dict:
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            import logging
            logging.warning("status.json corrupted — resetting")
    return {}


def save_status(status: dict) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = STATUS_FILE.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(status, indent=2, ensure_ascii=False))
    tmp_path.replace(STATUS_FILE)


def get_course_status(slug: str) -> dict:
    return load_status().get(slug, {})


def is_course_complete(slug: str) -> bool:
    s = get_course_status(slug)
    return s.get("downloaded", False) and s.get("uploaded", False)


def print_status() -> None:
    courses = load_courses()
    status = load_status()
    if not courses:
        print("No courses found in course-data/courses.jsonl")
        return
    print(f"{'SLUG':<55} {'DOWNLOADED':>12} {'UPLOADED':>12}")
    print("-" * 81)
    for c in courses:
        s = status.get(c["slug"], {})
        dl = "✅" if s.get("downloaded") else "⬜"
        up = "✅" if s.get("uploaded") else "⬜"
        print(f"{c['slug']:<55} {dl:>12} {up:>12}")


def mark_download_status(slug: str) -> None:
    status = load_status()
    status.setdefault(slug, {})["downloaded"] = True
    save_status(status)


def mark_upload_status(slug: str) -> None:
    status = load_status()
    status.setdefault(slug, {})["uploaded"] = True
    save_status(status)


def clear_status(slug: str) -> None:
    status = load_status()
    status.pop(slug, None)
    save_status(status)


# ---------------------------------------------------------------------------
# Week-level upload state (upload_state.json)
# ---------------------------------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            import logging
            logging.warning("upload_state.json corrupted — resetting")
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = STATE_FILE.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    tmp_path.replace(STATE_FILE)


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


# ---------------------------------------------------------------------------
# Remote status sync (from Baidu directory listing)
# ---------------------------------------------------------------------------

def sync_status_from_baidu() -> None:
    from utils import run as _run

    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        print("config.yaml not found")
        return

    config = yaml.safe_load(config_path.read_text())
    if not config:
        print("config.yaml is empty")
        return

    binary_path = config.get("baidu", {}).get("binary_path", "./bin/BaiduPCS-Go")
    remote_root = config.get("baidu", {}).get("remote_root", "/coursera")
    baidu_bin = resolve_path({"baidu": {"binary_path": binary_path}}, "baidu.binary_path")
    if not baidu_bin.exists():
        print("BaiduPCS-Go not found at", baidu_bin)
        return

    def parse_names(output):
        names = set()
        for line in output.split("\n"):
            parts = line.split()
            if len(parts) >= 5 and parts[0].isdigit():
                names.add(" ".join(parts[4:]).rstrip("/"))
        return names

    def _ls_or_empty(path: str) -> str:
        result = _run([str(baidu_bin), "ls", path])
        if result.returncode == 0:
            return result.stdout
        stderr = (result.stderr or "").lower()
        if "31062" in stderr or "invalid" in stderr:
            return ""
        return ""

    bduss = os.environ.get("BDUSS", "")
    stoken = os.environ.get("STOKEN", "")
    if not bduss or not stoken:
        bduss = subprocess.run(["grep", "^export BDUSS=", str(Path.home()/".zshrc")], capture_output=True, text=True).stdout.strip().replace("export BDUSS=", "")
        stoken = subprocess.run(["grep", "^export STOKEN=", str(Path.home()/".zshrc")], capture_output=True, text=True).stdout.strip().replace("export STOKEN=", "")
    login_result = _run([str(baidu_bin), "login", f"-bduss={bduss}", f"-stoken={stoken}"])
    if login_result.returncode != 0:
        print("Baidu login failed")
        return

    baidu_courses = set()
    for top_dir in parse_names(_ls_or_empty(remote_root)):
        top_path = f"{remote_root}/{top_dir}"
        for cat in parse_names(_ls_or_empty(top_path)):
            cat_path = f"{top_path}/{cat}"
            for course in parse_names(_ls_or_empty(cat_path)):
                baidu_courses.add(course)

    courses = load_courses()
    status = load_status()
    fixed = 0
    for c in courses:
        name = c["name"]
        on_baidu = name in baidu_courses
        cur = status.get(c["slug"], {})
        if cur.get("downloaded") != on_baidu or cur.get("uploaded") != on_baidu:
            status.setdefault(c["slug"], {})["downloaded"] = on_baidu
            status.setdefault(c["slug"], {})["uploaded"] = on_baidu
            fixed += 1
            print(f"{'✅' if on_baidu else '⬜'} {c['slug']}")
    save_status(status)
    print(f"\nSynced {fixed} entries. {len(baidu_courses)} courses on Baidu.")
