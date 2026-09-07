#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a single-file, offline web UI (web/index.html) from bjcp.db.
Usage: python3 export_web.py [bjcp.db] [output.html]
Edit TEMPLATE below (the whole UI lives here), rerun to regenerate.
"""
import json, os, sqlite3, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "bjcp.db")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "index.html")

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
editions = [dict(r) for r in db.execute("SELECT key, title, is_current AS current FROM editions ORDER BY CASE key WHEN 'bjcp-2021-beer' THEN 0 WHEN 'bjcp-2015-mead' THEN 1 WHEN 'bjcp-2025-cider' THEN 2 WHEN 'bjcp-2015-beer' THEN 3 ELSE 4 END")]
for e in editions:
    e["kind"] = {"beer": "Beer", "mead": "Mead", "cider": "Cider"}[e["key"].rsplit("-", 1)[1]]
    e["current"] = bool(e["current"])
cats = [{"e": r["edition_key"], "no": r["category_no"], "name": r["category_name"]}
        for r in db.execute("SELECT edition_key, category_no, category_name FROM categories")]
styles = []
for r in db.execute("SELECT * FROM styles"):
    sec = json.loads(r["sections_json"]) if r["sections_json"] else {}
    st = {
        "e": r["edition_key"], "c": r["category_no"], "id": r["style_code"], "n": r["name"],
        "lead": r["lead"] or "", "sec": sec, "vital": r["vital_statistics"] or "",
        "ex": r["examples"] or "", "tags": r["tags"] or "",
        "og": [r["og_min"], r["og_max"]], "fg": [r["fg_min"], r["fg_max"]],
        "ibu": [r["ibu_min"], r["ibu_max"]], "srm": [r["srm_min"], r["srm_max"]],
        "abv": [r["abv_min"], r["abv_max"]],
    }
    styles.append(st)
db.close()
data = {"generated": datetime.datetime.now().isoformat(timespec="seconds"), "editions": editions, "categories": cats, "styles": styles}
def jdump(o):
    return json.dumps(o, ensure_ascii=False, separators=(",", ":")).replace("</", "<" + chr(92) + "/")
TRDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "translations")
def jload(name):
    try:
        with open(os.path.join(TRDIR, name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
zh_all = jload("zh.json")
cat_zh = jload("categories_zh.json")
sec_zh = jload("section_labels_zh.json")
payload_en = jdump(data)
payload_zh = jdump({"data": data, "zh": zh_all, "cats": cat_zh, "sec": sec_zh})

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BJCP 风格查询（本地）</title>
<style>
:root{--amber:#8a5a1f;--amber2:#c98f3d;--bg:#faf6ef;--card:#fffdf8;--line:#e8dcc6;--ink:#2f2413;--muted:#8a7a5c;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);}
header{background:linear-gradient(135deg,#6b4a17,#a06a24);color:#fff;padding:12px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
header h1{margin:0;font-size:18px;font-weight:700;letter-spacing:.5px;}
header .sub{opacity:.85;font-size:12px;}
header select{margin-left:auto;padding:6px 8px;border-radius:8px;border:1px solid #d9c08a;background:#fffdf6;font-size:14px;}
.toolbar{display:flex;gap:10px;padding:10px 18px;flex-wrap:wrap;align-items:center;background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5;}
#q{flex:1 1 280px;min-width:200px;padding:9px 12px;border-radius:10px;border:1px solid var(--line);font-size:15px;background:var(--card);}
.count{color:var(--muted);font-size:13px;white-space:nowrap;}
.wrap{display:grid;grid-template-columns:230px 320px 1fr;gap:0;min-height:calc(100vh - 120px);}
.panel{overflow:auto;}
.panel h3{font-size:12px;letter-spacing:1px;color:var(--muted);margin:0;padding:10px 14px 4px;text-transform:uppercase;}
#cats{background:#f6efdd;border-right:1px solid var(--line);}
.cat{padding:7px 14px;cursor:pointer;font-size:13.5px;display:flex;justify-content:space-between;border-left:3px solid transparent;}
.cat:hover{background:#efe4c8;}
.cat.on{background:#fff;border-left-color:var(--amber);font-weight:600;}
.cat .num{color:var(--muted);font-size:11px;margin-top:1px;}
#list{background:#fff;border-right:1px solid var(--line);}
.st{padding:9px 14px;cursor:pointer;border-bottom:1px solid #f3ecdd;}
.st:hover{background:#fbf5e8;}
.st.on{background:#f3e7cd;box-shadow:inset 3px 0 0 var(--amber2);}
.st .cod{color:var(--amber);font-weight:700;font-size:12px;letter-spacing:.5px;}
.st .nam{font-size:14px;margin-top:1px;}
.st .tiny{color:var(--muted);font-size:11px;margin-top:2px;}
#detail{background:var(--card);padding:18px 22px;max-width:900px;}
#btnMenu,#btnCats,#btnList,#chipsBar,#dim{display:none;}
.minibtn{background:#fff;border:1px solid var(--line);border-radius:10px;padding:7px 11px;font-size:13.5px;cursor:pointer;color:#5d4a20;white-space:nowrap;}
.minibtn:active{background:#f3e7cd;}
.chips{display:none;align-items:center;gap:6px;padding:8px 12px;overflow-x:auto;background:#fff;border-bottom:1px solid var(--line);}
#chipsBar.on{display:flex;}
.chip{flex:0 0 auto;background:#f3e7cd;border:1px solid #e0d0ac;border-radius:999px;padding:4px 11px;font-size:12.5px;cursor:pointer;color:#5d4a20;white-space:nowrap;}
.chip.sel{background:var(--amber);border-color:var(--amber);color:#fff;}
@media (max-width:1000px){
  .wrap{display:block;}
  #list{display:none;}
  #cats{position:fixed;top:0;bottom:0;left:0;width:min(86vw,340px);background:#fff;z-index:40;max-height:none;box-shadow:6px 0 30px rgba(60,45,15,.22);transform:translateX(-106%);transition:transform .2s ease;}
  #cats.open{transform:none;}
  #dim{position:fixed;inset:0;background:rgba(50,35,10,.32);z-index:35;display:none;}
  #dim.on{display:block;}
  #btnMenu{display:inline-block;}
  header select, header .sub{display:none;}
  header h1{font-size:16px;}
  #detail{padding:14px;}
  .menu-head{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);padding:10px 14px;font-size:11px;letter-spacing:1px;color:var(--muted);text-transform:uppercase;z-index:1;}
  .editem{padding:9px 14px;font-size:14px;cursor:pointer;border-bottom:1px solid #f3ecdd;}
  .editem.on{background:#f3e7cd;color:var(--amber);font-weight:600;}
}
.hero{border-bottom:2px solid var(--amber2);padding-bottom:10px;margin-bottom:12px;}
.hero .hcod{color:var(--amber);font-weight:800;font-size:15px;letter-spacing:1px;}
.hero .hname{font-size:24px;font-weight:800;margin:2px 0;}
.hero .hmeta{color:var(--muted);font-size:12.5px;}
.lead{background:#fbf3e0;border-left:4px solid var(--amber2);padding:10px 14px;border-radius:0 8px 8px 0;font-style:italic;margin:10px 0;}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0;}
.stat{background:#fff;border:1px solid var(--line);border-radius:10px;padding:6px 12px;text-align:center;min-width:86px;}
.stat .k{font-size:11px;color:var(--muted);}
.stat .v{font-size:15px;font-weight:700;color:var(--amber);}
.stat .u{font-size:10px;color:var(--muted);}
section.s{margin:12px 0;}
section.s h4{font-size:13px;letter-spacing:1px;color:#7a5a24;border-bottom:1px solid #efe4cd;padding-bottom:4px;margin:14px 0 6px;text-transform:uppercase;}
section.s p{margin:6px 0;line-height:1.75;font-size:14.5px;}
ul{line-height:1.75;font-size:14.5px;padding-left:22px;margin:6px 0;}
.ex{font-size:14.5px;line-height:1.75;}
.tag{display:inline-block;background:#f0e6d2;border:1px solid #e0d0ac;border-radius:999px;padding:2px 10px;font-size:12px;margin:2px 4px 2px 0;color:#5d4a20;}
.empty{color:var(--muted);padding:30px 18px;text-align:center;font-size:14px;}
footer{color:var(--muted);font-size:11.5px;padding:10px 18px;border-top:1px solid var(--line);background:#fff;line-height:1.6;}
b{color:#7a4f00;}
</style>
</head>
<body>
<header>
  <button class="minibtn" id="btnMenu" type="button" aria-label="菜单">☰</button>
  <h1 id="appTitle">BJCP Style Lookup</h1>
  <span class="sub" id="sub"></span>
  <select id="edition"></select>
</header>
<div class="toolbar">
  <input id="q" type="search" placeholder="">
  <span class="count" id="count"></span>
</div>
<div id="chipsBar" class="chips"></div>
<div id="dim"></div>
<div class="wrap">
  <div class="panel" id="cats"><h3 id="cath3"></h3><div id="catlist"></div></div>
  <div class="panel" id="list"><h3 id="sth3"></h3><div id="styList"></div></div>
  <div class="panel" id="detail"><div class="empty" id="dempty"></div><div id="card"></div></div>
</div>
<footer>
  <span id="footNote"></span>
  <span id="genNote"></span>
</footer>
<script>
var P = /*__BJCP_JSON__*/;
var DATA = P.data || P;
var ZH = P.zh || {};
var CAT_ZH = P.cats || {};
var SEC_ZH = P.sec || {};
var HAS_ZH = !!(P.zh && Object.keys(P.zh).length);
var LANG = HAS_ZH ? 'zh' : 'en';
var ED = 'bjcp-2021-beer', catAll = true, curCat = null, sel = null;
var byEdition = {}, catsByEdition = {};
DATA.editions.forEach(function(e){ byEdition[e.key] = []; catsByEdition[e.key] = []; });
DATA.categories.forEach(function(c){ catsByEdition[c.e].push(c); });
DATA.styles.forEach(function(s){ byEdition[s.e].push(s); });

var ED_ZH = {'bjcp-2021-beer':'BJCP 2021 啤酒风格指南（现行）','bjcp-2015-mead':'BJCP 2015 蜂蜜酒风格指南（现行）','bjcp-2025-cider':'BJCP 2025 苹果酒风格指南（现行）','bjcp-2015-beer':'BJCP 2015 啤酒风格指南（旧版）','bjcp-2015-cider':'BJCP 2015 苹果酒风格指南（旧版）'};
var UI = {
  en: {title:'BJCP Style Lookup (local)', appTitle:'🍺 BJCP Style Lookup', sub:'Local database', ph:'Search code / name / examples / tags, e.g. 21A, IPA, imperial…', cats:'Categories', styles:'Styles', empty:'Pick a category, or search', nohit:'No matching style', of:'styles', andOf:'/ total ', units:'styles', examples:'Commercial Examples', tags:'Tags', og:'OG', fg:'FG', ibu:'IBU', srm:'SRM', abv:'ABV', ogU:'original gravity', fgU:'final gravity', ibuU:'IBU', srmU:'SRM color', abvU:'alcohol %vol', notset:'No official fixed range (see text below)', zh:'中文', en:'English', foot:'Data: official BJCP Style Guidelines (styles.bjcp.org / github.com/bjcp/styles), generated locally. Content © BJCP, Inc. — personal / study use only; do not sell or repost reformatted versions online.', by:'language', gen:'generated'},
  zh: {title:'BJCP 风格查询（本地）', appTitle:'🍺 BJCP 风格查询（本地）', sub:'本地数据库', ph:'搜索风格码 / 名称 / 商业例子 / 标签，如 21A、IPA、Imperial…', cats:'分类', styles:'风格', empty:'选择左侧分类或搜索风格', nohit:'没有匹配的风格', of:'个风格', andOf:' / 共 ', units:'个风格', examples:'商业例子', tags:'标签', og:'OG', fg:'FG', ibu:'IBU', srm:'SRM', abv:'ABV', ogU:'原麦汁比重', fgU:'终麦汁比重', ibuU:'苦度 IBU', srmU:'色度 SRM', abvU:'酒精度 %vol', notset:'官方未设固定范围（见下方数值说明）', zh:'中文（译文）', en:'English（原文）', foot:'数据来源：BJCP 官方风格指南（styles.bjcp.org / github.com/bjcp/styles），本地生成。内容 © BJCP, Inc.，仅限个人/学习使用；请勿出售或公开转载重排版本。', by:'语言', gen:'本地生成于'},
  keys: {en: {'overall impression':'Overall Impression','aroma':'Aroma','appearance':'Appearance','flavor':'Flavor','mouthfeel':'Mouthfeel','comments':'Comments','history':'History','characteristic ingredients':'Characteristic Ingredients','ingredients':'Ingredients','style comparison':'Style Comparison','entry instructions':'Entry Instructions','vital statistics':'Vital Statistics','aroma/flavor':'Aroma/Flavor','varieties':'Varieties','aroma, appearance, flavor, mouthfeel':'Aroma, Appearance, Flavor, Mouthfeel','currently defined types':'Currently Defined Types','strength classifications':'Strength Classifications','specialty ipa: belgian ipa':'Specialty IPA: Belgian IPA','specialty ipa: black ipa':'Specialty IPA: Black IPA','specialty ipa: brown ipa':'Specialty IPA: Brown IPA','specialty ipa: red ipa':'Specialty IPA: Red IPA','specialty ipa: rye ipa':'Specialty IPA: Rye IPA','specialty ipa: white ipa':'Specialty IPA: White IPA','specialty ipa: brut ipa':'Specialty IPA: Brut IPA'}, zh: {}},
};
var SEC_EN = UI.keys.en;
function T(k){ return (UI[LANG] && UI[LANG][k]) || k; }
function secLabel(key){ if (LANG === 'zh' && SEC_ZH[key]) return SEC_ZH[key]; if (SEC_EN[key]) return SEC_EN[key]; return key; }
function zfind(e, code){ var m = ZH[e]; if (!m) return null; return m[code] || null; }
function styleName(s){ if (LANG === 'zh'){ var z = zfind(s.e, s.id); if (z && z.name_zh) return z.name_zh; } return s.n; }
function leadBody(s){ if (LANG === 'zh'){ var z = zfind(s.e, s.id); if (z && z.lead_zh && z.lead_zh.trim()) return z.lead_zh; } return s.lead || ''; }
function secBody(s, key){ if (LANG === 'zh'){ var z = zfind(s.e, s.id); if (z && z.sec && z.sec[key] && z.sec[key].trim()) return z.sec[key]; } var o = s.sec[key]; return o || ''; }
function catTitle(c){ if (LANG === 'zh' && CAT_ZH[c.e] && CAT_ZH[c.e][c.no]) return CAT_ZH[c.e][c.no]; return c.name.replace(/^\d+\.\s*/, ''); }
function catTitleFull(c){ if (LANG === 'zh' && CAT_ZH[c.e] && CAT_ZH[c.e][c.no]) return CAT_ZH[c.e][c.no]; return c.name; }
function editionTitle(e){ if (LANG === 'zh' && ED_ZH[e.key]) return ED_ZH[e.key]; return e.title; }

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function md(t){
  t = esc(t);
  t = t.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
  t = t.replace(/(^|[^*_])_([^_]+)_(?=[^_]|$)/g, '$1<em>$2</em>');
  var paras = [], cur = [], inList = false, items = [];
  function flushP(){
    if (inList){ if (items.length) paras.push('<ul><li>' + items.join('</li><li>') + '</li></ul>'); items = []; inList = false; }
    if (cur.length){ paras.push('<p>' + cur.join(' ') + '</p>'); cur = []; }
  }
  String(t).split('\n').forEach(function(l){
    l = l.trim();
    if (!l){ flushP(); return; }
    var m = l.match(/^[-*]\s+(.*)$/);
    if (m){ if (!inList && cur.length) flushP(); inList = true; items.push(m[1]); }
    else { flushP(); cur.push(l); }
  });
  flushP();
  return paras.join('');
}
function num(s){ var lo = s[0], hi = s[1]; if (lo === null || lo === undefined) return null; return lo === hi ? lo : [lo, hi]; }
function fmtF(v){ return Number(v).toFixed(3); }
function fmtInt(v){ return String(Math.round(v)); }
function fmtABV(v){ return String(Math.round(Number(v) * 10) / 10); }
function statChip(k, s){
  var n = num(s); if (!n) return '';
  var f = (k === 'og' || k === 'fg') ? fmtF : (k === 'abv' ? fmtABV : fmtInt);
  var lo = f(n[0]), hi = f(n[1]);
  var label = T(k === 'og' ? 'og' : k === 'fg' ? 'fg' : k === 'ibu' ? 'ibu' : k === 'srm' ? 'srm' : 'abv');
  var unit = T(k === 'og' ? 'ogU' : k === 'fg' ? 'fgU' : k === 'ibu' ? 'ibuU' : k === 'srm' ? 'srmU' : 'abvU');
  return '<div class="stat"><div class="k">' + label + '</div><div class="v">' + (lo === hi ? lo : lo + ' – ' + hi) + '</div><div class="u">' + unit + '</div></div>';
}
var ORDER = ['overall impression','aroma','appearance','flavor','mouthfeel','comments','history','characteristic ingredients','style comparison','entry instructions'];
function detailCard(s){
  var zhMode = (LANG === 'zh');
  var h = '<div class="hero">';
  if (zhMode){ h += '<span class="hcod">' + esc(s.id) + '</span><div class="hname">' + esc(styleName(s)) + '</div>'; }
  else { h += '<span class="hcod">' + esc(s.id) + '</span><div class="hname">' + esc(s.n) + '</div>'; }
  var meta = [];
  meta.push(catTitleFull(catOf(s)));
  if (zhMode && CAT_ZH[s.e] && CAT_ZH[s.e][s.c]) meta.push(catOf(s).name);
  if (zhMode && styleName(s) !== s.n) meta.push('Official: ' + s.n);
  h += '<div class="hmeta">' + esc(meta.join('  ·  ')) + '</div></div>';
  var lead = leadBody(s);
  if (lead) h += '<div class="lead">' + md(lead) + '</div>';
  var chips = statChip('og', s.og) + statChip('fg', s.fg) + statChip('ibu', s.ibu) + statChip('srm', s.srm) + statChip('abv', s.abv);
  if (chips) h += '<div class="stats">' + chips + '</div>';
  var done = {};
  ORDER.forEach(function(k){
    var v = secBody(s, k); if (!v) return; done[k] = true;
    h += '<section class="s"><h4>' + secLabel(k) + '</h4>' + md(v) + '</section>';
  });
  Object.keys(s.sec).forEach(function(k){
    if (done[k]) return;
    if (k === 'commercial examples' || k === 'tags') return;
    var v = secBody(s, k); if (!v) return;
    h += '<section class="s"><h4>' + esc(secLabel(k)) + '</h4>' + md(v) + '</section>';
  });
  if (s.ex) h += '<section class="s"><h4>' + T('examples') + '</h4><div class="ex">' + md(s.ex) + '</div></section>';
  if (s.tags) h += '<div>' + s.tags.split(',').map(function(t){ return '<span class="tag">' + esc(t.trim()) + '</span>'; }).join('') + '</div>';
  return h;
}
function catOf(s){ var list = catsByEdition[s.e] || []; for (var i = 0; i < list.length; i++){ if (list[i].no === s.c) return list[i]; } return { e: s.e, no: s.c, name: s.c }; }
function haystack(s){
  var hz = s.id + ' ' + s.n + ' ' + s.ex + ' ' + s.tags;
  if (LANG === 'zh'){ var z = zfind(s.e, s.id); if (z){ hz += ' ' + (z.name_zh || ''); } }
  return hz.toLowerCase();
}
function visibleStyles(){
  var q = document.getElementById('q').value.trim().toLowerCase();
  var list = byEdition[ED];
  if (q) return list.filter(function(s){ return haystack(s).indexOf(q) >= 0; });
  if (!catAll && curCat) return list.filter(function(s){ return s.c === curCat; });
  return list;
}
function renderCats(){
  var box = document.getElementById('catlist');
  box.innerHTML = '';
  if (isMobile()){
    var emh = document.createElement('div');
    emh.className = 'menu-head'; emh.textContent = T('by');
    box.appendChild(emh);
    DATA.editions.forEach(function(e){
      var d = document.createElement('div');
      d.className = 'editem' + (ED === e.key ? ' on' : '');
      d.textContent = editionTitle(e);
      d.onclick = function(){ ED = e.key; catAll = true; curCat = null; sel = null; document.getElementById('q').value = ''; var es = document.getElementById('edition'); if (es) es.value = e.key; closeDrawers(); renderCats(); renderList(); };
      box.appendChild(d);
    });
    var ch = document.createElement('div');
    ch.className = 'menu-head'; ch.textContent = T('cats');
    box.appendChild(ch);
  }
  var all = document.createElement('div');
  all.className = 'cat' + (catAll ? ' on' : '');
  all.innerHTML = '<span>' + T('cats') + '（全部）</span><span class="num">' + byEdition[ED].length + '</span>';
  all.onclick = function(){ catAll = true; curCat = null; sel = null; renderCats(); renderList(); afterCatPick(); };
  box.appendChild(all);
  catsByEdition[ED].forEach(function(c){
    var d = document.createElement('div');
    d.className = 'cat' + (!catAll && curCat === c.no ? ' on' : '');
    var nm = (LANG === 'zh') ? catTitleFull(c) : c.name;
    d.innerHTML = '<span>' + esc(c.no) + '. ' + esc(nm) + '</span><span class="num">' + byEdition[ED].filter(function(s){ return s.c === c.no; }).length + '</span>';
    d.onclick = function(){ catAll = false; curCat = c.no; sel = null; renderCats(); renderList(); afterCatPick(); };
    box.appendChild(d);
  });
}
function renderList(){
  var box = document.getElementById('styList');
  var list = visibleStyles();
  var total = byEdition[ED].length;
  document.getElementById('count').textContent = list.length + ' ' + T('of') + (list.length !== total ? T('andOf') + total : '');
  box.innerHTML = '';
  if (!list.length){
    box.innerHTML = '<div class="empty">' + T('nohit') + '</div>';
    sel = null;
    document.getElementById('card').innerHTML = '';
    document.getElementById('dempty').style.display = '';
    renderChips([]);
    return;
  }
  list.forEach(function(s){
    var d = document.createElement('div');
    d.className = 'st' + (sel && sel.id === s.id ? ' on' : '');
    var line = '';
    var abv = num(s.abv);
    if (abv) line = 'ABV ' + fmtABV(abv[0]) + '–' + fmtABV(abv[1]) + '%';
    var ibu = num(s.ibu);
    if (ibu) line += (line ? ' · ' : '') + 'IBU ' + fmtInt(ibu[0]) + '–' + fmtInt(ibu[1]);
    d.innerHTML = '<div class="cod">' + esc(s.id) + '</div><div class="nam">' + esc(styleName(s)) + '</div>' + (line ? '<div class="tiny">' + line + '</div>' : '');
    d.onclick = function(){ sel = s; closeDrawers(); renderList(); scrollToDetail(); };
    box.appendChild(d);
  });
  if (!sel || !list.some(function(s){ return s.id === sel.id; })) sel = list[0];
  renderChips(list);
  renderDetail();
}
function renderDetail(){
  if (!sel) return;
  document.getElementById('dempty').style.display = 'none';
  document.getElementById('card').innerHTML = detailCard(sel);
  document.getElementById('detail').scrollTop = 0;
}
function setChrome(){
  document.title = T('title');
  document.getElementById('appTitle').textContent = T('appTitle');
  document.getElementById('dempty').textContent = T('empty');
  document.getElementById('sub').textContent = T('sub') + ' · ' + DATA.styles.length + ' ' + (LANG === 'zh' ? T('of') : T('units')) + ' · ' + DATA.editions.length + ' ' + (LANG === 'zh' ? '版本' : 'editions');
  document.getElementById('q').placeholder = T('ph');
  document.getElementById('cath3').textContent = T('cats');
  document.getElementById('sth3').textContent = T('styles');
  document.getElementById('footNote').textContent = T('foot');
  document.getElementById('genNote').textContent = T('gen') + ' ' + DATA.generated;
  var edSel = document.getElementById('edition');
  for (var i = 0; i < edSel.options.length; i++){
    var e = DATA.editions[i];
    if (e) edSel.options[i].textContent = editionTitle(e);
  }
}
function afterCatPick(){ closeDrawers(); }
function closeDrawers(){ drawer('cats', false); }
function drawer(id, on){ var el = document.getElementById(id); if (!el.classList) return; if (on){ el.classList.add('open'); } else { el.classList.remove('open'); } dimSync(); }
function dimSync(){ var c = document.getElementById('cats').classList.contains('open'); document.getElementById('dim').className = c ? 'on' : ''; }
function isMobile(){ return typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(max-width:1000px)').matches; }
function scrollToDetail(){ if (!isMobile()) return; var d = document.getElementById('detail'); if (d && d.scrollIntoView) d.scrollIntoView({behavior:'smooth', block:'start'}); }
function renderChips(list){
  var bar = document.getElementById('chipsBar');
  if (!bar) return;
  var q = document.getElementById('q').value.trim();
  if (!isMobile()){ bar.className = 'chips'; bar.innerHTML = ''; return; }
  var show = q || (!catAll && curCat);
  if (!show){ bar.className = 'chips'; bar.innerHTML = ''; return; }
  var items = list.slice(0, 60);
  var html = items.map(function(s){ return '<span class="chip' + (sel && sel.id === s.id ? ' sel' : '') + '">' + esc(s.id) + ' ' + esc(styleName(s)).slice(0, 18) + '</span>'; }).join('');
  if (list.length > 60) html += '<span class="chip">…共 ' + list.length + '</span>';
  bar.innerHTML = html;
  bar.className = 'chips on';
  for (var i = 0; i < bar.children.length && i < items.length; i++){
    (function(s, el){ el.onclick = function(){ sel = s; closeDrawers(); renderList(); scrollToDetail(); }; })(items[i], bar.children[i]);
  }
}
function init(){
  var edSel = document.getElementById('edition');
  DATA.editions.forEach(function(e){
    var o = document.createElement('option');
    o.value = e.key; o.textContent = editionTitle(e);
    edSel.appendChild(o);
  });
  edSel.value = ED;
  edSel.onchange = function(){ ED = edSel.value; catAll = true; curCat = null; sel = null; document.getElementById('q').value = ''; renderCats(); renderList(); };
  if (HAS_ZH){
    var langSel = document.createElement('select');
    langSel.id = 'lang';
    var o1 = document.createElement('option'); o1.value = 'zh'; o1.textContent = '中文（译文）';
    var o2 = document.createElement('option'); o2.value = 'en'; o2.textContent = 'English（原文）';
    langSel.appendChild(o1); langSel.appendChild(o2);
    langSel.value = LANG;
    langSel.onchange = function(){ LANG = langSel.value; sel = null; setChrome(); renderCats(); renderList(); };
    edSel.parentNode.insertBefore(langSel, edSel);
  }
  var q = document.getElementById('q');
  var timer = null;
  q.oninput = function(){ clearTimeout(timer); timer = setTimeout(function(){ sel = null; renderList(); }, 120); };
  var bm = document.getElementById('btnMenu'); if (bm) bm.onclick = function(){ closeDrawers(); drawer('cats', true); };
  var dimEl = document.getElementById('dim'); if (dimEl) dimEl.onclick = function(){ closeDrawers(); };
  setChrome();
  renderCats(); renderList();
}
init();
</script>
</body>
</html>
"""

WEB = os.path.dirname(os.path.abspath(__file__))
Q = chr(34) * 3
def write_page(name, payload):
    html = TEMPLATE.replace("/*__BJCP_JSON__*/", payload)
    assert "/*__BJCP_JSON__*/" not in html, "placeholder not replaced"
    assert html.count(Q) == 0
    path = os.path.join(WEB, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("wrote", os.path.abspath(path), "%.2f MB" % (os.path.getsize(path) / 1e6))
write_page("index.en.html", payload_en)
write_page("index.zh.html", payload_zh)
write_page("index.html", payload_zh if zh_all else payload_en)
print("styles:", len(styles), "| editions:", len(editions), "| categories:", len(cats))
print("zh styles translated:", sum(len(v) for v in zh_all.values()))
