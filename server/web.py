#!/usr/bin/env python3
"""
ops-mcp web dashboard — fleet status and tool call audit log.

Reads hosts.yaml for the fleet; queries all hosts in parallel.
Secrets loaded from /opt/ops-mcp/.env at startup.

Run: /opt/ops-mcp/.venv/bin/python3 /opt/ops-mcp/web.py
"""

import json
import os
import shlex
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Load .env before anything else
_ENV_FILE = Path(os.environ.get("OPS_ENV_FILE", "/opt/ops-mcp/.env"))
if _ENV_FILE.exists():
    for _line in _ENV_FILE.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            os.environ.setdefault(_k.strip(), _v.strip())

import yaml
from flask import Flask, Response, jsonify

sys.path.insert(0, "/opt/ops-mcp")
from state import init_db, recent_calls  # noqa: E402

app = Flask(__name__)

# Load fleet config
_HOSTS_FILE = Path(os.environ.get("OPS_HOSTS_FILE", "/opt/ops-mcp/hosts.yaml"))
FLEET: dict = {}
if _HOSTS_FILE.exists():
    FLEET = yaml.safe_load(_HOSTS_FILE.read_text()).get("fleet", {})


def _run(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return 1, str(e)


def _run_on(host: str, cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    cfg = FLEET.get(host, {})
    ssh_addr = cfg.get("ssh")
    if ssh_addr is None:
        return _run(cmd, timeout)
    user = cfg.get("user", "")
    target = f"{user}@{ssh_addr}" if user else ssh_addr
    ssh_cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no"]
    if cfg.get("identity_file"):
        ssh_cmd += ["-i", cfg["identity_file"]]
    ssh_cmd += [target, shlex.join(cmd)]
    return _run(ssh_cmd, timeout + 6)


def _query_host(hostname: str) -> tuple[str, dict]:
    try:
        rc, out = _run_on(hostname, ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"])
        containers = []
        if rc == 0:
            for line in out.splitlines():
                p = line.split("\t", 1)
                if len(p) == 2 and not any(w in line for w in ["Authorised", "monitored", "prohibited"]):
                    containers.append({"name": p[0], "status": p[1]})

        rc2, disk_out = _run_on(hostname, ["df", "-h", "/", "--output=pcent"])
        disk_pct = "?"
        if rc2 == 0:
            for line in disk_out.splitlines():
                val = line.strip().rstrip("%")
                if val.isdigit():
                    disk_pct = val
                    break

        rc3, mem_out = _run_on(hostname, ["free", "-m"])
        ram: dict = {}
        for line in mem_out.splitlines():
            if line.startswith("Mem:"):
                p = line.split()
                if len(p) >= 3:
                    total, used = int(p[1]), int(p[2])
                    ram = {"total_mb": total, "used_mb": used, "pct": round(used / total * 100)}

        rc4, up_out = _run_on(hostname, ["uptime", "-p"])
        uptime = "?"
        if rc4 == 0:
            for line in up_out.splitlines():
                if line.strip().startswith("up "):
                    uptime = line.strip()
                    break

        return hostname, {
            "ok": True,
            "containers": containers,
            "container_count": len(containers),
            "up_count": sum(1 for c in containers if c["status"].startswith("Up")),
            "disk_pct": disk_pct,
            "ram": ram,
            "uptime": uptime,
        }
    except Exception as e:
        return hostname, {"ok": False, "error": str(e), "containers": []}


HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>fleet ops</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       font-size: 14px; background: #f1f5f9; color: #1e293b; }
header { background: #0f172a; color: #f8fafc; padding: 12px 24px;
         display: flex; align-items: center; justify-content: space-between;
         position: sticky; top: 0; z-index: 10; }
header h1 { font-size: 15px; font-weight: 700; }
#conn { font-size: 12px; display: flex; align-items: center; gap: 6px; color: #94a3b8; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; display: inline-block; }
.dot.stale { background: #f59e0b; }
.page { padding: 16px 24px; max-width: 1600px; margin: 0 auto; }

/* Fleet strip — compact, one row per host */
#fleet-strip { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.host-pill { background: white; border: 1px solid #e2e8f0; border-radius: 10px;
             flex: 1; min-width: 220px; overflow: hidden; }
.host-pill.error { border-color: #fca5a5; }
.pill-header { padding: 8px 14px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
               display: flex; align-items: center; justify-content: space-between; cursor: pointer;
               user-select: none; }
.pill-header:hover { background: #f1f5f9; }
.host-name { font-size: 13px; font-weight: 700; color: #0f172a; }
.pill-stats { display: flex; gap: 14px; font-size: 11px; color: #64748b; }
.pill-stat { display: flex; flex-direction: column; align-items: center; }
.pill-stat-val { font-size: 15px; font-weight: 800; color: #0f172a; line-height: 1; }
.pill-stat-lbl { font-size: 9px; text-transform: uppercase; letter-spacing: 0.4px; color: #94a3b8; margin-top: 2px; }
.toggle-btn { font-size: 11px; color: #6366f1; font-weight: 600; white-space: nowrap; padding-left: 10px; }
.container-panel { display: none; padding: 10px 14px; border-top: 1px solid #f1f5f9; }
.container-panel.open { display: block; }
.container-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 5px; }
.ccard { border-radius: 5px; padding: 5px 9px; border: 1px solid; }
.ccard.up   { background: #f0fdf4; border-color: #86efac; }
.ccard.down { background: #fef2f2; border-color: #fca5a5; }
.ccard.other{ background: #fefce8; border-color: #fde047; }
.cname { font-weight: 600; font-size: 11px; word-break: break-all; color: #0f172a; }
.cstatus { font-size: 10px; color: #64748b; margin-top: 1px; }

/* Audit log */
.card-full { background: white; border: 1px solid #e2e8f0; border-radius: 10px;
             overflow: hidden; margin-bottom: 16px; }
.card-header { padding: 11px 16px; border-bottom: 1px solid #e2e8f0; font-size: 11px;
               font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.6px;
               background: #f8fafc; display: flex; align-items: center; justify-content: space-between; }
table { width: 100%; border-collapse: collapse; }
th { padding: 9px 12px; background: #f8fafc; border-bottom: 2px solid #e2e8f0;
     font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
     color: #64748b; text-align: left; white-space: nowrap; }
td { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr.blocked td { background: #fff5f5; }
.mono { font-family: 'SF Mono', Consolas, Monaco, monospace; }
.tool-name { font-weight: 700; font-size: 12px; }
.args-cell { font-size: 11px; color: #475569; max-width: 220px; overflow: hidden;
             text-overflow: ellipsis; white-space: nowrap; }
.result-cell { font-size: 11px; color: #64748b; max-width: 260px; overflow: hidden;
               text-overflow: ellipsis; white-space: nowrap; }
.ts-cell { font-size: 11px; color: #94a3b8; white-space: nowrap; }
.dur-cell { font-size: 11px; color: #94a3b8; white-space: nowrap; text-align: right; }
.host-cell { font-size: 11px; color: #6366f1; font-weight: 600; }
.badge { display: inline-block; border-radius: 9999px; padding: 2px 8px;
         font-size: 10px; font-weight: 700; }
.badge-ok      { background: #dcfce7; color: #15803d; }
.badge-blocked { background: #fee2e2; color: #b91c1c; }
.empty { padding: 32px; text-align: center; color: #94a3b8; font-size: 13px; }
</style>
</head>
<body>
<header>
  <h1>&#9670; fleet ops</h1>
  <span id="conn"><span class="dot" id="dot"></span><span id="conn-text">connecting...</span></span>
</header>
<div class="page">
  <div id="fleet-strip"></div>

  <div class="card-full">
    <div class="card-header">
      <span>Tool Call Audit Log</span>
      <span id="call-count" style="font-size:11px;color:#94a3b8;font-weight:400;text-transform:none;letter-spacing:0"></span>
    </div>
    <div style="overflow-x: auto;">
      <table>
        <thead>
          <tr>
            <th>Time (UTC)</th>
            <th>Host</th>
            <th>Tool</th>
            <th>Args</th>
            <th>Result</th>
            <th style="text-align:right">ms</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody id="log-body">
          <tr><td colspan="7" class="empty">No tool calls yet — connect Claude Code to the ops MCP server</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
<script>
function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function renderHost(name, d) {
  if (!d.ok) {
    return `<div class="host-pill error">
      <div class="pill-header"><span class="host-name">${esc(name)}</span>
      <span style="color:#b91c1c;font-size:11px;">${esc(d.error||'unreachable')}</span></div>
    </div>`;
  }
  const ram = d.ram || {};
  const uptime = (d.uptime||'—').replace('up ','');
  const running = d.up_count || 0;
  const total = d.container_count || 0;
  const id = 'panel-' + name.replace(/[^a-z0-9]/gi,'_');

  const containers = (d.containers||[]).map(c => {
    const st = c.status||'';
    const cls = st.startsWith('Up') ? 'up' : st.startsWith('Exited') ? 'down' : 'other';
    return `<div class="ccard ${cls}"><div class="cname">${esc(c.name)}</div><div class="cstatus">${esc(st)}</div></div>`;
  }).join('');

  return `<div class="host-pill">
    <div class="pill-header" onclick="togglePanel('${id}')">
      <span class="host-name">${esc(name)}</span>
      <div style="display:flex;align-items:center;gap:16px;">
        <div class="pill-stats">
          <div class="pill-stat"><span class="pill-stat-val">${esc(d.disk_pct||'?')}%</span><span class="pill-stat-lbl">disk</span></div>
          <div class="pill-stat"><span class="pill-stat-val">${ram.pct != null ? ram.pct+'%' : '—'}</span><span class="pill-stat-lbl">ram</span></div>
          <div class="pill-stat"><span class="pill-stat-val">${running}/${total}</span><span class="pill-stat-lbl">containers</span></div>
          <div class="pill-stat"><span class="pill-stat-val" style="font-size:11px;">${esc(uptime)}</span><span class="pill-stat-lbl">uptime</span></div>
        </div>
        <span class="toggle-btn" id="btn-${id}">▸ show</span>
      </div>
    </div>
    <div class="container-panel" id="${id}">
      <div class="container-grid">${containers||'<div class="empty">No containers</div>'}</div>
    </div>
  </div>`;
}

function togglePanel(id) {
  const panel = document.getElementById(id);
  const btn = document.getElementById('btn-' + id);
  const open = panel.classList.toggle('open');
  btn.textContent = open ? '▾ hide' : '▸ show';
}

async function loadFleet() {
  try {
    const r = await fetch('/api/fleet');
    if (!r.ok) throw new Error(r.status);
    const fleet = await r.json();
    // Preserve open/closed state across refreshes
    const openPanels = new Set(
      [...document.querySelectorAll('.container-panel.open')].map(el => el.id)
    );
    document.getElementById('fleet-strip').innerHTML =
      Object.entries(fleet).map(([name, data]) => renderHost(name, data)).join('');
    openPanels.forEach(id => {
      const panel = document.getElementById(id);
      if (panel) {
        panel.classList.add('open');
        const btn = document.getElementById('btn-' + id);
        if (btn) btn.textContent = '▾ hide';
      }
    });
    setConn(true);
  } catch(e) { setConn(false); }
}

async function loadCalls() {
  try {
    const r = await fetch('/api/calls');
    if (!r.ok) throw new Error(r.status);
    const calls = await r.json();
    document.getElementById('call-count').textContent = calls.length ? `${calls.length} recent` : '';
    const tbody = document.getElementById('log-body');
    if (!calls.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty">No tool calls yet — connect Claude Code to the ops MCP server</td></tr>';
      return;
    }
    tbody.innerHTML = calls.map(c => {
      let args = '';
      try {
        const a = JSON.parse(c.args_json||'{}');
        args = Object.entries(a).map(([k,v]) => `${k}=${JSON.stringify(v)}`).join(' ');
      } catch(_) {}
      const result = String(c.result_json||'').substring(0,120);
      const ts = (c.ts||'').replace('T',' ').substring(0,19);
      const allowed = c.allowed !== 0;
      const badge = allowed
        ? '<span class="badge badge-ok">ok</span>'
        : '<span class="badge badge-blocked">blocked</span>';
      return `<tr class="${allowed?'':'blocked'}">
        <td class="ts-cell">${esc(ts)}</td>
        <td class="host-cell mono">${esc(c.host||'—')}</td>
        <td><span class="tool-name mono">${esc(c.tool)}</span></td>
        <td><span class="args-cell mono" title="${esc(args)}">${esc(args)}</span></td>
        <td><span class="result-cell" title="${esc(result)}">${esc(result)}</span></td>
        <td class="dur-cell">${c.duration_ms||0}</td>
        <td>${badge}</td>
      </tr>`;
    }).join('');
  } catch(e) { console.error('calls error', e); }
}

function setConn(ok) {
  document.getElementById('dot').className = 'dot' + (ok ? '' : ' stale');
  document.getElementById('conn-text').textContent = ok
    ? 'live · ' + new Date().toLocaleTimeString() : 'error';
}

loadFleet();
loadCalls();
setInterval(loadFleet, 15000);
setInterval(loadCalls, 5000);
</script>
</body>
</html>"""


@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")


@app.route("/api/fleet")
def api_fleet():
    results = {}
    with ThreadPoolExecutor(max_workers=max(len(FLEET), 1)) as ex:
        futures = {ex.submit(_query_host, h): h for h in FLEET}
        for future in futures:
            hostname, result = future.result()
            results[hostname] = result
    return jsonify(results)


@app.route("/api/calls")
def api_calls():
    return jsonify(recent_calls(50))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=7770, debug=False)
