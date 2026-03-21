# Enterprise Architecture Diagrams

Application landscape diagrams for the Airlines Process Wiki.
Generated from L4 process step data — showing which systems participate in each L2 process group.

## Files

| File | Domain | Description |
|------|--------|-------------|
| `np-ea-landscape.mmd` | Network Planning & Scheduling | Application landscape across all 4 L2 process groups |
| `np-ea-landscape.png` | Network Planning & Scheduling | Rendered PNG (generate with mmdc command below) |

## Generating the PNG

```bash
cd ~/Downloads/airline-process-wiki

mmdc -i ea-diagrams/np-ea-landscape.mmd \
     -o ea-diagrams/np-ea-landscape.png \
     -w 3840 -H 2160 \
     --scale 2 \
     --backgroundColor white
```

## Diagram structure

```
L2 Process Groups (top)
    ↓ connects to
System Categories (below):
  🔵 Planning Suite     — Amadeus Sky suite, OAG, SITA, crew systems
  🟢 PSS & Inventory    — Altéa PSS, NDC gateway
  🟠 Revenue & Pricing  — NRM, PROS RM, ATPCO
  🟣 Distribution & GDS — Sabre, Travelport, Amadeus GDS, IATA
  🩵 Analytics & BI     — AWS, Tableau, Power BI
  🩷 Finance & CRM      — SAP S/4HANA, Salesforce
```

## How to generate for other L1 domains

Run `python3 scripts/build_ea_diagram.py --domain CX` (script coming soon).
