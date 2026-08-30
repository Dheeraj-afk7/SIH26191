# PS Requirement Traceability Matrix
# SIH26191 — Rudraprayag District, Uttarakhand
# Generated: 2026-08-30

This matrix traces each Problem Statement requirement to its dataset, processing script,
output file, API endpoint, frontend feature, and scientific limitation.

---

## PS-1: Dynamically Identify and Update Multi-Hazard Red Zones

| Field | Current | Target |
|-------|---------|--------|
| Dataset | Copernicus GLO-30 DEM (`data/raw/copernicus_glo30_rudraprayag.tif`) | + New hazard data ingestion endpoint |
| Processing Script | `processing/multihazard/derive_multihazard_score.py`, `processing/redzones/identify_candidate_zones.py` | + `scripts/recompute_pipeline.sh` or `POST /api/pipeline/trigger` |
| Output | `data/outputs/candidate_hazard_based_red_zones.geojson` (289 polygons) | + Updated outputs on re-run |
| API Endpoint | None for dynamic update | `POST /api/pipeline/trigger` (Phase A) |
| Frontend Feature | GIS Map static display | + Update timestamp display; status notification |
| Limitation | Static pipeline. Manual re-run required. No live government API feed. |
| Compliance | 35% — architecture supports re-run; no dynamic trigger mechanism demonstrated |

---

## PS-2: Integrate Hazard Intensity

| Field | Current | Target |
|-------|---------|--------|
| Dataset | GLO-30 DEM -> slope, aspect; TWI hydrology | + GSI geology (Phase B), IMD rainfall (future) |
| Processing Script | `processing/terrain/`, `processing/hydrology/`, `processing/multihazard/derive_multihazard_score.py` | + Named intensity bands |
| Output | `multihazard_score.tif`, `multihazard_classes.tif` (classes 1/2/3) | + Low/Moderate/Higher/VeryHigh named bands |
| API Endpoint | `GET /api/hazards` — hazard layer metadata | No change needed |
| Frontend Feature | GIS Map hazard layer; Village Detail MH Class display | + Named intensity labels in UI |
| Limitation | Equal 50/50 terrain-flood weighting is uncalibrated. Only 2 hazard factors. 30m DEM precision. |
| Compliance | 55% — score and classes exist; named intensity bands and calibrated weights absent |

---

## PS-3: Integrate Population Vulnerability

| Field | Current | Target |
|-------|---------|--------|
| Dataset | Census 2011 PCA (`PCA_CDB-0503-F-Census.xlsx`), SHRUG centroids | No new dataset needed |
| Processing Script | `processing/priority/build_village_priority.py` — computes 5 indicators as context fields | + Threshold-based vulnerability flags integrated into priority classification (Phase C) |
| Output | `village_priority_profiles.gpkg` — contains `illiteracy_rate`, `child_proportion`, `sc_proportion`, `st_proportion`, `non_worker_rate` as context | + `vulnerability_dimensions`, `population_exposure_class` fields |
| API Endpoint | `GET /api/villages/{id}` — returns all village fields including indicators | No change needed |
| Frontend Feature | Village Detail page shows vulnerability indicators | + Vulnerability Context Panel showing flagged dimensions |
| Limitation | Indicators NOT integrated into tier classification. No elderly or disability data. Census 2011 vintage. |
| Compliance | 40% — data exists and is displayed; not integrated into priority decision |

---

## PS-4: Integrate Disaster History

| Field | Current | Target |
|-------|---------|--------|
| Dataset | NONE | NDMA / USDMA / ISRO Bhuvan Landslide Atlas / EM-DAT (Phase B) |
| Processing Script | NONE | `processing/disaster_history/build_disaster_layer.py` (Phase B) |
| Output | NONE | `data/processed/disaster_history/disaster_incidents.geojson`, `village_disaster_proximity.gpkg` |
| API Endpoint | NONE | `GET /api/disaster-history` (Phase B) |
| Frontend Feature | Methodology page shows "NOT_ACQUIRED" status | + Historical Incident overlay on GIS map; Village Detail disaster history panel |
| Limitation | No data acquired. NDMA/SDMA data may require official request. Cannot be invented. |
| Compliance | 0% — zero implementation |

---

## PS-5: Assess Suitability of Safer Alternative Sites

| Field | Current | Target |
|-------|---------|--------|
| Dataset | GLO-30 DEM slope, TWI, red zone mask | + ISRO Bhuvan LULC (forest exclusion); OSM road network |
| Processing Script | `processing/sites/identify_candidate_areas.py` — binary exclusion + vectorization | + Suitability scoring; slope threshold config; MMU config |
| Output | `candidate_topographically_feasible_areas_attributed.geojson` (5 polygons, CA-0001 = 361,307 ha) | + Meaningfully filtered areas with suitability scores |
| API Endpoint | `GET /api/candidate-areas` | No change needed once output is improved |
| Frontend Feature | CandidateAreasPage shows 5 areas with attributes | + Suitability score display; suitability class badge |
| Limitation | CA-0001 is 361,307 ha (unconfigured slope threshold/MMU). No LULC exclusion. No road accessibility. |
| Compliance | 45% — binary exclusion exists; suitability scoring and meaningful segmentation absent |

---

## PS-6: Assess Carrying Capacity of Safer Alternative Sites

| Field | Current | Target |
|-------|---------|--------|
| Dataset | NONE (no planning standard) | NDMA / PM Awaas Yojana Gramin norms / IS 4954 (Phase D) |
| Processing Script | `processing/capacity/build_candidate_context.py` — capacity_status = NOT_ESTIMATED | + capacity.yaml configured; estimate computed |
| Output | `candidate_area_context.gpkg` — all areas: capacity_status = "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD" | + `estimated_household_capacity`, `estimated_population_capacity` per area |
| API Endpoint | `GET /api/candidate-areas` — returns capacity_status = NOT_ESTIMATED | + capacity numeric fields returned |
| Frontend Feature | CandidateAreasPage shows "not estimated" notice | + Capacity scenario display with planning standard citation |
| Limitation | No verified planning standard found/configured. Area per household/person not set in capacity.yaml. |
| Compliance | 10% — architecture ready; no numeric estimate generated |

---

## PS-7: Prioritize Habitations for Immediate / Short-Term / Medium-Term Relocation

| Field | Current | Target |
|-------|---------|--------|
| Dataset | Habitation exposure + multi-hazard class | + Disaster history (PS-4); vulnerability flags (PS-3) |
| Processing Script | `processing/priority/build_village_priority.py` — 4-tier rule-based classification | + `relocation_horizon` field; vulnerability modulation (Phase E) |
| Output | `village_priority_profiles.gpkg` — Tier1/Tier2/Tier3/BeyondProximity | + `relocation_horizon`: IMMEDIATE_FIELD_ASSESSMENT / SHORT_TERM_PLANNING_REVIEW / MEDIUM_TERM_MONITORING / ROUTINE_MONITORING |
| API Endpoint | `GET /api/villages?priority_tier=Tier1_AttentionPriority` | + Filter by relocation_horizon |
| Frontend Feature | VillageExplorerPage tier filter; VillageDetailPage tier display | + Relocation horizon badge; recommended action text |
| Limitation | Tiers do not use PS terminology. Vulnerability not integrated. No disaster history confirmation for Tier 1. |
| Compliance | 45% — classification exists; PS horizon terminology and full integration absent |

---

## PS-8: Provide Actionable Insights to State Disaster Management Authorities

| Field | Current | Target |
|-------|---------|--------|
| Dataset | decision_summary.json, village_priority_profiles.gpkg | Same + relocation_horizon, vulnerability context |
| Processing Script | `processing/priority/generate_decision_summary.py` | + Authority action narrative generator (Phase F) |
| Output | `decision_summary.json` — district statistics | + `authority_action_report.json` per village; exportable CSV |
| API Endpoint | `GET /api/decision/summary` | + `GET /api/authority/action-queue`, `GET /api/authority/report.csv` (Phase F) |
| Frontend Feature | DashboardPage KPIs; VillageDetailPage per-village | + `/authority-action` page (Phase F) with action queue, block aggregation, export |
| Limitation | No "what to do next" synthesis. No block-level aggregation. No exportable report. |
| Compliance | 50% — data accessible; actionable synthesis and authority-facing module absent |

---

## PS-9: Support Proactive Planning (Not Purely Reactive)

| Field | Current | Target |
|-------|---------|--------|
| Dataset | Pre-disaster GIS data (DEM, Census) | + Disaster history for pre-disaster signal confirmation |
| Processing Script | Full 10-step pipeline — pre-disaster screening | + Dynamic update demonstration (Phase A) |
| Output | Village priority tiers; candidate areas | + Relocation horizon labels; carrying capacity; authority action narratives |
| API Endpoint | All existing endpoints serve pre-disaster classification | + Dynamic update endpoint; relocation horizon endpoint |
| Frontend Feature | Dashboard framed as pre-disaster screening | + Authority Action Center for proactive planning use |
| Limitation | Without dynamic updates, disaster history, and capacity estimates, "proactive planning" is a claim without full demonstration. |
| Compliance | 55% — proactive framing exists; full proactive planning demonstration requires Phases A+B+C+D+E |

---

## Summary Traceability Table

| PS Req | Dataset | Processing Script | Output File | API Endpoint | Frontend Feature | Compliance |
|--------|---------|------------------|-------------|-------------|-----------------|-----------|
| PS-1 | GLO-30 DEM | derive_multihazard_score.py, identify_candidate_zones.py | candidate_hazard_based_red_zones.geojson | None (dynamic update) | Map (static) | 35% |
| PS-2 | GLO-30 DEM | derive_multihazard_score.py | multihazard_score.tif, multihazard_classes.tif | GET /api/hazards | Map, Village Detail MH Class | 55% |
| PS-3 | Census PCA 2011 | build_village_priority.py | village_priority_profiles.gpkg (context fields) | GET /api/villages/{id} | Village Detail indicators | 40% |
| PS-4 | NONE | NONE | NONE | NONE | Methodology NOT_ACQUIRED | 0% |
| PS-5 | GLO-30 DEM | identify_candidate_areas.py | candidate_topographically_feasible_areas_attributed.geojson | GET /api/candidate-areas | CandidateAreasPage | 45% |
| PS-6 | NONE (capacity standard) | build_candidate_context.py | candidate_area_context.gpkg (NOT_ESTIMATED) | GET /api/candidate-areas | CandidateAreasPage (NOT_ESTIMATED) | 10% |
| PS-7 | Exposure + MH class | build_village_priority.py | village_priority_profiles.gpkg (Tier1/2/3) | GET /api/villages | VillageExplorer, VillageDetail | 45% |
| PS-8 | decision_summary.json | generate_decision_summary.py | decision_summary.json | GET /api/decision/summary | Dashboard, VillageDetail | 50% |
| PS-9 | All | Full pipeline | All outputs | All endpoints | All pages | 55% |

---

## Phase Traceability (Post-Step-13)

| Phase | Satisfies PS | Key Output | Key API | Key Frontend |
|-------|-------------|-----------|---------|-------------|
| Phase A — Dynamic Update | PS-1, PS-9 | scripts/recompute_pipeline.sh | POST /api/pipeline/trigger | Update notification |
| Phase B — Disaster History | PS-4, PS-7 | disaster_incidents.geojson, village_disaster_proximity.gpkg | GET /api/disaster-history | Map overlay, Village Detail |
| Phase C — Vulnerability Integration | PS-3, PS-7 | village_priority_profiles.gpkg + vulnerability_dimensions | GET /api/villages/{id} | Village Detail vulnerability panel |
| Phase D — Carrying Capacity | PS-6 | candidate_area_context.gpkg (with capacity values) | GET /api/candidate-areas | CandidateAreasPage capacity scenario |
| Phase E — Relocation Horizons | PS-7 | village_priority_profiles.gpkg + relocation_horizon | GET /api/villages | VillageDetail horizon badge |
| Phase F — Authority Action Center | PS-8 | authority_action_report.csv | GET /api/authority/action-queue | /authority-action page |
| Phase G — Traceability | Demo readiness | docs/ps_requirement_traceability_matrix.md | — | — |

---

*Generated by: Antigravity Strict PS Compliance Auditor — 2026-08-30*
*Project: SIH26191 — Rudraprayag District, Uttarakhand*
