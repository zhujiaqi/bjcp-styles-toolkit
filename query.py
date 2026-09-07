#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BJCP Style local lookup CLI.

Examples:
  python3 query.py 21A                  # show style 21A (current beer, 2021)
  python3 query.py "west coast"         # fuzzy name search (contains, case-insensitive)
  python3 query.py --mead M1A           # pick edition kind (beer|mead|cider)
  python3 query.py --edition bjcp-2015-beer 1B
  python3 query.py list --kind beer     # list current beer styles
"""
import sqlite3, sys, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bjcp.db")

KIND_EDITION = {
    "beer": "bjcp-2021-beer",
    "mead": "bjcp-2015-mead",
    "cider": "bjcp-2025-cider",
}

def sec(text):
    return "\n".join(l.rstrip() for l in text.splitlines()) if text else "(—)"

def show(db, row):
    print("=" * 78)
    cat = db.execute("SELECT category_name FROM categories WHERE edition_key=? AND category_no=?",
                     (row["edition_key"], row["category_no"])).fetchone()
    print(f"{row['style_code']}. {row['name']}   [{row['edition_key']}]")
    print("Category:", cat[0] if cat else row["category_no"])
    print("=" * 78)
    if row["lead"]:
        print(">", sec(row["lead"])); print()
    for label, key in [("Overall Impression", "overall_impression"), ("Aroma", "aroma"),
                       ("Appearance", "appearance"), ("Flavor", "flavor"),
                       ("Mouthfeel", "mouthfeel"), ("Comments", "comments"),
                       ("History", "history"), ("Characteristic Ingredients", "ingredients"),
                       ("Style Comparison", "style_comparison")]:
        v = row[key]
        if v:
            print(f"[{label}]"); print(sec(v)); print()
    if row["vital_statistics"]:
        print("[Vital Statistics]")
        for line in row["vital_statistics"].splitlines():
            print(" ", line.strip())
        print()
    if row["examples"]:
        print("[Commercial Examples]"); print(sec(row["examples"])); print()
    if row["tags"]:
        print("[Tags]", row["tags"])

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); return
    edition = None
    mode = "find"
    if "--edition" in args:
        i = args.index("--edition"); edition = args[i + 1]; del args[i:i + 2]
    for kind, ed in KIND_EDITION.items():
        if f"--{kind}" in args:
            edition = ed; args.remove(f"--{kind}")
    db = sqlite3.connect(DB); db.row_factory = sqlite3.Row
    if args and args[0] == "list":
        rows = db.execute("SELECT style_code,name FROM styles WHERE edition_key=? ORDER BY style_code",
                          (edition or "bjcp-2021-beer",)).fetchall()
        for r in rows:
            print(f"{r['style_code']:<6} {r['name']}")
        return
    term = " ".join(args)
    if not edition:
        edition = "bjcp-2021-beer"
    # 1) exact code first, else name/substring search
    row = db.execute("SELECT * FROM styles WHERE edition_key=? AND upper(style_code)=?",
                     (edition, term.upper().strip())).fetchone()
    if not row:
        like = f"%{term}%"
        rows = db.execute("SELECT * FROM styles WHERE edition_key=? AND (lower(name) LIKE ? OR lower(style_code) LIKE ? OR lower(examples) LIKE ?)",
                          (edition, like.lower(), like.lower(), like.lower())).fetchall()
        if not rows:
            rows = db.execute("SELECT * FROM styles WHERE lower(name) LIKE ? OR lower(style_code) LIKE ?",
                              (like.lower(), like.lower())).fetchall()
        if not rows:
            print("no match"); return
        if len(rows) > 1:
            for r in rows:
                print(f"{r['style_code']:<6} {r['name']:<42} {r['edition_key']}")
            print("\nuse an exact code or a more specific search"); return
        row = rows[0]
    show(db, row)

if __name__ == "__main__":
    main()
