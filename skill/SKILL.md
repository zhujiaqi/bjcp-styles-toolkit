---
name: bjcp-styles
description: 查询本地 BJCP 风格数据库（145 个现行风格：2021 啤酒、2015 蜂蜜酒、2025 苹果酒，含 OG/FG/IBU/SRM/ABV 区间、完整特点描述、标签与商业例子）。当用户询问啤酒风格分类、某风格定义与数值、风格间对比、按风格找参数等时使用。
whenToUse: 用户问到 BJCP 风格（如 "21A 是什么"、"帝国世涛的 ABV 范围"、"低苦度琥珀色风格有哪些"、"XX 和 YY 的区别"）需要查询本地数据库给出确切数据时。
---

# BJCP 风格查询（本地数据库）

数据全部在本机 SQLite，无需联网、无需 LLM 工具即可回答；本 skill 说明如何准确查询。

## 数据文件

- SQLite 数据库：YOUR_LOCAL_PROJECT/bjcp.db
- 命令行查看器：YOUR_LOCAL_PROJECT/query.py（python3 query.py 21A / "west coast" / --cider C1A）
- 离线网页版（双击即用）：YOUR_LOCAL_PROJECT/web/index.html
- 原始数据与重建脚本：YOUR_LOCAL_PROJECT/（data/styles-main 官方 Markdown、build_db.py）

## 表结构（styles 表关键列）

- edition_key：bjcp-2021-beer（现行啤酒）/ bjcp-2015-mead（现行蜂蜜酒）/ bjcp-2025-cider（现行苹果酒）；旧版（2015 Beer/Cider）已移除
- style_code：如 21A、M1A、C1A；name：风格名
- 文字列：overall_impression, aroma, appearance, flavor, mouthfeel, comments, history, ingredients, style_comparison, examples, tags
- 数值列：og_min/og_max, fg_min/fg_max, ibu_min/ibu_max, srm_min/srm_max, abv_min/abv_max（无固定范围时全为 NULL）
- vital_statistics：数值区间原文；sections_json：各小节原文；categories 表存 edition 的分类名

## 查询方法（任选）

1. 整卡输出最快：python3 YOUR_LOCAL_PROJECT/query.py 21A
2. 自定义 SQL（推荐，能数值筛选）：

    python3 -c "import sqlite3;db=sqlite3.connect('YOUR_LOCAL_PROJECT/bjcp.db');db.row_factory=sqlite3.Row;print([dict(r) for r in db.execute('SELECT style_code,name,abv_min,abv_max FROM styles WHERE edition_key=? AND abv_max>=? ORDER BY abv_max DESC',('bjcp-2021-beer',9.0))])"

## 查询习惯与注意

- 用户给风格码时按 edition_key + 大写 style_code 精确匹配；给文字时做名称（必要时 examples/tags）模糊 LIKE。
- 版本优先现行版（啤酒默认 2021）；用户没说明时给出 2021 啤酒版结果，跨版本或旧版数据在回答中注明 edition。
- og/fg 保留三位小数阅读（如 1.056 - 1.070）；ibu/srm 整数；abv 一位小数。区间格式：1.056 – 1.070、40 – 70 IBU。
- 部分风格数值列全为 NULL 属正常：2021 啤酒中 27A、28A-28C、29A-29C、30A-30D、31A-31B、32A-32B、33A-33B、34A-34C 是 Specialty/可变风格，官方未设固定范围；蜂蜜酒 2015 版官方无逐风格数值表。此时引用 vital_statistics/正文说明，不要编造区间。
- 文本查询用 python3 sqlite3 或 sqlite3 CLI 均可；命令中含引号较多时优先写成临时 .py/.sql 文件再执行，避免 shell 转义问题。
- 回答中可给出 2-4 个代表性商业例子与标签辅助说明，但保持简洁；风格差异对比优先引用 style_comparison 与官方原文措辞。

## 语言说明（重要）

- 本 skill 的查询对象始终是 **SQLite 里的官方英文原文**（bjcp.db），不涉及中文译文。
- 中文译文独立存放在 translations/zh.json，只被网页生成器 web/export_web.py 使用（网页的中文版/原文对照切换）。数据库本身永远只存原文，因此 skill 的使用不受双语影响。
- 需要把查询结果讲给用户时，可直接基于英文原文用自然语言回答（中文/英文均可），不要改写官方数值。

## 数据与译文维护

    # 一键更新：拉官方源 -> 重建 SQLite/CSV/离线网页，并自动检查译文是否需要补齐
    python3 YOUR_LOCAL_PROJECT/update.py
    python3 YOUR_LOCAL_PROJECT/update.py check    # 只查官方源有无更新
    python3 YOUR_LOCAL_PROJECT/update.py coverage # 只查译文是否与原文一致

当 update.py 提示"官方正文有新增或变更，中文译文需要增量补齐"（产生了 translations/work/pending.json）时：
1. 读取术语表 translations/glossary.md；
2. 读取 pending.json，只翻译其中列出的风格（name/lead/sec 各字段），输出与分块输入相同结构；
3. 把结果放到 translations/work/outputs/ 下并运行 merge_translations.py（会校验键一致并写入 en_hash），再运行 python3 web/export_web.py 重新生成网页。
已有译文且哈希一致的部分不要重译。

## 许可注意

数据内容 © BJCP, Inc.，仅个人/学习用途：不要出售、不要在网上公开发布重排版本，不要把整库数据直接贴给第三方服务。
