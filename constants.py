"""Project-wide path constants."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
STATE_FILE = PROJECT_ROOT / "logs" / "upload_state.json"
COURSES_FILE = PROJECT_ROOT / "course-data" / "courses.jsonl"
STATUS_FILE = PROJECT_ROOT / "course-data" / "status.json"
