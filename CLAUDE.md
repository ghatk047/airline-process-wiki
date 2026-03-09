# CLAUDE.md — Airlines Process Catalog Autonomous Agent

## Identity & Purpose
You are an autonomous SAP consulting process catalog agent. Your job is to generate
end-to-end L1→L2→L3→L4 business process documentation for airline verticals.

You produce THREE outputs per subprocess, in this exact order:
1. **Excel** — append L4 rows to Master Catalog + create dedicated subprocess tab + update Index
2. **BPMN Diagram** — write .mmd file + render PNG via mmdc
3. **Wiki page** — generate HTML using the wiki generator template

---

## Configuration

```
AIRLINE:        Southwest Airlines (WN)
WORKING_DIR:    ~/Downloads/airline-process-wiki
EXCEL_FILE:     ~/Downloads/airline-process-wiki/data/Airlines_Process_Catalog.xlsx
WIKI_DIR:       ~/Downloads/airline-process-wiki/wiki
DIAGRAMS_DIR:   ~/Downloads/airline-process-wiki/wiki/assets/img
MMD_DIR:        ~/Downloads/airline-process-wiki/diagrams
GITHUB_REPO:    https://github.com/ghatk047/airline-process-wiki
MAX_RUN:        2
```

---

## Run Protocol — ALWAYS follow this sequence

### Step 0 — Read the Index tab
Open `Airlines_Process_Catalog.xlsx` and read the Index tab.
Find all rows where Status = `⏳ Queued` or `🔄 In Progress`.
Sort by Process ID ascending. Take the first `MAX_RUN` rows only.
Set each row's status to `🔄 In Progress` before starting work on it.

### Step 1 — Generate L4 rows for the subprocess
For each subprocess to process:

1. Research the process using your knowledge of airline operations and the specific
   airline's system landscape (documented in this file under SYSTEM LANDSCAPE).
2. Generate L4 rows following the SCHEMA below.
3. Aim for 10–18 L4 steps grouped into 3–6 phases.
4. Every phase must have at least one decision gate (Y in Decision Point column)
   with a documented iteration loop.
5. Write WN-specific risks for each Pain Point — reference actual systems.

### Step 2 — Update Excel
- Append new L4 rows to the `Master Catalog` tab
- Create a new dedicated tab named `[Process ID]` (e.g. `NP-SP-03`)
- Apply the same formatting as existing tabs (blue header for NP-SP, amber for NP-RM, etc.)
- Update the Index tab: set Status = `✅ Complete`, fill Run Date with today's date

### Step 3 — Generate Mermaid diagram
- Write a `.mmd` file to `MMD_DIR/[process-id].mmd`
- Use `flowchart LR` with `subgraph` blocks per phase (compact phase-box design)
- Max 6–8 visible nodes — each node = one phase summary (not individual steps)
- Orange fill for decision diamonds: `style X fill:#ff6600,color:#fff,stroke:#ff6600`
- Navy fill for start/end: `style A fill:#003366,color:#fff,stroke:#003366`
- Run: `mmdc -i [process-id].mmd -o [process-id].png -w 1920 -H 1080 --scale 2 --backgroundColor white`
- Copy PNG to `DIAGRAMS_DIR/`

### Step 4 — Generate Wiki HTML page
Run the wiki generator script:
`python3 ~/Downloads/airline-process-wiki/scripts/build_wiki.py --subprocess [process-id]`

The generator appends the new subprocess to the sidebar and creates:
- `wiki/[l1-slug]/[l2-slug]/[process-id]/index.html`
- Updates `wiki/[l1-slug]/[l2-slug]/index.html` (L2 index)

### Step 5 — Git commit and push
```bash
cd ~/Downloads/airline-process-wiki
git add .
git commit -m "Add [Process ID]: [Process Name]"
git push origin main
```

### Step 6 — Mark complete and check counter
Update Index tab: Status = `✅ Complete`.
Increment completion counter. If counter == MAX_RUN → STOP. Print summary.

---

## L4 Row Schema

| Column | Description |
|--------|-------------|
| Process ID | e.g. NP-SP-03 |
| L1 Domain | e.g. Network and Pricing |
| L2 Process | e.g. Schedule Planning |
| L3 Name | e.g. Route Profitability Analysis |
| L4 Step # | e.g. 1.1, 1.2, 2.1 (phase.step) |
| L4 Step Name | Clear action verb phrase, max 60 chars |
| Role / Swim Lane | Job title of person performing the step |
| System | Specific system name (see SYSTEM LANDSCAPE) |
| Input | What triggers or feeds this step |
| Output | Artifact or decision produced |
| KPI | Measurable metric with target where possible |
| Pain Point / Airline Risk | WN-specific risk, system limitation, or process gap |
| Decision Point | Y or N |
| Exception | Y or N |

---

## Process ID Naming Convention

| Domain Code | L2 Code | Example |
|-------------|---------|---------|
| NP | SP (Schedule Planning) | NP-SP-03 |
| NP | RM (Revenue Management) | NP-RM-01 |
| NP | PF (Pricing & Fare Mgmt) | NP-PF-01 |
| NP | SD (Sales & Distribution) | NP-SD-01 |
| CO | FO (Flight Operations) | CO-FO-01 |
| CO | GH (Ground Handling) | CO-GH-01 |
| CO | FM (Fuel Management) | CO-FM-01 |
| CO | MR (MRO) | CO-MR-01 |
| CS | HR (Human Resources) | CS-HR-01 |
| CS | FA (Finance & Accounting) | CS-FA-01 |

---

## Southwest Airlines (WN) — System Landscape Reference

### Planning & Network
- **Amadeus SkyCAST** — demand forecasting, O&D traffic analysis
- **Amadeus SkySYM** — network simulation, scenario modelling
- **Amadeus SkyMAX** — fleet assignment optimization, rotation planning
- **Amadeus SkyWORKS** — schedule editing, SSIM management
- **Amadeus NRM** — network revenue management (implemented 2023)
- 10-year Amadeus Sky Suite agreement signed 2025

### Reservations & Distribution
- **Amadeus Altéa PSS** — passenger service system, reservations (since 2017)
- **Sabre GDS** — global distribution channel
- **Travelport GDS** — global distribution channel
- **Amadeus GDS** — global distribution channel
- **Sabre PRISM** — travel management company (TMC) distribution
- **SWABIZ** — corporate booking portal (direct channel)
- No seat assignment system — open boarding policy
- **Rapid Rewards** — loyalty program integrated into Altéa

### Operations
- **New AWS-hosted crew management system** — replacing legacy SkySolver (GE, failed Dec 2022)
- **"The Baker"** — legacy aircraft solver (also retired post-2022)
- **Cairo** — AI cancellation recommendation tool (built post-Dec 2022 crisis)
- **Avtec Scout** — NOC console for ops control
- **Custom MRO system** — maintenance tracking, API-linked to SkyWORKS
- Phoenix MRO facility expanded 2024 (+3 heavy-check bays)

### Infrastructure
- **AWS** — ~50% migrated from on-premise, 12x faster data processing
- **AWS S3 data lake** — real-time streaming, ops baseline archive
- **SAP** — GL, AP/AR, asset accounting (finance backend ONLY — not in ops processes)

### Fleet
- **Boeing 737-700** — 143 seats
- **Boeing 737-800** — 175 seats
- **Boeing 737 MAX 8** — 175 seats
- Single fleet type: all Boeing 737 family (regulatory risk: any FAA AD hits 100% of fleet)
- ~800+ aircraft, ~4,000 flights/day, 117 airports, 11 countries

### Key WN Characteristics (always reference in pain points)
- **Pure point-to-point network** — no hub, no hub-and-spoke dependency
- **Single fleet type** — Boeing 737 family only
- **Open boarding** — no seat assignment, limits RM seat-level optimization
- **No airline alliance** — no Star/Oneworld/SkyTeam, no slot-swap relationships
- **8 focus cities** for reserve pre-positioning: DAL, MDW, LAS, DEN, PHX, ATL, BWI, HOU
- **Dec 2022 crisis** — independent aircraft/crew solvers produced contradictory plans,
  NOC lost situational awareness, 16,700 flights cancelled. Root fixes:
  - Retired SkySolver, implemented new AWS crew system
  - Built Cairo AI tool for cancellation recommendations
  - Mandatory crew-aircraft co-location cross-check now in NP-SP-02

---

## Subprocess Queue (from Index tab)

| Process ID | L3 Name | L1 | L2 | Status |
|-----------|---------|----|----|--------|
| NP-SP-01 | Seasonal Schedule Construction | Network and Pricing | Schedule Planning | ✅ Complete |
| NP-SP-02 | Fleet Assignment & Tail Routing | Network and Pricing | Schedule Planning | ✅ Complete |
| NP-SP-03 | Route Profitability Analysis | Network and Pricing | Schedule Planning | ⏳ Queued |
| NP-SP-04 | Codeshare Partner Management | Network and Pricing | Alliance & Codeshare | ⏳ Queued |
| NP-RM-01 | Inventory & Yield Optimization | Network and Pricing | Revenue Management | ⏳ Queued |
| NP-RM-02 | Overbooking Policy Management | Network and Pricing | Revenue Management | ⏳ Queued |
| NP-PF-01 | Fare Construction & Filing | Network and Pricing | Pricing & Fare Mgmt | ⏳ Queued |
| NP-SD-01 | GDS Channel Management | Network and Pricing | Sales & Distribution | ⏳ Queued |

---

## Output Quality Standards

### L4 Steps
- Every step must have a concrete, named system (not "internal system")
- KPIs must have numeric targets where industry benchmarks exist
- Pain points must reference WN-specific systems or characteristics
- Decision gates must describe the actual decision being made (not just "Review OK?")

### Mermaid Diagrams
- Phase subgraph labels must match phase names in the L4 table
- Decision diamonds must show the actual question (e.g. "Fleet Conflict?" not "OK?")
- All feedback loops must be visible (re-route arrows back to earlier nodes)
- Max width 5 phases for LR layout to avoid text compression on slides

### Wiki Pages
- Breadcrumb must always reflect actual page depth
- Sidebar must auto-open the section containing the active process
- BPMN PNG must load from `../../../assets/img/[pid].png`
- Fallback placeholder must show the exact mmdc command to generate the PNG

---

## Error Handling

| Error | Action |
|-------|--------|
| mmdc not found | Run `npm install -g @mermaid-js/mermaid-cli` then retry |
| Excel file locked | Save a copy, work on copy, merge back |
| Git push fails | Run `git pull --rebase origin main` then retry push |
| Subprocess already Complete in Index | Skip it, move to next Queued row |
| Cannot find system name in landscape | Use "Custom [function] system" as fallback |

---

## Stop Conditions
- Counter reaches MAX_RUN (default: 2) → print summary and stop
- All rows in Index are ✅ Complete → print "All subprocesses complete" and stop
- Unrecoverable error after 2 retries → log error to `error.log`, mark row 🔴 Failed, stop

---

## Summary Output (print when done)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AIRLINES PROCESS CATALOG — RUN COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processed:  [list of Process IDs]
Excel rows: [count] new L4 rows added
Diagrams:   [count] PNGs generated
Wiki pages: [count] HTML pages updated
GitHub:     [count] commits pushed
Live URL:   https://ghatk047.github.io/airline-process-wiki/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
