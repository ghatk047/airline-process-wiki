#!/usr/bin/env python3
"""
build_index.py — Regenerate ALL index pages from processes.json:
  - index.html (home)
  - {l1_slug}/index.html (one per L1 domain)
  - {l1_slug}/{l2_slug}/index.html (one per L2 process group)

Run after each pipeline batch. Usage: python3 scripts/build_index.py
"""
import json, sys
from pathlib import Path
from collections import OrderedDict
from datetime import datetime
from html import escape

SCRIPT_DIR = Path(__file__).parent
REPO_DIR   = SCRIPT_DIR.parent
PROCESSES  = REPO_DIR / "data" / "processes.json"

with open(PROCESSES) as f:
    procs = json.load(f)["processes"]

now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

# ── Group L1 → L2 → processes ─────────────────────────────────────
l1_groups = OrderedDict()
for p in procs:
    l1s = p["l1_slug"]; l2s = p["l2_slug"]
    if l1s not in l1_groups:
        l1_groups[l1s] = {
            "name": p["l1_domain"], "slug": l1s,
            "l2s": OrderedDict(), "total": 0, "complete": 0
        }
    # Key by l2_process name so different L2 groups with same slug show separately
    l2_key = p["l2_process"]
    if l2_key not in l1_groups[l1s]["l2s"]:
        l1_groups[l1s]["l2s"][l2_key] = {
            "name": p["l2_process"], "slug": l2s,
            "procs": [], "total": 0, "complete": 0
        }
    l1_groups[l1s]["l2s"][l2_key]["procs"].append(p)
    l1_groups[l1s]["l2s"][l2_key]["total"] += 1
    l1_groups[l1s]["total"] += 1
    if p["status"] == "Complete":
        l1_groups[l1s]["complete"] += 1
        l1_groups[l1s]["l2s"][l2_key]["complete"] += 1

total_all    = len(procs)
complete_all = sum(1 for p in procs if p["status"] == "Complete")
queued_all   = sum(1 for p in procs if p["status"] == "Queued")

# ── Shared sidebar builder ─────────────────────────────────────────
def build_sidebar(active_l1s=None, active_l2s=None, depth=1):
    root = "./" if depth == 0 else "../" * depth
    lines = []
    for l1s, l1d in l1_groups.items():
        is_active_l1 = (l1s == active_l1s)
        open_cls = " open" if is_active_l1 else ""
        lines += [
            f'  <div class="sidebar-section">',
            f'    <div class="sidebar-domain{open_cls}"><span>{escape(l1d["name"])}</span><span class="chevron">▶</span></div>',
            f'    <div class="sidebar-l2{open_cls}">',
        ]
        for l2s, l2d in l1d["l2s"].items():
            lines.append(f'      <a class="sidebar-l2-link" href="{root}{l1s}/{l2s}/">{escape(l2d["name"])}</a>')
            lines.append(f'      <div class="sidebar-l3">')
            for p in l2d["procs"]:
                dot = "status-done" if p["status"] == "Complete" \
                      else "status-wip" if p["status"] == "In Progress" \
                      else "status-queue"
                lines.append(
                    f'        <a class="sidebar-l3-link" href="{root}{l1s}/{l2s}/{p["id"].lower()}/">'
                    f'<span class="status-dot {dot}"></span>'
                    f'<span class="pid">{p["id"]}</span>{escape(p["l3_name"])}</a>'
                )
            lines.append(f'      </div>')
        lines += [f'    </div>', f'  </div>']
    return "\n".join(lines)

# ── Shared page shell ──────────────────────────────────────────────
def page_shell(title, css_root, topbar_home, sidebar_html, main_html, js_root):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Airlines Process Wiki</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css_root}assets/css/wiki.css">
</head>
<body>
<header class="topbar">
  <a href="{topbar_home}" class="topbar-logo">Airlines <span>Process Wiki</span></a>
  <span class="topbar-badge">v1.0</span>
  <div class="topbar-right">
    <input type="text" id="searchBox" class="search-box" placeholder="Search processes… (/)" autocomplete="off">
    <a href="{topbar_home}">Home</a>
    <a href="https://github.com/ghatk047/airline-process-wiki" class="gh-btn" target="_blank">⭐ GitHub</a>
  </div>
</header>
<nav class="sidebar" id="sidebar">
{sidebar_html}
</nav>
<button class="sidebar-toggle" id="sidebarToggle" title="Toggle sidebar">◀</button>
<main class="main">
{main_html}
</main>
<script src="{js_root}assets/js/wiki.js"></script>
</body>
</html>"""

# ══════════════════════════════════════════════════════════════════
#  1. HOME PAGE — index.html
# ══════════════════════════════════════════════════════════════════
def build_home():
    cards = []
    for l1s, l1d in l1_groups.items():
        n_l2 = len(l1d["l2s"])
        cards.append(f"""<div class="domain-card">
  <div class="domain-card-hdr"><h3>{escape(l1d["name"])}</h3><p>Airlines · {n_l2} process groups</p></div>
  <div class="domain-card-body">
    <div class="domain-card-stat">{l1d["complete"]} of {l1d["total"]} subprocesses complete</div>
    <a class="domain-card-link" href="{l1s}/">Explore domain →</a>
  </div>
</div>""")

    main = f"""<div class="hero">
  <div class="hero-eyebrow">Process Catalog</div>
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
<div class="domain-grid">{"".join(cards)}</div>"""

    html = page_shell("Airlines Process Wiki — SAP Consulting",
                      "./", "./", build_sidebar(depth=0), main, "./")
    out = REPO_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  ✅ index.html ({complete_all} complete / {total_all} total)")

# ══════════════════════════════════════════════════════════════════
#  2. L1 PAGES — {l1_slug}/index.html
# ══════════════════════════════════════════════════════════════════
def build_l1_pages():
    for l1s, l1d in l1_groups.items():
        cards = []
        for l2s, l2d in l1d["l2s"].items():
            cards.append(f"""<div class="domain-card">
  <div class="domain-card-hdr"><h3>{escape(l2d["name"])}</h3><p>{escape(l1d["name"])}</p></div>
  <div class="domain-card-body">
    <div class="domain-card-stat">{l2d["complete"]} of {l2d["total"]} subprocesses complete</div>
    <a class="domain-card-link" href="{l2s}/">View subprocesses →</a>
  </div>
</div>""")

        main = f"""<div class="breadcrumb">
  <a href="../">Home</a><span class="sep">›</span>
  <span class="current">{escape(l1d["name"])}</span>
</div>
<div class="page-header">
  <div class="page-header-left">
    <h1>{escape(l1d["name"])}</h1>
    <p>Airlines · {len(l1d["l2s"])} process groups · {l1d["complete"]} of {l1d["total"]} complete · Updated {now_str}</p>
  </div>
</div>
<div class="domain-grid">{"".join(cards)}</div>"""

        sidebar = build_sidebar(active_l1s=l1s, depth=1)
        html = page_shell(l1d["name"], "../", "../", sidebar, main, "../")
        out_dir = REPO_DIR / l1s
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"  ✅ {l1s}/index.html ({l1d['complete']}/{l1d['total']})")

# ══════════════════════════════════════════════════════════════════
#  3. L2 PAGES — {l1_slug}/{l2_slug}/index.html
# ══════════════════════════════════════════════════════════════════
def build_l2_pages():
    for l1s, l1d in l1_groups.items():
        for l2s, l2d in l1d["l2s"].items():
            rows = []
            for p in l2d["procs"]:
                dot = "status-done" if p["status"] == "Complete" \
                      else "status-wip" if p["status"] == "In Progress" \
                      else "status-queue"
                emoji = "✅" if p["status"] == "Complete" \
                        else "🔄" if p["status"] == "In Progress" else "⏳"
                steps = len(p.get("l4_steps", []))
                gates = sum(1 for s in p.get("l4_steps", []) if s.get("decision_point") == "Y")
                step_str = f"{steps} steps · {gates} gates" if steps else "Queued"
                rows.append(f"""<div class="domain-card">
  <div class="domain-card-hdr">
    <h3><span class="pid-badge" style="font-size:11px;margin-right:8px">{p["id"]}</span>{escape(p["l3_name"])}</h3>
    <p>{escape(l2d["name"])} · {step_str}</p>
  </div>
  <div class="domain-card-body">
    <div class="domain-card-stat">{emoji} {p["status"]}</div>
    <a class="domain-card-link" href="{p['id'].lower()}/">{"View process →" if p["status"] == "Complete" else "Queued"}</a>
  </div>
</div>""")

            main = f"""<div class="breadcrumb">
  <a href="../../">Home</a><span class="sep">›</span>
  <a href="../">{escape(l1d["name"])}</a><span class="sep">›</span>
  <span class="current">{escape(l2d["name"])}</span>
</div>
<div class="page-header">
  <div class="page-header-left">
    <h1>{escape(l2d["name"])}</h1>
    <p>{escape(l1d["name"])} · {l2d["complete"]} of {l2d["total"]} subprocesses complete · Updated {now_str}</p>
  </div>
</div>
<div class="domain-grid">{"".join(rows)}</div>"""

            sidebar = build_sidebar(active_l1s=l1s, active_l2s=l2s, depth=3)
            html = page_shell(f"{l2d['name']} · {l1d['name']}", "../../", "../../", sidebar, main, "../../")
            out_dir = REPO_DIR / l1s / l2s
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(html, encoding="utf-8")
            print(f"  ✅ {l1s}/{l2s}/index.html ({l2d['complete']}/{l2d['total']})")

# ── Run all ────────────────────────────────────────────────────────
print(f"\n🏗  Rebuilding all index pages from processes.json...")
print(f"   {complete_all} complete · {queued_all} queued · {total_all} total\n")
build_home()
build_l1_pages()
build_l2_pages()
print(f"\n✅ All index pages rebuilt.")

