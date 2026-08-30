# POST-STEP-13 — SIH26191 Problem Statement Compliance Audit

> **Audit Type:** Strict Post-Implementation Problem Statement Compliance Audit
> **Project:** SIH26191 — Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations
> **Pilot District:** Rudraprayag, Uttarakhand, India
> **Audit Date:** 2026-08-30
> **Auditor Role:** SIH Evaluator + GIS Decision-Support Architect + Senior Software Engineer
> **Codebase Inspection:** Complete — all source files, outputs, configs, and docs reviewed

---

## 1. Executive Summary

The SIH26191 system is a disciplined, scientifically honest, and technically functional GIS decision-support prototype. The 13-step pipeline successfully delivers terrain analysis, multi-hazard screening, candidate red zone identification, habitation exposure overlay, and rule-based priority classification.

**However, strict PS compliance evaluation reveals that the project satisfies approximately 38-42% of the full Problem Statement requirements.** Five of the nine explicit PS requirements are either MISSING or only PARTIALLY implemented. The three most critical gaps are:

1. **Disaster history integration** — Zero verified disaster incident data acquired or integrated.
2. **Carrying capacity assessment** — Architecturally prepared but numerically not estimated; `capacity_status = NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD` for all 5 candidate areas.
3. **Relocation horizon alignment** — The Tier 1/2/3 system does not formally map to Immediate/Short-Term/Medium-Term relocation planning as required by the PS.

These gaps are **known to the team** and are explicitly disclosed in code, configs, and documentation (a sign of scientific integrity), but they represent material non-compliance with the Problem Statement as stated.

**Final PS Compliance Score: 38-42% (Strict) / 58-62% (Generous)**

---

## 2. Official Problem Statement Requirements (Extracted)

From the PS description and expected solution (Ministry of Home Affairs / NDRF, DM Division):

| # | PS Requirement |
|---|----------------|
| PS-1 | Dynamically identify and update multi-hazard Red Zones |
| PS-2 | Integrate hazard intensity |
| PS-3 | Integrate population vulnerability |
| PS-4 | Integrate disaster history |
| PS-5 | Assess suitability of safer alternative sites |
| PS-6 | Assess carrying capacity of safer alternative sites |
| PS-7 | Prioritize vulnerable habitations for Immediate / Short-Term / Medium-Term relocation |
| PS-8 | Provide actionable insights to State Disaster Management Authorities |
| PS-9 | Support proactive planning rather than purely reactive post-disaster response |

---

## 3. Current System Architecture Summary

### 3.1 Processing Pipeline (13 Steps)

| Step | Module | Script | Output |
|------|--------|--------|--------|
| Steps 1-3 | DEM Acquisition & Terrain | — | `slope_degrees.tif`, `aspect_degrees.tif` |
| Steps 4-5 | Hazard Proxies | `processing/terrain/`, `processing/hydrology/` | `terrain_susceptibility_proxy.tif`, `flood_exposure_proxy.tif`, `topographic_wetness_index.tif` |
| Step 6 | Multi-Hazard Score | `processing/multihazard/derive_multihazard_score.py` | `multihazard_score.tif`, `multihazard_classes.tif` |
| Step 7 | Red Zone Generation | `processing/redzones/identify_candidate_zones.py` | `candidate_hazard_based_red_zones.geojson/.gpkg` (289 polygons) |
| Step 8 | Habitation Baseline + Exposure | `processing/exposure/` | `habitation_baseline.geojson`, `habitation_exposure.geojson` |
| Step 9 | Candidate Areas | `processing/sites/identify_candidate_areas.py` | `candidate_topographically_feasible_areas_attributed.geojson` (5 polygons) |
| Step 10 | Decision Engine | `processing/priority/build_village_priority.py`, `generate_decision_summary.py`, `capacity/build_candidate_context.py` | `village_priority_profiles.gpkg`, `decision_summary.json` |
| Step 11 | Backend API | `backend/main.py` + routes | FastAPI on port 8000 |
| Steps 12-13 | Frontend | `frontend/src/` (React+Vite) | 7-page interactive dashboard |

### 3.2 Available Data

| Dataset | Source | Status |
|---------|--------|--------|
| Copernicus GLO-30 DEM | ESA / Copernicus | ACQUIRED |
| Census 2011 PCA | Office of Registrar General | ACQUIRED (PCA_CDB-0503-F-Census.xlsx) |
| SHRUG v2.2 Centroids | Development Data Lab | ACQUIRED (rudraprayag_census_villages_shrug.geojson) |
| OSM Settlements | OpenStreetMap | ACQUIRED (rudraprayag_settlements_osm.geojson) |
| SHRUG demographic keys | Development Data Lab | ACQUIRED (multiple SHRID CSV files) |
| NDMA/SDMA Disaster History | SDMA Uttarakhand | NOT ACQUIRED |
| Critical Infrastructure | OSM / Dept. Surveys | NOT ACQUIRED |
| Road Network (routable) | PWD / Survey of India | NOT ACQUIRED |
| LULC / Forest Cover | ISRO Bhuvan | NOT ACQUIRED |
| Verified Capacity Standards | NDMA / State Housing Board | NOT CONFIGURED |

### 3.3 Frontend Pages (7 pages)

- `/dashboard` — Executive overview with KPIs, tier distribution
- `/map` — Interactive Leaflet GIS map (red zones + habitations)
- `/villages` — Village Explorer with priority tier filter
- `/villages/:id` — Village Detail Profile
- `/candidate-areas` — Candidate area cards (capacity = NOT_ESTIMATED)
- `/methodology` — Methodology + Limitations page
- `/status` — System/Data Status page

### 3.4 API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET /api/health | System health check |
| GET /api/metadata | Project metadata |
| GET /api/decision/summary | District-level statistics |
| GET /api/decision/metadata | Processing provenance |
| GET /api/villages | All village profiles (filterable by tier, name) |
| GET /api/villages/{id} | Single village detail |
| GET /api/red-zones | Candidate red zone polygons |
| GET /api/candidate-areas | Candidate topographically feasible areas |
| GET /api/hazards | Hazard layer metadata |

---

## 4. Strict PS Compliance Matrix

### PS-1: Dynamically Identify and Update Multi-Hazard Red Zones

**Current Implementation:** Static multi-step pipeline. Red zones are pre-generated from fixed DEM inputs. No runtime update mechanism exists. Config-driven thresholds enable re-run, but there is no API endpoint for pipeline triggering, no file-watcher, no webhook, and no dynamic update UI. The system correctly does NOT fake real-time data.

**Code/File Evidence:**
- `processing/redzones/identify_candidate_zones.py` — manual re-run only
- `configs/project.yaml` — config-driven but static
- `backend/main.py` — no pipeline trigger endpoint
- `backend/services/data_loader.py` — loads on startup, no hot-reload

**Status:** PARTIAL | **Compliance:** 35%

**Gap:** No dynamic update demonstration. PS specifically requires "dynamically identify and update." Manual pipeline re-run exists but is not exposed to any UI or API endpoint. No data ingestion endpoint. No update workflow demonstrated.

**Recommended Action:** Phase A — Implement a documented "operator re-run workflow" with `scripts/recompute_pipeline.sh` OR a `POST /api/pipeline/trigger` endpoint. Demonstrate the data -> validate -> recompute -> refresh cycle live in SIH demo.

---

### PS-2: Integrate Hazard Intensity

**Current Implementation:** Multi-hazard score integrates terrain susceptibility proxy (slope/aspect-based) and TWI-based flood exposure proxy with equal 50%/50% weights. Zonal statistics (mean score, max score, terrain/flood contribution) are attributed to red zone polygons. MH class at village centroid (1/2/3) is sampled from raster and used in tier classification.

**Code/File Evidence:**
- `processing/multihazard/derive_multihazard_score.py` — `M(x,y) = 0.5*T + 0.5*F`
- `processing/redzones/identify_candidate_zones.py` — zonal stats on red zone polygons
- `processing/priority/build_village_priority.py` L486-500 — `mh_class_at_centroid` used in Tier 1 condition

**Status:** PARTIAL | **Compliance:** 55%

**Gap:** (a) Equal 50/50 weighting is explicitly noted as "uncalibrated deterministic baseline." (b) Only terrain + hydrology — no rainfall, geology, lithology, or LULC hazard factors. (c) No named hazard intensity bands (Low/Medium/High/Very High LSI).

**Recommended Action:** Formalize MH class into named intensity bands in UI and reports. Research open GSI lithology or IMD gridded rainfall for Phase B supplemental inputs.

---

### PS-3: Integrate Population Vulnerability

**Current Implementation:** Five vulnerability indicators are computed from Census 2011 PCA: `illiteracy_rate`, `child_proportion`, `sc_proportion`, `st_proportion`, `non_worker_rate`. These are stored as CONTEXT FIELDS and displayed in Village Detail Page. Code explicitly states: "Vulnerability indicators are NOT used in tier assignment. No composite weight is applied."

**Code/File Evidence:**
- `processing/priority/build_village_priority.py` L37-40: indicators are context fields only
- `configs/priority_thresholds.yaml` L123-129: vulnerability marked NOT_ACQUIRED/context-only

**Status:** PARTIAL | **Compliance:** 40%

**Gap:** Data exists and is displayed, but is NOT integrated into the priority classification decision. PS requires vulnerability to be **integrated** — it should influence or modulate the priority output.

**Recommended Action:** Phase C — Design a transparent vulnerability framework using threshold-based flags (not AHP/MCDA). Modulate tier labels or publish separate Vulnerability Priority Index.

---

### PS-4: Integrate Disaster History

**Current Implementation:** ZERO disaster history integration. `configs/priority_thresholds.yaml` disaster_history section: `status: "NOT_ACQUIRED"`. No NDMA, SDMA, or EM-DAT data was acquired.

**Code/File Evidence:**
- `configs/priority_thresholds.yaml` L108-121: `status: "NOT_ACQUIRED"`
- `frontend/src/pages/MethodologyPage.tsx` L11: `{ name: 'Disaster History (NDMA / SDMA)', status: 'NOT_ACQUIRED' }`
- `docs/step10_decision_engine_report.md` L146: "Historical disaster evidence | NOT ACQUIRED"

**Status:** MISSING | **Compliance:** 0%

**Gap:** No disaster incident data. No GIS incident layer. No village proximity-to-incident analysis. No historical pattern analysis. PS explicitly requires disaster history integration. PROJECT_SPEC Module 5 states: "disaster history is a required scoring input where verified data exists."

**Recommended Action:** Phase B (Critical) — Research and acquire NDMA/BHUVAN/USDMA disaster datasets. Design incident data model and GIS layer. If zero data is acquirable, design the unavailable-data fallback UI showing "NOT ACQUIRED — pending SDMA authorization."

---

### PS-5: Assess Suitability of Safer Alternative Sites

**Current Implementation:** Step 9 identifies 5 Candidate Topographically Feasible Areas using terrain screening (slope exclusion, hazard zone exclusion, TWI exclusion). Sites are attributed with mean slope, distance to red zone, nearest village. All labeled "PRELIMINARY DECISION-SUPPORT CANDIDATES REQUIRING FIELD VERIFICATION."

**Code/File Evidence:**
- `processing/sites/identify_candidate_areas.py` — multi-criterion exclusion masks (Step 9A/9B/9C)
- `data/outputs/candidate_topographically_feasible_areas_attributed.geojson` — 5 polygons
- `data/processed/decision/candidate_area_context.gpkg`
- `frontend/src/pages/CandidateAreasPage.tsx`

**Status:** PARTIAL | **Compliance:** 45%

**Gap:** (a) CA-0001 covers 361,307 ha — virtually the entire district — making it a meaningless "area." Configurable slope threshold and MMU filters are NOT_CONFIGURED. (b) No LULC exclusion. (c) No road accessibility suitability scoring. (d) No multi-criterion suitability score per site.

**Recommended Action:** Configure slope upper threshold (e.g., 15 degrees) and MMU (e.g., 1 ha) in `project.yaml`. Research ISRO Bhuvan LULC for forest exclusion. Implement scored suitability output field.

---

### PS-6: Assess Carrying Capacity of Safer Alternative Sites

**Current Implementation:** Architecture exists in `processing/capacity/build_candidate_context.py` and `configs/capacity.yaml`. The capacity config correctly requires a verified planning authority citation before generating any estimate. All 5 candidate areas carry `capacity_status = "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD"`.

**Code/File Evidence:**
- `configs/capacity.yaml` L6: `status: "NOT_CONFIGURED"`, L44: `area_per_household_m2: null`
- `processing/capacity/build_candidate_context.py` L80: `_CAPACITY_STATUS = "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD"`
- `docs/step10_decision_engine_report.md` L34: "Capacity status | NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD"

**Status:** MISSING (Architecture Prepared, Values Absent) | **Compliance:** 10%

**Gap:** This is a critical PS requirement and the PS title phrase "Carrying Capacity Assessment." Currently no capacity estimate exists for any site. A defensible planning scenario must be researched.

**Recommended Action:** Phase D (Critical) — Research Indian government planning standards: IS 4954:1968, PM Awaas Yojana Gramin norms (25 m2 per household), NDMA National Guidelines. If found, configure `capacity.yaml` and generate a clearly labeled "Preliminary Capacity Scenario" estimate.

---

### PS-7: Prioritize Habitations for Immediate / Short-Term / Medium-Term Relocation

**Current Implementation:** Three tiers exist: Tier 1 (Attention Priority), Tier 2 (Elevated Attention), Tier 3 (Monitoring). These are proximity + MH class based. The tier labels do NOT use the PS terminology "Immediate / Short-Term / Medium-Term." Tier 1 classification does NOT incorporate disaster history.

**Code/File Evidence:**
- `processing/priority/build_village_priority.py` L469-550 — rule logic
- `configs/priority_thresholds.yaml` — tier definitions
- `docs/step10_decision_engine_report.md` L49-56 — Tier table

**Status:** PARTIAL | **Compliance:** 45%

**Gap:** (a) Tier labels do not formally map to PS-mandated relocation horizons. (b) Vulnerability is not integrated into tier assignment. (c) Disaster history is absent from Tier 1 definition.

**Recommended Action:** Phase E — Map Tier 1 to "Immediate Field Assessment Required," Tier 2 to "Short-Term Planning Review," Tier 3 to "Medium-Term Monitoring." Add vulnerability and disaster history as modulating factors.

---

### PS-8: Provide Actionable Insights to State Disaster Management Authorities

**Current Implementation:** Dashboard provides KPIs, tier distribution, top-priority village list. Village Detail page shows per-village profiles. Methodology page explains limitations. API provides machine-readable JSON. However, no dedicated "Authority Action Center" exists. No "what to do next" recommendation module. No printable report.

**Code/File Evidence:**
- `frontend/src/pages/DashboardPage.tsx` — KPIs
- `frontend/src/pages/VillageDetailPage.tsx` — per-village profile
- `backend/api/routes/decision.py` — GET /api/decision/summary

**Status:** PARTIAL | **Compliance:** 50%

**Gap:** "Actionable insights" requires more than a dashboard. SDMA needs: (a) a prioritized action queue, (b) recommended next steps per priority class, (c) exportable report for planning meetings.

**Recommended Action:** Phase F — Design Authority Action Center page with village-by-village recommended actions, block-level aggregation, exportable priority report.

---

### PS-9: Support Proactive Planning (Not Purely Reactive)

**Current Implementation:** The system is proactive in concept — it performs pre-disaster screening rather than post-disaster damage mapping. However, without disaster history integration, dynamic updates, or carrying capacity, the "proactive planning" narrative is incomplete at a SIH demonstration level.

**Code/File Evidence:**
- `docs/PROJECT_SPEC.md` L9: "Supports dynamic recalculation when new relevant data is supplied"
- `frontend/src/pages/DashboardPage.tsx` — pre-disaster framing

**Status:** PARTIAL | **Compliance:** 55%

**Gap:** Without dynamic update capability, "proactive" is a claim but not a demonstrated feature. Without carrying capacity, planning cannot be quantified. Without disaster history, the proactive signal lacks historical validation.

**Recommended Action:** Phases A + B + C + D + E together constitute the proactive planning completion.

---

## 5. Aggregate PS Compliance Summary Table

| PS Requirement | Status | Compliance % |
|----------------|--------|-------------|
| PS-1: Dynamic Red Zone Updates | PARTIAL | 35% |
| PS-2: Hazard Intensity Integration | PARTIAL | 55% |
| PS-3: Population Vulnerability Integration | PARTIAL | 40% |
| PS-4: Disaster History Integration | MISSING | 0% |
| PS-5: Suitability of Alternative Sites | PARTIAL | 45% |
| PS-6: Carrying Capacity Assessment | MISSING (arch only) | 10% |
| PS-7: Immediate/Short-Term/Medium-Term Prioritization | PARTIAL | 45% |
| PS-8: Actionable Insights to SDMA | PARTIAL | 50% |
| PS-9: Proactive Planning | PARTIAL | 55% |
| **WEIGHTED AVERAGE** | — | **38-42%** |

---

## 6. What the System Has Completed (Credit)

| Feature | Status | Evidence |
|---------|--------|----------|
| Copernicus GLO-30 DEM acquisition and validation | COMPLETE | `data/raw/copernicus_glo30_rudraprayag.tif` |
| Slope + aspect terrain analysis | COMPLETE | `data/processed/terrain/slope_degrees.tif` |
| TWI-based flood exposure proxy | COMPLETE | `data/processed/hydrology/topographic_wetness_index.tif` |
| Multi-hazard score and classes (deterministic baseline) | COMPLETE | `data/processed/hazards/multihazard_score.tif` |
| 289 candidate red zone polygons with zonal stats | COMPLETE | `data/outputs/candidate_hazard_based_red_zones.geojson` |
| Census 2011 habitation baseline (653 villages) | COMPLETE | `data/processed/habitations/habitation_baseline.geojson` |
| Habitation hazard proximity overlay | COMPLETE | `data/processed/exposure/habitation_exposure.geojson` |
| 5 candidate terrain area polygons | PARTIAL | `data/outputs/candidate_topographically_feasible_areas_attributed.geojson` |
| Vulnerability indicators as context fields | PARTIAL | `village_priority_profiles.gpkg` |
| Rule-based 4-tier priority classification | COMPLETE | `village_priority_profiles.gpkg` |
| Decision summary JSON | COMPLETE | `data/processed/decision/decision_summary.json` |
| FastAPI backend with 7 endpoint groups | COMPLETE | `backend/main.py`, `backend/api/routes/` |
| Interactive GIS Map (Leaflet) | COMPLETE | `frontend/src/pages/MapPage.tsx` |
| Executive Dashboard | COMPLETE | `frontend/src/pages/DashboardPage.tsx` |
| Village Explorer + Detail | COMPLETE | `frontend/src/pages/VillageExplorerPage.tsx`, `VillageDetailPage.tsx` |
| Methodology + Transparency page | COMPLETE | `frontend/src/pages/MethodologyPage.tsx` |
| System Status page | COMPLETE | `frontend/src/pages/SystemStatusPage.tsx` |
| Scientific disclaimers throughout | COMPLETE | All scripts, config, UI |
| Configurable thresholds via YAML | COMPLETE | `configs/priority_thresholds.yaml`, `capacity.yaml`, `project.yaml` |

---

## 7. Missing Requirements (Detail)

### 7.1 Disaster History (PS-4) — Zero Implementation

- No NDMA data, no SDMA data, no EM-DAT data
- No GIS incident layer; no village proximity-to-incident analysis
- Only documentation of absence (NOT_ACQUIRED label in configs and methodology page)

**Severity: CRITICAL** — PS explicitly names this as a required integration.

### 7.2 Carrying Capacity (PS-6) — Architecture Only

- `configs/capacity.yaml` exists but all values are null
- `capacity_status = "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD"` on all 5 areas
- No NDMA/BIS/State Housing Board standard has been researched or configured

**Severity: CRITICAL** — PS title literally includes "Carrying Capacity Assessment."

### 7.3 Dynamic Update Architecture (PS-1) — Manual Only

- No pipeline trigger API endpoint; no new-data ingestion endpoint
- `data_loader.load_all()` runs once at startup; no hot-reload

**Severity: HIGH** — PS explicitly requires "dynamically identify and update."

---

## 8. Critical Scientific / Data Gaps

| # | Gap | Scientific Impact | Severity |
|---|-----|------------------|----------|
| G-1 | No verified disaster history dataset | Cannot confirm Tier 1 by historical evidence | CRITICAL |
| G-2 | Carrying capacity = 0 numeric outputs | PS title requirement unmet | CRITICAL |
| G-3 | CA-0001 = 361,307 ha (unconfigured filters) | Candidate area output non-demonstrable | HIGH |
| G-4 | Vulnerability not integrated into priority | PS-3 only 40% satisfied | HIGH |
| G-5 | No dynamic update demonstration | PS-1 only 35% satisfied | HIGH |
| G-6 | Equal-weight MH integration (uncalibrated) | Scientific basis for weights not verified | MEDIUM |
| G-7 | Administrative centroids not settlement footprints | Proximity distances may understate real exposure | MEDIUM |
| G-8 | Census 2011 baseline (15 years old) | Population figures outdated | MEDIUM |
| G-9 | No road accessibility analysis | Candidate area accessibility unmeasured | MEDIUM |
| G-10 | No LULC / forest exclusion | Protected area status of candidate areas unknown | MEDIUM |

---

## 9. Dataset Acquisition Recommendations

### 9.1 NDMA / SDMA Disaster History (Priority: CRITICAL)

| Field | Detail |
|-------|--------|
| Official Source | NDMA (ndma.gov.in), BHUVAN (bhuvan.nrsc.gov.in), USDMA |
| Public Availability | BHUVAN Hazard Atlas: partially public; NDMA: requires data request |
| Geographic Coverage | District-level and below |
| Format | Shapefile / GeoJSON / CSV |
| Scientific Reliability | Official government data — high if sourced directly |
| Recommended Action | (a) Download BHUVAN Landslide Hazard Zones for Uttarakhand; (b) Submit data request to USDMA Dehradun for Rudraprayag district disaster records; (c) Use ISRO Bhuvan "Disaster Management" layer; (d) EM-DAT (emdat.be) as supplemental |
| Proxy if Unavailable | Design incident data model with NOT_AVAILABLE status; document acquisition attempt |

### 9.2 ISRO Bhuvan LULC (Priority: HIGH)

| Field | Detail |
|-------|--------|
| Official Source | ISRO Bhuvan (bhuvan.nrsc.gov.in) — National Land Use Land Cover |
| Public Availability | Available for download; requires free registration |
| Format | GeoTIFF / Shapefile |
| Recommended Action | Download Uttarakhand LULC; clip to Rudraprayag; use forest/protected area classes to exclude from candidate areas |

### 9.3 GSI Landslide Inventory (Priority: HIGH for PS-4)

| Field | Detail |
|-------|--------|
| Official Source | Geological Survey of India (gsi.gov.in) |
| Public Availability | Landslide Atlas of India (ISRO-NRSC) — partially public |
| Recommended Action | Download "Landslide Atlas of India" from NRSC; extract district-level incident records; convert to GIS points |

### 9.4 Capacity Planning Standard (Priority: CRITICAL)

| Field | Detail |
|-------|--------|
| Research Targets | IS 4954:1968; PM Awaas Yojana Gramin norms (25 m2 per unit); NDMA National DM Plan (rehabilitation chapter); Uttarakhand State DMP |
| Recommended Action | Review NDMA National DM Guidelines Chapter on Rehabilitation and Resettlement. If standard found: document exact citation, configure `capacity.yaml`, generate "Preliminary Capacity Scenario" |

### 9.5 OSM Road Network (Priority: MEDIUM)

| Field | Detail |
|-------|--------|
| Source | OpenStreetMap via GEOFABRIK India extract |
| Public Availability | Freely downloadable |
| Recommended Action | Download India OSM extract; clip to Rudraprayag; compute distance from candidate areas to nearest village |

---

## 10. Post-Step-13 Implementation Roadmap

### PHASE A — Dynamic Red Zone Update Architecture

**Priority:** HIGH (PS-1) | **Complexity:** Medium | **Risk:** Low

Demonstrate this data flow for SIH judges:

    New hazard data supplied (operator copy)
        -> Input validation (schema, CRS, completeness check)
        -> Hazard layer update (terrain or flood proxy)
        -> Multi-hazard recomputation (Step 6)
        -> Red zone regeneration (Step 7)
        -> Habitation exposure reclassification (Step 8)
        -> Village priority reclassification (Step 10)
        -> API hot-reload / backend restart
        -> Dashboard/map refresh

Implementation: Operator re-run workflow with `scripts/recompute_pipeline.sh` OR `POST /api/pipeline/trigger` endpoint.

**Key rule:** Do NOT fake real-time data. Demonstrate update cycle with updated weight config or pre-prepared DEM variant.

---

### PHASE B — Disaster History Intelligence

**Priority:** CRITICAL (PS-4) | **Complexity:** Medium-High | **Risk:** Medium (data acquisition required)

**Incident Data Model:**

    disaster_incident:
      incident_id: str        # e.g., "DIS-RDP-2013-001"
      date: date              # YYYY-MM-DD
      hazard_type: str        # "LANDSLIDE" | "FLOOD" | "CLOUDBURST"
      district: str           # "RUDRAPRAYAG"
      block: str              # Sub-district block name
      location_name: str      # Village / settlement name
      geometry: Point         # WGS84 coordinates
      severity: str           # "MINOR" | "MODERATE" | "MAJOR" | "CATASTROPHIC"
      deaths: int             # null if unknown
      affected_population: int # null if unknown
      source: str             # "NDMA" | "USDMA" | "ISRO_BHUVAN" | "NEWS_REPORT"
      verification_status: str # "OFFICIAL" | "SECONDARY" | "UNVERIFIED"

Processing Design:
- GIS incident layer: `data/processed/disaster_history/disaster_incidents.geojson`
- Village proximity analysis: compute `nearest_incident_distance_m`, `incidents_within_1km`, `incidents_within_5km`
- Tier modulation: villages with confirmed historical incident within 1 km AND Tier 2 proximity -> elevate to Tier 1 consideration
- Unavailable data fallback UI: "Disaster History: NOT ACQUIRED — pending SDMA authorization"

---

### PHASE C — Population Vulnerability Integration

**Priority:** HIGH (PS-3) | **Complexity:** Medium | **Risk:** Low-Medium

**Available Census PCA 2011 Indicators (VERIFIED):**

| Indicator | Field | Status |
|-----------|-------|--------|
| Total population | tot_pop | VERIFIED |
| Total households | households | VERIFIED |
| SC population | pop_sc | VERIFIED |
| ST population | pop_st | VERIFIED |
| Children under 6 | P_06 | VERIFIED (Census PCA) |
| Illiterate population | P_ILL | VERIFIED (Census PCA) |
| Non-worker population | NON_WORK_P | VERIFIED (Census PCA) |

NOT available (do NOT invent):
- Elderly population (65+) — not a distinct PCA field
- Disability population — not in standard PCA

**Vulnerability Framework Design (threshold-based, NOT AHP/MCDA):**

    DIMENSION 1 — Exposure Scale
      population_exposure_class = "Very High" / "High" / "Moderate" / "Low"

    DIMENSION 2 — Demographic Vulnerability Context Flags
      child_vulnerability = child_proportion > threshold -> "High Child Pop"
      sc_st_context = sc_proportion + st_proportion > threshold -> "High SC/ST"
      non_worker_dependency = non_worker_rate > threshold -> "High Dependency"
      illiteracy_context = illiteracy_rate > threshold -> "High Illiteracy"

    OUTPUT — Vulnerability Context Profile (NOT a composite score)
      vulnerability_dimensions: ["High Child Pop", "High Dependency"]
      vulnerability_note: "2 of 4 vulnerability factors flagged"

Critical design rule — clearly distinguish:
- VERIFIED DATA: tot_pop, pop_sc, pop_st
- DERIVED INDICATOR: illiteracy_rate = P_ILL / TOT_P
- DECISION-SUPPORT CLASSIFICATION: "High Dependency" (threshold-based category)

---

### PHASE D — Carrying Capacity Assessment

**Priority:** CRITICAL (PS-6, PS Title) | **Complexity:** Low-Medium | **Risk:** High if no verified standard found

Research tasks:
1. NDMA "National Disaster Management Guidelines" (2007) — Appendix on resettlement
2. NDMA "National Disaster Management Plan" (2019) — Chapter 7: Response & Relief
3. PM Awaas Yojana Gramin technical guidelines — plot size norms (18-25 m2 built area)
4. IS 4954:1968 "Recommendations for housing sites" — density and plot area norms
5. Uttarakhand State Disaster Management Plan — rehabilitation site norms

If verified standard found:

    planning_standard:
      authority: "Ministry of Rural Development"
      document: "Pradhan Mantri Awaas Yojana - Gramin Technical Guidelines"
      section: "Annex 4 — Cluster Housing Norms"
      year: 2023
      citation: "MoRD, PMAY-G Technical Guidelines 2023, Annex 4, p. 47"

    area_per_household_m2: 25.0

    # Output per candidate area (example for CA-0002 = 0.9 ha):
    estimated_household_capacity: 360    # 9000 / 25
    estimated_population_capacity: 1440  # 360 * 4.0 avg_hh_size
    confidence: "PRELIMINARY_PLANNING_SCENARIO"
    limitations: "Excludes setbacks, roads, common areas. Not engineering certified."

If NO verified standard found:
- Retain NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD
- Create `docs/capacity_research_notes.md` documenting what was researched
- Demonstrate due diligence to SIH judges

---

### PHASE E — Relocation Planning Horizon

**Priority:** HIGH (PS-7) | **Complexity:** Low | **Risk:** Low

Tier-to-Horizon Mapping:

    Tier 1 (dist <= 500m, MH Class >= 2 OR overlap):
      -> Relocation Horizon: IMMEDIATE_FIELD_ASSESSMENT
      -> Authority action: "Recommend immediate field verification by SDMA team"

    Tier 2 (dist <= 2000m):
      -> Relocation Horizon: SHORT_TERM_PLANNING_REVIEW
      -> Authority action: "Recommend inclusion in 1-3 year district planning cycle"

    Tier 3 (dist <= 5000m):
      -> Relocation Horizon: MEDIUM_TERM_MONITORING
      -> Authority action: "Include in district hazard monitoring programme"

    Beyond Proximity:
      -> Relocation Horizon: ROUTINE_MONITORING

Output fields to add to `village_priority_profiles.gpkg`:
- `relocation_horizon`: "IMMEDIATE_FIELD_ASSESSMENT" | "SHORT_TERM_PLANNING_REVIEW" | "MEDIUM_TERM_MONITORING" | "ROUTINE_MONITORING"
- `recommended_action`: str
- `horizon_rationale`: str (which indicators triggered this)
- `horizon_limitations`: str (what was not available to confirm this)

Critical rule: Every output must include "DECISION SUPPORT ONLY — NOT AN OFFICIAL RELOCATION ORDER"

---

### PHASE F — Authority Action Center

**Priority:** HIGH (PS-8) | **Complexity:** Medium | **Risk:** Low

New frontend page `/authority-action` serving as the SDMA-facing decision-support module.

Components:
1. Priority Action Queue — Tier 1 villages with recommended field actions
2. Block-Level Aggregation — tier distribution by tehsil/block
3. Candidate Area Action Panel — sites with verification actions required
4. Export Module — CSV export of priority list; browser print for report
5. Disclaimer Banner — "Decision Support Only — Official SDMA Authorization Required"

Action narrative template:

    Village: Marora (Tier 1, 42m from RZ-017)
      Recommended: IMMEDIATE field assessment by SDMA team
      Priority reason: Centroid 42m from Candidate Red Zone; MH Class 2 at site
      Next step: Geotechnical survey; community consultation; official site visit report

---

### PHASE G — PS Traceability and Demo Readiness

**Priority:** MEDIUM | **Complexity:** Low | **Risk:** None

Create `docs/ps_requirement_traceability_matrix.md` and SIH demo script.

Demo Script for SIH presentation:
1. Show DEM -> Red Zone pipeline output (GIS map)
2. Show Tier 1 villages with vulnerability context
3. Show (if acquired) disaster history overlay
4. Show candidate areas with capacity scenario
5. Show authority action recommendations
6. Show "dynamic update": change threshold in `configs/priority_thresholds.yaml` -> re-run Step 10 -> show updated tier counts

---

## 11. Priority Order for Implementation

| Priority | Phase | PS Requirement | Reason to Do First |
|----------|-------|---------------|--------------------|
| 1 (CRITICAL) | Phase D — Carrying Capacity | PS-6 | PS title includes "Carrying Capacity Assessment." Currently 0 numeric output. Architecturally ready — blocked only by research (1-2 days). |
| 2 (CRITICAL) | Phase B — Disaster History | PS-4 | Required by PS and PROJECT_SPEC Module 5. Currently 0% compliant. Even partial dataset dramatically improves score. |
| 3 (CRITICAL) | Phase E — Relocation Horizon Labels | PS-7 | Low effort, high impact. Adds Immediate/Short-Term/Medium-Term language directly from PS. |
| 4 (HIGH) | Phase C — Vulnerability Integration | PS-3 | Data exists. Framework design needed. |
| 5 (HIGH) | Phase A — Dynamic Update Demo | PS-1 | Manual re-run with documented workflow satisfies PS. |
| 6 (HIGH) | Phase F — Authority Action Center | PS-8 | Tangible SDMA-facing output. Very high demo impact. |
| 7 (MEDIUM) | Configure CA slope/MMU thresholds | PS-5 | Configuring project.yaml to set slope upper limit (15 deg) and MMU (1 ha) resolves CA-0001 problem. |
| 8 (MEDIUM) | Phase G — Traceability Matrix | Demo | Helps answer judge questions. |

---

## 12. Estimated Implementation Complexity

| Phase | Effort | Blocking Dependencies | Weeks (solo) |
|-------|--------|----------------------|-------------|
| Phase A — Dynamic Update | Medium | None | 1-2 |
| Phase B — Disaster History | High | Dataset acquisition | 2-4 |
| Phase C — Vulnerability Integration | Medium | Data already available | 1-2 |
| Phase D — Carrying Capacity | Low-Medium | Standard research | 1 |
| Phase E — Relocation Horizons | Low | Phases C, D (partial) | 0.5-1 |
| Phase F — Authority Action Center | Medium | Phases C, D, E | 1-2 |
| Phase G — Traceability | Low | None | 0.5 |
| CA-0001 Threshold Config | Very Low | None | 0.5 |

---

## 13. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| NDMA/SDMA disaster data not publicly available | HIGH | HIGH | Use ISRO Bhuvan Landslide Atlas + published government reports; design unavailable-data fallback |
| No verified carrying capacity standard found | MEDIUM | HIGH | Document research attempt; use PMAY-G norms as provisional scenario with heavy disclaimer |
| CA-0001 problem not resolved before demo | MEDIUM | HIGH | Configure slope threshold (15 deg) and MMU (1 ha) in project.yaml — 1-hour fix |
| Vulnerability composite score scientifically challenged | HIGH | MEDIUM | Use explainable threshold-based flags rather than AHP/composite score |
| Dynamic update demo crashes live | MEDIUM | MEDIUM | Pre-record the update demo as a video; have pipeline re-run scripted |
| Census 2011 data vintage challenged | HIGH | LOW | Acknowledge openly; Census 2021 was delayed; 2011 is the authoritative current source |

---

## 14. Recommended Next Phase

**IMMEDIATE PRIORITY — Implement Phase D (Carrying Capacity) first.**

The project title is "Carrying Capacity Assessment." Judges will ask "what is the carrying capacity?" and the current answer is `NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD` for all sites. This gap is simultaneously:

1. The highest-visibility PS requirement (title-level)
2. Architecturally almost complete (config + script ready)
3. Blocked only by research (not engineering)
4. Resolvable within 1-2 days if an Indian planning standard is found

Research action: Review NDMA website, PM Awaas Yojana technical guidelines, IS 4954:1968, and Uttarakhand State DMP. If PMAY-G norms (18-25 m2 per household) are found, configure `capacity.yaml`, re-run `build_candidate_context.py`, and display carrying capacity scenarios in UI.

**Second immediate priority — Phase E (Relocation Horizon Labels).** Adding `relocation_horizon` field mapping Tier 1 to "IMMEDIATE_FIELD_ASSESSMENT" is a 4-hour implementation that directly satisfies a PS explicit requirement.

---

## 15. Final PS Compliance Score

| Dimension | Score |
|-----------|-------|
| Technical pipeline completeness | 72% |
| PS requirement coverage | 38-42% |
| Scientific rigor and transparency | 90% |
| Data integrity (no fabricated data) | 100% |
| UI/UX and authority usability | 55% |
| **Overall SIH Evaluation Estimate** | **50-55%** |

> **Note on Scientific Rigor Score (90%):** Many competing SIH teams fabricate disaster data, invent AHP weights, or claim unofficial sites are "safe." This team's explicit disclaimer culture, NOT_ACQUIRED labeling, and NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD markers demonstrate scientific honesty that will be recognized by experienced evaluators. The honest disclosure of limitations is itself a strong PS compliance signal — it demonstrates that the team understands the problem deeply enough to know what is missing.

---

## 16. Files Inspected for This Audit

- `processing/priority/build_village_priority.py` (820 lines)
- `processing/priority/generate_decision_summary.py` (624 lines)
- `processing/multihazard/derive_multihazard_score.py` (354 lines)
- `processing/redzones/identify_candidate_zones.py` (479 lines)
- `processing/sites/identify_candidate_areas.py` (1183 lines)
- `processing/exposure/habitation_exposure_overlay.py` (609 lines)
- `processing/capacity/build_candidate_context.py` (402 lines)
- `backend/main.py`, `backend/api/routes/` (all 6 route files)
- `backend/services/data_loader.py`
- `frontend/src/pages/` (all 7 page files)
- `configs/capacity.yaml`, `configs/priority_thresholds.yaml`, `configs/project.yaml`
- `data/processed/decision/decision_summary.json`
- `data/outputs/` (directory listing)
- `data/raw/` (directory listing + habitations subdirectory)
- `docs/step10_decision_engine_report.md`
- `docs/PROJECT_SPEC.md`

*Audit produced by: Antigravity Strict PS Compliance Auditor — 2026-08-30*
