# Coursera2Cloud — Gotchas & Lessons Learned

> 项目开发过程中遇到的所有坑和解决方案，按阶段分类沉淀。

---

## 目录

- [环境与安装](#环境与安装)
- [认证与凭证](#认证与凭证)
- [coursera-helper 下载](#coursera-helper-下载)
- [BaiduPCS-Go 上传](#baidupcs-go-上传)
- [路径与命名](#路径与命名)
- [并发与性能](#并发与性能)
- [校验与状态](#校验与状态)
- [代码 BUG 修复记录](#代码-bug-修复记录)

---

## 环境与安装

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| **G1** | `pip install` 在 macOS 上被拒绝 | PEP 668: Homebrew Python 3.14 标记为 externally-managed | `pip3 install --break-system-packages` |
| **G2** | Go build BaiduPCS-Go 失败 | go.mod 要求 ≥1.23，系统 Go 1.22；Go proxy 下载被墙 | 改用预编译二进制 |
| **G3** | BaiduPCS-Go 下载 404 | GitHub release 文件名是 `darwin-osx-arm64` 而非 `darwin-arm64` | 修复 setup_baidu.sh 的 platform 映射 |
| **G4** | `coursera-helper` 在 Python 3.14 崩溃 | `distutils` 在 Python 3.12+ 被移除 | 必须用 `python3.11 -m coursera_helper.coursera_dl` |
| **G5** | 环境变量在 OpenCode 子进程间不共享 | 每个 `bash` 调用创建独立子 shell | 用 `run.sh` 从 `~/.zshrc` 直接提取凭证 |

---

## 认证与凭证

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| **G6** | 环境变量名不匹配 | config.yaml 用 `${COURSERA_CAUTH}` 但 `.zshrc` 是 `export CAUTH` | 统一为 `$CAUTH` `$BDUSS` `$STOKEN` |
| **G7** | `eval "$(grep export ~/.zshrc)"` 失败 | CAUTH 值含 `.` `_` 等特殊字符，被 shell 解释 | 单行 `grep` + `sed` 提取后 `export`，CAUTH 用单引号 |
| **G8** | BDUSS/STOKEN 过期 (31045) | Token 约 30 天有效期 | 浏览器重新登录 pan.baidu.com → F12 → Cookies 提取 |
| **G9** | CAUTH 为空时 coursera-helper 静默失败 | argparse 验证走到 else 分支，提示 `-u` 或 `-n` 而非明确报错 | 启动前检查 `$CAUTH` 长度 ≥ 100 |
| **G10** | coursera-helper 即使有 `-ca` 也要求 `-u` 或 `-n` | commandline.py:519 的验证逻辑要求 cookie 方式必须非空才跳过 | 确保 `$CAUTH` 不为空（不是空字符串） |

---

## coursera-helper 下载

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| **G11** | 下载返回 0 sections | CAUTH 过期或无效 | 重新登录 coursera.org → F12 → Cookies → CAUTH |
| **G12** | 部分下载后中断，下次运行跳过 | `download_course()` 只检查目录是否存在，不检查完整性 | 添加 `_downloaded` 状态标记；`force_redownload` 配置项可强制重下 |
| **G13** | 大量课程连续下载超时 | Information Theory 等大课程下载时间 >10 分钟 | sync.py 中 `_run()` 默认 timeout 3600s，大课程需更久 |
| **G14** | coursera-helper `--list-courses` 需要 `-u` | listing 仍需要认证凭据 | 需同时传 `-ca` 和 `-u dummy@x.com` |

---

## BaiduPCS-Go 上传

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| **G15** | 上传返回成功但百度网盘无文件 | 路径中的 `&` 被 Baidu API 当作特殊字符 | 类别名用 `and` 替代 `&`，避免 `#` `?` `&` |
| **G16** | `ls`/`tree` 返回 31062 "file name is invalid" | BaiduPCS-Go 的 list 命令无法处理含 ` / ` 的路径（空格-斜杠-空格），但 `u` 命令可以 | verify_upload 检测 31062 时跳过校验而非报错 |
| **G17** | 上传预创建目录导致双重嵌套 | `ensure_remote_dir(week_target)` + `u week_dir week_target` → BaiduPCS-Go 在目标下再创建同名子目录 | 不要预创建周目录，直接上传到课程根目录 |
| **G18** | Baidu quota 偶尔返回 31045 | BDUSS session 过期 | 重新提取 BDUSS/STOKEN |

---

## 路径与命名

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| **G19** | 中文类别名在 Baidu `ls` 中显示异常 | BaiduPCS-Go 输出编码问题 | 使用英文类别路径 |
| **G20** | 类别路径中 ` / ` 导致 BaiduPCS-Go `ls` 失败 | 空格-斜杠-空格是 Baidu API 的边界情况 | 见 G16；新加课程尽量用无空格下划线 |
| **G21** | 课程 slug 与 Baidu 显示名不同 | JSONL 的 `slug` 用于 Coursera URL，`name` 用于 Baidu 目录 | 两者独立配置，slug 不能含中文 |

---

## 并发与性能

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| **G22** | 免费用户调高并发后速度归零 | 百度对免费账号有激进限速，多线程触发惩罚 | 免费用户 `max_parallel=1`；SVIP 可设 10-20 |
| **G23** | `config set` 失败静默忽略 | sync.py 中 `_run()` 未检查 returncode | 添加 returncode 检查 + warning 日志 |
| **G24** | 309 门课程全部 enabled=false | 生成课程列表时默认禁用 | 批量设置 `enabled: true`（注意 2TB+ 下载量） |

---

## 校验与状态

| # | 问题 | 根因 | 解决 |
|---|------|------|------|
| **G25** | status.json 显示 ⬜ 但文件实际已在百度网盘 | status 跟踪机制在上传完成后才添加 | status.json 是反映现实，非真相来源；可手动修复 |
| **G26** | 原课程从 JSONL 移除 | 重写 courses.jsonl 时未保留 | 加回并设 `enabled: true` |
| **G27** | verify_upload 远程计数偏少 | `ls` 输出解析未过滤列标题行 `文件(目录)` | 添加过滤条件 |
| **G28** | 上传进度计数器恒为 1 | `skipped + 1` 逻辑错误 | 改为独立 `uploaded` 计数器每轮 `+=1` |

---

## 代码 BUG 修复记录

| # | 行/函数 | BUG | 修复 |
|---|---------|-----|------|
| **B1** | `resolve_path()` | `config["baidu.binary_path"]` 无法访问嵌套 dict | 新增 `_nested_get()` 支持点号嵌套键 |
| **B2** | `upload_course()` | 预创建 week_target + 作为上传目标 → 双重嵌套 | 改为上传到课程根目录，不预创建周目录 |
| **B3** | `main()` | `logging.basicConfig()` 在 `logging.error()` 之后调用 | 移到 `main()` 开头 |
| **B4** | `download_course()` | 缺少 `--resume` 标志 | 添加 `--resume` |
| **B5** | `download_course()` | 部分下载中断后跳过 | 添加 `force_redownload` 配置 |
| **B6** | `check_tools()` | 硬编码 `"coursera-helper"` 二进制名 | 返回 resolved command list，传给 `download_course()` |
| **B7** | `load_config()` | 可选配置键缺失时崩溃 | try/except KeyError 守卫 |
| **B8** | `upload_course()` | 死变量 `level = _nested_get(...)` 且 remote_target 被覆盖 | 清理死代码 |
| **B9** | `verify_upload()` | 只统计文件不统计目录，口径不一致 | `rglob("*")` 统一统计所有条目 |
| **B10** | `verify_upload()` | `ls` 路径含特殊字符返回 31062 | 检测 31062 后跳过校验返回 True |
| **B11** | `_expand_env()` | 单行 wrapper 无抽象价值 | 移除，直接调用 `os.path.expandvars` |

---

## 快速自查清单

部署或排查时按顺序检查：

```
☐ Python 3.11 可用（非 3.12+）
☐ coursera-helper 已安装
☐ BaiduPCS-Go 二进制在 bin/ 下
☐ ~/.zshrc 有 export CAUTH=... BDUSS=... STOKEN=...
☐ config.yaml 路径无 & # ? 等特殊字符
☐ courses.jsonl 中 enabled: true
☐ status.json 已完成课程显示 ✅✅
☐ 免费用户 max_parallel ≤ 1
☐ 类别名不含 &，尽量不含空格
☐ sync.py --status 可正常显示
```
