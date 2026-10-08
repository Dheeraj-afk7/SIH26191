# Project Overview: SIH26191

## Project Title
**Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations**

## Problem Statement ID & Domain
- **Problem Statement ID:** SIH26191
- **Organization / Ministry:** Ministry of Home Affairs (MoHA)
- **Department:** National Disaster Response Force (NDRF), Disaster Management Division
- **Category:** Software
- **Theme:** Disaster Management
- **Pilot Geographic District:** Rudraprayag District, Uttarakhand, India

---

## Problem Being Solved
- **Recurring Mountain Hazards:** In mountainous terrain such as Rudraprayag District, Uttarakhand, recurring natural hazards—including landslides, flash floods, cloudbursts, and debris flows—pose chronic, existential threats to rural habitations.
- **Reactive Disaster Management Gap:** Current disaster response mechanisms are predominantly reactive, mobilizing relief, temporary shelters, and ad-hoc rehabilitation only after catastrophic disaster events occur rather than planning spatial relocation proactively.
- **Lack of Integrated Spatial Decision Support:** District and State Disaster Management Authorities (DDMA/SDMA) lack unified, reproducible, GIS-enabled tools that integrate terrain physics, multi-hazard exposure, demographic vulnerability, critical infrastructure access, disaster history, and topographically feasible relocation site capacity.

---

## Target Users
1. **State Disaster Management Authorities (SDMA / USDMA):** Strategic disaster mitigation planning, policy formulation, and district-level resource allocation.
2. **District Disaster Management Authorities (DDMA) & District Magistrates (DM):** Tactical relocation scheduling, block-level risk prioritization, and commissioning geotechnical field inspections.
3. **National Disaster Response Force (NDRF) & Ministry of Home Affairs (MoHA):** National risk monitoring and emergency preparedness alignment.
4. **Block Development Officers (BDOs) & Tehsil Administration (Ukhimath, Augustmuni, Jakholi):** Ground-level validation, village dossier inspection, and rehabilitation logistics.
5. **Town & Country Planners / Rural Housing Agencies (PMAY-G):** Spatial site suitability assessment and preliminary dwelling-unit scenario modeling.

---

## Motivation
- **The 2013 Kedarnath Disaster Context:** The June 2013 multi-hazard disaster in Rudraprayag demonstrated that vulnerable settlements situated along steep valley flanks and floodplains suffer catastrophic loss of life and permanent economic disruption.
- **Proactive Relocation Planning:** Providing an objective, deterministic, transparent, and reproducible spatial decision-support platform enables authorities to systematically identify at-risk habitations years ahead of disaster triggers and evaluate safe relocation terrain alternatives.

---

## Proposed Solution
An enterprise-grade, glass-box, **GIS-enabled Decision-Support System (DSS)** that deterministically ingests satellite Digital Elevation Models (DEM), multi-hazard screening proxies, Census socio-demographics, historical disaster registries, road networks, and land-cover constraints to:
1. Identify and vectorize **Candidate Hazard-Based Red Zones** across the district.
2. Calculate metric Euclidean and road network proximity for all **653 Census habitations**.
3. Classify habitations into **4 Explainable Priority Tiers** aligned with official administrative relocation planning horizons.
4. Screen non-hazardous, low-slope ($\le 20^\circ$) terrain to identify **Candidate Topographically Feasible Relocation Sites** ($1–10\text{ ha}$ MMU).
5. Model **Dwelling-Unit and Population Capacity Scenarios** using Ministry of Rural Development (MoRD) PMAY-G $25\text{ m}^2/\text{HH}$ housing norms with a $40\%$ net buildable efficiency factor.
6. Provide an interactive **SDMA Authority Action Center**, sub-district block aggregation, exportable CSV reporting, and an operator-triggered **Dynamic Pipeline Recomputation Engine**.

---

## Key Objectives
1. **Multi-Hazard Screening:** Compute continuous terrain susceptibility (slope, aspect) and flood exposure (D8 hydrology, Topographic Wetness Index) rasters at $30\text{m}$ resolution.
2. **Candidate Red Zone Delineation:** Segment contiguous high-hazard pixels ($\text{Class } 3$) using morphological 8-connectivity clustering ($\text{area} \ge 5,000\text{ m}^2$).
3. **Habitation Vulnerability Profiling:** Georeference 653 Census 2011 habitations via SHRUG v2.2 centroids and benchmark 4 socio-demographic vulnerability indicators against district upper-tertile ($P_{75}$) cutoffs.
4. **Relocation Horizon Assignment:** Categorize habitations into Immediate (0–1 yr), Short-Term (1–3 yr), Medium-Term (3–10 yr), and Routine (10+ yr) planning horizons.
5. **Alternative Site Extraction:** Isolate topographically feasible candidate relocation polygons outside hazard zones and compute PMAY-G dwelling capacities capped at $100\text{ ha}$ scale protection.
6. **Infrastructure & Network Overlay:** Ingest OpenStreetMap critical facilities (health, education, emergency) and a $6,397.35\text{ km}$ routable road network to assess mountain isolation.
7. **Empirical Disaster History Alignment:** Map 22 canonical historical disaster events (1998–2024; 6,913 fatalities recorded) to establish chronic hazard exposure perimeters.
8. **Explainable & Dynamic Workflow:** Maintain 100% deterministic, rule-based, glass-box algorithms with dynamic pipeline recomputation triggered via REST API.

---

## Expected Outcome
- A fully deployed, operational web platform (**FastAPI Backend + React 18 / Vite / Leaflet GIS Frontend**) providing interactive maps, tabular directories, single-village dossiers, site capacity visualizers, and block risk summaries.
- A standardized, repeatable decision-support framework replacing subjective political or ad-hoc relocation decisions with empirical spatial evidence.
- Full compliance with SIH26191 requirements (PS-1 through PS-9) under strict scientific integrity constraints (no black-box AI governing life-safety decisions, mandatory human-in-the-loop disclaimers).

---

## Core Features
1. **Interactive Multi-Layer Leaflet GIS Map (`/map`):** Simultaneous visualization of DEM hillshading, 289 Candidate Red Zones, 653 Habitations, 2,998 Candidate Relocation Sites, 291 Critical Infrastructure points, 22 Historical Disaster markers, and routable road networks.
2. **District Executive Dashboard (`/dashboard`):** High-level KPI cards, priority tier distributions, at-risk population totals ($27,762$ in Tiers 1 & 2), and navigation shortcuts.
3. **Habitation Screening Explorer (`/villages`):** Filterable, searchable directory of 653 habitations sorted by hazard distance, demographic metrics, and priority tier.
4. **Single-Habitation Deep-Dive Dossier (`/villages/:id`):** Granular profile featuring "Why This Classification?" explainability cards, demographic breakdowns, nearest hazard polygon attribution, and administrative next steps.
5. **Candidate Relocation Sites Explorer (`/candidate-areas`):** Interactive browser for candidate relocation polygons with slope statistics, road accessibility categories, ESA WorldCover land cover, and PMAY-G capacity cards.
6. **SDMA Authority Action Center (`/authority-action`):** Priority action queue sorted by distance to hazard, Tehsil/Block risk aggregation (Ukhimath, Augustmuni, Jakholi), and one-click printable CSV report export.
7. **Operator Dynamic Recompute Control Panel (`/recompute`):** UI interface to trigger pipeline re-executions (`POST /api/pipeline/recompute`), view background execution status, and inspect per-step execution logs.
8. **Methodology & Transparency Disclosures (`/methodology`):** Detailed documentation of formulas, threshold parameters, and explicit data limitations.
9. **System & Provenance Status (`/status`):** Real-time API health probe, dataset cache integrity auditor, and OpenAPI route catalog.

---

## End-to-End Workflow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. DATA INGESTION & REPROJECTION (EPSG:4326 -> EPSG:32644)                            │
│    • Copernicus GLO-30 DEM (30m raster)                                               │
│    • Census of India 2011 Primary Census Abstract (PCA Excel)                         │
│    • DDL SHRUG v2.2 Habitation Centroids (653 villages)                               │
│    • Literature-Curated Disaster Registry (22 canonical events 1998-2024)             │
│    • OpenStreetMap Critical Infrastructure (291 points) & Road Network (6,397 km)     │
│    • ESA WorldCover 10m Land Cover Raster (Tile N30E078)                              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. GEOSPATIAL PROCESSING & SCREENING PIPELINE (processing/ Steps 3–10)                 │
│    • Step 3: Metric Slope & Aspect Derivation                                         │
│    • Step 4: Terrain Susceptibility Proxy (Slope [0°-60°] -> [0.0-1.0])               │
│    • Step 5: D8 Flow Accumulation & Topographic Wetness Index (TWI) -> Flood Proxy    │
│    • Step 6: Multi-Hazard Score: M(x,y) = 0.5 * Terrain + 0.5 * Flood                 │
│    • Step 7: Morphological 8-Connectivity Clustering -> 289 Candidate Red Zones       │
│    • Step 8: Spatial Bridge (Census PCA + SHRUG) & Point-in-Polygon / Proximity Join  │
│    • Step 9: Slope <= 20° & Exclusion Masking -> 2,998 Candidate Relocation Sites     │
│    • Step 10: Rule-Based Priority Tiers, P75 Vulnerability Flags & PMAY-G Capacity    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. FASTAPI BACKEND ASGI MICROSERVICE (backend/)                                        │
│    • In-Memory Spatial Cache (DataLoader with GeoPandas R-tree spatial indexing)      │
│    • 12 Modular REST Routers (/villages, /red-zones, /candidate-areas, /authority, …) │
│    • Dynamic Pipeline Runner (POST /api/pipeline/recompute via Python subprocess)     │
│    • Streaming CSV Exporter (/api/authority/report.csv)                               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 4. REACT 18 + VITE GIS COMMAND CENTER FRONTEND (frontend/src/)                         │
│    • Fullscreen Multi-Layer Leaflet GIS Viewer                                         │
│    • Executive KPI Dashboard, Village Dossiers, Relocation Area Capacity Cards         │
│    • SDMA Action Center with Block-Level Aggregation & Print/Export Features          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
