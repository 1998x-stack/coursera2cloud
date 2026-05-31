# BaiduPCS-Go 完全指南：历史、用法、配置与替代方案

> 百度网盘命令行客户端的深度分析——从原版 iikira 到加强版 qjfoidnh，涵盖安装、认证、命令大全、服务器部署与自动化集成。

---

## 目录

1. [什么是 BaiduPCS-Go？](#1-什么是-baidupcs-go)
2. [历史：从 iikira 到 qjfoidnh](#2-历史从-iikira-到-qjfoidnh)
3. [安装与运行](#3-安装与运行)
4. [认证配置](#4-认证配置)
5. [核心命令完全指南](#5-核心命令完全指南)
6. [配置优化策略](#6-配置优化策略)
7. [服务器与自动化场景](#7-服务器与自动化场景)
8. [替代方案对比](#8-替代方案对比)
9. [法律与风险](#9-法律与风险)
10. [总结与建议](#10-总结与建议)

---

## 1. 什么是 BaiduPCS-Go？

**BaiduPCS-Go** 是一个用 Go 语言编写的百度网盘命令行客户端，提供仿 Linux Shell 的交互式文件管理体验。它将百度网盘变成了一个可以通过终端操作的文件系统入口。

### 为什么需要它？

百度网盘官方客户端存在诸多限制：

| 痛点 | BaiduPCS-Go 的解决方案 |
|------|----------------------|
| 非 SVIP 下载限速严重（KB/s 级别） | 通过多线程并发最大化带宽利用率（SVIP 用户可跑满宽带） |
| 无 Linux 原生客户端 | 提供 Linux/macOS/Windows/OpenWrt/Android(Termux) 全平台二进制 |
| 无法在无 GUI 的服务器上使用 | 纯命令行操作，适合 SSH 远程管理 |
| 批量操作繁琐 | 支持通配符、批量上传/下载、脚本集成 |
| 无法自动化/定时任务 | 可通过 shell 脚本、cron、CI/CD 调度 |
| 分享链接转存困难 | 内置 `transfer` 命令一键转存分享链接 |
| 离线下载管理不便 | 支持添加/查询/取消磁力链接和远程下载任务 |

### 核心能力一览

```
┌─────────────────────────────────────────────────────────┐
│  BaiduPCS-Go 功能矩阵                                    │
├─────────────────────────────────────────────────────────┤
│  文件操作    │ ls, cd, pwd, mkdir, rm, cp, mv, tree      │
│  上传下载    │ upload, download, 断点续传（下载）, 秒传    │
│  分享管理    │ share set/list/cancel                     │
│  分享转存    │ transfer（核心特色功能）                    │
│  离线下载    │ offline add/query/cancel/delete            │
│  回收站      │ recycle list/restore/delete               │
│  多账号      │ login, loglist, su, logout                │
│  直链获取    │ locate（获取文件下载直链）                   │
│  搜索        │ search（支持递归搜索）                      │
│  配置管理    │ config / config set                       │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 历史：从 iikira 到 qjfoidnh

### 2.1 原版 iikira/BaiduPCS-Go

- **作者：** iikira
- **活跃期：** 2017–2020
- **最后版本：** v3.6.2
- **现状：** **仓库已被删除**（约 2020 年 5 月）

关于原版仓库被删除的原因，社区普遍认为与百度的法律压力有关。iikira 本人从未公开说明原因，但多个 fork 维护者和社区成员在 GitHub Issues 中暗示了"百度法务部门的茶"（Baidu legal department tea）。

事实上，不仅仅是 BaiduPCS-Go——同期多个百度网盘第三方工具（如 PanDownload、Erope 的 baidupcs-web）也相继被关闭或下架。

### 2.2 加强版 qjfoidnh/BaiduPCS-Go

- **仓库：** [github.com/qjfoidnh/BaiduPCS-Go](https://github.com/qjfoidnh/BaiduPCS-Go)
- **基于：** iikira v3.6.2
- **首次发布：** 2020 年 11 月
- **当前版本：** v4.0.1 (2026 年 3 月)
- **状态：** **活跃维护**（持续更新中）

qjfoidnh 在原版基础上添加了**分享链接转存功能**（`transfer` 命令），这也是"加强版"名称的由来。此后持续跟进百度网盘的接口变更，修复了大量兼容性问题。

### 2.3 版本里程碑

| 版本 | 日期 | 关键变化 |
|------|------|---------|
| v3.7.0 | 2020-12 | 替换失效仓库，支持短链接转存 |
| v3.9.6 | 2024-12 | 多项接口适配与稳定性修复 |
| v3.9.9 | 2025-08 | 上传速度优化 |
| **v4.0.0** | **2025-10** | 上传同名文件覆盖策略、代理配置、单文件最大 128GB |

---

## 3. 安装与运行

### 3.1 预编译二进制（推荐）

从 [Releases 页面](https://github.com/qjfoidnh/BaiduPCS-Go/releases) 下载对应平台的压缩包：

| 平台 | 文件 |
|------|------|
| Linux amd64 | `BaiduPCS-Go-v4.0.0-linux-amd64.zip` |
| Linux arm64 | `BaiduPCS-Go-v4.0.0-linux-arm64.zip` |
| macOS amd64 | `BaiduPCS-Go-v4.0.0-darwin-amd64.zip` |
| macOS arm64 | `BaiduPCS-Go-v4.0.0-darwin-arm64.zip` |
| Windows amd64 | `BaiduPCS-Go-v4.0.0-windows-amd64.zip` |

```bash
# Linux/macOS 安装示例
wget https://github.com/qjfoidnh/BaiduPCS-Go/releases/download/v4.0.0/BaiduPCS-Go-v4.0.0-linux-amd64.zip
unzip BaiduPCS-Go-v4.0.0-linux-amd64.zip
cd BaiduPCS-Go-v4.0.0-linux-amd64
chmod +x BaiduPCS-Go
./BaiduPCS-Go
```

### 3.2 包管理器安装

```bash
# Arch Linux（官方 Extra 仓库）
sudo pacman -S baidupcs-go

# macOS（Homebrew — 如可用）
brew install baidupcs-go
```

### 3.3 从源码编译

```bash
git clone https://github.com/qjfoidnh/BaiduPCS-Go.git
cd BaiduPCS-Go
go build
./BaiduPCS-Go version
```

要求 Go 1.18+。

### 3.3 两种运行模式

**交互模式（新手推荐）：**

直接双击或运行可执行文件，进入仿 Linux Shell 的 CLI 交互界面：

```
BaiduPCS-Go >
```

输入 `help` 查看所有命令，输入命令后回车执行。

**命令行模式（自动化推荐）：**

```bash
./BaiduPCS-Go <command> [arguments]

# 示例
./BaiduPCS-Go login -bduss=xxxxx
./BaiduPCS-Go ls /
./BaiduPCS-Go download /movies/video.mp4
```

> **注意：** 命令前缀 `BaiduPCS-Go` 仅在命令行模式下使用。在交互模式下直接输入命令即可（如 `ls` 而非 `BaiduPCS-Go ls`）。

---

## 4. 认证配置

**这是使用 BaiduPCS-Go 最关键的步骤。** 没有正确的认证凭据，所有后续操作都无法进行。

### 4.1 三种认证方式对比

| 方式 | 命令 | 可靠性 | 推荐场景 |
|------|------|--------|---------|
| BDUSS + STOKEN | `login -bduss=... -stoken=...` | ⭐⭐⭐⭐⭐ | 日常使用、服务器 |
| 完整 Cookies | `login -cookies="..." ` | ⭐⭐⭐⭐ | 需要使用转存功能 |
| 交互式账号密码 | `login`（然后输入） | ⭐⭐ | 临时测试（维护较少） |

**项目 README 提示：常规交互式登录方式长期不维护，推荐使用 BDUSS/STOKEN 或 Cookies。**

### 4.2 获取 BDUSS 和 STOKEN（详细步骤）

以 Chrome/Edge 浏览器为例：

1. **登录百度网盘：** 访问 `https://pan.baidu.com/`，用你的百度账号登录
2. **打开开发者工具：** 按 `F12`（macOS: `Cmd+Option+I`）
3. **切换到 Application（应用程序）标签页**
4. **找到 Cookies：** 左侧 Storage → Cookies → `https://pan.baidu.com`
5. **复制 BDUSS：** 在 Cookie 列表中找到 `BDUSS`，双击 Value 列，全选复制
6. **复制 STOKEN：** 同样找到 `STOKEN`，复制其值

**⚠️ 注意：**
- STOKEN **不是** `bdstoken`！后者是页面参数，不能用于登录
- STOKEN 中通常包含大写字母；如果全是小写，可能拿错了
- STOKEN **必须从百度网盘页面**的 Cookie 中获取，百度其他页面的同名字段无效

### 4.3 登录验证

```bash
# 方式一：BDUSS + STOKEN（推荐）
./BaiduPCS-Go login -bduss='你的BDUSS值' -stoken='你的STOKEN值'

# 方式二：完整 Cookies
./BaiduPCS-Go login -cookies="BDUSS=xxx; STOKEN=yyy; BAIDUID=zzz"

# 验证登录状态
./BaiduPCS-Go who        # 查看当前账号
./BaiduPCS-Go quota      # 查看网盘容量
./BaiduPCS-Go ls /       # 列出根目录
```

### 4.4 多账号管理

```bash
./BaiduPCS-Go login -bduss=账号1的BDUSS -stoken=账号1的STOKEN
./BaiduPCS-Go login -bduss=账号2的BDUSS -stoken=账号2的STOKEN

./BaiduPCS-Go loglist              # 列出所有已登录账号
./BaiduPCS-Go su <uid>             # 切换到指定账号
./BaiduPCS-Go logout <uid>         # 退出指定账号
```

### 4.5 安全提醒

BDUSS 和 STOKEN **等同于你的百度账号密码**。拿到它们的人可以访问你的网盘文件。务必：

- ❌ 不要截图分享
- ❌ 不要提交到 Git 仓库
- ❌ 不要在公共频道中发送
- ❌ 不要粘贴到在线 Cookie 格式化工具
- ✅ 通过环境变量传递：`export BAIDU_BDUSS=xxx && ./BaiduPCS-Go login -bduss="$BAIDU_BDUSS" ...`
- ✅ 使用后立即清除：`unset BAIDU_BDUSS BAIDU_STOKEN`
- ✅ BDUSS 有效期约 30 天，过期后需重新获取

---

## 5. 核心命令完全指南

### 5.1 文件浏览

```bash
# 列出当前目录
ls
ls /我的资源
ls -l                    # 详细信息（大小、时间）

# 树形显示
tree /我的资源
tree -d 3                # 限制深度为 3 层

# 切换工作目录
cd /我的资源/视频
cd ..                    # 返回上级
cd -                     # 返回上一个目录

# 查看当前路径
pwd

# 搜索文件
search 关键词
search -path /我的资源 -r 关键词    # 递归搜索
```

### 5.2 下载文件

```bash
# 基本下载
download /path/to/file.zip
d /path/to/file.zip                # 简写

# 多文件下载
d /video1.mp4 /video2.mp4 /video3.mp4

# 下载整个目录
d /movies/

# 指定保存路径（命令行模式）
./BaiduPCS-Go d /file.zip --saveto /local/path/

# 设置下载保存目录（持久配置）
config set -savedir /home/user/Downloads/Baidu
```

**下载特性：**
- 默认保存到程序所在目录的 `download/` 子目录
- 同名文件自动跳过
- **支持断点续传**（仅下载）
- 默认单线程保守策略

### 5.3 上传文件

```bash
# 基本上传（到当前工作目录）
upload /local/file.zip
u /local/file.zip

# 上传到指定网盘目录
upload /local/file1.zip /local/file2.zip /网盘目标目录/

# 跳过秒传检测
u --norapid /local/file.zip /网盘目录/

# 同名文件覆盖策略
u --policy overwrite /local/file.zip /网盘目录/    # 覆盖
u --policy skip /local/file.zip /网盘目录/          # 跳过（默认）
u --policy rsync /local/file.zip /网盘目录/         # 仅同大小文件跳过
```

**上传特性（v4.0.0）：**
- 默认分片上传
- **不再支持断点续传**（因百度接口变更）
- 单文件最大支持 128GB
- 默认检测秒传（可通过 `--norapid` 跳过）
- 不会覆盖同名目录

### 5.4 分享链接转存

这是加强版的**核心特色功能**：

```bash
# 转存分享链接中的文件到当前网盘目录
transfer "https://pan.baidu.com/s/xxxxx" 提取码

# 带下载参数
transfer --download "https://pan.baidu.com/s/xxxxx" 提取码

# 转存秒传链接
transfer --rapid "秒传链接字符串"
```

**注意：** 转存功能需要以 Cookies 方式登录（而非仅 BDUSS+STOKEN），因为需要额外的 Cookie 字段。

### 5.5 分享管理

```bash
# 创建分享
share set /path/to/file
share set -passwd 1234 /path/to/file        # 带提取码

# 列出已分享文件
share list

# 取消分享
share cancel <share_id>
```

### 5.6 离线下载

```bash
# 添加离线下载任务（支持磁力链接、HTTP 链接等）
offline add "magnet:?xt=urn:btih:xxxxx"

# 查看任务列表
offline list

# 查询特定任务
offline query <task_id>

# 取消任务
offline cancel <task_id>

# 删除任务记录
offline delete <task_id>
```

### 5.7 文件操作

```bash
mkdir /新目录                     # 创建目录
rm /path/to/file                 # 删除文件
cp /source /destination          # 复制
mv /oldname /newname             # 移动/重命名
meta /path/to/file               # 查看文件元信息
locate /path/to/file             # 获取下载直链
```

### 5.8 回收站

```bash
recycle list                      # 列出回收站内容
recycle restore /path             # 还原文件
recycle delete /path              # 删除单个文件
recycle delete --all              # 清空回收站
```

### 5.9 工具箱

```bash
tool                              # 显示可用工具
env                               # 显示程序环境变量
update                            # 检测程序更新
```

---

## 6. 配置优化策略

### 6.1 核心配置项

```bash
# 查看当前配置
config

# 查看所有可配置项
config -h
config set -h
```

| 配置项 | 含义 | 推荐值（普通用户） | 推荐值（SVIP） |
|--------|------|-------------------|---------------|
| `savedir` | 下载保存目录 | 自定义路径 | 自定义路径 |
| `max_parallel` | 总最大并发连接数 | **1** | 10-20 |
| `max_download_load` | 同时下载文件数 | **1** | 1-2 |
| `max_upload_parallel` | 单文件上传并发数 | 4 | 8 |
| `max_upload_load` | 同时上传文件数 | 2 | 4 |
| `max_download_rate` | 下载限速 | 0（不限） | 0（不限） |
| `max_upload_rate` | 上传限速 | 0（不限） | 0（不限） |
| `upload_policy` | 同名文件策略 | skip | skip/overwrite |
| `proxy` | HTTP 代理 | 按需设置 | 按需设置 |

**⚠️ 重要：** 普通用户（非 SVIP）**务必**将 `max_parallel` 和 `max_download_load` 都设为 1。调大线程数只会在短时间内提升速度，但极易触发百度的限速机制，导致账号在几小时甚至几天内接近 0 速。

**SVIP 用户**可以将 `max_parallel` 设为 10-20，实验表明可稳定满速下载。

### 6.2 配置示例

```bash
# 基础配置（普通用户）
config set -savedir ~/Downloads/Baidu
config set -max_parallel 1
config set -max_download_load 1
config set -max_upload_parallel 4
config set -max_upload_load 2
config set -upload_policy skip

# SVIP 极速配置
config set -max_parallel 15
config set -max_download_load 2
config set -max_upload_parallel 8

# 限速配置（避免占满带宽）
config set -max_download_rate 10MB/s
config set -max_upload_rate 5MB/s

# 代理配置（国外 VPS 用户回源加速）
config set -proxy 'http://127.0.0.1:7890'
config set -proxy_hostnames 'pan.baidu.com'
```

### 6.3 配置文件位置

配置文件默认存储在：
- Linux/macOS: `~/.config/BaiduPCS-Go/`
- Windows: `%APPDATA%\BaiduPCS-Go\`

可通过环境变量自定义：
```bash
export BAIDUPCS_GO_CONFIG_DIR="$HOME/.config/baidupcs-agent"
```

**谨慎修改** `appid`、`user_agent`、`pcs_ua`、`pan_ua` 等配置——错误的值会导致无法访问网盘。

---

## 7. 服务器与自动化场景

### 7.1 服务器部署模板

```bash
# 1. 下载并解压
wget https://github.com/qjfoidnh/BaiduPCS-Go/releases/download/v4.0.0/BaiduPCS-Go-v4.0.0-linux-amd64.zip
unzip BaiduPCS-Go-v4.0.0-linux-amd64.zip
cd BaiduPCS-Go-v4.0.0-linux-amd64
chmod +x BaiduPCS-Go

# 2. 设置独立的配置目录（避免与个人使用冲突）
export BAIDUPCS_GO_CONFIG_DIR="$HOME/.config/baidupcs-server"
mkdir -p "$BAIDUPCS_GO_CONFIG_DIR"

# 3. 登录
./BaiduPCS-Go login -bduss="$BAIDU_BDUSS" -stoken="$BAIDU_STOKEN"
unset BAIDU_BDUSS BAIDU_STOKEN   # 立即清除凭据环境变量

# 4. 基础配置
./BaiduPCS-Go config set -savedir /data/baidu-downloads
./BaiduPCS-Go config set -max_parallel 1
./BaiduPCS-Go config set -max_download_load 1

# 5. 验证
./BaiduPCS-Go who
./BaiduPCS-Go quota
```

### 7.2 后台下载

```bash
# nohup 后台运行
nohup ./BaiduPCS-Go d /大文件.zip --saveto /data/ &

# 查看进度
tail -f nohup.out
```

### 7.3 Cron 定时任务

```bash
# 每天凌晨 2 点同步下载目录
0 2 * * * /path/to/BaiduPCS-Go d /云端备份/* --saveto /local/backup/
```

### 7.4 为 AI Agent 配置（给 Claude/Codex/Agent 使用）

```bash
# 为 Agent 创建独立配置目录
export BAIDUPCS_GO_CONFIG_DIR="$HOME/.config/baidupcs-agent"
mkdir -p "$BAIDUPCS_GO_CONFIG_DIR"
./BaiduPCS-Go login -bduss='xxx' -stoken='yyy'
./BaiduPCS-Go config set -savedir "$HOME/agent-downloads/baidupcs" -max_parallel 1 -max_download_load 1
```

**给 Agent 的安全边界 prompt：**

```
使用 BaiduPCS-Go 操作百度网盘，遵守以下边界：
1. 只允许执行 who, quota, pwd, ls, tree, meta, search, download, upload, mkdir
2. 禁止执行 rm, share set, share cancel, logout（除非明确授权）
3. 下载只允许保存到 $HOME/agent-downloads/baidupcs
4. 上传只允许写入 /AgentDrop 或明确指定的目录
5. 所有写操作前先列计划，执行后用 ls/meta/quota 验证
6. 禁止输出任何 BDUSS、STOKEN、Cookie 值
```

### 7.5 常见服务器场景

**场景一：从服务器下载数据集到本地**

```bash
# 先上传到百度网盘（通过本地客户端或 BaiduPCS-Go）
# 然后在服务器上拉取
./BaiduPCS-Go login -bduss=xxx -stoken=yyy
./BaiduPCS-Go d /datasets/imagenet.tar.gz --saveto /data/
```

**场景二：服务器备份到百度网盘**

```bash
./BaiduPCS-Go u /data/backup/db_dump.sql /云端备份/
```

**场景三：国外 VPS 回国加速**

```bash
# 为 pan.baidu.com 配置回国代理
./BaiduPCS-Go config set -proxy 'http://127.0.0.1:7890'
./BaiduPCS-Go config set -proxy_hostnames 'pan.baidu.com'
```

---

## 8. 替代方案对比

### 8.1 工具矩阵

| 工具 | 类型 | 优势 | 劣势 | 推荐场景 |
|------|------|------|------|---------|
| **BaiduPCS-Go** | CLI 客户端 | 功能最全、命令式操作、脚本友好 | 需要获取 BDUSS，学习曲线存在 | 服务器部署、批量操作、自动化 |
| **AList + Baidu Driver** | WebDAV/Web UI | 图形界面、多网盘聚合、WebDAV 挂载 | 大文件上传不稳定、配置较复杂 | 多网盘统一管理、文件浏览分享 |
| **rclone (Baidu backend)** | CLI 同步工具 | 多云统一接口、增量同步 | 需要百度开发者 API Key，大文件上传问题 | 跨云同步备份 |
| **官方客户端** | 桌面 GUI | 官方支持、稳定 | Windows/macOS 限定、广告多、免费限速 | 普通用户日常使用 |
| **PanDownload** | GUI 客户端 | 曾经最流行的加速工具 | ❌ **已关闭**（2020 年 4 月，作者蔡某萌被扬州宝应警方以"非法侵入计算机信息系统"罪名逮捕。据称通过 SVIP 账号池为免费用户加速，个人获利约 30 万元） | 历史参考，不可用 |

### 8.2 AList vs BaiduPCS-Go

| 维度 | AList | BaiduPCS-Go |
|------|-------|-------------|
| 操作界面 | Web UI（浏览器） | 终端 CLI |
| 多网盘支持 | ✅（百度/阿里/夸克/OneDrive 等 20+） | ❌（仅百度网盘） |
| WebDAV | ✅ 原生支持 | ❌ |
| 大文件上传（>40GB） | ⚠️ 不稳定（有 31299 错误报告） | ✅ 稳定（测试可到 100GB+） |
| 批量脚本 | ⚠️ 通过 API | ✅ 原生命令行 |
| 资源占用 | 中（Web 服务） | 低（单一二进制） |
| 文件预览 | ✅ | ❌ |

**选择建议：**
- 需要 Web 界面 + 多网盘管理 → **AList**
- 需要稳定的大文件上传 + 脚本自动化 → **BaiduPCS-Go**
- 两者可以互补使用：AList 做浏览和 WebDAV 挂载，BaiduPCS-Go 做后台上传下载

### 8.3 rclone Baidu 后端

```bash
# rclone 配置百度网盘
rclone config
# → new remote → 输入名称 → 选择 "Baidu Netdisk" (14)
# → 输入 API Key/Secret（需要百度开发者账号）

# 同步操作
rclone sync baidu:/云端目录 /本地目录 --progress --transfers 8
```

**注意：** rclone 的百度后端**从未被合并到主分支**（详见 rclone Issue #2099），原因包括：(1) 百度无官方 API，(2) 免费用户单线程限速 ~50-100KB/s，(3) 百度持续封禁第三方客户端的 App ID，(4) 测试需要中国手机号注册百度开发者。目前 rclone 主分支没有可用的百度网盘后端。BaiduPCS-Go 和 AList 是仅有的成熟方案。

---

## 9. 法律与风险

### 9.1 法律状态

百度对第三方网盘客户端的态度是明确的**反对**：

- **2020 年 5 月：** 原版 iikira/BaiduPCS-Go 仓库被删除（普遍认为与百度法务压力有关）
- **2020 年 6 月：** Erope/baidupcs-web（Web 版百度网盘客户端）仓库也被删除
- **2020 年 4 月：** PanDownload 作者蔡某萌被扬州宝应警方以"非法侵入计算机信息系统"罪名逮捕，据称其通过破解百度 SVIP 限速机制，使用账号池为免费用户提供高速下载，个人获利约 30 万元
- **2026 年：** 中国启动被称为"史上最严"的云盘专项整治行动，重点打击海外版权内容的网盘传播

当前 qjfoidnh/BaiduPCS-Go 能持续运行，主要因为：
- 它是一个**命令行工具**（用户基数相对较小）
- 它不提供"破解限速"功能，速度提升依赖于用户自身的 SVIP 身份
- 代码中使用的 API 端点与百度官方 Linux/macOS 客户端相同

### 9.2 使用风险

| 风险 | 等级 | 说明 |
|------|------|------|
| 账号封禁 | 低 | 使用官方 API 端点，行为与官方客户端相似 |
| BDUSS 泄露 | 中 | 凭据等同于密码，需严格保管 |
| BDUSS 过期 | 中 | 约 30 天有效期，需定期更新 |
| 接口变更 | 中 | 百度随时可能修改 API，工具可能暂时失效 |
| 法律风险 | 低（个人使用） | 仅供个人文件管理，不涉及破解或分发 |

### 9.3 安全使用准则

1. **BDUSS 当作密码对待**——不截图、不发群、不提交 Git
2. **使用环境变量传递凭据**，用后立即 `unset`
3. **定期轮换凭据**——重新从浏览器提取最新的 BDUSS
4. **为不同用途使用独立配置目录**（`BAIDUPCS_GO_CONFIG_DIR`）
5. **不给 Agent 写删除/分享权限**
6. **国外 VPS 用户配置代理**——直接访问百度 API 可能不稳定

---

## 10. 总结与建议

### 10.1 最佳使用流程

```
新手 → 双击运行 → 交互模式 → 熟悉命令
       ↓
       获取 BDUSS + STOKEN → login
       ↓
       配置 savedir、并发等
       ↓
进阶 → 命令行模式 → 脚本化 → 服务器部署
       ↓
       配置独立 config_dir + Agent 安全边界
```

### 10.2 快速上手命令序列

```bash
# 1. 下载
wget https://github.com/qjfoidnh/BaiduPCS-Go/releases/download/v4.0.0/BaiduPCS-Go-v4.0.0-linux-amd64.zip
unzip BaiduPCS-Go-v4.0.0-linux-amd64.zip && cd BaiduPCS-Go-v4.0.0-linux-amd64

# 2. 登录
./BaiduPCS-Go login -bduss='你的BDUSS' -stoken='你的STOKEN'

# 3. 配置
./BaiduPCS-Go config set -savedir ~/Downloads/Baidu
./BaiduPCS-Go config set -max_parallel 1 -max_download_load 1

# 4. 开始使用
./BaiduPCS-Go ls /
./BaiduPCS-Go d /path/to/file
```

### 10.3 核心建议

| 场景 | 推荐方案 |
|------|---------|
| 服务器上下载百度网盘文件 | **BaiduPCS-Go**（最稳定） |
| 大量小文件批量操作 | **BaiduPCS-Go**（脚本化） |
| 大文件上传（>40GB） | **BaiduPCS-Go**（比 AList 更可靠） |
| 多网盘统一 Web 管理 | **AList**（20+ 网盘支持） |
| 跨云同步备份 | **rclone**（统一接口） |
| 普通桌面用户 | **官方客户端**（省心） |
| AI Agent 操作网盘 | **BaiduPCS-Go + 安全边界** |

### 10.4 关键技术要点

1. **BDUSS + STOKEN 是唯一的可靠登录方式**——交互式密码登录维护较少
2. **普通用户保持单线程**——多线程只会触发限速，适得其反
3. **SVIP 用户可放心调高并发**——10-20 线程可稳定跑满带宽
4. **上传不再支持断点续传**（v4.0.0）——下载不受影响
5. **配置文件隔离至关重要**——人用和 Agent 用必须分开

---

## 附录

### A. 命令速查表

| 命令 | 简写 | 功能 |
|------|------|------|
| `login` | — | 登录百度账号 |
| `who` | — | 查看当前账号 |
| `quota` | — | 查看网盘容量 |
| `ls` | — | 列出目录 |
| `tree` | — | 树形列出目录 |
| `cd` | — | 切换工作目录 |
| `pwd` | — | 显示当前路径 |
| `download` | `d` | 下载文件/目录 |
| `upload` | `u` | 上传文件/目录 |
| `mkdir` | — | 创建目录 |
| `rm` | — | 删除文件/目录 |
| `cp` | — | 复制文件/目录 |
| `mv` | — | 移动/重命名 |
| `search` | — | 搜索文件 |
| `meta` | — | 查看文件元信息 |
| `locate` | — | 获取下载直链 |
| `transfer` | — | 转存分享链接 |
| `share set` | — | 创建分享 |
| `share list` | — | 列出分享 |
| `share cancel` | — | 取消分享 |
| `offline add` | — | 添加离线下载 |
| `offline list` | — | 离线任务列表 |
| `recycle list` | — | 回收站列表 |
| `recycle restore` | — | 还原回收站文件 |
| `config` | — | 查看/设置配置 |
| `loglist` | — | 列出已登录账号 |
| `su` | — | 切换账号 |
| `logout` | — | 退出账号 |
| `env` | — | 显示环境变量 |
| `update` | — | 检测更新 |
| `help` | — | 查看帮助 |

### B. 配置文件字段参考

关键配置文件 `~/.config/BaiduPCS-Go/pcs_config.json` 结构（部分）：

```json
{
  "baidu_active_uid": 0,
  "baidu_user_list": [],
  "appid": 266719,
  "max_parallel": 1,
  "max_download_load": 1,
  "max_upload_parallel": 4,
  "max_upload_load": 2,
  "max_download_rate": 0,
  "max_upload_rate": 0,
  "savedir": "download/",
  "upload_policy": "skip",
  "proxy": "",
  "proxy_hostnames": "",
  "user_agent": "netdisk",
  "pcs_ua": "",
  "pan_ua": "",
  "fix_pcs_addr": false
}
```

### C. 参考链接

- **qjfoidnh/BaiduPCS-Go（加强版）：** https://github.com/qjfoidnh/BaiduPCS-Go
- **Releases 下载：** https://github.com/qjfoidnh/BaiduPCS-Go/releases
- **Wiki 文档：** https://github.com/qjfoidnh/BaiduPCS-Go/wiki
- **原版讨论（iikira 删库）：** https://github.com/felixonmars/BaiduPCS-Go/issues/1
- **AList（多网盘管理）：** https://github.com/AlistGo/alist
- **实战教程（魔都水滴）：** https://blog.margrop.net/post/baidupcs-go-cli-agent-guide/

---

*本文撰写于 2026 年 5 月。百度网盘接口可能变化，使用前请检查 GitHub 仓库的最新版本和 Issue 反馈。*
