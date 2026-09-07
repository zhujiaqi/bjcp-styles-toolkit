#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge per-chunk translation outputs into translations/zh.json (validate first).

Usage: python3 merge_translations.py
Report: missing chunks, missing styles, section-key mismatches, per-edition stats.
"""
import json, os, glob, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "translations", "work")
MANIFEST = json.load(open(os.path.join(WORK, "manifest.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "translations", "zh.json")

have = {}
missing_chunks = []
problems = []
total_styles = 0
total_chars = 0

for m in MANIFEST:
    p = os.path.join(WORK, "outputs", "chunk_%03d.json" % m["chunk"])
    if not os.path.exists(p):
        missing_chunks.append(m["chunk"])
        continue
    data = json.load(open(p, encoding="utf-8"))
    src = json.load(open(os.path.join(WORK, "inputs", "chunk_%03d.json" % m["chunk"]), encoding="utf-8"))
    by_code_src = {it["code"]: it for it in src["items"]}
    items = data.get("items", [])
    got_codes = []
    for it in items:
        code = it["code"]
        got_codes.append(code)
        s = by_code_src.get(code)
        if s is None:
            problems.append("chunk %d: unknown code %s" % (m["chunk"], code)); continue
        # section key parity
        src_keys = set(s["sec"].keys())
        out_keys = set((it.get("sec") or {}).keys())
        if src_keys != out_keys:
            problems.append("chunk %d %s: sec key mismatch src=%s out=%s" % (m["chunk"], code, sorted(src_keys), sorted(out_keys)))
        entry = {"name_zh": it.get("name_zh", ""), "lead_zh": it.get("lead_zh", "") or "", "sec": it.get("sec") or {}}
        have.setdefault(data.get("edition"), {})[code] = entry
        total_chars += sum(len(v) for v in [entry["name_zh"], entry["lead_zh"]] + list(entry["sec"].values()))
        total_styles += 1
    # ensure all src codes present
    for c in by_code_src:
        if c not in got_codes:
            problems.append("chunk %d: missing output for %s" % (m["chunk"], c))

if missing_chunks:
    print("MISSING chunks:", missing_chunks)
    print("aborted - do not merge yet")
    sys.exit(1)

if problems:
    print("PROBLEMS (%d):" % len(problems))
    for p in problems[:50]:
        print(" -", p)
    sys.exit(2)

zh_all = {}
for m in MANIFEST:
    ed = m["edition"]
    zh_all.setdefault(ed, {})
    # fill in style-code order already inside have
    for code, entry in have.get(ed, {}).items():
        zh_all[ed][code] = entry

import hashlib
import sqlite3

def _canonical(sec):
    return json.dumps(sorted((k, v) for k, v in sec.items() if k not in ("vital statistics", "commercial examples", "tags")), ensure_ascii=False)

def _en_hash(name, lead, sec):
    return hashlib.sha256("\x1f".join([name or "", lead or "", _canonical(sec)]).encode("utf-8")).hexdigest()

_db = sqlite3.connect(os.path.join(HERE, "bjcp.db"))
_db.row_factory = sqlite3.Row
srcmap = {}
for _r in _db.execute("SELECT edition_key, style_code, name, lead, sections_json FROM styles"):
    srcmap[(_r["edition_key"], _r["style_code"])] = (_r["name"], _r["lead"] or "", json.loads(_r["sections_json"] or "{}"))
_db.close()

for _ed in zh_all:
    for _code in zh_all[_ed]:
        key = (_ed, _code)
        if key in srcmap:
            _n, _l, _s = srcmap[key]
            zh_all[_ed][_code]["en_hash"] = _en_hash(_n, _l, _s)
        else:
            zh_all[_ed][_code]["en_hash"] = ""

json.dump(zh_all, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("merged ->", OUT)
for ed, codes in zh_all.items():
    print("  %-18s %d styles" % (ed, len(codes)))
print("total styles:", total_styles, "| zh chars:", total_chars)
