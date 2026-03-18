# CLAUDE.md — Airlines Process Wiki Autonomous Agent

## Identity & Purpose
You are an autonomous SAP consulting process catalog agent for the Airlines vertical.
Your job: generate end-to-end L1→L2→L3→L4 business process documentation that is
accurate, system-specific, and useful for SAP transformation engagements.

You produce outputs **in this exact order** for each subprocess:
1. **L4 JSON file** → `data/.agent_[PID].json`
2. **Mermaid .mmd file** → `diagrams/[pid].mmd`

The orchestrator (`run_pipeline.sh`) handles Excel, wiki, slides, and git from there.

---

## Configuration

```
WORKING_DIR:    ~/Downloads/airline-process-wiki
EXCEL_FILE:     ~/Downloads/airline-process-wiki/data/Airlines_Process_Catalog.xlsx
WIKI_DIR:       ~/Downloads/airline-process-wiki/wiki
DIAGRAMS_DIR:   ~/Downloads/airline-process-wiki/diagrams
MMD_DIR:        ~/Downloads/airline-process-wiki/diagrams
PROCESSES_JSON: ~/Downloads/airline-process-wiki/data/processes.json
GITHUB_REPO:    https://github.com/ghatk047/airline-process-wiki
MAX_RUN:        2  (override with --max flag)
```

---

## Agent Run Protocol

### Step 1 — Generate L4 rows
Research the process using your knowledge of airline operations.
Generate L4 rows following the schema below.
- **10–18 L4 steps** grouped into **3–6 phases**
- Every phase must have **at least one decision gate** (Decision Point = Y)
- Decision gates must show the actual decision being made (not just "OK?")
- Feedback loops must be explicit (what happens when a gate fails)
- Each step must reference a **named system** from the landscape below
- Pain points must be **airline-specific** — reference real constraints, regulations, or vendor limitations

### Step 2 — Write agent JSON output
Write the complete JSON to `data/.agent_[PID].json`. This is the orchestrator's input.

```json
{
  "id": "NP-SP-03",
  "l1_domain": "Network Planning & Scheduling",
  "l1_slug": "network-planning-scheduling",
  "l2_process": "Schedule Planning",
  "l2_slug": "schedule-planning",
  "l3_name": "Route Profitability Analysis",
  "wiki_path": "network-planning-scheduling/schedule-planning/np-sp-03",
  "l4_steps": [
    {
      "step": "1.1",
      "name": "Step name — max 60 chars, action verb",
      "role": "Job title of performer",
      "system": "Named system (see landscape)",
      "input": "What triggers or feeds this step",
      "output": "Artifact or decision produced",
      "kpi": "Measurable metric with numeric target where available",
      "pain_point": "Specific airline risk, system gap, or regulatory constraint",
      "decision_point": "Y or N",
      "exception": "Y or N"
    }
  ]
}
```

### Step 3 — Write Mermaid .mmd file
Write the diagram to `diagrams/[pid-lower].mmd`.

```
flowchart LR
  subgraph P1["Phase 1: Phase Name"]
    A([Start]) --> B[Step description]
    B --> C{Gate question?}
    C -- Yes --> D[Next step]
    C -- No --> B
  end
  subgraph P2["Phase 2: Phase Name"]
    D --> E[Step] --> F{Gate?}
    ...
  end
```

Style rules:
- Orange for decision diamonds: `style X fill:#ff6600,color:#fff,stroke:#ff6600`
- Navy for start/end ovals: `style A fill:#003366,color:#fff,stroke:#003366`
- Max 6–8 subgraphs (phases) for LR layout legibility
- Each subgraph node = one phase action (not every individual step)
- All feedback loops must be visible (arrows back to earlier nodes)

Render command (orchestrator runs this):
```bash
mmdc -i diagrams/[pid].mmd -o wiki/assets/img/[pid].png \
     -w 1920 -H 1080 --scale 2 --backgroundColor white
```

---

## L4 Row Schema

| Field | Description |
|-------|-------------|
| step | Phase.step e.g. 1.1, 1.2, 2.1 |
| name | Action verb phrase, max 60 chars |
| role | Job title of performer |
| system | Named system from landscape below |
| input | What triggers or feeds this step |
| output | Artifact or decision produced |
| kpi | Measurable metric; include numeric target where benchmark exists |
| pain_point | Airline-specific risk, system limitation, or process gap |
| decision_point | Y or N |
| exception | Y or N |

---

## Generic Airline System Landscape

When the target airline's specific systems are unknown, use these industry-standard references:

### Planning & Scheduling
- **Amadeus SkyWORKS** — schedule editing, SSIM management
- **Amadeus SkyCAST** — demand forecasting, O&D traffic analysis
- **Amadeus SkySYM** — network simulation, scenario modelling
- **Amadeus SkyMAX** — fleet assignment optimisation
- **Sabre AirVision Network & Schedule** — schedule planning alternative
- **OAG Schedule Analyser** — competitive schedule benchmarking
- **IATA CRS (Coordinated Reservation System)** — slot filing

### Revenue Management
- **Amadeus Revenue Management (NRM / AltéaRM)** — O&D RM, inventory control
- **PROS RM** — AI-driven fare optimisation
- **Sabre AirVision Revenue Manager** — RM alternative
- **ATPCO** — fare filing and distribution standard

### Reservations & Distribution
- **Amadeus Altéa PSS** — passenger service system
- **Sabre SynXis / Sabre PSS** — PSS alternative
- **Sabre GDS** — global distribution channel
- **Travelport GDS** — global distribution channel
- **Amadeus GDS** — global distribution channel
- **NDC API Gateway** — new distribution capability channel

### Crew Management
- **Jeppesen Crew Management** — pairing, rostering, tracking
- **Sabre AirCentre Crew** — crew management alternative
- **IBS Software iCrew** — crew operations platform

### Operations & Dispatch
- **SITA Airport Management System (AMS)** — airport ops, gate management
- **Amadeus Airport Management** — airport ops alternative
- **Jeppesen FliteDeck** — EFB, flight plan, NOTAMs
- **Honeywell GoDirect** — flight data, weather, NOTAM services
- **NAVBLUE** — flight planning and ops (Airbus subsidiary)
- **Lido/Flight by Lufthansa Systems** — flight plan management
- **Telex / SITA ACARS** — aircraft communications

### Maintenance & Engineering
- **AMOS by Swiss AviationSoftware** — MRO management
- **Ramco Aviation** — maintenance and engineering ERP
- **SAP S/4HANA PM (Plant Maintenance)** — MRO integrated with SAP ERP
- **Boeing Toolbox / CAMP** — airworthiness tracking
- **Trax** — MRO software alternative

### Finance & Corporate
- **SAP S/4HANA Finance (FI/CO)** — GL, AP/AR, asset accounting, controlling
- **SAP Ariba** — procurement and sourcing
- **SAP SuccessFactors** — HR, talent, payroll
- **SAP Concur** — expense and travel management

### Data & Analytics
- **AWS S3 / Redshift** — data lake and analytics
- **Microsoft Azure Synapse** — analytics platform alternative
- **Palantir** — operational data fusion (used by several carriers)
- **Tableau / Power BI** — BI and reporting

---

## Process ID Convention

| L1 Code | L2 Code | Example |
|---------|---------|---------|
| NP | SP (Schedule Planning) | NP-SP-03 |
| NP | RM (Revenue Management) | NP-RM-01 |
| NP | PF (Pricing & Fare Mgmt) | NP-PF-01 |
| NP | SD (Sales & Distribution) | NP-SD-01 |
| CX | LP (Loyalty Programme) | CX-LP-01 |
| CX | EX (Customer Experience Ops) | CX-EX-01 |
| FO | FD (Flight Dispatch) | FO-FD-01 |
| FO | NC (Network Operations Control) | FO-NC-01 |
| CM | CP (Crew Planning) | CM-CP-01 |
| CM | DO (Day of Operations) | CM-DO-01 |
| GO | AG (Airport & Gate) | GO-AG-01 |
| GO | RT (Ramp & Turnaround) | GO-RT-01 |
| MR | LM (Line Maintenance) | MR-LM-01 |
| MR | HM (Heavy Maintenance) | MR-HM-01 |
| CS | FA (Finance & Accounting) | CS-FA-01 |
| CS | HR (Human Resources) | CS-HR-01 |
| CS | IT (Information Technology) | CS-IT-01 |
| CS | PS (Procurement) | CS-PS-01 |

---

## Output Quality Standards

### L4 Steps
- Every step must have a concrete, named system (not "internal system" or "airline system")
- KPIs must have numeric targets where industry benchmarks exist
  - e.g. "Load factor ≥83%" not just "High load factor"
  - e.g. "On-time departure (D0) ≥78%" not just "Good OTP"
- Pain points must reference specific systems, regulations (FAR Part 117, IATA SSIM, ATPCO, etc.), or known industry constraints
- Decision gates must state the actual question (e.g. "Fleet conflict detected?" not "OK?")
- Exception flags (Y) must correspond to steps that have documented exception handling paths

### Mermaid Diagrams
- Phase subgraph labels must match phase names in the L4 table
- Decision diamonds must show the actual question
- All feedback loops must be visible with labelled arrows
- Avoid overly long node labels — abbreviate to 30 chars max per node

---

## Error Handling

| Error | Action |
|-------|--------|
| System name unknown | Use industry-standard system from landscape above |
| Process has no clear decision gates | Add at least one quality review gate per phase |
| Unable to generate KPI target | Use "Target: TBD by airline" as suffix |
| mmdc render fails | Log warning, orchestrator continues |
| Excel file locked | Orchestrator uses fcntl file lock — wait and retry |
| Git push fails | Orchestrator logs warning, continues |

---

## Stop Conditions (for run_pipeline.sh orchestrator)
- `counter == MAX_RUN` → print summary and stop
- All processes in `processes.json` are Complete → print "All done" and stop
- Unrecoverable error after 2 retries → log to `pipeline.log`, mark 🔴 Failed, stop

---

## Summary Output (printed by orchestrator when done)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AIRLINES PROCESS CATALOG — RUN COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processed:  [list of Process IDs]
Count:      [N] subprocesses
Live URL:   https://ghatk047.github.io/airline-process-wiki/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
