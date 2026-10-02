#!/usr/bin/env python3
"""
generate_ea_qwen.py — Generate the 10 new cross-domain EA Mermaid diagrams (EA-X21..X30)
via local Qwen (Ollama), in the Airport-Wiki style (labelled arrows, emoji subgraph
headers, navy hubs, orange orchestrators).

Usage:
  python3 generate_ea_qwen.py --all
  python3 generate_ea_qwen.py --id ea-x21
  python3 generate_ea_qwen.py --all --no-render
"""
import argparse, json, re, subprocess, os, sys, time
from pathlib import Path

REPO_DIR   = Path(os.environ.get("WIKI_REPO", str(Path.home() / "Downloads" / "airline-process-wiki")))
EA_DIR     = REPO_DIR / "ea-diagrams"
MANIFEST   = EA_DIR / "ea_manifest.json"

OLLAMA_URL      = os.environ.get("OLLAMA_URL", "http://localhost:11434")
PRIMARY_MODEL   = os.environ.get("QWEN_MODEL", "qwen2.5-coder:14b")
FALLBACK_MODEL  = os.environ.get("QWEN_FALLBACK", "qwen2.5:latest")

EA_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are an airline enterprise architect. Produce a single Mermaid
flowchart describing the cross-domain SYSTEM integration and DATA FLOW for the given theme.

Return ONLY the Mermaid code, NO markdown fences, NO commentary.

STYLE (follow exactly):
- Line 1: %%{init: {'theme':'base','themeVariables':{'fontSize':'13px','fontFamily':'Inter, Arial, sans-serif'}}}%%
- Line 2: flowchart TB   (or LR if more readable; NO blank line after line 1)
- Group systems into 5 to 7 subgraphs with emoji + short title, e.g.:
    subgraph BOOK["Booking and Reservation"]
- Each node = a REAL airline system with a two-line label using \\n, e.g.:
    PSS["Amadeus Altea PSS\\nInventory Bookings Ticketing"]
- EVERY arrow MUST be labelled with the data/message type:
    PSS -->|"reservation data"| DCS
- Use 6 to 12 subgraph phases/groups and 20 to 30 nodes total.
- Add classDef styles; make one hub node navy and one orchestrator orange:
    classDef hub fill:#003366,color:#fff,stroke:#003366
    classDef key fill:#ff6600,color:#fff,stroke:#ff6600
- Assign classes with: class NODEID hub

HARD RULES (violations break rendering):
- Node IDs start with a LETTER, unique, no dots.
- Arrows ALWAYS -->  never --gt.
- NO parentheses, ampersands (&), or angle brackets inside [ ] or " " labels — spell out "and".
- Output ONLY Mermaid text starting with %%{init...}%%.
"""

USER_TEMPLATE = """Theme: {title}
Scope: {desc}

Produce the Mermaid cross-domain integration diagram now. Mermaid only."""

def call_ollama(title, desc, model):
    import urllib.request
    payload = {"model": model, "system": SYSTEM_PROMPT,
               "prompt": USER_TEMPLATE.format(title=title, desc=desc),
               "stream": False, "options": {"temperature": 0.5, "num_ctx": 8192}}
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read()).get("response","")

def sanitise(mmd):
    mmd = re.sub(r'^```[a-z]*\n?', '', mmd, flags=re.MULTILINE)
    mmd = re.sub(r'```$', '', mmd, flags=re.MULTILINE)
    mmd = re.sub(r'^---.*?---\s*', '', mmd, flags=re.DOTALL)
    mmd = mmd.replace('--&gt;','-->').replace('--gt','-->')
    # escape stray & inside labels → "and"
    mmd = re.sub(r'&(?!(amp|lt|gt|quot|apos|#)\w*;)', 'and', mmd)
    # ensure init line
    if '%%{init' not in mmd:
        mmd = "%%{init: {'theme':'base','themeVariables':{'fontSize':'13px'}}}%%\n" + mmd
    lines = [l for l in mmd.strip().split('\n')]
    # drop blank line right after init
    out = []
    for l in lines:
        if out and out[-1].startswith('%%{init') and l.strip()=='':
            continue
        out.append(l)
    return '\n'.join(out).strip()

def render_png(eid, mmd):
    mmd_path = EA_DIR / f"{eid}.mmd"
    png_path = EA_DIR / f"{eid}.png"
    mmd_path.write_text(mmd)
    try:
        subprocess.run(["mmdc","-i",str(mmd_path),"-o",str(png_path),
                        "-w","2400","-H","1400","--scale","2","--backgroundColor","white"],
                       check=True, capture_output=True, timeout=180)
        return True
    except Exception as e:
        print(f"    ⚠ mmdc failed {eid}: {str(e)[:120]}")
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--id", type=str)
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--model", type=str, default=PRIMARY_MODEL)
    args = ap.parse_args()

    if not MANIFEST.exists():
        print(f"❌ EA manifest not found: {MANIFEST}\n   Copy ea_manifest.json into {EA_DIR}/ first.")
        sys.exit(1)
    man = json.loads(MANIFEST.read_text())["ea_diagrams"]

    if args.id:
        todo = [d for d in man if d["id"] == args.id]
    else:
        todo = man
    if not todo:
        print("Nothing to do."); return

    for d in todo:
        eid = d["id"]; title = d["title"]; desc = d["desc"]
        print(f"\n▶ {eid.upper()} — {title}")
        mmd = None
        for model in (args.model, FALLBACK_MODEL):
            try:
                raw = call_ollama(title, desc, model)
                mmd = sanitise(raw)
                if 'flowchart' in mmd: break
            except Exception as e:
                print(f"    ⚠ {model} failed: {str(e)[:80]}")
        if not mmd or 'flowchart' not in mmd:
            print(f"    ❌ {eid} skipped — no valid mermaid")
            continue
        (EA_DIR / f"{eid}.mmd").write_text(mmd)
        print(f"    ✅ wrote {eid}.mmd ({len(mmd)} chars)")
        if not args.no_render:
            if render_png(eid, mmd):
                print(f"    ✅ rendered {eid}.png")
        time.sleep(1)

    print("\n✅ EA generation complete. Build EA wiki pages + git push next.")

if __name__ == "__main__":
    main()
