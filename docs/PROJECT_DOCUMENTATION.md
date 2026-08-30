# SIH26191 — Comprehensive Project Documentation & Demo Visuals

This document serves as the visual and technical evidence of the implemented decision-support platform for SIH26191 (Prioritization of villages and finding topographically feasible areas for rehabilitation). 

All outputs and classifications depicted herein are **PRELIMINARY DECISION-SUPPORT CANDIDATES** and are strictly not official authorizations or government declarations.

---

## 1. Executive Dashboard Overview

![Figure 1: Executive Dashboard](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/01_dashboard.png)
**Figure 1: Executive Dashboard**
- **Feature Name:** Project Dashboard
- **Workflow / Value:** Provides a high-level summary of the entire Rudraprayag district analysis, indicating the number of habitations screened (653), the breakdown of Priority Tiers, and total at-risk populations.
- **Data Sources:** Census 2011 PCA, Copernicus GLO-30 DEM.
- **Limitations:** Dependent on the accuracy of the spatial join and the 30m resolution DEM. 

---

## 2. Interactive Map (Copernicus DEM & Multi-Hazard Overlays)

![Figure 2: Interactive Map](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/02_interactive_map.png)
**Figure 2: Interactive Map**
- **Feature Name:** Geospatial Viewer
- **Workflow / Value:** Allows SDMA officials to visually inspect the overlapping layers of terrain steepness, flood exposure, and settlement locations.
- **Data Sources:** Copernicus GLO-30 DEM, derived slope models.
- **Limitations:** Spatial precision is limited by 30m resolution; micro-topography variations are not captured.

---

## 3. Hazard Layers & Topography

![Figure 3: Hazard Layers](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/03_hazard_layers.png)
**Figure 3: Hazard Layers Explainability**
- **Feature Name:** Methodology - Hazard Inputs
- **Workflow / Value:** Details how multihazard scores (landslide/flood proxies) are determined and mapped to 289 distinct Candidate Hazard-Based Red Zones.
- **Data Sources:** Synthesized hazard raster proxies.
- **Limitations:** Preliminary risk indicators only; geotechnical field assessments are mandatory for actual susceptibility mapping.

---

## 4. Village Priority Explorer

![Figure 4: Village Priority Explorer](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/04_village_explorer.png)
**Figure 4: Village Priority Explorer**
- **Feature Name:** Habitation Screening Table
- **Workflow / Value:** Displays the 653 Census habitations, ranked by their proximity to red zones. Officials can filter by vulnerability flags or tier status.
- **Data Sources:** SHRUG Spatial Bridge, Census 2011 PCA.
- **Limitations:** Relies on habitation centroids rather than full polygon footprints.

---

## 5. High-Priority Village Profile

![Figure 5: High-Priority Village Profile](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/05_high_priority_village_profile.png)
**Figure 5: High-Priority Village Profile**
- **Feature Name:** Single Village Drill-down
- **Workflow / Value:** Shows exact distance to the nearest hazard zone, demographic breakdown, and vulnerability flags for a specific Tier 1 village to inform immediate field assessment teams.
- **Data Sources:** Census 2011, Geospatial proximity joins.
- **Limitations:** Demographic data represents 2011 baselines and may not reflect current socio-economic realities.

---

## 6. Vulnerability Context Analysis

![Figure 6: Vulnerability Analysis](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/06_vulnerability_analysis.png)
**Figure 6: Vulnerability Context Filter**
- **Feature Name:** High-Vulnerability Filter
- **Workflow / Value:** Demonstrates how villages with multiple socio-economic stress flags (e.g., high illiteracy, high child population) can be surfaced, acting as context (but not altering spatial hazard tiers).
- **Data Sources:** Census 2011 PCA thresholding (top 25% of district).
- **Limitations:** Vulnerability is a secondary contextual layer, subordinate to physical hazard proximity.

---

## 7. Candidate Topographically Feasible Areas

![Figure 7: Candidate Area Explorer](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/07_candidate_area_explorer.png)
**Figure 7: Candidate Area Explorer**
- **Feature Name:** Preliminary Candidate Area Identification Table
- **Workflow / Value:** Lists the 5,991 extracted candidate polygons (1–10 hectares) that meet the strict slope (≤20 degrees) and hazard exclusion rules, offering alternative relocation sites.
- **Data Sources:** Morphological image processing on Copernicus DEM.
- **Limitations:** Areas are "topographically feasible" only; legal land use (e.g., forest reserves) is NOT verified.

---

## 8. Candidate Area Deep-Dive Profile

![Figure 8: Candidate Area Profile](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/08_candidate_area_profile.png)
**Figure 8: Candidate Area Profile**
- **Feature Name:** Detailed Candidate Area View
- **Workflow / Value:** Shows slope distributions, nearest hazard distances, and the specific geographic footprint for a single candidate site (e.g., CA-5980).
- **Data Sources:** Vectorized extraction from feasibility raster.
- **Limitations:** Requires detailed site surveys for groundwater, bedrock stability, and access infrastructure.

---

## 9. Preliminary Dwelling-Unit Scenario

![Figure 9: Dwelling Scenario](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/09_capacity_or_dwelling_scenario.png)
**Figure 9: Preliminary Dwelling-Unit Scenario**
- **Feature Name:** Capacity Estimation Status
- **Workflow / Value:** Displays the estimated household capacity based on the PMAY-G 25 m²/HH norm (40% land efficiency), explicitly relabeled to avoid implying an official carrying capacity authorization.
- **Data Sources:** Ministry of Rural Development (MoRD) housing standards applied to GIS polygon areas.
- **Limitations:** Theoretical maximums only; real-world capacity will be much lower due to setbacks, road networks, and soil conditions.

---

## 10. Relocation Planning Horizons

![Figure 10: Relocation Planning Horizons](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/10_relocation_planning_horizons.png)
**Figure 10: Relocation Planning Horizons**
- **Feature Name:** Authority Action Queue (Horizons)
- **Workflow / Value:** Shows Tier 1 mapped to "Immediate Field Assessment" and Tier 2 mapped to "Short-Term Planning Review" to drive SDMA actionable timelines.
- **Data Sources:** Rule-based logic engine `priority_thresholds.yaml`.
- **Limitations:** Planning horizons are administrative suggestions, not legally binding eviction or relocation notices.

---

## 11. Authority Action Center (Sub-District Aggregations)

![Figure 11: Authority Action Center](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/11_authority_action_center.png)
**Figure 11: Authority Action Center**
- **Feature Name:** Sub-District Summary Tab
- **Workflow / Value:** Aggregates Tier 1/2 villages by administrative block, allowing District Magistrates and SDMA planners to allocate resources efficiently based on concentrated risk.
- **Data Sources:** SHRUG Sub-District ID groupings.
- **Limitations:** Depends entirely on the completeness of the spatial bridge join.

---

## 12. Operator-Triggered Dynamic Recomputation

![Figure 12: Dynamic Recompute](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/12_dynamic_recompute.png)
**Figure 12: Operator-Triggered Dynamic Recomputation**
- **Feature Name:** Pipeline Recompute Engine
- **Workflow / Value:** Allows an authorized operator to manually re-run the classification pipelines (Steps 10B/C/D) when YAML thresholds or underlying raster data change, proving architectural dynamism.
- **Data Sources:** Backend FastAPI execution triggers.
- **Limitations:** Recomputations overwrite existing GeoPackage caches; requires explicit operator note for audit trailing.

---

## 13. Methodology Explainability & Transparency

![Figure 13: Methodology Explainability](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/13_methodology_explainability.png)
**Figure 13: Methodology Explainability**
- **Feature Name:** Methodology Disclosures
- **Workflow / Value:** Exposes the exact algorithms (e.g., 500m proximity for Tier 1) and data benchmarks (e.g., 75th percentile Census indicators) used by the engine, ensuring "glass-box" transparency.
- **Data Sources:** System configuration definitions.
- **Limitations:** Transparency does not imply accuracy; scientific caveats remain paramount.

---

## 14. Data Status & Missing Data Architectures

![Figure 14: Data Limitations](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/docs/screenshots/14_data_status_limitations.png)
**Figure 14: Data Status & Limitations**
- **Feature Name:** Known Missing Datasets Register
- **Workflow / Value:** Honestly acknowledges data gaps (e.g., Missing Land Ownership Cadastrals, Missing Disaster History verification) rather than inventing fake data. Shows how the system architecture gracefully handles missing inputs.
- **Data Sources:** System health checks.
- **Limitations:** Certain analyses (like socioeconomic capacity optimization) are fundamentally impossible without these authoritative missing datasets.
