#!/usr/bin/env python3
"""
build_slides.py — Generate a 3-slide HTML presentation for a subprocess.

Usage:
    python3 build_slides.py --process-id NP-SP-03

Slides:
    A — BPMN PNG (full bleed)
    B — Process Attributes (metadata + swim lanes + systems)
    C — KPIs & Pain Points (risk register table)

Output: wiki/<l1-slug>/<l2-slug>/<pid>/slides.html
        (printable to PDF via browser Ctrl+P)
"""
import argparse
import json
import sys
from pathlib import Path
from html import escape
from collections import Counter

SCRIPT_DIR = Path(__file__).parent
REPO_DIR   = SCRIPT_DIR.parent
DATA_DIR   = REPO_DIR / "data"
PROCESSES  = DATA_DIR / "processes.json"
WIKI_DIR   = REPO_DIR          # pages live at repo root
IMG_DIR    = REPO_DIR / "assets" / "img"


def generate_slides(proc):
    pid    = proc["id"]
    l1     = proc["l1_domain"]
    l2     = proc["l2_process"]
    l3     = proc["l3_name"]
    steps  = proc.get("l4_steps", [])

    out_dir = WIKI_DIR / proc["l1_slug"] / proc["l2_slug"] / pid.lower()
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Derived metadata ──────────────────────────────────────────────────
    n_steps  = len(steps)
    n_gates  = sum(1 for s in steps if s.get("decision_point") == "Y")
    n_exc    = sum(1 for s in steps if s.get("exception") == "Y")
    systems  = sorted(set(s.get("system","") for s in steps if s.get("system","")))
    roles    = sorted(set(s.get("role","") for s in steps if s.get("role","")))

    img_rel  = f"../../../assets/img/{pid.lower()}.png"
    img_path = IMG_DIR / f"{pid.lower()}.png"

    # ── Slide A — BPMN ────────────────────────────────────────────────────
    if img_path.exists():
        slide_a_body = f'<img src="{img_rel}" alt="BPMN for {pid}" class="bpmn-full">'
    else:
        mmdc = (
            f"mmdc -i diagrams/{pid.lower()}.mmd "
            f"-o wiki/assets/img/{pid.lower()}.png "
            f"-w 1920 -H 1080 --scale 2 --backgroundColor white"
        )
        slide_a_body = f"""
        <div class="placeholder">
          <p>BPMN diagram not yet generated</p>
          <code>{mmdc}</code>
        </div>"""

    # ── Slide B — Process Attributes ──────────────────────────────────────
    systems_html = "".join(f'<li>{escape(s)}</li>' for s in systems) or "<li>—</li>"
    roles_html   = "".join(f'<li>{escape(r)}</li>' for r in roles)   or "<li>—</li>"

    phases_seen = {}
    for s in steps:
        phase_num = s.get("step","1.1").split(".")[0]
        if phase_num not in phases_seen:
            phases_seen[phase_num] = s.get("name","")
    phases_html = "".join(
        f'<li><strong>Phase {k}:</strong> {escape(v[:50])}</li>'
        for k, v in phases_seen.items()
    ) or "<li>—</li>"

    # ── Slide C — KPIs & Pain Points ──────────────────────────────────────
    kpi_rows = []
    for s in steps:
        if s.get("kpi") or s.get("pain_point"):
            dp = "⚠" if s.get("decision_point") == "Y" else ""
            kpi_rows.append(f"""      <tr>
        <td class="step-col">{escape(s.get('step',''))}</td>
        <td>{escape(s.get('name',''))}</td>
        <td class="kpi-col">{escape(s.get('kpi','—'))}</td>
        <td class="pain-col">{escape(s.get('pain_point','—'))}</td>
        <td class="gate-col">{dp}</td>
      </tr>""")
    kpi_table = ("""    <table class="kpi-table">
      <thead>
        <tr>
          <th>Step</th><th>L4 Step Name</th>
          <th>KPI / Target</th><th>Pain Point / Risk</th><th>Gate</th>
        </tr>
      </thead>
      <tbody>
""" + "\n".join(kpi_rows) + """
      </tbody>
    </table>""") if kpi_rows else "<p>No KPI data available.</p>"

    # ── Full HTML ─────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{pid} Slides — {escape(l3)}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin:0; padding:0; }}
  :root {{
    --navy:   #003366;
    --orange: #FF6600;
    --light:  #F0F7FF;
    --mid:    #D6E4F0;
    --text:   #1a1a1a;
  }}
  body {{ font-family: 'Inter', 'Segoe UI', sans-serif; background:#1a1a1a; color:var(--text); }}

  /* ── Slide container ── */
  .slide {{
    width:1280px; height:720px; background:#fff;
    margin:32px auto; padding:0;
    display:flex; flex-direction:column;
    box-shadow:0 8px 40px rgba(0,0,0,.4);
    page-break-after: always;
    overflow:hidden;
  }}

  /* ── Header bar ── */
  .slide-header {{
    background:var(--navy); color:#fff;
    padding:14px 32px; display:flex;
    align-items:center; justify-content:space-between;
    flex-shrink:0;
  }}
  .slide-header .pid-tag {{
    background:var(--orange); color:#fff;
    padding:3px 12px; border-radius:4px;
    font-weight:700; font-size:13px; letter-spacing:.5px;
  }}
  .slide-header h1 {{ font-size:18px; font-weight:600; flex:1; margin:0 20px; }}
  .slide-header .meta {{ font-size:12px; opacity:.8; white-space:nowrap; }}

  /* ── Slide body ── */
  .slide-body {{ flex:1; overflow:hidden; display:flex; flex-direction:column; }}

  /* ── Slide A — BPMN ── */
  .bpmn-full {{
    width:100%; height:100%; object-fit:contain;
    background:#f8f8f8; display:block;
  }}
  .placeholder {{
    flex:1; display:flex; flex-direction:column;
    align-items:center; justify-content:center; gap:16px;
    background:var(--light); color:#666;
  }}
  .placeholder code {{
    font-size:11px; background:#fff;
    padding:8px 16px; border-radius:4px;
    border:1px solid #ddd;
  }}

  /* ── Slide B — Attributes ── */
  .attrs-grid {{
    display:grid; grid-template-columns:1fr 1fr 1fr;
    gap:0; height:100%;
  }}
  .attr-panel {{
    padding:24px 28px;
    border-right:1px solid #e0e0e0;
  }}
  .attr-panel:last-child {{ border-right:none; }}
  .attr-panel h3 {{
    font-size:12px; font-weight:700; text-transform:uppercase;
    letter-spacing:.8px; color:var(--orange); margin-bottom:12px;
  }}
  .stat-row {{
    display:flex; gap:24px; margin-bottom:20px;
  }}
  .stat-box {{
    background:var(--light); border-radius:8px;
    padding:10px 16px; text-align:center; flex:1;
  }}
  .stat-box .num {{ font-size:28px; font-weight:700; color:var(--navy); }}
  .stat-box .lbl {{ font-size:10px; color:#666; text-transform:uppercase; letter-spacing:.5px; }}
  ul.attr-list {{ list-style:none; }}
  ul.attr-list li {{
    padding:5px 0; border-bottom:1px solid #f0f0f0;
    font-size:12px; line-height:1.4;
  }}
  ul.attr-list li:last-child {{ border-bottom:none; }}

  /* ── Slide C — KPIs ── */
  .kpi-wrap {{ padding:16px 28px; overflow:auto; height:100%; }}
  .kpi-table {{ width:100%; border-collapse:collapse; font-size:11px; }}
  .kpi-table thead tr {{ background:var(--navy); color:#fff; }}
  .kpi-table th {{
    padding:8px 10px; text-align:left;
    font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:.5px;
  }}
  .kpi-table tbody tr:nth-child(even) {{ background:var(--light); }}
  .kpi-table td {{ padding:7px 10px; border-bottom:1px solid #eee; vertical-align:top; }}
  .step-col {{ font-weight:700; color:var(--navy); white-space:nowrap; width:55px; }}
  .gate-col {{ text-align:center; width:45px; color:var(--orange); font-size:14px; }}
  .kpi-col  {{ width:200px; }}
  .pain-col {{ color:#7f3f00; }}

  /* ── Footer ── */
  .slide-footer {{
    background:var(--light); padding:8px 32px;
    display:flex; justify-content:space-between;
    font-size:10px; color:#666; flex-shrink:0;
    border-top:2px solid var(--orange);
  }}

  /* ── Print ── */
  @media print {{
    body {{ background:#fff; }}
    .slide {{ margin:0; box-shadow:none; width:100vw; height:100vh; }}
  }}
</style>
</head>
<body>

<!-- ══ SLIDE A — BPMN ══════════════════════════════════════════════════ -->
<div class="slide">
  <div class="slide-header">
    <span class="pid-tag">{pid}</span>
    <h1>{escape(l3)}</h1>
    <span class="meta">Slide 1 of 3 — Process Flow</span>
  </div>
  <div class="slide-body">
{slide_a_body}
  </div>
  <div class="slide-footer">
    <span>Airlines Process Wiki · SAP Consulting</span>
    <span>{l1} › {l2}</span>
  </div>
</div>

<!-- ══ SLIDE B — PROCESS ATTRIBUTES ════════════════════════════════════ -->
<div class="slide">
  <div class="slide-header">
    <span class="pid-tag">{pid}</span>
    <h1>{escape(l3)}</h1>
    <span class="meta">Slide 2 of 3 — Process Attributes</span>
  </div>
  <div class="slide-body">
    <div class="attrs-grid">
      <div class="attr-panel">
        <h3>Overview</h3>
        <ul class="attr-list">
          <li><strong>Process ID:</strong> {pid}</li>
          <li><strong>L1 Domain:</strong> {escape(l1)}</li>
          <li><strong>L2 Process:</strong> {escape(l2)}</li>
          <li><strong>L3 Name:</strong> {escape(l3)}</li>
        </ul>
        <div class="stat-row" style="margin-top:20px">
          <div class="stat-box"><div class="num">{n_steps}</div><div class="lbl">L4 Steps</div></div>
          <div class="stat-box"><div class="num">{n_gates}</div><div class="lbl">Decision Gates</div></div>
          <div class="stat-box"><div class="num">{n_exc}</div><div class="lbl">Exceptions</div></div>
        </div>
        <h3 style="margin-top:12px">Process Phases</h3>
        <ul class="attr-list">{phases_html}</ul>
      </div>
      <div class="attr-panel">
        <h3>Roles / Swim Lanes</h3>
        <ul class="attr-list">{roles_html}</ul>
      </div>
      <div class="attr-panel">
        <h3>Systems</h3>
        <ul class="attr-list">{systems_html}</ul>
      </div>
    </div>
  </div>
  <div class="slide-footer">
    <span>Airlines Process Wiki · SAP Consulting</span>
    <span>{l1} › {l2}</span>
  </div>
</div>

<!-- ══ SLIDE C — KPIs & RISK ════════════════════════════════════════════ -->
<div class="slide">
  <div class="slide-header">
    <span class="pid-tag">{pid}</span>
    <h1>{escape(l3)}</h1>
    <span class="meta">Slide 3 of 3 — KPIs &amp; Risk Register</span>
  </div>
  <div class="slide-body">
    <div class="kpi-wrap">
{kpi_table}
    </div>
  </div>
  <div class="slide-footer">
    <span>Airlines Process Wiki · SAP Consulting</span>
    <span>{l1} › {l2}</span>
  </div>
</div>

</body>
</html>
"""
    out_file = out_dir / "slides.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"  ↳ Slides: {out_file}")
    return out_file


def main():
    parser = argparse.ArgumentParser(description="Generate HTML slide deck for a subprocess")
    parser.add_argument("--process-id", required=True)
    args = parser.parse_args()

    with open(PROCESSES) as f:
        data = json.load(f)

    proc = next((p for p in data["processes"] if p["id"] == args.process_id), None)
    if not proc:
        print(f"ERROR: '{args.process_id}' not in processes.json")
        sys.exit(1)

    print(f"\n📊 Generating slides for {args.process_id}...")
    out = generate_slides(proc)
    print(f"✅ Done: {out}")


if __name__ == "__main__":
    main()
