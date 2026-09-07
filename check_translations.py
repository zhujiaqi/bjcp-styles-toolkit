#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check Chinese translation coverage against the (possibly updated) English DB.

What it does:
  * Scans the current editions (bjcp-2021-beer, bjcp-2015-mead, bjcp-2025-cider)
    in bjcp.db and compares each style's English text with the zh translation
    entry stored in translations/zh.json.
  * zh.json entries carry an "en_hash" (SHA-256 of the canonical English text).
    A style needs (re-)translation when:
      - zh.json is missing entirely (initial translation), or
      - the style has no zh entry, or
      - en_hash differs (the official text changed since it was translated).
  * Only translatable prose is hashed: style name, lead, and description
    sections. 'vital statistics', 'commercial examples' and 'tags' are excluded
    (they stay in the official original in every language).

Output: prints a summary; if any style needs translation it writes
translations/work/pending.json (same item shape as the chunk inputs used for
the initial translation), which the AI/LLM step consumes to translate ONLY the
delta.

Usage:
    python3 check_translations.py            # check + write pending.json if needed
    python3 check_translations.py --quiet    # machine-friendly single-line summary
"""
import hashlib, json, os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "bjcp.db")
ZH_PATH = os.path.join(HERE, "translations", "zh.json")
PENDING = os.path.join(HERE, "translations", "work", "pending.json")
CURRENT_ED = ["bjcp-2021-beer", "bjcp-2015-mead", "bjcp-2025-cider"]
SKIP_KEYS = {"vital statistics", "commercial examples", "tags"}

def canonical(sec):
    return json.dumps(sorted((k, v) for k, v in sec.items() if k not in SKIP_KEYS),
                      ensure_ascii=False)

def en_hash(name, lead, sec):
    payload = "\x1f".join([name or "", lead or "", canonical(sec)]).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

def main():
    quiet = "--quiet" in sys.argv
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    zh = {}
    if os.path.exists(ZH_PATH):
        zh = json.load(open(ZH_PATH, encoding="utf-8"))

    pending = []
    missing_all = not zh
    catname = {}
    for r in db.execute("SELECT edition_key, category_no, category_name FROM categories"):
        catname[(r["edition_key"], r["category_no"])] = r["category_name"]

    rows = db.execute(
        "SELECT * FROM styles WHERE edition_key IN (%s) ORDER BY edition_key, style_code" %
        ",".join("?" * len(CURRENT_ED)), CURRENT_ED).fetchall()
    need = 0
    for r in rows:
        sec = json.loads(r["sections_json"]) if r["sections_json"] else {}
        h = en_hash(r["name"], r["lead"] or "", sec)
        entry = zh.get(r["edition_key"], {}).get(r["style_code"])
        ok = entry is not None and entry.get("en_hash") == h
        if ok:
            continue
        need += 1
        keep = {k: v for k, v in sec.items() if k not in SKIP_KEYS}
        pending.append({
            "e": r["edition_key"], "code": r["style_code"], "name": r["name"],
            "cat": catname.get((r["edition_key"], r["category_no"]), r["category_no"]),
            "lead": r["lead"] or "", "sec": keep,
        })
    db.close()

    if quiet:
        print("coverage: %d/%d current-edition styles need translation" % (need, len(rows)))
    else:
        print("current editions checked:", len(rows), "styles")
        print("need (re)translation:", need)
        if missing_all:
            print("(zh.json missing - this is the INITIAL translation state, not an update delta)")
        if need:
            os.makedirs(os.path.dirname(PENDING), exist_ok=True)
            json.dump(pending, open(PENDING, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print("pending written:", PENDING)
        else:
            if os.path.exists(PENDING):
                os.remove(PENDING)
            print("translations are up to date (no delta)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
