# BJCP Styles Toolkit (framework only)

[English](#english) · [中文](#中文)

A **code-only toolkit** to build, maintain, and host a personal BJCP
(Beer Judge Certification Program) style-guidelines lookup app — web UI,
SQLite builder, translation pipeline, AI-skill example, and a
password-protected Cloudflare Pages deploy setup.

> ⚠️ **This repository contains NO guideline data.** The BJCP Style
> Guidelines text (and any translations of it) is copyrighted by BJCP, Inc.
> Everything here is framework code and documentation. You create the data
> yourself on your own machine by running the scripts, and you are
> responsible for following BJCP's usage terms (personal/educational use;
> do not sell or publicly repost reformatted guidelines without permission).

---

## English

### What's included

| Path | Purpose |
|---|---|
| `update.py` | One-command data refresh: clones the **official** BJCP styles repo into `data/`, rebuilds the SQLite DB, CSVs, offline web pages, and checks whether Chinese translations are stale |
| `build_db.py` | Parse official Markdown → SQLite (`bjcp.db`, English originals only) |
| `check_translations.py` / `merge_translations.py` | Hash-based translation coverage check & merge (translations stay out of this repo) |
| `query.py` | CLI: `python3 query.py 21A`, `"west coast"`, `--cider C1A` |
| `web/export_web.py` | Generate the **single-file offline web UI** (bilingual page template; generated `index*.html` embed the data and are NOT committed) |
| `skill/SKILL.md` | AI-assistant skill example for querying the local DB |
| `cloudflare/` | Cloudflare Pages deploy: Basic-Auth middleware, sync script, bilingual deploy guide |
| `tools/` | Password-protected preview server (for BJCP review links) |
| `docs/glossary.md` | Translation glossary/conventions (self-authored guidance) |

### Quick start (build your own local copy)
```bash
# 0) requirements: python3 (sqlite3 stdlib), git
# 1) fetch the OFFICIAL guideline source and build local artifacts
python3 update.py
# 2) try the CLI / generate the offline web UI
python3 query.py 21A
python3 web/export_web.py        # -> web/index.html etc. (personal use only)
```

`update.py` downloads the official Markdown from
github.com/bjcp/styles (the same source as styles.bjcp.org) **onto your
machine** — it does not upload anything.

### Hosting / deployment
See `cloudflare/DEPLOY-GUIDE.md` for a free, password-protected
Cloudflare Pages setup (custom domain, Basic Auth via Pages Functions).
Note: publishing pages that contain the full guideline text is public
redistribution — get BJCP permission first.

### Reporting translation issues
If you spot a translation mistake (or any content mismatch), please open an
issue using the **Translation correction / 翻译纠错** template. Include the
style code, the current text, a suggested correction, and the official English
source when possible. Please don't include personal or sensitive information.

### License
Code in this repository: **MIT** (see LICENSE). The BJCP Style Guidelines
are © BJCP, Inc. and are **not** distributed here.

---

## 中文

### 包含什么

| 文件 | 用途 |
|---|---|
| `update.py` | 一键更新：从**官方** BJCP 仓库克隆到本地 `data/`，重建 SQLite/CSV/离线网页，并检查中文译文是否过期 |
| `build_db.py` | 官方 Markdown → SQLite（仅英文原文） |
| `check_translations.py` / `merge_translations.py` | 基于哈希的译文覆盖检查与合并（译文不放进本仓库） |
| `query.py` | 命令行查询：`python3 query.py 21A` 等 |
| `web/export_web.py` | 生成单文件离线网页的模板（生成的 `index*.html` 含数据，不提交） |
| `skill/SKILL.md` | AI 助手 skill 示例（查本地库） |
| `cloudflare/` | Cloudflare Pages 部署：Basic Auth 中间件、同步脚本、双语部署指南 |
| `tools/` | 带密码的评审预览服务器（用于给 BJCP 发评审链接） |
| `docs/glossary.md` | 翻译术语表与约定（自撰） |

### 快速开始（在你自己电脑上生成数据）
```bash
# 0) 需要 python3、git
# 1) 拉取官方源并在本地构建
python3 update.py
# 2) 试用 CLI / 生成离线网页
python3 query.py 21A
python3 web/export_web.py        # 生成 web/index.html 等（仅供个人使用）
```

`update.py` 只把官方 Markdown（github.com/bjcp/styles，与 styles.bjcp.org
同源）下载到你本地——不会上传任何内容。

### 部署 / 托管
见 `cloudflare/DEPLOY-GUIDE.md`：免费、带密码的 Cloudflare Pages 方案。
注意：把含指南全文的页面公开上线属于"公开重排"，需先取得 BJCP 许可。

### 反馈翻译问题
如果发现译文有误（或任何内容不一致），请用 **Translation correction /
翻译纠错** 模板提交 issue，附上风格代码、当前文字、建议修改，并尽量给出官方
英文原文作为依据。请勿填写个人或敏感信息。

### 许可
本仓库代码：**MIT**（见 LICENSE）。BJCP 风格指南 © BJCP, Inc.，**不随本仓库分发**。
