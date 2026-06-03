# AGENTS.md — Coursera Sync

Python 3 environment — no tests, no lint, no build. Multi-module orchestration pipeline (8 files).

## How to run

```bash
bash run.sh                  # full sync (reads creds from ~/.zshrc)
bash nohup_sync.sh           # background sync with PID file + log
python3 sync.py --status     # print course completion table
python3 sync.py --resolve    # refresh course names from Coursera.org
python3 sync.py --sync-status  # sync status.json from Baidu directory listing
```

Do NOT run `python3 sync.py` directly without `bash run.sh` — credentials live in `~/.zshrc` and `run.sh` exports them before invoking `sync.py`.

## Module structure

```
sync.py          (77 lines)  — main() entry, argument dispatch
constants.py     (8 lines)   — PROJECT_ROOT plus file path constants
utils.py         (30 lines)  — _run() subprocess helper, sanitize_baidu_path()
config.py        (43 lines)  — YAML loading, _nested_get, resolve_path
courses.py       (245 lines) — catalog, status/state persistence, resolve, sync_status
baidu.py         (83 lines)  — BaiduPCS-Go login, mkdir, upload, verify_upload
downloader.py    (91 lines)  — coursera-helper tool detection + download_course
pipeline.py      (106 lines) — upload_course + process_course orchestration
```

Dependency chain is linear — no circular imports:
`constants → utils → config → courses → {baidu, downloader} → pipeline → sync`

## Python version — 3.11 required

coursera-helper uses `distutils`, removed in Python 3.12+. The script auto-detects `python3.11` and builds the command as `python3.11 -m coursera_helper.coursera_dl`. Installing on macOS Homebrew Python requires `--break-system-packages` (PEP 668).

## Credentials

Three env vars, stored in `~/.zshrc`:
- `BDUSS` — Baidu session token
- `STOKEN` — Baidu security token (uppercase letters; NOT `bdstoken`)
- `CAUTH` — Coursera cookie auth

Tokens expire ~30 days. Re-extract from browser cookies when auth fails.

## Course catalog

Courses live in `course-data/courses.jsonl` (JSON Lines), NOT in `config.yaml`:

```json
{"slug": "course-slug", "name": "Display Name", "category": "Cat / Subcategory", "enabled": true}
```

`config.yaml` contains global settings (resolution, upload policy, retries, delays). It is gitignored — do not commit credentials.

## Baidu path gotchas — auto-sanitized

- Characters `&`, `#`, `?` in category or course names break BaiduPCS-Go paths. `sanitize_baidu_path()` in `utils.py` automatically replaces `&` → `and` and strips `#`/`?` at upload time. A warning is also logged at course load if any name contains these characters.
- Paths containing `--` cause BaiduPCS-Go `ls` to fail with error 31062. Both `verify_upload()` and `ensure_remote_dir()` in `baidu.py` detect this error and gracefully proceed (skip verification, attempt mkdir anyway).

## State files

- `course-data/status.json` — per-course `{downloaded: bool, uploaded: bool}`. Automatic checkpoints after download and upload. Complete courses are skipped on re-run.
- `logs/upload_state.json` — per-week upload checkpoint. Enables resume after partial upload.
- These two are the sole sources of resume state. Deleting either forces re-work.
- All state writes are **atomic** (write to `.tmp` first, then `replace()`). Corrupted files are detected on load with a warning and reset.

## Pipeline architecture

```
run.sh → python3 sync.py
           ├── check_tools() → finds python3.11 + bin/BaiduPCS-Go
           ├── login_baidu() → BaiduPCS-Go login -bduss=... -stoken=...
           └── for each enabled course in courses.jsonl:
                 ├── download_course() → python3.11 -m coursera_helper.coursera_dl -ca $CAUTH --resume ...
                 ├── upload_course() → BaiduPCS-Go u ./tmp/week_dir/ /coursera/Category/Course/
                 └── cleanup tmp/ on success (if cleanup_after_upload: true)
```

## Adding courses

Add a line to `course-data/courses.jsonl`. No other files need changing. Run `python3 sync.py --resolve` to auto-fetch the course name from Coursera if you only know the slug.

## Force re-download

Set `behavior.force_redownload: true` in `config.yaml`, run once, then set back to `false`. This deletes `tmp/{slug}/` and resets the download checkpoint before re-downloading.

Note: `force_redownload` only works if the course is NOT already marked complete in `status.json`. If a previously-completed course needs re-downloading, clear its entry from `status.json` first or delete `course-data/status.json` entirely.
