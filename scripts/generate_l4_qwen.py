#!/usr/bin/env python3
"""
generate_l4_qwen.py — Generate L4 steps for expansion processes via local Qwen (Ollama).

KEY CHANGE (v2): Qwen supplies ONLY the L4 step content (rich, 12-14 steps, proper
1.1/2.1 numbering). The Mermaid BPMN is then built DETERMINISTICALLY in Python from
those steps — proper phase subgraphs, sequential arrows, decision diamonds, and a
swimlane-style layout — matching the rich original diagrams. We do NOT trust the LLM
to draw the diagram.

Usage:
  python3 generate_l4_qwen.py --max 10
  python3 generate_l4_qwen.py --id FO-FW-01
  python3 generate_l4_qwen.py --dry-run
  python3 generate_l4_qwen.py --max 10 --no-render
  python3 generate_l4_qwen.py --rebuild-mmd FO-FW-01   # rebuild diagram from existing steps
"""
import argparse, json, re, subprocess, sys, os, time
from pathlib import Path
from datetime import datetime, timezone

REPO_DIR   = Path(os.environ.get("WIKI_REPO", str(Path.home() / "Downloads" / "airline-process-wiki")))
DATA_DIR   = REPO_DIR / "data"
DIAGRAMS   = REPO_DIR / "diagrams"
IMG_DIR    = REPO_DIR / "assets" / "img"

# Ensure subprocess (mmdc) sees Homebrew + node bin dirs regardless of shell env
os.environ["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", "")
QUEUE_FILE = DATA_DIR / "expansion_queue.json"
SOT_FILE   = DATA_DIR / "processes.json"

OLLAMA_URL      = os.environ.get("OLLAMA_URL", "http://localhost:11434")
PRIMARY_MODEL   = os.environ.get("QWEN_MODEL", "qwen2.5-coder:14b")
FALLBACK_MODEL  = os.environ.get("QWEN_FALLBACK", "qwen2.5:latest")

for d in (DIAGRAMS, IMG_DIR, DATA_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Qwen system prompt — CONTENT ONLY, no mermaid ───────────────────
SYSTEM_PROMPT = """You are a senior airline operations and SAP consulting SME.
Generate a DETAILED, realistic L4 process breakdown for a commercial airline.

Return ONLY valid JSON, NO markdown fences, NO commentary. Schema:
{
  "description": "3-4 sentence operational description of this L3 process",
  "trigger": "what initiates the process",
  "outcome": "what successful completion produces",
  "l4_steps": [
    {
      "step": "1.1",
      "name": "Concise step name (3-6 words)",
      "role": "Specific airline role e.g. Flight Dispatcher, Load Controller, Revenue Analyst",
      "system": "Real airline system e.g. Amadeus Altea PSS, Jeppesen, AMOS, SAP S4HANA, ServiceNow, NAVBLUE",
      "input": "Input document or data",
      "output": "Output document or deliverable",
      "kpi": "Measurable KPI with a numeric target",
      "decision_point": "Y or N",
      "exception": "Y or N",
      "pain_point": "Real operational pain point"
    }
  ],
  "systems": ["System A","System B","System C","System D"],
  "kpis": ["KPI with numeric target","KPI with numeric target","KPI with numeric target","KPI with numeric target"],
  "risks": ["Operational risk","Compliance risk","Financial/operational risk"]
}

MANDATORY CONTENT RULES — follow EXACTLY:
- Produce BETWEEN 12 AND 14 l4_steps. Never fewer than 12.
- Steps MUST be grouped into EXACTLY 3 phases and numbered strictly:
    Phase 1 (Initiation): 1.1, 1.2, 1.3, 1.4  (4 steps)
    Phase 2 (Execution):  2.1, 2.2, 2.3, 2.4, 2.5, 2.6  (5-6 steps)
    Phase 3 (Close/Control): 3.1, 3.2, 3.3, 3.4  (3-4 steps)
- The "step" field MUST be dotted numbers like "1.1" — NEVER "StepA" or "1" or "A".
- Mark AT LEAST 3 steps with decision_point = "Y" (real go/no-go gates).
- Mark AT LEAST 2 steps with exception = "Y".
- Use REAL, specific airline systems and REAL role titles throughout.
- 4 to 6 systems, 4 to 6 KPIs with numeric targets, 3 to 5 risks.
- Do NOT include a mermaid field. Output JSON only.
"""

USER_TEMPLATE = """Generate the detailed L4 process for:
Process ID: {pid}
L1 Domain: {l1}
L2 Process Group: {l2}
L3 Process Name: {l3}

Remember: 12-14 steps, dotted numbering 1.1/2.1/3.1, at least 3 decision gates.
Return ONLY the JSON object."""

# ── Deterministic Mermaid BPMN builder (from steps) ─────────────────
PHASE_NAMES = {"1": "Phase 1 Initiation", "2": "Phase 2 Execution", "3": "Phase 3 Close"}
PHASE_FILL  = {"1": "#dbeafe", "2": "#fef9c3", "3": "#dcfce7"}
PHASE_STROKE= {"1": "#3b82f6", "2": "#f59e0b", "3": "#22c55e"}

def _clean(txt):
    """Strip characters that break mermaid labels."""
    txt = re.sub(r'[()&<>\[\]{}|"\'`]', '', str(txt))
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt[:42]

def build_bpmn(pid, l3_name, steps):
    """Construct a rich flowchart LR from ordered L4 steps.
    - one subgraph per phase (by leading digit of step number)
    - sequential arrows between consecutive steps
    - decision_point == Y rendered as a diamond with Yes/No branches
    - exception == Y rendered as a dashed branch to an exception node
    """
    # order steps by (phase, minor)
    def keyf(s):
        m = re.match(r'(\d+)\.(\d+)', str(s.get("step","1.1")))
        return (int(m.group(1)), int(m.group(2))) if m else (9, 9)
    steps = sorted(steps, key=keyf)

    # Cap decision points at 4 — keep the most meaningful gates, downgrade the rest.
    # This edits the step data in place so the L4 table's DEC? column matches the diagram.
    _yc = 0
    for _s in steps:
        if str(_s.get("decision_point", "N")).upper() == "Y":
            _yc += 1
            if _yc > 4:
                _s["decision_point"] = "N"

    lines = ["%%{init: {'theme':'base','themeVariables':{'fontSize':'12px','fontFamily':'Inter, Arial'}}}%%",
             "flowchart LR"]

    # group by phase
    from collections import OrderedDict
    phases = OrderedDict()
    for s in steps:
        ph = str(s.get("step","1.1")).split(".")[0]
        phases.setdefault(ph, []).append(s)

    node_ids = {}          # step -> node id
    exc_nodes = []         # (from_id, exc_id, label)
    dec_nodes = set()      # ids that are decision diamonds
    counter = 0

    # Start node
    lines.append('  START([Start])')

    for ph, plist in phases.items():
        pname = PHASE_NAMES.get(ph, f"Phase {ph}")
        lines.append(f'  subgraph P{ph}["{pname}"]')
        lines.append('    direction TB')
        for s in plist:
            counter += 1
            nid = f"N{counter}"
            node_ids[s.get("step")] = nid
            label = _clean(s.get("name","Step"))
            role  = _clean(s.get("role",""))
            full = f"{label}<br/>{role}" if role else label
            if str(s.get("decision_point","N")).upper() == "Y":
                lines.append(f'    {nid}{{"{full}"}}')
                dec_nodes.add(nid)
            else:
                lines.append(f'    {nid}["{full}"]')
        lines.append('  end')

    # Sequential flow with decision branches
    ordered = [s.get("step") for s in steps]
    prev_id = "START"
    for i, stp in enumerate(ordered):
        nid = node_ids[stp]
        s = next(x for x in steps if x.get("step")==stp)
        # link previous -> current
        if prev_id in dec_nodes:
            lines.append(f'  {prev_id} -->|Yes| {nid}')
        else:
            lines.append(f'  {prev_id} --> {nid}')
        # exception branch
        if str(s.get("exception","N")).upper() == "Y":
            counter += 1
            exid = f"E{counter}"
            exc_label = _clean("Exception " + s.get("name","handling"))
            lines.append(f'  {exid}["{exc_label}"]')
            lines.append(f'  {nid} -.->|Exception| {exid}')
            exc_nodes.append(exid)
        prev_id = nid

    # End node
    lines.append('  DONE([Complete])')
    if prev_id in dec_nodes:
        lines.append(f'  {prev_id} -->|Yes| DONE')
    else:
        lines.append(f'  {prev_id} --> DONE')

    # Decision "No" loopbacks (route No back to prior node for realism)
    dec_list = [nid for nid in node_ids.values() if nid in dec_nodes]
    all_ids = list(node_ids.values())
    for nid in dec_nodes:
        idx = all_ids.index(nid)
        back = all_ids[idx-1] if idx > 0 else "START"
        lines.append(f'  {nid} -.->|No| {back}')

    # Styles
    lines.append('  classDef startEnd fill:#003366,color:#fff,stroke:#003366')
    lines.append('  classDef exc fill:#fee2e2,stroke:#ef4444,color:#991b1b')
    lines.append('  class START,DONE startEnd')
    if exc_nodes:
        lines.append(f'  class {",".join(exc_nodes)} exc')
    for ph in phases:
        lines.append(f'  style P{ph} fill:{PHASE_FILL.get(ph,"#f1f5f9")},stroke:{PHASE_STROKE.get(ph,"#64748b")}')

    return "\n".join(lines)

# ── Ollama ──────────────────────────────────────────────────────────
def call_ollama(pid, l1, l2, l3, model):
    import urllib.request
    payload = {"model": model, "system": SYSTEM_PROMPT,
               "prompt": USER_TEMPLATE.format(pid=pid,l1=l1,l2=l2,l3=l3),
               "stream": False, "format": "json",
               "options": {"temperature": 0.4, "num_ctx": 8192}}
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read()).get("response","")

def parse_json(raw):
    raw = raw.strip()
    raw = re.sub(r'^```[a-z]*\n?', '', raw)
    raw = re.sub(r'\n?```$', '', raw)
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m: raise ValueError("no JSON object found")
    return json.loads(m.group())

def normalize_steps(steps):
    """Repair step numbering if the model drifted (StepA, 1, A...) into 1.1/2.1/3.1."""
    good = all(re.match(r'^\d+\.\d+$', str(s.get("step",""))) for s in steps)
    if good and len(steps) >= 10:
        return steps
    # Re-number into 3 phases: 4 / (n-8) / 4
    n = len(steps)
    p1 = 4; p3 = 4; p2 = max(1, n - p1 - p3)
    plan = ["1."+str(i) for i in range(1,p1+1)] + \
           ["2."+str(i) for i in range(1,p2+1)] + \
           ["3."+str(i) for i in range(1,p3+1)]
    for s, num in zip(steps, plan):
        s["step"] = num
    return steps

def render_png(pid, mmd):
    mmd_path = DIAGRAMS / f"{pid.lower()}.mmd"
    png_path = IMG_DIR / f"{pid.lower()}.png"
    mmd_path.write_text(mmd)
    try:
        subprocess.run(["mmdc","-i",str(mmd_path),"-o",str(png_path),
                        "-w","1920","-H","1080","--scale","2","--backgroundColor","white"],
                       check=True, capture_output=True, timeout=180)
        return True
    except Exception as e:
        print(f"    ⚠ mmdc failed {pid}: {str(e)[:160]}")
        return False

def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default
def save(path, data):
    path.write_text(json.dumps(data, indent=2))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=10)
    ap.add_argument("--id", type=str, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--rebuild-mmd", type=str, default=None,
                    help="Rebuild BPMN for an existing completed PID from its stored steps")
    ap.add_argument("--model", type=str, default=PRIMARY_MODEL)
    args = ap.parse_args()

    # Rebuild-mmd mode: redraw diagram from steps already in processes.json
    if args.rebuild_mmd:
        sot = load(SOT_FILE, {"processes":[]})
        p = next((x for x in sot["processes"] if x["id"]==args.rebuild_mmd), None)
        if not p: print(f"❌ {args.rebuild_mmd} not found"); sys.exit(1)
        mmd = build_bpmn(p["id"], p["l3_name"], p["l4_steps"])
        p["mermaid"] = mmd
        save(SOT_FILE, sot)
        if not args.no_render: render_png(p["id"], mmd)
        print(f"✅ Rebuilt BPMN for {p['id']} ({mmd.count('-->')+mmd.count('-.->')} arrows)")
        return

    if not QUEUE_FILE.exists():
        print(f"❌ Queue not found: {QUEUE_FILE}"); sys.exit(1)

    queue = load(QUEUE_FILE, {"processes":[]})
    sot   = load(SOT_FILE, {"processes":[]})

    if args.id:
        todo = [p for p in queue["processes"] if p["id"]==args.id]
        if not todo: print(f"❌ ID not in queue: {args.id}"); sys.exit(1)
    else:
        todo = [p for p in queue["processes"] if p["status"]=="Queued"][:args.max]

    if not todo:
        print("✅ Nothing queued."); return

    print(f"{'DRY RUN — ' if args.dry_run else ''}{len(todo)} process(es):\n")
    for p in todo:
        print(f"  {p['id']:<12} {p['l1_domain']} › {p['l2_process']} › {p['l3_name']}")
    if args.dry_run: return

    done = 0
    for p in todo:
        pid = p["id"]
        print(f"\n▶ {pid} — {p['l3_name']}")
        data = None
        for model in (args.model, FALLBACK_MODEL):
            try:
                raw = call_ollama(pid, p["l1_domain"], p["l2_process"], p["l3_name"], model)
                data = parse_json(raw)
                break
            except Exception as e:
                print(f"    ⚠ {model} failed ({str(e)[:80]})")
                data = None
        if not data or not data.get("l4_steps"):
            print(f"    ❌ {pid} skipped — no valid steps"); continue

        # Normalize numbering, then BUILD the diagram deterministically
        data["l4_steps"] = normalize_steps(data["l4_steps"])
        mmd = build_bpmn(pid, p["l3_name"], data["l4_steps"])
        data["mermaid"] = mmd

        merged = {**p, **data, "status":"Complete",
                  "run_date": datetime.now(timezone.utc).strftime("%Y-%m-%d")}

        if not args.no_render:
            render_png(pid, mmd)

        sot["processes"] = [x for x in sot["processes"] if x["id"] != pid]
        sot["processes"].append(merged)
        save(SOT_FILE, sot)
        for q in queue["processes"]:
            if q["id"]==pid: q["status"]="Complete"; q["run_date"]=merged["run_date"]
        save(QUEUE_FILE, queue)

        done += 1
        nsteps = len(data["l4_steps"])
        ngates = sum(1 for s in data["l4_steps"] if str(s.get("decision_point","N")).upper()=="Y")
        narrows = mmd.count("-->") + mmd.count("-.->")
        print(f"    ✅ {pid}: {nsteps} steps, {ngates} gates, {narrows} arrows in BPMN")
        time.sleep(1)

    print(f"\n✅ Completed {done}/{len(todo)}. Now: build pages + push.")

if __name__ == "__main__":
    main()
