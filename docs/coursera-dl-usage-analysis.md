# coursera-dl 完全指南：历史、用法、替代方案与现状分析

> 本文详细分析 coursera-dl 的安装配置、核心用法、常见问题、生态替代方案，以及 2026 年的现状与推荐工具。

---

## 目录

1. [什么是 coursera-dl？](#1-什么是-coursera-dl)
2. [历史与现状](#2-历史与现状)
3. [安装方法](#3-安装方法)
4. [核心使用指南](#4-核心使用指南)
5. [认证机制详解](#5-认证机制详解)
6. [高级功能](#6-高级功能)
7. [常见问题与排错](#7-常见问题与排错)
8. [替代方案与生态](#8-替代方案与生态)
9. [法律与伦理考量](#9-法律与伦理考量)
10. [2026 年推荐方案](#10-2026-年推荐方案)

---

## 1. 什么是 coursera-dl？

**coursera-dl** 是一个用 Python 编写的命令行工具，用于批量下载 Coursera 课程的学习资源（视频、幻灯片、PDF、字幕、笔记本等）。它于 2012 年首次发布，托管在 GitHub 仓库 [coursera-dl/coursera-dl](https://github.com/coursera-dl/coursera-dl)，拥有超过 10,000 颗星标。

### 核心价值

相比直接使用 `wget` 或 `youtube-dl` 等通用下载工具，coursera-dl 解决了几个关键痛点：

| 问题 | coursera-dl 的解决方案 |
|------|----------------------|
| 视频文件名混乱，无法反映课程顺序 | 从课程大纲页面提取结构化命名（周次-讲座序号-标题） |
| 下载重复或无关视频 | 精确解析课程页面，只下载发布的资源 |
| 无法批量处理多门课程 | 支持空格分隔同时下载多门课程 |
| 不保存课程组织结构 | 自动创建 `课程名/周次/` 目录结构 |
| 无法下载字幕、测验、笔记本 | 支持 `--subtitle-language`、`--download-quizzes`、`--download-notebooks` |

### 核心功能一览

- 支持新老平台的所有课程类型（时间制 + 按需制）
- 正则表达式过滤：按章节名（`-sf`）或讲座名（`-lf`）选择性下载
- 文件格式过滤（`-f "ppt"` 只下载 PPT）
- 多种认证方式：命令行密码、`.netrc` 文件、CAUTH Cookie、配置文件
- 外部下载器支持（aria2c、wget、curl）
- 断点续传（`--resume`）
- 视频分辨率选择（360p / 540p / 720p）
- Docker 部署支持

---

## 2. 历史与现状

### 版本时间线

| 版本 | 日期 | 主要变化 |
|------|------|---------|
| 0.9.0 | 2017-05 | 初始稳定版 |
| 0.10.0 | 2018-02 | 支持 Coursera Notebooks |
| 0.11.0 | 2018-06 | 切换到新 API 端点 |
| 0.11.3 | 2018-06 | 支持 Specialization 自动展开 |
| **0.11.5** | **2019-12-16** | **最后一个正式版本，增加 `--cauth` 参数** |

### 当前状态：已停止维护

**原版 coursera-dl (v0.11.5) 自 2019 年 12 月起已不再更新。** 这意味着自 2020 年以来 Coursera 网站的任何变更（API 升级、认证机制调整、页面结构改变）都可能导致原版工具无法正常工作。

常见症状：
- `Found 0 sections and 0 lectures on this page` — 最常见的报错，通常意味着 Coursera 的页面结构或 API 已变更
- 认证失败
- SSL/TLS 握手错误

### 为什么要了解它？

尽管原版已死，但其架构设计和命令行接口深刻影响了后续所有 fork 和替代工具。**理解 coursera-dl，就理解了整个 Coursera 下载工具生态的 DNA。**

---

## 3. 安装方法

### 3.1 原版安装（仅作参考）

```bash
# 推荐方式：通过 pip 安装（Python 3.6-3.9）
pip install coursera-dl

# 从源码安装（用于开发或调试）
git clone https://github.com/coursera-dl/coursera-dl
cd coursera-dl
pip install -r requirements.txt
```

**注意：** 原版不支持 Python 3.10+，且依赖库（requests, beautifulsoup4 等）版本可能过旧。

### 3.2 虚拟环境安装（推荐模式）

```bash
# 创建独立虚拟环境，避免污染系统 Python
mkdir ~/coursera
cd ~/coursera
python3 -m venv venv
source venv/bin/activate

# 安装 coursera-dl（或 fork 版本）
pip install coursera-dl
```

### 3.3 Docker 部署

原版提供了 Docker 镜像，适合快速使用：

```bash
# 基本用法
docker run --rm -it -v "$(pwd):/courses" \
    courseradl/courseradl -u <USER> -p <PASSWORD>

# 使用 .netrc 文件
docker run --rm -it \
    -v "$(pwd):/courses" -v "$HOME/.netrc:/netrc" \
    courseradl/courseradl -n /netrc
```

工作目录为 `/courses`，所有下载内容默认存放于此。

### 3.4 依赖项

核心依赖：
- `requests >= 2.4` — HTTP 请求
- `six >= 1.5` — Python 2/3 兼容
- `beautifulsoup4 >= 4.1` — HTML 解析
- `urllib3` — URL 处理

可选依赖（用于特定功能）：
- `ffmpeg` — 视频处理与合并
- `aria2c` / `wget` / `curl` — 外部下载加速器

---

## 4. 核心使用指南

### 4.1 查找课程标识符 (course-slug)

课程标识符来自 Coursera URL 中的 slug。例如：

```
https://www.coursera.org/learn/machine-learning
                                   ^^^^^^^^^^^^^^^^
                                   这就是 course-slug
```

### 4.2 基本命令

```bash
# 最简单的用法（会提示输入密码）
coursera-dl -u your_email@example.com machine-learning

# 指定密码（不推荐，密码会留在 shell 历史中）
coursera-dl -u your_email@example.com -p 'your_password' machine-learning

# 下载多门课程
coursera-dl -u your_email@example.com -p 'password' course1 course2 course3
```

### 4.3 过滤与选择

```bash
# 按章节名过滤（正则表达式）
coursera-dl -u user -p pass -sf "Week_Four" crypto-course

# 按讲座名过滤
coursera-dl -u user -p pass -lf "3.1_" ml-course

# 只下载特定格式的资源
coursera-dl -u user -p pass -f "ppt" course-name     # 只下载 PPT
coursera-dl -u user -p pass -f "mp4" course-name     # 只下载视频
coursera-dl -u user -p pass -f "pdf" course-name     # 只下载 PDF
```

### 4.4 视频分辨率

```bash
# 默认 540p，可选 360p / 540p / 720p
coursera-dl -u user -p pass --video-resolution 720p course-slug
```

### 4.5 字幕下载

```bash
# 下载英文字幕（不下载视频本身）
coursera-dl -u user -p pass \
    --ignore-formats mp4 \
    --subtitle-language en \
    course-slug

# 同时下载中英文字幕
coursera-dl -u user -p pass \
    --subtitle-language en,zh-CN \
    course-slug
```

### 4.6 下载路径与断点续传

```bash
# 指定下载目录
coursera-dl -u user -p pass \
    --path=/home/user/Coursera/CS \
    course-slug

# 断点续传
coursera-dl -u user -p pass --resume course-slug
```

### 4.7 测验与笔记本

```bash
# 同时下载测验
coursera-dl -u user -p pass --download-quizzes course-slug

# 下载 Jupyter Notebooks
coursera-dl -u user -p pass --download-notebooks course-slug
```

### 4.8 使用外部下载器（加速）

```bash
# 使用 aria2c 加速下载（推荐）
coursera-dl -u user -p pass --aria course-slug

# 使用 wget
coursera-dl -u user -p pass --wget course-slug
```

### 4.9 批量维护多门课程

```bash
# 初始化课程目录
mkdir -p CURRENT/{course1,course2,course3}

# 一键更新所有课程
coursera-dl -n --path CURRENT `\ls CURRENT`
```

---

## 5. 认证机制详解

coursera-dl 支持多种认证方式，按推荐度排序：

### 5.1 `.netrc` 文件（推荐）

在用户主目录创建 `~/.netrc` 文件：

```
machine coursera-dl login your_email@example.com password your_password
```

然后使用 `-n` 选项无需输入凭据：

```bash
coursera-dl -n -- course-slug
```

**优点：** 密码不暴露在命令行历史中，复用方便。
**注意：** `.netrc` 文件权限应设为 `600`（`chmod 600 ~/.netrc`）。

### 5.2 `coursera-dl.conf` 配置文件

在运行目录创建 `coursera-dl.conf`：

```
--username your_email@example.com
--password your_password
--subtitle-language en,zh-CN
--download-quizzes
--video-resolution 720p
```

之后直接运行：

```bash
coursera-dl course-slug
```

### 5.3 CAUTH Cookie（现代方式）

这是最可靠的认证方式，尤其在原版工具失效但 forks 仍然可用的情况下：

1. 在 Chrome 中登录 Coursera
2. 打开开发者工具（F12）→ Application → Cookies
3. 找到 `CAUTH` 这个 cookie，复制其值（很长的字符串）
4. 使用：

```bash
coursera-dl -ca 'your-cauth-value-here' course-slug
```

**这是现代 forks（cs-dlp、coursera-helper）推荐的主要认证方式**，因为它绕过了 Coursera 日益复杂的登录验证（如 reCAPTCHA）。

---

## 6. 高级功能

### 6.1 Specialization（专项课程）下载

```bash
# 自动展开专项课程中的所有子课程
coursera-dl -u user -p pass --specialization specialization-slug
```

### 6.2 预览模式

某些未报名课程允许预览部分内容：

```bash
coursera-dl -u user -p pass --preview course-slug
```

### 6.3 本地页面处理

如果你有课程页面的 HTML 文件（比如朋友保存的），可以离线解析：

```bash
coursera-dl --process_local_page /path/to/course_page.html
```

### 6.4 MathJax CDN 自定义

在中国大陆等地区，默认的 MathJax CDN 可能不可用：

```bash
coursera-dl --mathjax-cdn https://cdn.bootcss.com/mathjax/2.7.1/MathJax.js course-slug
```

---

## 7. 常见问题与排错

### 7.1 `Found 0 sections and 0 lectures on this page`

**原因：** Coursera API 或页面结构已变更（最常见的问题）。

**排查步骤：**
1. 确认你已报名该课程
2. 尝试 `--preview` 选项
3. 对于已关闭报名的旧课程，获取课程页面 HTML 后用 `--process_local_page`
4. **升级到活跃维护的 fork**（见第 8 节）

### 7.2 认证失败

**对于原版 coursera-dl：**
- 确保密码中的特殊字符用单引号包裹
- 尝试 CAUTH Cookie 方式（`-ca` 参数）

**对于现代 forks：**
- 优先使用 `--cauth-auto chrome` 自动提取浏览器 cookie
- 手动复制 CAUTH cookie 值

### 7.3 SSL/TLS 错误

```
SSLError: [Errno 1] _ssl.c:504: error:14094410:SSL routines:SSL3_READ_BYTES:sslv3 alert handshake failure
```

**解决：**
- 升级到 Python 3.9+（内置 TLS 1.2/1.3 支持）
- 安装 `ndg-httpsclient` 包（仅限旧版 Python 2）

### 7.4 下载超时

**解决：**
- 使用外部下载器并配置超时：`--aria` 或 `--wget`
- 使用 `--resume` 断点续传
- 中国大陆用户考虑使用代理

### 7.5 Windows 权限问题

```bash
# 使用 --user 安装而非全局安装
pip install --user coursera-dl
```

---

## 8. 替代方案与生态

### 8.1 活跃维护的命令行工具

#### cs-dlp (raffaem/cs-dlp) — ⭐ 推荐

- **仓库：** [github.com/raffaem/cs-dlp](https://github.com/raffaem/cs-dlp)
- **状态：** 活跃维护 (2025-03 最后更新)
- **特点：**
  - 直接从 coursera-dl 继承架构，命令行接口几乎完全兼容
  - 支持现代 Python 3.9+
  - 新增 `--cauth-auto chrome` 自动从浏览器提取 cookie
  - 修复了大量 Coursera 新 API 兼容问题
- **安装：**
  ```bash
  git clone https://github.com/raffaem/cs-dlp
  cd cs-dlp
  python -m pip install --user .
  ```
- **用法示例：**
  ```bash
  cs-dlp --cauth-auto chrome machine-learning
  cs-dlp --cauth-auto chrome --video-resolution 720p course-slug
  ```

#### coursera-helper (csyezheng/coursera-helper)

- **仓库：** [github.com/csyezheng/coursera-helper](https://github.com/csyezheng/coursera-helper)
- **状态：** 活跃维护 (2026-01 最后更新，124 stars)
- **特点：**
  - 友好的命令行提示
  - 从 coursera-dl fork 而来，API 有调整
  - `coursera-helper` 是新的命令名
  - 支持 Python 3.8-3.11
  - Docker 部署支持
- **安装：**
  ```bash
  pip install coursera-helper
  ```
- **用法示例：**
  ```bash
  coursera-helper -u your_email course-slug
  coursera-helper --cauth <CAUTH> --download-quizzes course-slug
  coursera-helper --cauth <CAUTH> --download-notebooks course-slug
  ```

### 8.2 浏览器扩展

#### Coursera Course Downloader (Chrome 扩展)

- **仓库：** [github.com/BhashkarGupta/Coursera-Course-Downloader](https://github.com/BhashkarGupta/Coursera-Course-Downloader)
- **状态：** 2026 年活跃更新
- **特点：**
  - 纯浏览器端运行，无需 Python 环境
  - 并行下载（1-5 个视频同时下载）
  - 自动命名（模块名-视频名.mp4）
  - 支持暂停/停止/重新扫描
  - 可下载视频 + PDF 阅读材料
- **使用步骤：**
  1. 在 Coursera 课程页面展开所有模块
  2. 点击扩展的 "Scan Course"
  3. 点击 "Start Download"
- **限制：** 依赖 DOM 解析，Coursera 改版可能导致失效；部分交互式阅读材料可能无法下载

### 8.3 通用工具（针对 Coursera 视频）

虽然 `yt-dlp` 和 `youtube-dl` 是最强大的视频下载器，但用于 Coursera 时有显著限制：

| 需求 | 专用工具 | 通用工具 (yt-dlp/wget) |
|------|---------|----------------------|
| 自动命名（周-课-标题） | ✅ | ❌（需手动重命名） |
| 目录结构（按周组织） | ✅ | ❌ |
| 下载字幕、笔记、PDF | ✅ | ⚠️（部分支持） |
| 下载测验 | ✅ | ❌ |
| 批量多课程 | ✅ | ❌ |
| 下载速度 | ⚠️ | ✅（yt-dlp 更快） |

**混合策略：** 如果专用工具解析失败但你能获取视频 URL 列表，可以用 `yt-dlp` 作为后备下载器。

### 8.4 社区修复补丁

如果坚持使用原版 coursera-dl，需要注意社区发现的一些修复方案：

- **API v2 适配：** 有用户 fork 了原版并提交了针对新 API 的补丁（如 absurd-thought/coursera-dl）
- **安装修复版：**
  ```bash
  pip install -e git+https://github.com/absurd-thought/coursera-dl#egg=coursera-dl
  ```

### 8.5 工具对比矩阵

| 特性 | coursera-dl<br>(原版) | cs-dlp | coursera-helper | Chrome 扩展 |
|------|---------------------|--------|-----------------|-------------|
| 维护状态 | ❌ 已停止 (2019) | ✅ 活跃 (2025) | ✅ 活跃 (2026) | ✅ 活跃 (2026) |
| Python 环境 | ✅ | ✅ | ✅ | ❌ 不需要 |
| 命令行接口 | ✅ | ✅ | ✅ | ❌ |
| 浏览器界面 | ❌ | ❌ | ❌ | ✅ |
| 自动命名 | ✅ | ✅ | ✅ | ✅ |
| 并行下载 | ❌ | ✅ | ✅ | ✅ |
| 断点续传 | ✅ | ✅ | ✅ | ❌ |
| CAUTH 自动提取 | ❌ | ✅ (`--cauth-auto`) | ❌ | ✅ (内置) |
| 下载测验 | ✅ | ✅ | ✅ | ❌ |
| 下载 Notebooks | ✅ | ✅ | ✅ | ❌ |
| Docker 支持 | ✅ | ⚠️ | ✅ | ❌ |
| 跨平台 | ✅ | ✅ | ✅ | Chrome 系浏览器 |
| 学习曲线 | 中 | 中 | 低 | 极低 |

---

## 9. 法律与伦理考量

### 9.1 Coursera 服务条款

根据 Coursera 的 [Terms of Use](https://www.coursera.org/about/terms)，相关条款包括：

> "Coursera grants you a personal, non-exclusive, non-transferable license to access and use the Sites. You may download material from the Sites only for your own personal, non-commercial use. You may not otherwise copy, reproduce, retransmit, distribute, publish, commercially exploit or otherwise transfer any material, nor may you modify or create derivatives works of the material."

**关键原则：**
1. ✅ **个人学习用途** — 你在合法注册课程后，下载资料用于个人离线学习
2. ✅ **非商业用途** — 不利用下载材料盈利
3. ❌ **二次分发** — 不得重新分发、上传到公开平台
4. ❌ **商业利用** — 不得用于商业目的
5. ❌ **制作衍生作品** — 不得修改或创建衍生作品

### 9.2 最佳实践

- **仅供已注册课程使用：** 不要下载未报名的课程（即使工具允许）
- **个人使用，禁止分享：** 尊重内容创作者的版权
- **及时删除过期材料：** 课程结束后如不再需要，删除本地副本
- **不绕过付费墙：** 需要付费的课程先付费再下载
- **尊重 Honor Code：** 遵守每门课程特定的 Honor Code

### 9.3 工具开发者的免责声明

coursera-dl 的 README 明确声明：

> "coursera-dl is meant to be used only for your material that Coursera gives you access to download. We do not encourage any use that violates their Terms Of Use."

所有合法的 fork 和替代工具都遵循相同的伦理准则。

---

## 10. 2026 年推荐方案

### 场景一：命令行高级用户

**推荐：cs-dlp (raffaem/cs-dlp)**

```bash
# 一键安装
git clone https://github.com/raffaem/cs-dlp
cd cs-dlp && python -m pip install --user .

# 单门课程下载
cs-dlp --cauth-auto chrome machine-learning

# 批量下载（720p + 测验 + 字幕）
cs-dlp --cauth-auto chrome \
    --video-resolution 720p \
    --download-quizzes \
    --subtitle-language en,zh-CN \
    course1 course2 course3
```

**为什么选 cs-dlp？**
- 最接近原版 coursera-dl 的使用体验
- `--cauth-auto` 自动提取浏览器 cookie，无需手动复制
- 活跃社区维护

### 场景二：不想碰命令行的用户

**推荐：Coursera Course Downloader（Chrome 扩展）**

1. 从 [GitHub](https://github.com/BhashkarGupta/Coursera-Course-Downloader) 下载
2. Chrome → 扩展程序 → 开发者模式 → 加载已解压的扩展程序
3. 打开 Coursera 课程页面 → 展开所有模块 → 点击扫描 → 开始下载

**为什么选浏览器扩展？**
- 零配置，无需 Python
- 可视化操作
- 新用户 5 分钟上手

### 场景三：需要最稳定体验

**推荐：coursera-helper (csyezheng/coursera-helper)**

```bash
pip install coursera-helper
coursera-helper -u your_email course-slug
```

**为什么选 coursera-helper？**
- 通过 PyPI 直接安装，最简单
- 124 stars，社区验证
- 持续更新到 2026 年

### 总结建议

```
┌──────────────────────────────────────────────────┐
│                                                  │
│   会命令行 ──→ cs-dlp (最强大)                     │
│                                                  │
│   会命令行、想简单 ──→ coursera-helper (最易装)      │
│                                                  │
│   不会命令行 ──→ Chrome 扩展 (最省心)               │
│                                                  │
│   不要用原版 coursera-dl ── 它已于 2019 年死亡       │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## 附录

### A. 源代码架构速览

coursera-dl 的代码结构（约 17 个模块）体现了清晰的关注点分离：

```
coursera/
├── __init__.py          # 版本定义 (v0.11.5)
├── api.py               # Coursera API 端点交互
├── commandline.py       # CLI 参数解析与入口
├── cookies.py           # Cookie 处理
├── coursera_dl.py       # 核心下载逻辑
├── credentials.py       # 认证凭据管理
├── define.py            # 常量与类型定义
├── downloaders.py       # 下载器抽象（内置 + 外部）
├── extractors.py        # 课程页面内容提取
├── filtering.py         # 章节/讲座/格式过滤
├── formatting.py        # 文件名与路径格式化
├── network.py           # 网络请求封装
├── parallel.py          # 并行下载调度
├── playlist.py          # 播放列表生成
├── test/                # 测试用例
├── utils.py             # 通用工具函数
└── workflow.py          # 工作流编排
```

**架构洞察：** 这种模块化设计使得 forks 可以轻松替换个别模块（如 `api.py` 适配新 API，`network.py` 修复 SSL 问题）而不需要重写整个工具。这也是为什么 fork 生态能持续繁荣的根本原因。

### B. 关键命令速查表

| 需求 | 命令 |
|------|------|
| 基本下载 | `coursera-dl -u email -p pass course-slug` |
| 免密下载 | `coursera-dl -n -- course-slug` |
| Cookie 认证 | `coursera-dl -ca 'CAUTH_VALUE' course-slug` |
| 720p 高清 | `--video-resolution 720p` |
| 只下载字幕 | `--ignore-formats mp4 --subtitle-language en` |
| 只下载 PPT | `-f "ppt"` |
| 过滤章节 | `-sf "Week_Three"` |
| 过滤讲座 | `-lf "3.1_"` |
| 断点续传 | `--resume` |
| 指定路径 | `--path=/download/folder` |
| aria2 加速 | `--aria` |
| 下载测验 | `--download-quizzes` |
| 下载笔记本 | `--download-notebooks` |
| 查看帮助 | `--help` |

### C. 参考链接

- **原版 coursera-dl：** https://github.com/coursera-dl/coursera-dl
- **cs-dlp (推荐)：** https://github.com/raffaem/cs-dlp
- **coursera-helper：** https://github.com/csyezheng/coursera-helper
- **Chrome 扩展：** https://github.com/BhashkarGupta/Coursera-Course-Downloader
- **PyPI 页面：** https://pypi.org/project/coursera-dl/
- **Docker 镜像：** https://hub.docker.com/r/courseradl/courseradl

---

*本文撰写于 2026 年 5 月。工具生态快速变化，使用前请检查各仓库的最新状态。*
