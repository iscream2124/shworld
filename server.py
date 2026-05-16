#!/usr/bin/env python3
"""
File Search — Everything-like web UI
Run:  python3 ~/.search/server.py
Open: http://127.0.0.1:7070
"""
import json
import os
import sqlite3
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.db")

HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>File Search</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden}
body{
  font-family:-apple-system,BlinkMacSystemFont,"Helvetica Neue",sans-serif;
  font-size:13px;
  background:#1c1c1e;
  color:#d1d1d1;
  display:flex;
  flex-direction:column;
}
#topbar{
  display:flex;
  align-items:center;
  gap:10px;
  padding:10px 14px;
  background:#252527;
  border-bottom:1px solid #3a3a3c;
  flex-shrink:0;
}
#q{
  flex:1;
  background:#3a3a3c;
  border:1px solid #555;
  border-radius:7px;
  color:#fff;
  font-size:15px;
  padding:7px 12px;
  outline:none;
  transition:border-color .15s;
}
#q:focus{border-color:#0a84ff}
#q::placeholder{color:#666}
#status{
  font-size:12px;
  color:#888;
  white-space:nowrap;
  min-width:170px;
  text-align:right;
}
.scroll{flex:1;overflow-y:auto}
table{width:100%;border-collapse:collapse}
thead th{
  position:sticky;top:0;
  background:#252527;
  border-bottom:1px solid #3a3a3c;
  padding:6px 12px;
  text-align:left;
  color:#888;
  font-weight:500;
  user-select:none;
}
tbody tr{border-bottom:1px solid #28282a;cursor:default}
tbody tr:hover{background:#2c2c2e}
tbody tr.active{background:#0a3a6e}
td{padding:4px 12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.col-name{width:260px;max-width:260px;color:#e8e8e8;font-weight:500}
.col-type{width:48px;max-width:48px;text-align:center}
.col-path{color:#aaa}
.col-date{width:155px;max-width:155px;color:#777;text-align:right}
#empty{
  display:none;
  align-items:center;
  justify-content:center;
  color:#555;
  padding:60px 0;
  font-size:14px;
}
::-webkit-scrollbar{width:8px}
::-webkit-scrollbar-track{background:#1c1c1e}
::-webkit-scrollbar-thumb{background:#3a3a3c;border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:#48484a}
</style>
</head>
<body>
<div id="topbar">
  <input id="q" type="text" placeholder="파일 이름 검색..." autofocus spellcheck="false">
  <div id="status">입력하여 검색</div>
</div>
<div class="scroll">
  <table id="tbl">
    <thead>
      <tr>
        <th class="col-name">이름</th>
        <th class="col-type">유형</th>
        <th class="col-path">경로</th>
        <th class="col-date">수정일</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
  <div id="empty">검색 결과가 없습니다</div>
</div>

<script>
const qEl = document.getElementById('q');
const tbody = document.getElementById('tbody');
const status = document.getElementById('status');
const empty = document.getElementById('empty');
let timer, activeIdx = -1;

function fmt(ts) {
  if (!ts) return '';
  const d = new Date(ts * 1000);
  return d.toLocaleDateString('ko-KR', {year:'numeric',month:'2-digit',day:'2-digit'})
       + ' ' + d.toLocaleTimeString('ko-KR', {hour:'2-digit',minute:'2-digit',hour12:false});
}

function render(rows, ms) {
  tbody.innerHTML = '';
  activeIdx = -1;
  if (!rows.length) {
    empty.style.display = 'flex';
    status.textContent = '결과 없음';
    return;
  }
  empty.style.display = 'none';
  const frag = document.createDocumentFragment();
  rows.forEach((r, i) => {
    const tr = document.createElement('tr');
    const icon = r.type === 'd' ? '📁' : '📄';
    tr.innerHTML =
      `<td class="col-name" title="${escHtml(r.name)}">${escHtml(r.name)}</td>` +
      `<td class="col-type">${icon}</td>` +
      `<td class="col-path" title="${escHtml(r.path)}">${escHtml(r.path)}</td>` +
      `<td class="col-date">${fmt(r.mtime)}</td>`;
    tr.onclick = () => setActive(i);
    tr.ondblclick = () => openPath(r.path);
    frag.appendChild(tr);
  });
  tbody.appendChild(frag);
  status.textContent = `${rows.length.toLocaleString()}개 결과 · ${ms}ms`;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function setActive(i) {
  const rows = tbody.rows;
  if (activeIdx >= 0 && rows[activeIdx]) rows[activeIdx].classList.remove('active');
  activeIdx = i;
  if (rows[i]) {
    rows[i].classList.add('active');
    rows[i].scrollIntoView({block: 'nearest'});
  }
}

async function openPath(path) {
  await fetch('/api/open?path=' + encodeURIComponent(path));
}

async function doSearch(val) {
  if (!val.trim()) {
    status.textContent = '입력하여 검색';
    tbody.innerHTML = '';
    empty.style.display = 'none';
    return;
  }
  status.textContent = '검색 중…';
  try {
    const res = await fetch('/api/search?q=' + encodeURIComponent(val));
    const data = await res.json();
    render(data.results, data.time_ms);
  } catch {
    status.textContent = '오류 발생';
  }
}

qEl.addEventListener('input', e => {
  clearTimeout(timer);
  timer = setTimeout(() => doSearch(e.target.value), 150);
});

document.addEventListener('keydown', e => {
  const rows = tbody.rows;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    setActive(Math.min(activeIdx + 1, rows.length - 1));
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    setActive(Math.max(activeIdx - 1, 0));
  } else if (e.key === 'Enter') {
    if (activeIdx >= 0 && rows[activeIdx]) {
      openPath(rows[activeIdx].cells[2].title);
    }
  } else if (e.key === 'Escape') {
    qEl.value = '';
    doSearch('');
    qEl.focus();
  }
});
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif parsed.path == "/api/search":
            params = parse_qs(parsed.query)
            q_val = params.get("q", [""])[0].strip()
            limit = min(int(params.get("limit", ["500"])[0]), 2000)
            t0 = time.monotonic()
            results = _search(q_val, limit) if q_val else []
            elapsed = round((time.monotonic() - t0) * 1000, 1)
            self.send_json({"results": results, "count": len(results), "time_ms": elapsed})

        elif parsed.path == "/api/open":
            params = parse_qs(parsed.query)
            path = params.get("path", [""])[0]
            if path and os.path.exists(path):
                subprocess.run(["open", "-R", path], check=False)
            self.send_json({"ok": True})

        else:
            self.send_error(404)

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # suppress per-request logs


def _search(q, limit):
    if not os.path.exists(DB_PATH):
        return []
    try:
        con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        return []
    try:
        # Prefix match uses idx_name — fast
        prefix = con.execute(
            "SELECT name, path, type, mtime FROM files WHERE name LIKE ? LIMIT ?",
            (f"{q}%", limit),
        ).fetchall()

        if len(prefix) >= limit:
            return [_row(r) for r in prefix]

        # Substring fallback for remaining slots
        seen = {r[1] for r in prefix}
        remaining = limit - len(prefix)
        substr = con.execute(
            "SELECT name, path, type, mtime FROM files "
            "WHERE name LIKE ? AND name NOT LIKE ? LIMIT ?",
            (f"%{q}%", f"{q}%", remaining),
        ).fetchall()

        return [_row(r) for r in prefix] + [_row(r) for r in substr if r[1] not in seen]
    except sqlite3.OperationalError:
        return []
    finally:
        con.close()


def _row(r):
    return {"name": r[0], "path": r[1], "type": r[2], "mtime": r[3]}


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7070
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"File Search → http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
