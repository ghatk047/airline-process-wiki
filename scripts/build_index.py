#!/usr/bin/env python3
"""
build_index.py — Regenerate index.html from processes.json.
Run after each pipeline batch to keep home page counts accurate.
Usage: python3 scripts/build_index.py
"""
import json, sys
from pathlib import Path
from collections import OrderedDict
from datetime import datetime
from html import escape

SCRIPT_DIR = Path(__file__).parent
REPO_DIR   = SCRIPT_DIR.parent
PROCESSES  = REPO_DIR / "data" / "processes.json"
OUT_FILE   = REPO_DIR / "index.html"

with open(PROCESSES) as f:
    procs = json.load(f)["processes"]

# Group by L1 → L2
l1_groups = OrderedDict()
for p in procs:
    l1s = p["l1_slug"]; l2s = p["l2_slug"]
    if l1s not in l1_groups:
        l1_groups[l1s] = {"name": p["l1_domain"], "l2s": OrderedDict(), "total": 0, "complete": 0}
    if l2s not in l1_groups[l1s]["l2s"]:
        l1_groups[l1s]["l2s"][l2s] = {"name": p["l2_process"], "procs": []}
    l1_groups[l1s]["l2s"][l2s]["procs"].append(p)
    l1_groups[l1s]["total"] += 1
    if p["status"] == "Complete":
        l1_groups[l1s]["complete"] += 1

total_all    = len(procs)
complete_all = sum(1 for p in procs if p["status"] == "Complete")
queued_all   = sum(1 for p in procs if p["status"] == "Queued")
now_str      = datetime.now().strftime("%Y-%m-%d %H:%M")

def sidebar():
    lines = []
    for l1s, l1d in l1_groups.items():
        lines += [
            f'  <div class="sidebar-section">',
            f'    <div class="sidebar-domain"><span>{escape(l1d["name"])}</span><span class="chevron">▶</span></div>',
            f'    <div class="sidebar-l2">',
        ]
        for l2s, l2d in l1d["l2s"].items():
            lines.append(f'      <a class="sidebar-l2-link" href="./{l1s}/{l2s}/">{escape(l2d["name"])}</a>')
            lines.append(f'      <div class="sidebar-l3">')
            for p in l2d["procs"]:
                dot = "status-done" if p["status"]=="Complete" else "status-wip" if p["status"]=="In Progress" else "status-queue"
                lines.append(
                    f'        <a class="sidebar-l3-link" href="./{l1s}/{l2s}/{p["id"].lower()}/">'
                    f'<span class="status-dot {dot}"></span>'
                    f'<span class="pid">{p["id"]}</span>{escape(p["l3_name"])}</a>'
                )
            lines.append(f'      </div>')
        lines += [f'    </div>', f'  </div>']
    return "\n".join(lines)

def cards():
    out = []
    for l1s, l1d in l1_groups.items():
        n_l2 = len(l1d["l2s"])
        out.append(f"""<div class="domain-card">
  <div class="domain-card-hdr"><h3>{escape(l1d["name"])}</h3><p>Airlines · {n_l2} process groups</p></div>
  <div class="domain-card-body">
    <div class="domain-card-stat">{l1d["complete"]} of {l1d["total"]} subprocesses complete</div>
    <a class="domain-card-link" href="{l1s}/">Explore domain →</a>
  </div>
</div>""")
    return "".join(out)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Airlines Process Wiki — SAP Consulting</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="./assets/css/wiki.css">
</head>
<body>
<header class="topbar">
  <a href="./" class="topbar-logo">Airlines <span>Process Wiki</span></a>
  <span class="topbar-badge">v1.0</span>
  <div class="topbar-right">
    <input type="text" id="searchBox" class="search-box" placeholder="Search processes… (/)" autocomplete="off">
    <a href="./">Home</a>
    <a href="https://github.com/ghatk047/airline-process-wiki" class="gh-btn" target="_blank">⭐ GitHub</a>
  </div>
</header>
<nav class="sidebar" id="sidebar">
{sidebar()}
</nav>
<button class="sidebar-toggle" id="sidebarToggle" title="Toggle sidebar">◀</button>
<main class="main">
<div class="hero">
  <div class="hero-eyebrow">SAP Consulting · Process Catalog</div>
  <h1>Airlines Process Wiki</h1>
  <p>End-to-end L1 → L2 → L3 → L4 process documentation for airline verticals.
  Each subprocess includes BPMN flow diagrams, L4 step tables, swim lanes,
  system landscape, KPIs, and airline-specific risk analysis.</p>
  <div class="hero-stats">
    <span style="background:rgba(255,255,255,.15);color:#fff;padding:4px 14px;border-radius:4px;font-size:11px;font-weight:600">✅ {complete_all} subprocesses complete</span>
    <span style="background:rgba(255,255,255,.12);color:#fff;padding:4px 14px;border-radius:4px;font-size:11px">⏳ {queued_all} queued</span>
    <span style="background:rgba(255,255,255,.12);color:#fff;padding:4px 14px;border-radius:4px;font-size:11px">📋 L4 step detail included</span>
    <span style="background:rgba(255,255,255,.10);color:rgba(255,255,255,.7);padding:4px 14px;border-radius:4px;font-size:10px">Updated {now_str}</span>
  </div>
</div>
<div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:#6b7280;margin-bottom:12px">L1 Domains</div>
<div class="domain-grid">
{cards()}
</div>
</main>
<script src="./assets/js/wiki.js"></script>
</body>
</html>"""

OUT_FILE.write_text(html, encoding="utf-8")
print(f"✅ index.html regenerated — {complete_all} complete · {queued_all} queued · {total_all} total")
