#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BJCP 本地数据 · 一键更新器

用法（在该项目目录下，或任意目录）:
    python3 update.py          一键更新：拉取官方源 -> 重建 SQLite -> 重建 CSV/离线网页
    python3 update.py check    只检查官方源有没有新内容（不下载、不重建）
    python3 update.py --force  忽略"无更新"判断，强制完整重建
    python3 update.py coverage 只检查中文译文与官方原文是否一致（不下载、不重建）

说明:
    * 数据来自官方仓库 github.com/bjcp/styles（bjcp.org 在线版同源），需要网络；其余步骤全本地。
    * 本脚本只产生"本地产物"，不会把任何官方正文上传到任何地方。
"""
import os, subprocess, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "data", "styles-main")   # 官方 Markdown 源（git）
DB   = os.path.join(HERE, "bjcp.db")
STAMP = os.path.join(HERE, "data", "source_head.txt")
REMOTE = "https://github.com/bjcp/styles.git"

def sh(args, cwd=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)

def head_short(cwd):
    r = sh(["git", "rev-parse", "--short", "HEAD"], cwd)
    return r.stdout.strip() if r.returncode == 0 else None

def remote_head():
    r = sh(["git", "ls-remote", REMOTE, "HEAD"])
    if r.returncode != 0:
        return None
    return r.stdout.split()[0][:7]

def log(msg):
    print("[update]", msg)

def check_coverage():
    r = sh([sys.executable, os.path.join(HERE, "check_translations.py")])
    out = (r.stdout or "").strip()
    print(out if out else (r.stderr or "").strip()[:300])
    pending = os.path.join(HERE, "translations", "work", "pending.json")
    if os.path.exists(pending):
        print()
        print("[update] 官方正文有新增或变更，中文译文需要增量补齐（纯脚本无法翻译）。")
        print("[update] 步骤：请 AI（bjcp-styles skill 会话）按 glossary.md 翻译 translations/work/pending.json，")
        print("[update] 完成后运行：python3 merge_translations.py && python3 web/export_web.py")

def main():
    args = sys.argv[1:]
    force = "--force" in args
    check_only = "check" in args

    if "coverage" in args:
        check_coverage()
        return 0

    if sh(["git", "--version"]).returncode != 0:
        print("需要 git（brew install git）。已装则忽略。")
        return 1

    installed = os.path.isdir(os.path.join(SRC, ".git"))
    if not installed:
        rh = remote_head()
        if rh is None:
            print("无法访问官方仓库（无网络？）：", REMOTE)
            return 1
        if check_only:
            print("本地尚未安装数据。官方源当前 HEAD:", rh)
            return 0
        log("首次安装：克隆官方源（约 3 MB）...")
        os.makedirs(os.path.dirname(SRC), exist_ok=True)
        r = sh(["git", "clone", "--depth", "1", REMOTE, SRC])
        if r.returncode != 0:
            print("克隆失败：", (r.stderr or "").strip()[:400])
            return 1
        before = after = head_short(SRC)
        changed = True
    else:
        before = head_short(SRC)
        if check_only:
            rh = remote_head()
            if rh is None:
                print("无法访问官方仓库（无网络？）。本地 HEAD:", before)
                return 1
            if rh == before:
                print("已是最新：", before)
            else:
                print("官方有更新：", before, "->", rh, "（运行 python3 update.py 更新）")
            return 0
        log("拉取官方源更新...")
        r = sh(["git", "-C", SRC, "pull", "--ff-only", "--quiet"])
        if r.returncode != 0:
            print("拉取失败（可能无网络或本地被改动）：", (r.stderr or "").strip()[:400])
            print("若本地改动导致冲突：git -C %s stash 后重试" % SRC)
            return 1
        after = head_short(SRC)
        changed = before != after

    if not changed and not force:
        log("官方源无新提交（HEAD=%s），无需重建。用 --force 可强制重建。" % after)
        return 0

    log("重建数据库...")
    r = sh([sys.executable, os.path.join(HERE, "build_db.py"), SRC, DB])
    if r.returncode != 0:
        print("build_db.py 失败：", (r.stderr or "").strip()[:600])
        return 1
    for ln in r.stdout.strip().splitlines():
        print("   ", ln)

    log("导出 CSV...")
    import sqlite3, csv
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    cols = [d[0] for d in c.execute("SELECT * FROM styles LIMIT 1").description]
    def dump(path, sql):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(cols)
            for row in c.execute(sql):
                w.writerow([row[k] for k in cols])
    dump(os.path.join(HERE, "styles_full.csv"), "SELECT * FROM styles")
    dump(os.path.join(HERE, "styles_current.csv"),
         "SELECT s.* FROM styles s JOIN editions e ON e.key=s.edition_key WHERE e.is_current=1")
    c.close()

    log("重建离线网页...")
    r = sh([sys.executable, os.path.join(HERE, "web", "export_web.py")])
    if r.returncode != 0:
        print("export_web.py 失败：", (r.stderr or "").strip()[:600])
        return 1
    with open(STAMP, "w", encoding="utf-8") as f:
        f.write(after + " " + datetime.datetime.now().isoformat(timespec="minutes") + os.linesep)

    print()
    check_coverage()
    print()
    print("完成。官方源 HEAD:", after, (("（更新：%s -> %s）" % (before, after)) if changed else "（强制重建）"))
    print("  数据库  :", DB)
    print("  离线网页: %s（双击打开）" % os.path.join(HERE, "web", "index.html"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
