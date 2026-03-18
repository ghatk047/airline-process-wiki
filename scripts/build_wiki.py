#!/usr/bin/env python3
"""
build_wiki.py — Generate wiki HTML page for a completed subprocess.

Usage:
    python3 build_wiki.py --process-id NP-SP-03

Reads:  data/processes.json  (full process list + L4 steps for target)
Writes: wiki/<l1-slug>/<l2-slug>/<pid>/index.html
        Updates wiki/<l1-slug>/<l2-slug>/index.html  (L2 landing page)

The script reads the current sidebar structure from all existing
processes.json entries that are Complete or Queued, so the sidebar
always reflects the full taxonomy.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import date
from html import escape

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent
REPO_DIR     = SCRIPT_DIR.parent
DATA_DIR     = REPO_DIR / "data"
WIKI_DIR     = REPO_DIR / "wiki"
PROCESSES    = DATA_DIR / "processes.json"
IMG_DIR      = WIKI_DIR / "assets" / "img"

# ── Status helpers ─────────────────────────────────────────────────────────
STATUS_DOT = {
    "Complete":    '<span class="status-dot status-done"></span>',
    "In Progress": '<span class="status-dot status-wip"></span>',
    "Queued":      '<span class="status-dot status-queue"></span>',
}

def status_dot(status):
    return STATUS_DOT.get(status, STATUS_DOT["Queued"])

# ── Sidebar builder ────────────────────────────────────────────────────────
def build_sidebar(all_procs, active_pid, depth=3):
    """
    Returns an HTML string for the <nav class="sidebar"> content.
    depth = number of '../' needed to reach wiki root from current page.
    """
    root = "../" * depth
    lines = []

    # Group by L1 → L2 → processes
    from collections import defaultdict, OrderedDict
    l1_groups = OrderedDict()
    for p in all_procs:
        l1 = p["l1_domain"]
        l2 = p["l2_process"]
        if l1 not in l1_groups:
            l1_groups[l1] = OrderedDict()
        if l2 not in l1_groups[l1]:
            l1_groups[l1][l2] = []
        l1_groups[l1][l2].append(p)

    for l1_name, l2_dict in l1_groups.items():
        # Is this section active?
        active_in_l1 = any(
            p["id"] == active_pid
            for procs in l2_dict.values()
            for p in procs
        )
        open_class = " open" if active_in_l1 else ""

        # Derive L1 slug from first process in group
        first_proc = next(iter(next(iter(l2_dict.values()))))
        l1_slug = first_proc["l1_slug"]

        lines.append(f'  <div class="sidebar-section">')
        lines.append(f'    <div class="sidebar-domain{open_class}"><span>{escape(l1_name)}</span><span class="chevron">▶</span></div>')
        lines.append(f'    <div class="sidebar-l2{open_class}">')

        for l2_name, procs in l2_dict.items():
            l2_slug = procs[0]["l2_slug"]
            active_in_l2 = any(p["id"] == active_pid for p in procs)
            lines.append(f'      <a class="sidebar-l2-link" href="{root}{l1_slug}/{l2_slug}/">{escape(l2_name)}</a>')
            lines.append(f'      <div class="sidebar-l3">')
            for p in procs:
                active_cls = " active" if p["id"] == active_pid else ""
                dot = status_dot(p["status"])
                pid_lower = p["id"].lower()
                lines.append(
                    f'        <a class="sidebar-l3-link{active_cls}" '
                    f'href="{root}{l1_slug}/{l2_slug}/{pid_lower}/">'
                    f'{dot}<span class="pid">{p["id"]}</span>{escape(p["l3_name"])}</a>'
                )
            lines.append(f'      </div>')

        lines.append(f'    </div>')
        lines.append(f'  </div>')

    return "\n".join(lines)

# ── L4 table builder ───────────────────────────────────────────────────────
def build_l4_table(steps):
    if not steps:
        return '<p class="no-steps">L4 steps not yet generated for this subprocess.</p>'

    rows = []
    for s in steps:
        dp = "✓" if s.get("decision_point", "N") == "Y" else ""
        ex = "✓" if s.get("exception", "N") == "Y" else ""
        rows.append(f"""      <tr>
        <td class="step-num">{escape(str(s.get('step','')))}
        <td>{escape(s.get('name',''))}</td>
        <td>{escape(s.get('role',''))}</td>
        <td class="mono">{escape(s.get('system',''))}</td>
        <td>{escape(s.get('input',''))}</td>
        <td>{escape(s.get('output',''))}</td>
        <td>{escape(s.get('kpi',''))}</td>
        <td class="pain">{escape(s.get('pain_point',''))}</td>
        <td class="centre">{dp}</td>
        <td class="centre">{ex}</td>
      </tr>""")
    return """    <div class="table-wrapper">
    <table class="l4-table">
      <thead>
        <tr>
          <th>Step</th><th>L4 Step Name</th><th>Role</th><th>System</th>
          <th>Input</th><th>Output</th><th>KPI</th>
          <th>Pain Point / Risk</th><th>Decision</th><th>Exception</th>
        </tr>
      </thead>
      <tbody>
""" + "\n".join(rows) + """
      </tbody>
    </table>
    </div>"""

# ── BPMN section ───────────────────────────────────────────────────────────
def build_bpmn_section(pid, depth=3):
    root   = "../" * depth
    img_rel = f"{root}assets/img/{pid.lower()}.png"
    mmdc_cmd = (
        f"mmdc -i diagrams/{pid.lower()}.mmd "
        f"-o wiki/assets/img/{pid.lower()}.png "
        f"-w 1920 -H 1080 --scale 2 --backgroundColor white"
    )
    img_path = IMG_DIR / f"{pid.lower()}.png"
    if img_path.exists():
        return f"""    <div class="bpmn-container" id="bpmnContainer">
      <img src="{img_rel}" alt="BPMN diagram for {pid}" class="bpmn-img" id="bpmnImg"
           onclick="openLightbox(this.src)">
      <p class="bpmn-hint">Click to enlarge · Scroll to zoom · Drag to pan</p>
    </div>"""
    else:
        return f"""    <div class="bpmn-placeholder">
      <p>BPMN diagram not yet generated.</p>
      <code>{mmdc_cmd}</code>
    </div>"""

# ── Main page generator ────────────────────────────────────────────────────
def generate_page(proc, all_procs):
    pid    = proc["id"]
    l1     = proc["l1_domain"]
    l2     = proc["l2_process"]
    l3     = proc["l3_name"]
    status = proc["status"]
    steps  = proc.get("l4_steps", [])
    l1s    = proc["l1_slug"]
    l2s    = proc["l2_slug"]

    run_date = proc.get("run_date") or date.today().isoformat()
    n_steps  = len(steps)
    n_gates  = sum(1 for s in steps if s.get("decision_point") == "Y")

    # Output path
    out_dir = WIKI_DIR / l1s / l2s / pid.lower()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index.html"

    sidebar_html = build_sidebar(all_procs, active_pid=pid, depth=3)
    l4_table     = build_l4_table(steps)
    bpmn_section = build_bpmn_section(pid, depth=3)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{pid} · {escape(l3)} · Airlines Process Wiki</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../../../assets/css/wiki.css">
</head>
<body>
<header class="topbar">
  <a href="../../../" class="topbar-logo">Airlines <span>Process Wiki</span></a>
  <span class="topbar-badge">v1.0</span>
  <div class="topbar-right">
    <input type="text" id="searchBox" class="search-box" placeholder="Search processes… (/)" autocomplete="off">
    <a href="../../../">Home</a>
    <a href="../../../{l1s}/">{escape(l1)}</a>
    <a href="https://github.com/ghatk047/airline-process-wiki" class="gh-btn" target="_blank">⭐ GitHub</a>
  </div>
</header>
<nav class="sidebar" id="sidebar">
{sidebar_html}
</nav>
<button class="sidebar-toggle" id="sidebarToggle" title="Toggle sidebar">◀</button>
<main class="content" id="mainContent">
  <nav class="breadcrumb">
    <a href="../../../">Home</a> ›
    <a href="../../../{l1s}/">{escape(l1)}</a> ›
    <a href="../../../{l1s}/{l2s}/">{escape(l2)}</a> ›
    <span>{pid}</span>
  </nav>

  <div class="process-header">
    <div class="process-meta">
      <span class="pid-badge">{pid}</span>
      {status_dot(status)}
      <span class="status-label">{status}</span>
    </div>
    <h1>{escape(l3)}</h1>
    <div class="process-tags">
      <span class="tag tag-l1">{escape(l1)}</span>
      <span class="tag tag-l2">{escape(l2)}</span>
      <span class="tag">{n_steps} steps</span>
      <span class="tag">{n_gates} decision gates</span>
      <span class="tag">Updated {run_date}</span>
    </div>
  </div>

  <section class="section" id="bpmn">
    <h2>BPMN Process Flow</h2>
{bpmn_section}
  </section>

  <section class="section" id="l4">
    <h2>L4 Step Detail</h2>
{l4_table}
  </section>
</main>

<!-- Lightbox -->
<div id="lightbox" class="lightbox" onclick="closeLightbox()">
  <div class="lightbox-close" onclick="closeLightbox()">✕</div>
  <img id="lightboxImg" src="" alt="BPMN diagram">
</div>

<div id="searchResults" class="search-results" style="display:none"></div>

<script src="../../../assets/js/wiki.js"></script>
</body>
</html>
"""
    out_file.write_text(html, encoding="utf-8")
    print(f"  ↳ Wiki page: {out_file}")
    return out_file


# ── Entry point ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate wiki HTML page for a subprocess")
    parser.add_argument("--process-id", required=True, help="e.g. NP-SP-03")
    args = parser.parse_args()

    with open(PROCESSES) as f:
        data = json.load(f)

    all_procs = data["processes"]
    target    = next((p for p in all_procs if p["id"] == args.process_id), None)

    if not target:
        print(f"ERROR: Process ID '{args.process_id}' not found in processes.json")
        sys.exit(1)

    print(f"\n🌐 Generating wiki page for {args.process_id}...")
    out = generate_page(target, all_procs)
    print(f"✅ Done: {out}")


if __name__ == "__main__":
    main()
