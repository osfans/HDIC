#!/usr/bin/env python3
"""
Generate a static HTML search page from three HDIC TSV dictionaries:
  - SYP.tsv      (宋本玉篇 Songben Yupian)
  - KTB.tsv      (篆隸萬象名義 Tenrei Bansho Meigi)
  - TSJ_definitions.tsv (新撰字鏡 Shinsen Jikyo)
"""

import csv
import json
import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def read_tsv(path, comment="#"):
    """Read a TSV file, skipping comment lines. Returns (header, rows)."""
    rows = []
    header = None
    with open(path, encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if not row or row[0].startswith(comment):
                continue
            if header is None:
                header = row
            else:
                rows.append(row)
    return header, rows


def load_syp():
    header, rows = read_tsv(REPO_ROOT / "SYP.tsv")
    # SYID, SY_vol_radical, SY_radical, Entry, Entry_original, SY_def, ...
    idx = {h: i for i, h in enumerate(header)}
    records = []
    for row in rows:
        def get(col):
            i = idx.get(col)
            return row[i].strip() if i is not None and i < len(row) else ""
        records.append({
            "entry": get("Entry"),
            "entry_orig": get("Entry_original"),
        "def": get("SY_def"),
            "source": "SYP",
        })
    return records


def load_ktb():
    header, rows = read_tsv(REPO_ROOT / "KTB.tsv")
    # TBID, TB_vol_radical, TB_radical, Entry, Entry_type, Entry_diff, TB_def, ...
    idx = {h: i for i, h in enumerate(header)}
    records = []
    for row in rows:
        def get(col):
            i = idx.get(col)
            return row[i].strip() if i is not None and i < len(row) else ""
        records.append({
            "entry": get("Entry"),
            "entry_orig": get("Entry_diff"),
        "def": get("TB_def"),
            "source": "KTB",
        })
    return records


def load_tsj():
    header, rows = read_tsv(REPO_ROOT / "TSJ_definitions.tsv")
    # TSJ2ID, Entry_word, SJ_def, SJ_remarks, ZhangLei_page
    idx = {h: i for i, h in enumerate(header)}
    records = []
    for row in rows:
        def get(col):
            i = idx.get(col)
            return row[i].strip() if i is not None and i < len(row) else ""
        records.append({
            "entry": get("Entry_word"),
            "entry_orig": "",
        "def": get("SJ_def"),
            "source": "TSJ",
        })
    return records


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HDIC 字書檢索 / HDIC Dictionary Search</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Noto Serif CJK TC", "Source Han Serif TC", "PMingLiU", serif;
    background: #faf8f3;
    color: #2c2c2c;
    min-height: 100vh;
  }
  header {
    background: #4a3728;
    color: #f5e6c8;
    padding: 18px 24px 14px;
  }
  header h1 { font-size: 1.5rem; letter-spacing: .05em; }
  header p  { font-size: .8rem; opacity: .75; margin-top: 4px; }
  .search-bar {
    background: #fff;
    border-bottom: 1px solid #ddd;
    padding: 14px 24px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 6px rgba(0,0,0,.08);
  }
  .search-bar input[type=text] {
    flex: 1 1 220px;
    min-width: 160px;
    padding: 7px 12px;
    border: 1px solid #b0a090;
    border-radius: 4px;
    font-size: 1rem;
    font-family: inherit;
    background: #fffef9;
  }
  .search-bar input[type=text]:focus {
    outline: 2px solid #8b5e3c;
    border-color: #8b5e3c;
  }
  .search-bar select {
    padding: 7px 10px;
    border: 1px solid #b0a090;
    border-radius: 4px;
    font-size: .92rem;
    font-family: inherit;
    background: #fffef9;
  }
  .filters {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 16px;
    align-items: center;
  }
  .filter-group { display: flex; gap: 6px; align-items: center; }
  .filter-group label {
    cursor: pointer;
    font-size: .88rem;
    display: flex;
    align-items: center;
    gap: 3px;
    white-space: nowrap;
  }
  .sep { color: #ccc; }
  .results-meta {
    padding: 8px 24px;
    font-size: .82rem;
    color: #888;
    min-height: 28px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: .92rem;
  }
  thead {
    background: #ede8e0;
    position: sticky;
    top: 90px;
    z-index: 50;
  }
  thead th {
    padding: 8px 12px;
    text-align: left;
    font-weight: bold;
    border-bottom: 2px solid #c4b8a8;
    white-space: nowrap;
  }
  tbody tr { border-bottom: 1px solid #e8e4dc; }
  tbody tr:hover { background: #f0ece4; }
  td { padding: 6px 12px; vertical-align: top; }
  .badge {
    display: inline-block;
    padding: 1px 7px;
    border-radius: 3px;
    font-size: .78rem;
    font-weight: bold;
    letter-spacing: .03em;
    white-space: nowrap;
  }
  .badge-SYP { background: #d4ecd4; color: #2a5e2a; }
  .badge-KTB { background: #d4e4f5; color: #1e3f6e; }
  .badge-TSJ { background: #f5e4d4; color: #6e3a1e; }
  .entry-cell { font-size: 1.15rem; font-weight: bold; min-width: 3em; }
  .def-cell { max-width: 600px; line-height: 1.6; word-break: break-all; }
  .src-cell { white-space: nowrap; }
  mark { background: #ffe066; border-radius: 2px; }
  #no-results {
    text-align: center;
    padding: 60px 24px;
    color: #aaa;
    font-size: 1.1rem;
    display: none;
  }
  #loading {
    text-align: center;
    padding: 60px;
    color: #888;
  }
  .truncated { opacity: .7; font-style: italic; font-size: .82rem; }
  footer {
    padding: 20px 24px;
    font-size: .78rem;
    color: #aaa;
    border-top: 1px solid #e0d8cc;
    margin-top: 12px;
  }
</style>
</head>
<body>
<header>
  <h1>HDIC 字書檢索</h1>
  <p>平安時代漢字字書総合データベース · Integrated Database of Hanzi Dictionaries in Early Japan</p>
</header>

<div class="search-bar">
  <label style="font-size:.88rem;display:flex;align-items:center;gap:4px;white-space:nowrap;">
    <input type="checkbox" id="entry-only" checked> 僅字頭
  </label>
  <input type="text" id="q" placeholder="輸入字頭或釋義關鍵詞…" autofocus autocomplete="off">
  <div class="filters">
    <label style="font-size:.85rem;color:#666;display:flex;align-items:center;gap:8px;">
      字書：
      <select id="src">
        <option value="ALL" selected>全部字書</option>
        <option value="SYP">宋本玉篇</option>
        <option value="KTB">篆隸萬象名義</option>
        <option value="TSJ">新撰字鏡</option>
      </select>
    </label>
  </div>
</div>

<div class="results-meta" id="meta"></div>

<div id="loading">資料載入中…</div>
<div id="no-results">未找到相關條目</div>

<div id="table-wrap" style="display:none">
<table>
  <thead>
    <tr>

      <th>字頭</th>
      <th>釋義</th>
    </tr>
  </thead>
  <tbody id="tbody"></tbody>
</table>
</div>

<footer>
  資料來源：HDIC Project · CC BY-SA 4.0 · ikeda.shoju@gmail.com<br>
  宋本玉篇 / 篆隸萬象名義（高山寺本）/ 新撰字鏡（天治本）
</footer>

<script>
const DATA = __DATA_JSON__;
const IDX_SOURCE = 0;
const IDX_ENTRY = 1;
const IDX_ENTRY_ORIG = 2;
const IDX_DEF = 3;

const SRC_LABEL = {
  SYP: '宋本玉篇',
  KTB: '篆隸萬象名義',
  TSJ: '新撰字鏡',
};

const MAX_RESULTS = 500;

let debounceTimer = null;

function esc(s) {
  return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function highlight(text, kw) {
  if (!kw) return esc(text);
  const safe = kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const re = new RegExp(safe, 'gi');
  return esc(text).replace(re, m => `<mark>${m}</mark>`);
}

function render() {
  const q = document.getElementById('q').value.trim();
  const entryOnly = document.getElementById('entry-only').checked;
  const src = document.getElementById('src').value;

  const loading = document.getElementById('loading');
  const tableWrap = document.getElementById('table-wrap');
  const noResults = document.getElementById('no-results');
  const meta = document.getElementById('meta');
  const tbody = document.getElementById('tbody');

  loading.style.display = 'none';

  if (!q) {
    tableWrap.style.display = 'none';
    noResults.style.display = 'none';
    meta.textContent = `共 ${DATA.length.toLocaleString()} 筆記錄（輸入關鍵詞開始檢索）`;
    return;
  }

  const ql = q.toLowerCase();

  const matches = [];
  for (let i = 0; i < DATA.length; i++) {
    const r = DATA[i];
    const source = r[IDX_SOURCE];
    const entry = (r[IDX_ENTRY] || '').toLowerCase();
    const entryOrig = (r[IDX_ENTRY_ORIG] || '').toLowerCase();
    const defText = r[IDX_DEF] || '';

    if (src !== 'ALL' && source !== src) continue;

    let hit = entry.includes(ql) || entryOrig.includes(ql);
    if (!hit && !entryOnly) {
      hit = defText.toLowerCase().includes(ql);
    }
    if (hit) matches.push(r);
    if (matches.length > MAX_RESULTS + 1) break;
  }

  const truncatedList = matches.length > MAX_RESULTS;
  const display = truncatedList ? matches.slice(0, MAX_RESULTS) : matches;

  if (display.length === 0) {
    tableWrap.style.display = 'none';
    noResults.style.display = 'block';
    meta.textContent = `未找到含「${q}」的條目`;
    return;
  }

  noResults.style.display = 'none';
  tableWrap.style.display = 'block';

  meta.innerHTML = truncatedList
    ? `顯示前 ${MAX_RESULTS} 筆（匹配超過 ${MAX_RESULTS} 筆，請縮小檢索範圍）`
    : `找到 <strong>${matches.length}</strong> 筆匹配記錄`;

  const rows = display.map(r => {
    const source = r[IDX_SOURCE];
    const entryText = r[IDX_ENTRY] || '';
    const entryOrigText = r[IDX_ENTRY_ORIG] || '';
    const defText = r[IDX_DEF] || '';
    const badge = `<span class="badge badge-${source}">${SRC_LABEL[source] || source}</span>`;
    const entryDisp = entryText || entryOrigText || '—';
    return `<tr>
      <td class="entry-cell">${highlight(entryDisp, q)}</td>
      <td class="def-cell">${badge} ${highlight(defText, q)}</td>
    </tr>`;
  }).join('');

  tbody.innerHTML = rows;
}

function scheduleRender() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(render, 220);
}

document.getElementById('q').addEventListener('input', scheduleRender);
document.getElementById('entry-only').addEventListener('change', render);
document.getElementById('src').addEventListener('change', render);

// Initial state
document.getElementById('loading').style.display = 'none';
render();
</script>
</body>
</html>
"""


def main():
    print("Loading SYP…", flush=True)
    syp = load_syp()
    print(f"  {len(syp)} records")

    print("Loading KTB…", flush=True)
    ktb = load_ktb()
    print(f"  {len(ktb)} records")

    print("Loading TSJ…", flush=True)
    tsj = load_tsj()
    print(f"  {len(tsj)} records")

    all_records = syp + ktb + tsj
    print(f"Total: {len(all_records)} records")

    packed_records = [
        [r["source"], r["entry"], r["entry_orig"], r["def"]]
        for r in all_records
    ]

    data_json = json.dumps(packed_records, ensure_ascii=False, separators=(",", ":"))
    html = HTML_TEMPLATE.replace("__DATA_JSON__", data_json)

    out_path = REPO_ROOT / "hdic_search.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"\nGenerated: {out_path}")
    print(f"File size: {out_path.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
