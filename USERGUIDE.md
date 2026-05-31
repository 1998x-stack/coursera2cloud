# Coursera Sync — User Guide & Gotchas

This is the **definitive setup and troubleshooting guide** for the Coursera → Baidu Netdisk sync pipeline. Every issue documented below was encountered and resolved during real-world testing on macOS (Apple Silicon).

---

## Table of Contents

- [Prerequisites & First-Time Setup](#prerequisites--first-time-setup)
- [Running the Sync](#running-the-sync)
- [Gotchas & Resolved Issues](#gotchas--resolved-issues)
- [Verification Checklist](#verification-checklist)
- [Maintenance](#maintenance)

---

## Prerequisites & First-Time Setup

### Step 1: Install Python dependencies

```bash
cd coursera-sync
pip3 install --break-system-packages -r requirements.txt
pip3 install --break-system-packages coursera-helper
```

> ⚠️ **Gotcha 1 — PEP 668 on macOS Homebrew Python**: macOS Homebrew Python 3.14+ marks itself as "externally managed". You MUST use `--break-system-packages` with pip. Without it, pip refuses to install globally.

### Step 2: Set up BaiduPCS-Go

**Option A — From source (recommended, works offline):**

```bash
cd /path/to/BaiduPCS-Go  # local clone
go build -o ../coursera-sync/bin/BaiduPCS-Go .
```

> ⚠️ **Gotcha 2 — Go toolchain version mismatch**: The local BaiduPCS-Go clone requires Go ≥ 1.23 (`go.mod`), but macOS Homebrew Go may be 1.22.x. The Go proxy download (`golang.org/toolchain`) is blocked in China. Solution: download prebuilt binary OR use `GOTOOLCHAIN=local` (which fails because 1.22 < 1.23).

> ✅ **Resolution**: Download the prebuilt binary directly.

**Option B — Prebuilt binary (recommended):**

```bash
bash setup_baidu.sh
```

> ⚠️ **Gotcha 3 — macOS binary naming**: The setup script uses `darwin-arm64` but the actual GitHub release asset is named `darwin-osx-arm64`. The setup script was fixed to match.

### Step 3: Configure credentials

**The credentials live in `~/.zshrc`** with these exact variable names:

```bash
export BDUSS="your-bduss-value"
export STOKEN="your-stoken-value"
export CAUTH="your-cauth-value"
```

> ⚠️ **Gotcha 4 — Variable name mismatch**: The original config.yaml used `${COURSERA_CAUTH}`, `${BAIDU_BDUSS}`, `${BAIDU_STOKEN}`. The user's `.zshrc` uses `$CAUTH`, `$BDUSS`, `$STOKEN` (shorter names). Config was updated to match.

**How to get tokens:**

| Token | Source | Location in DevTools |
|-------|--------|---------------------|
| CAUTH | coursera.org → login | F12 → Application → Cookies → `coursera.org` → `CAUTH` |
| BDUSS | pan.baidu.com → login | F12 → Application → Cookies → `pan.baidu.com` → `BDUSS` |
| STOKEN | pan.baidu.com → login | F12 → Application → Cookies → `pan.baidu.com` → `STOKEN` |

> ⚠️ **Gotcha 5 — STOKEN ≠ bdstoken**: The `bdstoken` field is a different cookie. STOKEN contains uppercase letters. If your STOKEN is all lowercase, you copied the wrong field.

> ⚠️ **Gotcha 6 — Token expiry**: BDUSS and CAUTH expire approximately every 30 days. STOKEN expires with the same session. When sync fails with auth errors, re-extract fresh tokens from your browser.

### Step 4: Configure courses

Edit `config.yaml`:

```yaml
courses:
  - slug: "executing-full-text-queries-with-elasticsearch"
    name: "Executing Full Text Queries with Elasticsearch"
    category: "Computer Science / Databases & Search"
    enabled: true
```

The slug comes from the course URL: `coursera.org/learn/`**`executing-full-text-queries-with-elasticsearch`**

---

## Running the Sync

### Standard run (loads credentials from ~/.zshrc):

```bash
cd coursera-sync
bash run.sh
```

> ⚠️ **Gotcha 7 — Shell persistence**: In OpenCode's persistent shell, `export` in one `bash` call does NOT reliably persist to the next. The `run.sh` wrapper extracts credentials directly from `~/.zshrc` before each run, eliminating this issue.

### Manual credential export:

```bash
eval "$(grep -E '^export (BDUSS|STOKEN|CAUTH)=' ~/.zshrc)"
python3 sync.py
```

> ⚠️ **Gotcha 8 — Special characters in CAUTH**: The CAUTH cookie value contains `.` and `_` characters. When using `eval`, wrap the export in single quotes to prevent shell interpretation.

---

## Gotchas & Resolved Issues

### Setup Gotchas

| # | Issue | Root Cause | Resolution |
|---|-------|-----------|------------|
| G1 | `pip install` fails on macOS | PEP 668: externally-managed-environment | Use `--break-system-packages` |
| G2 | Go build fails (toolchain 1.23 required) | go.mod requires ≥1.23, system has 1.22 | Download prebuilt binary |
| G3 | BaiduPCS-Go download 404 | Asset name is `darwin-osx-arm64`, not `darwin-arm64` | Fixed setup script |
| G4 | Env var names mismatch | Config uses `BAIDU_BDUSS`, zshrc uses `BDUSS` | Updated config.yaml to match zshrc |
| G5 | STOKEN wrong field | Copied `bdstoken` instead of `STOKEN` | Correct field has uppercase letters |
| G6 | BDUSS/STOKEN expired | ~30 day TTL | Re-extract from browser |
| G7 | Env vars lost between bash calls | OpenCode subprocess isolation | Use `run.sh` wrapper |
| G8 | CAUTH special chars cause eval issues | `.` and `_` interpreted by shell | Single-quote the export value |

### Runtime Gotchas

| # | Issue | Root Cause | Resolution |
|---|-------|-----------|------------|
| R1 | `coursera-helper` crashes on Python 3.14 | `distutils` removed in Python 3.12+ | Use `python3.11 -m coursera_helper.coursera_dl` |
| R2 | coursera-helper requires `-u` or `-n` | Argparse validation at line 519 | Ensure CAUTH is non-empty AND correctly passed as `-ca` |
| R3 | Baidu quota error 31045 | Stale BDUSS token | Re-extract fresh BDUSS from browser |
| R4 | Download returns 0 sections | CAUTH expired or incorrect | Verify CAUTH in browser, re-extract |
| R5 | Download timeout (>10 min) | Large courses (e.g., Information Theory) | Increase subprocess timeout in sync.py (`timeout=7200`) |
| R6 | Upload returns success but files missing on Baidu | `&` in category path treated as shell special character by Baidu API | **Use `and` instead of `&` in category names**; avoid `&`, `#`, `?` in Baidu paths |

### Code Bugs Fixed (in sync.py)

| # | Bug | Impact | Fix |
|---|-----|--------|-----|
| B1 | `resolve_path()` crashes on nested dict keys | Script crashes on startup | Added `_nested_get()` with dot-notation support |
| B2 | Upload double-nests directories | Files land in wrong Baidu path | Don't pre-create week dirs; use parent as target |
| B3 | `logging.basicConfig()` after `logging.error()` | First error has no formatting | Moved `basicConfig()` to top of `main()` |
| B4 | Missing `--resume` flag on download | Interrupted downloads restart from scratch | Added `--resume` to coursera-helper command |
| B5 | Partial downloads re-skipped on retry | Directory exists but incomplete | Added `force_redownload` config option |
| B6 | Hardcoded `"coursera-helper"` binary name | Doesn't use resolved Python 3.11 path | `check_tools()` now returns resolved command list |
| B7 | `load_config()` crashes on missing keys | Optional config keys cause crash | Added try/except KeyError guards |
| B8 | Dead code in `upload_course()` | Confusing remote_target overwrite | Removed dead variable, unified path logic |

---

## Verification Checklist

After setup, verify each component before running a full sync:

```bash
# 1. Python dependencies
python3.11 -c "from coursera_helper.coursera_dl import main; print('OK')"

# 2. BaiduPCS-Go
./bin/BaiduPCS-Go version 2>&1 | grep "v4"

# 3. Baidu login
eval "$(grep -E '^export (BDUSS|STOKEN)=' ~/.zshrc)"
./bin/BaiduPCS-Go login -bduss="$BDUSS" -stoken="$STOKEN"
./bin/BaiduPCS-Go who        # should show 用户名 and uid > 0
./bin/BaiduPCS-Go quota      # should show 总空间 and 已用空间

# 4. Coursera auth
eval "$(grep '^export CAUTH=' ~/.zshrc)"
python3.11 -m coursera_helper.coursera_dl -ca "$CAUTH" --path ./tmp --list-courses

# 5. Config
python3 -c "
import yaml
c = yaml.safe_load(open('config.yaml'))
print(f'{len(c[\"courses\"])} courses configured')
"
```

If all 5 checks pass, run: `bash run.sh`

---

## Maintenance

### Weekly token refresh

BDUSS and CAUTH expire every ~30 days. Set a calendar reminder. When expired:

1. Open Chrome → pan.baidu.com → F12 → copy BDUSS and STOKEN
2. Open Chrome → coursera.org → F12 → copy CAUTH
3. Update `~/.zshrc` with new values
4. Verify: `bash run.sh`

### Updating BaiduPCS-Go

```bash
# Check current version
./bin/BaiduPCS-Go 2>&1 | head -3

# Download latest
bash setup_baidu.sh
```

### Adding new courses

Edit `config.yaml`, add a new entry:

```yaml
  - slug: "new-course-slug"
    name: "New Course Name"
    category: "Category / Subcategory"
    enabled: true
```

Then run: `bash run.sh`

### Force re-download

If a download was interrupted and the tmp directory exists but is incomplete:

```yaml
# In config.yaml:
behavior:
  force_redownload: true
```

Run once with this flag, then set back to `false`.

---

## Architecture Notes

### Why Python 3.11 for coursera-helper?

| Python Version | coursera-helper status |
|---------------|----------------------|
| 3.14 (macOS default) | ❌ `distutils` removed |
| 3.12 | ❌ `distutils` removed |
| 3.11 (conda) | ✅ Works (deprecation warnings only) |
| 3.10 | ✅ Works |
| 3.9 | ✅ Works |

The sync.py auto-detects `python3.11` and uses `python3.11 -m coursera_helper.coursera_dl` as the download command. If python3.11 is not available, it falls back to the `coursera-helper` binary (which may fail on Python 3.12+).

### Command Execution Model

```
run.sh
  ├── reads ~/.zshrc → exports BDUSS, STOKEN, CAUTH
  └── python3 sync.py
        ├── check_tools() → finds python3.11 + BaiduPCS-Go binary
        ├── login_baidu() → BaiduPCS-Go login -bduss=... -stoken=...
        └── for each course:
              ├── python3.11 -m coursera_helper.coursera_dl -ca $CAUTH ...
              └── BaiduPCS-Go u ./tmp/week_dir/ /coursera/Category/Course/
```

### Baidu Netdisk Result

```
/coursera/
  Computer Science /
    Databases & Search /
      Executing Full Text Queries with Elasticsearch /
        01_introduction-to-elasticsearch/
          ... (videos, slides, quizzes)
    Theory /
      Information Theory /
        ... (pending download)
```
