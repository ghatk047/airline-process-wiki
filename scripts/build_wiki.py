#!/usr/bin/env python3
"""
build_wiki.py — Generate wiki HTML matching the NP-SP-01/02 template exactly.
Usage: python3 build_wiki.py --process-id NP-SP-03
"""
import argparse, json, sys
from pathlib import Path
from datetime import datetime
from html import escape
from collections import OrderedDict

SCRIPT_DIR = Path(__file__).parent
REPO_DIR   = SCRIPT_DIR.parent
DATA_DIR   = REPO_DIR / "data"
PROCESSES  = DATA_DIR / "processes.json"
IMG_DIR    = REPO_DIR / "assets" / "img"

# ── System tag classifier ──────────────────────────────────────────
def stag(system):
    s = system.lower()
    if "amadeus" in s:   cls = "amadeus"
    elif "sabre" in s:   cls = "gds"
    elif "travelport" in s: cls = "gds"
    elif "aws" in s:     cls = "aws"
    elif "noc" in s or "faa" in s or "atc" in s: cls = "noc"
    elif "sap" in s:     cls = "sap"
    else:                cls = "custom"
    return f'<span class="stag {cls}">{escape(system)}</span>'

# ── Flag badge ─────────────────────────────────────────────────────
def flag(val):
    v = str(val).strip().upper()
    cls = "flag-y" if v == "Y" else "flag-n"
    return f'<span class="flag {cls}">{v}</span>'

# ── Swim lane colours ──────────────────────────────────────────────
SWIM_COLOURS = [
    "#3b82f6","#8b5cf6","#ec4899","#f59e0b",
    "#10b981","#06b6d4","#6366f1","#0ea5e9",
    "#84cc16","#ef4444","#f97316","#14b8a6",
]

# ── Sidebar builder (matches NP-SP-01 exactly) ─────────────────────
def build_sidebar(all_procs, active_pid):
    # Use the EXISTING wiki sidebar structure — hardcoded L1/L2 groups
    # matching what's already in the repo, not generated from processes.json
    lines = []

    # Group processes by l1_slug → l2_slug → list
    l1_order = OrderedDict()
    for p in all_procs:
        l1s = p["l1_slug"]
        l2s = p["l2_slug"]
        if l1s not in l1_order:
            l1_order[l1s] = {"name": p["l1_domain"], "l2s": OrderedDict()}
        if l2s not in l1_order[l1s]["l2s"]:
            l1_order[l1s]["l2s"][l2s] = {"name": p["l2_process"], "procs": []}
        l1_order[l1s]["l2s"][l2s]["procs"].append(p)

    for l1s, l1d in l1_order.items():
        active_in_l1 = any(
            p["id"] == active_pid
            for l2d in l1d["l2s"].values()
            for p in l2d["procs"]
        )
        open_cls = " open" if active_in_l1 else ""
        lines.append(f'  <div class="sidebar-section">')
        lines.append(f'    <div class="sidebar-domain{open_cls}"><span>{escape(l1d["name"])}</span><span class="chevron">▶</span></div>')
        lines.append(f'    <div class="sidebar-l2{open_cls}">')

        for l2s, l2d in l1d["l2s"].items():
            lines.append(f'      <a class="sidebar-l2-link" href="../../../{l1s}/{l2s}/">{escape(l2d["name"])}</a>')
            lines.append(f'      <div class="sidebar-l3">')
            for p in l2d["procs"]:
                active_cls = " active" if p["id"] == active_pid else ""
                status_map = {"Complete":"status-done","In Progress":"status-wip","Queued":"status-queue","Failed":"status-queue"}
                dot_cls = status_map.get(p["status"], "status-queue")
                pid_lower = p["id"].lower()
                lines.append(
                    f'        <a class="sidebar-l3-link{active_cls}" href="../../../{l1s}/{l2s}/{pid_lower}/">'
                    f'<span class="status-dot {dot_cls}"></span>'
                    f'<span class="pid">{p["id"]}</span>{escape(p["l3_name"])}</a>'
                )
            lines.append(f'      </div>')
        lines.append(f'    </div>')
        lines.append(f'  </div>')

    return "\n".join(lines)

# ── L4 table (matches NP-SP-01 exactly) ───────────────────────────
def build_l4_table(steps):
    if not steps:
        return '<p style="padding:20px;color:#6b7280">L4 steps not yet generated.</p>'

    rows = []
    prev_phase = None
    for s in steps:
        step_num  = s.get("step", "")
        phase_num = step_num.split(".")[0] if "." in step_num else step_num
        phase_name = f"Phase {phase_num}"

        # Derive phase name from step sequence
        if phase_num != prev_phase:
            phase_label = f'<div style="font-size:9px;font-weight:700;color:#ff6600;text-transform:uppercase;letter-spacing:.07em;margin-bottom:2px">{phase_name}</div>'
            step_cell   = f'{phase_label}{escape(step_num)}'
            row_cls     = ' class="phase-break"'
            prev_phase  = phase_num
        else:
            step_cell = escape(step_num)
            row_cls   = ""

        rows.append(f"""<tr{row_cls}>
  <td class="td-step">{step_cell}</td>
  <td class="td-name">{escape(s.get("name",""))}</td>
  <td class="td-role">{escape(s.get("role",""))}</td>
  <td>{stag(s.get("system",""))}</td>
  <td style="font-size:10px;color:#6b7280">{escape(s.get("input",""))}</td>
  <td style="font-size:10px">{escape(s.get("output",""))}</td>
  <td style="font-family:var(--mono);font-size:9px;color:#374151">{escape(s.get("kpi",""))}</td>
  <td style="text-align:center">{flag(s.get("decision_point","N"))}</td>
  <td style="text-align:center">{flag(s.get("exception","N"))}</td>
</tr>""")

    return f"""<div class="table-wrap"><table>
      <thead><tr>
        <th>Step</th><th>Step Name</th><th>Role / Swim Lane</th><th>System</th>
        <th>Input</th><th>Output</th><th>KPI</th><th>Dec?</th><th>Exc?</th>
      </tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table></div>"""

# ── Meta grid ──────────────────────────────────────────────────────
def build_meta(proc, steps):
    pid   = proc["id"]
    l1    = proc["l1_domain"]
    l2    = proc["l2_process"]
    l3    = proc["l3_name"]

    n_steps  = len(steps)
    n_gates  = sum(1 for s in steps if s.get("decision_point","N") == "Y")
    n_exc    = sum(1 for s in steps if s.get("exception","N") == "Y")

    # Count phases
    phases = list(dict.fromkeys(
        s.get("step","1").split(".")[0] for s in steps
    ))
    n_phases = len(phases)

    # Unique roles and systems
    roles   = list(dict.fromkeys(s.get("role","") for s in steps if s.get("role","")))
    systems = list(dict.fromkeys(s.get("system","") for s in steps if s.get("system","")))
    pains   = list(dict.fromkeys(s.get("pain_point","") for s in steps if s.get("pain_point","")))

    # Swim lanes HTML
    swim_html = "".join(
        f'<div class="swim"><div class="dot" style="background:{SWIM_COLOURS[i % len(SWIM_COLOURS)]}"></div>{escape(r)}</div>'
        for i, r in enumerate(roles)
    )

    # Systems HTML
    sys_html = "".join(stag(s) for s in systems)

    # Pain points HTML
    pain_html = "".join(f'<div class="risk-card">{escape(p)}</div>' for p in pains[:6])

    # KPIs from steps
    kpis = [(s.get("name",""), s.get("kpi","")) for s in steps if s.get("kpi","")]
    kpi_html = "".join(
        f'<div class="krow"><span class="kname">{escape(n)}</span><span class="kval">{escape(k)}</span></div>'
        for n, k in kpis[:8]
    )

    # Primary input/output
    first_step = steps[0] if steps else {}
    last_step  = steps[-1] if steps else {}

    return f"""<div class="card" id="meta">
  <div class="card-header"><span class="icon">📋</span><h2>Process Attributes</h2></div>
  <div class="card-body">
    <div class="meta-grid">
      <div>
        <div class="meta-section"><h3>Identification</h3>
          <div class="krow"><span class="kname">Process ID</span><span class="kval">{pid}</span></div>
          <div class="krow"><span class="kname">L1 Domain</span><span class="kval">{escape(l1)}</span></div>
          <div class="krow"><span class="kname">L2 Process</span><span class="kval">{escape(l2)}</span></div>
          <div class="krow"><span class="kname">L3 Name</span><span class="kval">{escape(l3)}</span></div>
          <div class="krow"><span class="kname">L4 Steps</span><span class="kval">{n_steps} across {n_phases} phases</span></div>
          <div class="krow"><span class="kname">Decision Gates</span><span class="kval">{n_gates} (all with iteration loops)</span></div>
          <div class="krow"><span class="kname">Exceptions</span><span class="kval">{n_exc} documented</span></div>
        </div>
        <div class="meta-section"><h3>Swim Lanes (Roles)</h3>{swim_html}</div>
        <div class="meta-section"><h3>Systems &amp; Tools</h3>{sys_html}</div>
      </div>
      <div>
        <div class="meta-section"><h3>Key Performance Indicators</h3>{kpi_html}</div>
        <div class="meta-section"><h3>Airline-Specific Risks &amp; Pain Points</h3>{pain_html}</div>
        <div class="meta-section"><h3>Inputs / Outputs</h3>
          <div class="krow"><span class="kname">Primary Input</span><span class="kval">{escape(first_step.get("input","—"))}</span></div>
          <div class="krow"><span class="kname">Primary Output</span><span class="kval">{escape(last_step.get("output","—"))}</span></div>
        </div>
      </div>
    </div>
  </div>
</div>"""

# ── Prev/Next nav ──────────────────────────────────────────────────
def build_pn_nav(proc, all_procs):
    ids = [p["id"] for p in all_procs]
    idx = ids.index(proc["id"])
    prev_p = all_procs[idx-1] if idx > 0 else None
    next_p = all_procs[idx+1] if idx < len(all_procs)-1 else None

    prev_html = ""
    next_html = ""
    if prev_p:
        prev_html = (
            f'<a class="pn-btn" href="../{prev_p["id"].lower()}/">'
            f'<span class="arrow">←</span>'
            f'<span><span class="sub">Previous</span>{prev_p["id"]} · {escape(prev_p["l3_name"])}</span></a>'
        )
    if next_p:
        next_html = (
            f'<a class="pn-btn" href="../{next_p["id"].lower()}/">'
            f'<span><span class="sub">Next</span>{next_p["id"]} · {escape(next_p["l3_name"])}</span>'
            f'<span class="arrow">→</span></a>'
        )
    return f'<div class="pn-nav">{prev_html}{next_html}</div>'

# ── Full page generator ────────────────────────────────────────────
def generate_page(proc, all_procs):
    pid    = proc["id"]
    l1     = proc["l1_domain"]
    l2     = proc["l2_process"]
    l3     = proc["l3_name"]
    status = proc["status"]
    steps  = proc.get("l4_steps", [])
    l1s    = proc["l1_slug"]
    l2s    = proc["l2_slug"]

    n_steps = len(steps)
    n_gates = sum(1 for s in steps if s.get("decision_point","N") == "Y")
    phases  = list(dict.fromkeys(s.get("step","1").split(".")[0] for s in steps))
    n_phases= len(phases)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Output path — write to repo ROOT matching existing structure
    out_dir = REPO_DIR / l1s / l2s / pid.lower()
    out_dir.mkdir(parents=True, exist_ok=True)

    sidebar_html = build_sidebar(all_procs, active_pid=pid)
    l4_table     = build_l4_table(steps)
    meta_grid    = build_meta(proc, steps)
    pn_nav       = build_pn_nav(proc, all_procs)

    # BPMN section — match NP-SP-01 exactly (no lightbox div, uses wiki.js)
    img_path = IMG_DIR / f"{pid.lower()}.png"
    if img_path.exists():
        bpmn_section = f"""<div class="diagram-wrap" id="diag-wrap-{pid.lower()}">
      <img src="../../../assets/img/{pid.lower()}.png" alt="{pid} BPMN diagram"
           style="max-width:100%;border-radius:6px;box-shadow:0 2px 12px rgba(0,0,0,.08)"
           onload="document.getElementById('diag-placeholder-{pid.lower()}').style.display='none'"
           onerror="this.style.display='none';document.getElementById('diag-placeholder-{pid.lower()}').style.display='flex'">
      <div id="diag-placeholder-{pid.lower()}" class="diagram-placeholder" style="display:none">
        <span class="ico">🗂</span>
        <span>PNG not yet generated.</span>
      </div>
    </div>"""
    else:
        bpmn_section = f"""<div id="diag-placeholder-{pid.lower()}" class="diagram-placeholder">
      <span class="ico">🗂</span>
      <span>PNG not yet generated. Run:<br>
      <code style="font-size:10px;background:#f1f5f9;padding:4px 8px;border-radius:3px">
      mmdc -i diagrams/{pid.lower()}.mmd -o assets/img/{pid.lower()}.png -w 1920 -H 1080 --scale 2 --backgroundColor white
      </code></span>
    </div>"""

    status_badge = "complete" if status == "Complete" else "queued"
    status_emoji = "✅" if status == "Complete" else "⏳"

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
<main class="main">
<div class="breadcrumb">
  <a href="../../../">Home</a><span class="sep">›</span>
  <a href="../../../{l1s}/">{escape(l1)}</a><span class="sep">›</span>
  <a href="../../../{l1s}/{l2s}/">{escape(l2)}</a><span class="sep">›</span>
  <span class="current">{pid} · {escape(l3)}</span>
</div>
<div class="page-header">
  <div class="page-header-left">
    <h1>{escape(l3)}</h1>
    <p>{escape(l1)} › {escape(l2)} · {n_steps} L4 steps · {n_phases} phases · {n_gates} decision gates · Updated {now_str}</p>
  </div>
  <div class="page-header-meta">
    <span class="pid-badge">{pid}</span>
    <span class="status-badge {status_badge}">{status_emoji} {status}</span>
  </div>
</div>
<div class="card" id="diagram">
  <div class="card-header"><span class="icon">📊</span><h2>Process Flow Diagram (BPMN)</h2></div>
  <div class="card-body">
    {bpmn_section}
  </div>
</div>
<div class="card" id="l4-steps">
  <div class="card-header"><span class="icon">📋</span><h2>L4 Process Steps</h2></div>
  <div class="card-body" style="padding:0">
    {l4_table}
  </div>
</div>
{meta_grid}
{pn_nav}
</main>
<script src="../../../assets/js/wiki.js"></script>
</body>
</html>"""

    out_file = out_dir / "index.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"  ↳ Wiki page: {out_file}")
    return out_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--process-id", required=True)
    args = parser.parse_args()

    with open(PROCESSES) as f:
        data = json.load(f)

    all_procs = data["processes"]
    proc = next((p for p in all_procs if p["id"] == args.process_id), None)
    if not proc:
        print(f"ERROR: '{args.process_id}' not in processes.json")
        sys.exit(1)

    print(f"\n🌐 Generating wiki page for {args.process_id}...")
    out = generate_page(proc, all_procs)
    print(f"✅ Done: {out}")

if __name__ == "__main__":
    main()
