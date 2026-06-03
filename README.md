# Coursera Sync

**Download Coursera courses → Organize by category → Upload to Baidu Netdisk — fully automated.**

[![Python](https://img.shields.io/badge/python-3.9–3.11-blue)](https://www.python.org/)
[![Tested](https://img.shields.io/badge/tested-macOS%20ARM64-brightgreen)]()
[![BaiduPCS-Go](https://img.shields.io/badge/BaiduPCS--Go-v4.0.1-orange)](https://github.com/qjfoidnh/BaiduPCS-Go)

---

## Quick Start

```bash
# 1. Install
cd coursera-sync
pip3 install --break-system-packages -r requirements.txt coursera-helper
bash setup_baidu.sh

# 2. Add credentials to ~/.zshrc (one-time):
#    export CAUTH="..."    # from coursera.org cookies
#    export BDUSS="..."    # from pan.baidu.com cookies
#    export STOKEN="..."   # from pan.baidu.com cookies

# 3. Configure courses in course-data/courses.jsonl (JSON Lines)

# 4. Run
bash run.sh
```

📖 **Full setup guide with credential extraction and troubleshooting**: [USERGUIDE.md](USERGUIDE.md)

---

## What It Does

```
run.sh → sync.py → coursera-helper → BaiduPCS-Go → cleanup
```

| Step | Tool | Action |
|------|------|--------|
| Download | coursera-helper v0.12.3 (Python 3.11) | Fetch videos, slides, quizzes, notebooks, subtitles to `./tmp/` |
| Upload | BaiduPCS-Go v4.0.1 | Week-by-week upload to `/coursera/{category}/{course}/` |
| Cleanup | sync.py | Remove local tmp after verified upload |

**Verified working** (May 2026, macOS ARM64):
- ✅ Elasticsearch course: download + upload → 4TB Baidu Netdisk
- ✅ Information Theory course: download in progress

**Baidu Netdisk result:**

```
/coursera/
  Computer Science /
    Databases and Search /
      Executing Full Text Queries with Elasticsearch /
        01_introduction-to-elasticsearch/
          ... (videos, slides, quizzes)
    Theory /
      Information Theory /
        ... (in progress)
```

---

## Configuration

Course catalog lives in `course-data/courses.jsonl` (JSON Lines):

```json
{"slug": "machine-learning", "name": "Machine Learning", "category": "Computer Science / AI and Machine Learning", "enabled": true}
```

`config.yaml` contains global settings:

| Setting | Default | Options |
|---------|---------|---------|
| `download.resolution` | `720p` | 360p / 540p / 720p |
| `download.subtitle_languages` | `"en"` | `"en,zh-CN"` or `""` to skip |
| `baidu.upload_policy` | `rsync` | skip / overwrite / rsync |
| `behavior.max_retries` | `3` | Retry count on failure |
| `behavior.force_redownload` | `false` | Set `true` for interrupted downloads |

> ⚠️ Category and course names containing `&`, `#`, `?` break BaiduPCS-Go paths. Use `and` instead of `&` (auto-sanitized at upload time, with a warning at load).

---

## Requirements

| Component | Version | Install |
|-----------|---------|---------|
| Python | 3.9–3.11 | (coursera-helper needs `distutils`, removed in 3.12+) |
| coursera-helper | 0.12.3 | `pip3 install coursera-helper` |
| BaiduPCS-Go | ≥4.0.0 | `bash setup_baidu.sh` |
| pyyaml | ≥6.0 | `pip3 install pyyaml` |

---

## Project Structure

```
coursera-sync/
├── sync.py             Orchestrator (77 lines)
├── constants.py        Root path constants
├── config.py           YAML config loading + path resolution
├── courses.py          Course catalog, status/state persistence
├── baidu.py            BaiduPCS-Go login, upload, verify
├── downloader.py       coursera-helper download + tool detection
├── pipeline.py         Upload + process orchestration
├── utils.py            Subprocess runner + Baidu path sanitization
├── run.sh              Launcher (reads ~/.zshrc for credentials)
├── nohup_sync.sh       Background sync with PID lock + log
├── setup_baidu.sh      BaiduPCS-Go installer
├── requirements.txt    pyyaml, requests
├── README.md           This file
├── USERGUIDE.md        Full guide + gotchas
├── config.yaml         Settings (gitignored)
├── course-data/        Course catalog + state + syllabus JSONs
├── bin/                BaiduPCS-Go binary
├── logs/               Log output + upload_state.json
└── tmp/                Temp downloads
```

## License

MIT
