#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a local SQLite database of BJCP Style Guidelines from the official
bjcp/styles Markdown source (github.com/bjcp/styles).
Data (c) BJCP, Inc. Personal / educational use only; see research.md.

Usage: python3 build_db.py [path-to-styles-main] [output.db]
"""
import os, re, sys, sqlite3, json, csv

ROOT = sys.argv[1] if len(sys.argv) > 1 else "data/styles-main"
OUT = sys.argv[2] if len(sys.argv) > 2 else "bjcp.db"

EDITION_META = {
    "bjcp-2021-beer":  ("BJCP 2021 Beer Style Guidelines (current)", True),
    "bjcp-2015-mead":  ("BJCP 2015 Mead Style Guidelines (current)", True),
    "bjcp-2025-cider": ("BJCP 2025 Cider Style Guidelines (current)", True),
}

ID_RE = re.compile(r"^[A-Za-z]?\d+[A-Za-z]?$")
H1_RE = re.compile(r"^#\s+(.+)$")
SEC_RE = re.compile(r"^##\s+(.+)$")
STAT_RE = re.compile(r"^\s*[-*]\s*([A-Za-z/ ]+?)\s*:\s*(.+?)\s*$")
NUM_RE = re.compile(r"(-?\d+(?:\.\d+)?)")

# candidate numeric ranges: <key> min max
STAT_KEYS = {
    "og":  "og", "original gravity": "og", "original_gravity": "og",
    "fg":  "fg", "final gravity": "fg", "final_gravity": "fg",
    "ibu": "ibu", "ibus": "ibu", "ibu/srm": "ibu_srm",
    "srm": "srm", "color": "srm", "ebc": "ebc", "lovibond": "srm",
    "abv": "abv",
    "carb": "carb", "carbonation": "carb", "co2": "carb", "volumes": "carb",
}

def norm_section(title: str) -> str:
    t = title.strip()
    # strip trailing colon and punctuation spacing
    t = re.sub(r":\s*$", "", t)
    return re.sub(r"\s+", " ", t).lower()

def parse_range(text: str):
    nums = [float(x) for x in NUM_RE.findall(text)]
    if not nums:
        return None, None
    if len(nums) == 1:
        return nums[0], nums[0]
    return min(nums[:2]), max(nums[:2])

def first_h1(text: str):
    for ln in text.splitlines():
        s = ln.strip()
        m = H1_RE.match(s)
        if m:
            return m.group(1).strip()
    return None

def parse_style(path: str):
    """Return dict for one style page, or None if not a style page."""
    base = os.path.basename(path)
    if base == "README.md":
        return None
    cat_dir = os.path.basename(os.path.dirname(path))
    # style files live directly inside a numeric (or X) category folder
    if not re.fullmatch(r"\d+|X\d*|x\d*", cat_dir):
        return None
    ident = base.split("-")[0]
    if not ID_RE.fullmatch(ident):
        return None
    raw = open(path, encoding="utf-8").read()
    lines = raw.splitlines()

    h1 = first_h1(raw)
    code = name = None
    if h1:
        m = re.match(r"^([A-Za-z]?\d+[A-Za-z]?)\s*[.．]\s*(.+)$", h1)
        if m:
            code, name = m.group(1).upper(), m.group(2).strip()
    if not code:
        code = ident.upper()
    if not name:
        slug = base[len(ident)+1:-3]
        name = slug.replace("-", " ").title()

    # split into lead + sections
    lead_parts, sections, cur_title = [], {}, None
    cur_body = []
    for ln in lines:
        if SEC_RE.match(ln):
            if cur_title is not None:
                sections[cur_title] = "\n".join(cur_body).strip()
            cur_title = norm_section(SEC_RE.match(ln).group(1))
            cur_body = []
        else:
            if cur_title is None:
                if ln.strip().startswith("# ") or not ln.strip():
                    continue  # skip the H1 title itself
                lead_parts.append(ln)
            else:
                cur_body.append(ln)
    if cur_title is not None:
        sections[cur_title] = "\n".join(cur_body).strip()

    lead = "\n".join(lead_parts).strip()
    # strip markdown italic markers in lead for cleanliness
    lead = re.sub(r"^[*_]+|[*_]+$", "", lead)

    stats = {}
    stats_raw = sections.get("vital statistics", "")
    for ln in stats_raw.splitlines():
        m = STAT_RE.match(ln)
        if not m:
            continue
        key = norm_section(m.group(1)).replace("/", "_")
        val = m.group(2).strip()
        tgt = STAT_KEYS.get(key, key.replace(" ", "_"))
        stats.setdefault(tgt, []).append(val)

    row = {
        "edition_key": os.path.basename(os.path.dirname(os.path.dirname(path))),
        "category_no": cat_dir,
        "style_code": code,
        "name": name,
        "slug": base[:-3],
        "lead": lead,
        "sections": json.dumps(sections, ensure_ascii=False),
        "overall": sections.get("overall impression", ""),
        "aroma": sections.get("aroma", ""),
        "appearance": sections.get("appearance", ""),
        "flavor": sections.get("flavor", ""),
        "mouthfeel": sections.get("mouthfeel", ""),
        "comments": sections.get("comments", ""),
        "history": sections.get("history", ""),
        "ingredients": sections.get("ingredients", ""),
        "style_comparison": sections.get("style comparison", ""),
        "examples": sections.get("commercial examples", ""),
        "tags": re.sub(r"^[_*]+|[_*]+$", "", sections.get("tags", "")).strip(),
        "vital_raw": stats_raw.strip(),
    }
    for k, label in [("og", "og"), ("fg", "fg"), ("ibu", "ibu"),
                     ("srm", "srm"), ("abv", "abv")]:
        vals = stats.get(k) or []
        lo, hi = None, None
        for v in vals:
            a, b = parse_range(v)
            if a is not None:
                lo = a if lo is None else min(lo, a)
                hi = b if hi is None else max(hi, b)
        row[f"{label}_min"], row[f"{label}_max"] = lo, hi
    row["stats_all"] = json.dumps(stats, ensure_ascii=False)
    return row

def category_name(path: str):
    """Best-effort category title from a category README or folder."""
    readme = os.path.join(path, "README.md")
    if os.path.exists(readme):
        t = open(readme, encoding="utf-8").read()
        for ln in t.splitlines():
            s = ln.strip()
            if s.startswith("#"):
                return s.lstrip("# ").strip()
    return os.path.basename(path)

def main():
    db = sqlite3.connect(OUT)
    cur = db.cursor()
    cur.executescript("""
    DROP TABLE IF EXISTS styles;
    DROP TABLE IF EXISTS categories;
    DROP TABLE IF EXISTS editions;
    CREATE TABLE editions (
      key TEXT PRIMARY KEY, title TEXT NOT NULL, is_current INTEGER NOT NULL
    );
    CREATE TABLE categories (
      edition_key TEXT NOT NULL, category_no TEXT NOT NULL, category_name TEXT,
      PRIMARY KEY (edition_key, category_no)
    );
    CREATE TABLE styles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      edition_key TEXT NOT NULL,
      category_no TEXT NOT NULL,
      style_code TEXT NOT NULL,
      name TEXT NOT NULL,
      slug TEXT,
      lead TEXT,
      overall_impression TEXT, aroma TEXT, appearance TEXT, flavor TEXT,
      mouthfeel TEXT, comments TEXT, history TEXT, ingredients TEXT,
      style_comparison TEXT, examples TEXT, tags TEXT,
      og_min REAL, og_max REAL, fg_min REAL, fg_max REAL,
      ibu_min REAL, ibu_max REAL, srm_min REAL, srm_max REAL,
      abv_min REAL, abv_max REAL,
      vital_statistics TEXT, sections_json TEXT
    );
    CREATE INDEX idx_styles_edition ON styles(edition_key);
    CREATE INDEX idx_styles_code ON styles(edition_key, style_code);
    CREATE INDEX idx_styles_name ON styles(name);
    """)
    for k, (title, cur_flag) in EDITION_META.items():
        cur.execute("INSERT OR IGNORE INTO editions VALUES (?,?,?)", (k, title, int(cur_flag)))

    counts = {}
    problems = []
    for ed in EDITION_META:
        eddir = os.path.join(ROOT, ed)
        if not os.path.isdir(eddir):
            problems.append(f"missing edition dir: {ed}")
            continue
        n = 0
        for cat in sorted(os.listdir(eddir)):
            cdir = os.path.join(eddir, cat)
            if not os.path.isdir(cdir):
                continue
            if not re.fullmatch(r"\d+", cat):
                # non-numeric folders are intro/appendix pages, not style categories
                continue
            cname = category_name(cdir)
            cur.execute("INSERT OR IGNORE INTO categories VALUES (?,?,?)",
                        (ed, cat, cname))
            for fn in sorted(os.listdir(cdir)):
                if not fn.endswith(".md"):
                    continue
                row = parse_style(os.path.join(cdir, fn))
                if not row:
                    continue
                cur.execute("""
                  INSERT INTO styles (edition_key, category_no, style_code, name, slug,
                    lead, overall_impression, aroma, appearance, flavor, mouthfeel,
                    comments, history, ingredients, style_comparison, examples, tags,
                    og_min, og_max, fg_min, fg_max, ibu_min, ibu_max, srm_min, srm_max,
                    abv_min, abv_max, vital_statistics, sections_json)
                  VALUES (:edition_key,:category_no,:style_code,:name,:slug,:lead,
                    :overall,:aroma,:appearance,:flavor,:mouthfeel,:comments,:history,
                    :ingredients,:style_comparison,:examples,:tags,
                    :og_min,:og_max,:fg_min,:fg_max,:ibu_min,:ibu_max,:srm_min,:srm_max,
                    :abv_min,:abv_max,:vital_raw,:sections)
                """, row)
                n += 1
        counts[ed] = n
    db.commit()
    print("styles imported per edition:")
    for ed in EDITION_META:
        print(f"  {ed}: {counts.get(ed, 0)}")
    for p in problems:
        print("WARN:", p)
    total = db.execute("SELECT COUNT(*) FROM styles").fetchone()[0]
    print("TOTAL styles:", total)
    db.close()
    print("database written:", os.path.abspath(OUT))

if __name__ == "__main__":
    main()
