#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  run_pipeline.sh — Airlines Process Wiki Autonomous Orchestrator
#  Reads processes.json, picks next N queued subprocesses,
#  calls `claude` CLI for each, then wraps up.
#
#  Usage:
#    ./scripts/run_pipeline.sh              # run MAX_RUN=2 (default)
#    ./scripts/run_pipeline.sh --max 5      # run 5 subprocesses
#    ./scripts/run_pipeline.sh --dry-run    # show what would run
#    ./scripts/run_pipeline.sh --id NP-SP-03   # run specific process
#
#  Requirements on Mac Mini:
#    - claude CLI installed and authenticated
#    - python3 with openpyxl: pip install openpyxl
#    - mmdc: npm install -g @mermaid-js/mermaid-cli
#    - git configured with push access to repo
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

# ── Config ─────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$REPO_DIR/data"
WIKI_DIR="$REPO_DIR"
DIAGRAMS_DIR="$REPO_DIR/diagrams"
IMG_DIR="$REPO_DIR/assets/img"
PROCESSES_JSON="$DATA_DIR/processes.json"
EXCEL_FILE="$DATA_DIR/Airlines_Process_Catalog.xlsx"
LOG_FILE="$REPO_DIR/pipeline.log"

MAX_RUN=2
DRY_RUN=false
SPECIFIC_ID=""

# ── Arg parsing ────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --max)    MAX_RUN="$2";        shift 2 ;;
    --dry-run) DRY_RUN=true;       shift   ;;
    --id)     SPECIFIC_ID="$2";   shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ── Logging ────────────────────────────────────────────────────────
log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

# ── Dependency check ───────────────────────────────────────────────
check_deps() {
  log "Checking dependencies..."
  command -v claude  >/dev/null 2>&1 || { log "ERROR: claude CLI not found. Install from https://docs.anthropic.com/claude-cli"; exit 1; }
  command -v python3 >/dev/null 2>&1 || { log "ERROR: python3 not found"; exit 1; }
  command -v mmdc    >/dev/null 2>&1 || { log "WARN: mmdc not found — diagrams will be skipped. Run: npm install -g @mermaid-js/mermaid-cli"; }
  python3 -c "import openpyxl" 2>/dev/null || { log "ERROR: openpyxl not installed. Run: pip install openpyxl"; exit 1; }
  [ -f "$PROCESSES_JSON" ] || { log "ERROR: $PROCESSES_JSON not found — run create_catalog.py first"; exit 1; }
  [ -f "$EXCEL_FILE" ]     || { log "ERROR: $EXCEL_FILE not found — run create_catalog.py first"; exit 1; }
  log "All dependencies OK."
}

# ── Pick queued processes ───────────────────────────────────────────
get_queued() {
  python3 - <<'PYEOF'
import json, sys, os
pf = os.environ.get("PROCESSES_JSON")
specific = os.environ.get("SPECIFIC_ID", "")
max_run  = int(os.environ.get("MAX_RUN", 2))

with open(pf) as f:
    data = json.load(f)

procs = data["processes"]
if specific:
    candidates = [p for p in procs if p["id"] == specific]
else:
    candidates = [p for p in procs if p["status"] == "Queued"]

picked = candidates[:max_run]
for p in picked:
    print(p["id"])
PYEOF
}

# ── Mark process as In Progress ────────────────────────────────────
mark_in_progress() {
  local pid="$1"
  python3 - "$pid" <<'PYEOF'
import json, sys, os
pid = sys.argv[1]
pf  = os.environ.get("PROCESSES_JSON")
with open(pf) as f: data = json.load(f)
for p in data["processes"]:
    if p["id"] == pid:
        p["status"] = "In Progress"
        break
with open(pf, "w") as f: json.dump(data, f, indent=2)
print(f"  Marked {pid} → In Progress")
PYEOF
}

# ── Write L4 data back to processes.json after agent run ───────────
update_processes_json() {
  local pid="$1"
  local agent_json="$2"
  python3 - "$pid" "$agent_json" <<'PYEOF'
import json, sys, os
from datetime import date
pid        = sys.argv[1]
agent_file = sys.argv[2]
pf         = os.environ.get("PROCESSES_JSON")

with open(agent_file) as f:  agent_data = json.load(f)
with open(pf) as f:           data       = json.load(f)

for p in data["processes"]:
    if p["id"] == pid:
        p["l4_steps"]  = agent_data.get("l4_steps", [])
        p["status"]    = "Complete"
        p["run_date"]  = date.today().isoformat()
        p["wiki_path"] = agent_data.get("wiki_path", "")
        break

with open(pf, "w") as f: json.dump(data, f, indent=2)
print(f"  Updated processes.json: {pid} → Complete")
PYEOF
}

# ── Run mmdc to generate BPMN PNG ─────────────────────────────────
run_mmdc() {
  local pid_lower="$1"
  local mmd_file="$DIAGRAMS_DIR/${pid_lower}.mmd"
  local png_file="$IMG_DIR/${pid_lower}.png"

  if ! command -v mmdc >/dev/null 2>&1; then
    log "  SKIP: mmdc not available"
    return 0
  fi
  if [ ! -f "$mmd_file" ]; then
    log "  SKIP: .mmd file not found at $mmd_file"
    return 0
  fi

  log "  Running mmdc for $pid_lower..."
  mkdir -p "$IMG_DIR"
  mmdc -i "$mmd_file" -o "$png_file" \
       -w 1920 -H 1080 --scale 2 --backgroundColor white \
    && log "  PNG generated: $png_file" \
    || log "  WARN: mmdc failed for $pid_lower"
}

# ── Git commit and push ────────────────────────────────────────────
git_push() {
  local pid="$1"
  local l3_name="$2"
  log "  Git commit + push..."
  cd "$REPO_DIR"
  git add .
  git commit -m "Add ${pid}: ${l3_name} — L4 steps, BPMN, slides, wiki page" \
    || { log "  Nothing to commit."; return 0; }
  git push origin main \
    && log "  Pushed to GitHub." \
    || { log "  WARN: push failed — check auth / network"; }
}

# ── Print summary ──────────────────────────────────────────────────
print_summary() {
  local completed=("$@")
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "AIRLINES PROCESS CATALOG — RUN COMPLETE"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "Processed:  ${completed[*]}"
  echo "Count:      ${#completed[@]} subprocesses"
  echo "Live URL:   https://ghatk047.github.io/airline-process-wiki/"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
main() {
  log "═══════════════════════════════════════"
  log " Airlines Process Wiki Pipeline"
  log " MAX_RUN=${MAX_RUN}  DRY_RUN=${DRY_RUN}"
  log "═══════════════════════════════════════"

  check_deps

  # Export env vars for python subprocesses
  export PROCESSES_JSON MAX_RUN SPECIFIC_ID

  # Pick queued processes
  mapfile -t QUEUE < <(get_queued)

  if [ ${#QUEUE[@]} -eq 0 ]; then
    log "No queued processes found. All done!"
    exit 0
  fi

  log "Queue: ${QUEUE[*]}"

  if $DRY_RUN; then
    log "DRY RUN — would process: ${QUEUE[*]}"
    exit 0
  fi

  COMPLETED=()
  mkdir -p "$DIAGRAMS_DIR" "$WIKI_DIR/assets/img"

  for PID in "${QUEUE[@]}"; do
    log ""
    log "▶ Starting: $PID"

    # Mark In Progress in processes.json
    mark_in_progress "$PID"

    # Temp file for agent output
    AGENT_OUT="$DATA_DIR/.agent_${PID}.json"

    # ── Call Claude CLI agent ──────────────────────────────────────
    # The agent is instructed to read CLAUDE.md, generate L4 rows,
    # write the .mmd file, then output a JSON blob to $AGENT_OUT.
    # We pass the process context inline as the prompt.
    log "  Invoking claude CLI for $PID..."

    PROMPT=$(python3 - "$PID" <<'PYEOF'
import json, sys, os
pid = sys.argv[1]
pf  = os.environ.get("PROCESSES_JSON")
with open(pf) as f: data = json.load(f)
proc = next(p for p in data["processes"] if p["id"] == pid)

print(f"""You are an autonomous airline process documentation agent.
Read CLAUDE.md for full instructions, system landscape, and output quality standards.

Your task: generate complete L4 documentation for:
  Process ID : {proc['id']}
  L1 Domain  : {proc['l1_domain']}
  L2 Process : {proc['l2_process']}
  L3 Name    : {proc['l3_name']}

Steps to complete IN ORDER:
1. Generate 10-18 L4 steps in 3-6 phases with full schema fields
2. Write the Mermaid .mmd file to: diagrams/{proc['id'].lower()}.mmd
   Format: flowchart LR with subgraph per phase, decision diamonds, feedback loops
   Command to render: mmdc -i diagrams/{proc['id'].lower()}.mmd -o wiki/assets/img/{proc['id'].lower()}.png -w 1920 -H 1080 --scale 2 --backgroundColor white
3. Output a JSON file to: data/.agent_{proc['id']}.json
   Schema:
   {{
     "id": "{proc['id']}",
     "l1_domain": "{proc['l1_domain']}",
     "l1_slug": "{proc['l1_slug']}",
     "l2_process": "{proc['l2_process']}",
     "l2_slug": "{proc['l2_slug']}",
     "l3_name": "{proc['l3_name']}",
     "wiki_path": "{proc['l1_slug']}/{proc['l2_slug']}/{proc['id'].lower()}",
     "l4_steps": [
       {{
         "step": "1.1",
         "name": "Step name (max 60 chars)",
         "role": "Job title",
         "system": "Named system",
         "input": "What triggers this step",
         "output": "Artifact or decision produced",
         "kpi": "Measurable metric with target",
         "pain_point": "Specific risk or process gap",
         "decision_point": "Y or N",
         "exception": "Y or N"
       }}
     ]
   }}

Quality rules:
- Every step must have a concrete named system (not "internal system")
- KPIs must have numeric targets where benchmarks exist
- Pain points must be airline-specific, referencing real systems/constraints
- Decision gates must describe the actual decision being made
- At least 1 decision gate per phase

Output ONLY the JSON file (no commentary). The orchestrator handles the rest.""")
PYEOF
)

    # Run claude with the prompt, working directory = repo
    cd "$REPO_DIR"
    if claude --dangerously-skip-permissions \
              -p "$PROMPT" \
              --output-format text \
              2>>"$LOG_FILE"; then
      log "  claude CLI completed for $PID"
    else
      log "  ERROR: claude CLI failed for $PID — marking Failed"
      python3 -c "
import json, os
pf = os.environ.get('PROCESSES_JSON')
with open(pf) as f: data = json.load(f)
for p in data['processes']:
    if p['id'] == '$PID':
        p['status'] = 'Failed'
        break
with open(pf, 'w') as f: json.dump(data, f, indent=2)
"
      continue
    fi

    # ── Validate agent output ───────────────────────────────────────
    if [ ! -f "$AGENT_OUT" ]; then
      log "  WARN: Agent did not produce $AGENT_OUT — skipping downstream steps"
      continue
    fi

    # ── Update processes.json ───────────────────────────────────────
    update_processes_json "$PID" "$AGENT_OUT"

    # ── Reload L3 name for git message ─────────────────────────────
    L3_NAME=$(python3 -c "
import json, os
pf = os.environ.get('PROCESSES_JSON')
with open(pf) as f: data = json.load(f)
p = next(x for x in data['processes'] if x['id'] == '$PID')
print(p['l3_name'])
")

    # ── Run mmdc ───────────────────────────────────────────────────
    run_mmdc "${PID,,}"

    # ── Run Excel writer ───────────────────────────────────────────
    log "  Writing Excel..."
    python3 "$SCRIPT_DIR/write_excel.py" \
      --process-id "$PID" \
      --json-file  "$AGENT_OUT" \
      --excel-file "$EXCEL_FILE" \
      2>>"$LOG_FILE" \
      && log "  Excel updated." \
      || log "  WARN: Excel write failed"

    # ── Build wiki page ────────────────────────────────────────────
    log "  Building wiki page..."
    python3 "$SCRIPT_DIR/build_wiki.py" \
      --process-id "$PID" \
      2>>"$LOG_FILE" \
      && log "  Wiki page built." \
      || log "  WARN: build_wiki.py failed"

    # ── Build slides ───────────────────────────────────────────────
    log "  Building slides..."
    python3 "$SCRIPT_DIR/build_slides.py" \
      --process-id "$PID" \
      2>>"$LOG_FILE" \
      && log "  Slides built." \
      || log "  WARN: build_slides.py failed"

    # ── Git commit ─────────────────────────────────────────────────

    # Rebuild home page
    log "  Rebuilding home page..."
    python3 "$SCRIPT_DIR/build_index.py" 2>>"$LOG_FILE" && log "  Home page rebuilt." || log "  WARN: build_index.py failed"

    git_push "$PID" "$L3_NAME"

    # ── Clean up temp agent file ───────────────────────────────────
    rm -f "$AGENT_OUT"

    COMPLETED+=("$PID")
    log "✅ $PID complete."
  done

  print_summary "${COMPLETED[@]}"
}

main "$@"
