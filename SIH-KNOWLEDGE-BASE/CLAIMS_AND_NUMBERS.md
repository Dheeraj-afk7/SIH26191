# Claims & Quantitative Numbers Registry: SIH26191

This registry contains every verified quantitative claim, metric, percentage, area, distance, latency, and threshold across the SIH26191 platform to ensure factual precision during presentations and judge questioning.

---

## Complete Quantitative Claims Table

| Claim | Value | Source Document / Section | Notes & Context |
| :--- | :--- | :--- | :--- |
| **Total Census Habitations Screened** | **653** | `PCA_CDB-0503-F-Census.xlsx` / Step 8 | 100% of rural revenue habitations in Rudraprayag District. |
| **Total District Population (Census 2011)** | **232,360** | `decision_summary.json` / Step 10 | Official Census 2011 baseline population. |
| **Total District Households (Census 2011)** | **50,882** | `decision_summary.json` / Step 10 | Official Census 2011 household count. |
| **Average Household Size (Census 2011)** | **~4.57 persons** | `configs/capacity.yaml` (L63) | District average ($232,360 / 50,882$). |
| **Planning Average Household Size** | **4.0 persons** | `configs/capacity.yaml` (L68) | Conservative planning assumption to avoid overclaiming capacity. |
| **Tier 1 (Attention Priority) Villages** | **12 villages (1.84%)** | `decision_summary.json` / `village_priority_profiles.gpkg` | Immediate Field Assessment horizon (0–1 years). |
| **Tier 1 At-Risk Population** | **4,750 persons** | `decision_summary.json` / Step 10 | Sum of population across 12 Tier 1 habitations. |
| **Tier 1 At-Risk Households** | **977 households** | `decision_summary.json` / Step 10 | Sum of households across 12 Tier 1 habitations. |
| **Tier 2 (Elevated Attention) Villages** | **69 villages (10.57%)** | `decision_summary.json` / `village_priority_profiles.gpkg` | Short-Term Planning Review horizon (1–3 years). |
| **Tier 2 At-Risk Population** | **23,012 persons** | `decision_summary.json` / Step 10 | Population across 69 Tier 2 habitations. |
| **Tier 2 At-Risk Households** | **4,674 households** | `decision_summary.json` / Step 10 | Households across 69 Tier 2 habitations. |
| **Tier 3 (Monitoring) Villages** | **204 villages (31.24%)** | `decision_summary.json` / `village_priority_profiles.gpkg` | Medium-Term Monitoring horizon (3–10 years). |
| **Tier 3 Population** | **64,463 persons** | `decision_summary.json` / Step 10 | Population across 204 Tier 3 habitations. |
| **Tier 3 Households** | **13,978 households** | `decision_summary.json` / Step 10 | Households across 204 Tier 3 habitations. |
| **Beyond Proximity Villages** | **368 villages (56.36%)** | `decision_summary.json` / `village_priority_profiles.gpkg` | Routine Monitoring horizon (10+ years). |
| **Beyond Proximity Population** | **140,135 persons** | `decision_summary.json` / Step 10 | Population across 368 Beyond Proximity habitations. |
| **Beyond Proximity Households** | **31,253 households** | `decision_summary.json` / Step 10 | Households across 368 Beyond Proximity habitations. |
| **Total Active Planning Villages (Tiers 1 & 2)** | **81 villages (12.41%)** | `decision_summary.json` / Step 10 | Combined Tier 1 + Tier 2 planning focus. |
| **Total Active Planning Population (Tiers 1 & 2)** | **27,762 persons** | `decision_summary.json` / Step 10 | Combined population needing near-term SDMA planning. |
| **Total Active Planning Households (Tiers 1 & 2)** | **5,651 households** | `decision_summary.json` / Step 10 | Combined households needing near-term SDMA planning. |
| **Top Attention Village Distance to Hazard** | **42.5 metres** | `decision_summary.json` (Marora, ID 42573) | Closest village to Candidate Red Zone (RZ-220). |
| **Second Closest Village Distance to Hazard** | **178.5 metres** | `decision_summary.json` (Tarsali, ID 42067) | Nearest red zone: RZ-018. |
| **Candidate Hazard-Based Red Zones Count** | **289 polygons** | `candidate_hazard_based_red_zones.geojson` / Step 7 | Vectorized morphological clusters ($\text{Class } 3 \ge 5,000\text{ m}^2$). |
| **Candidate Red Zone Size on Disk** | **518 KB** | `PROJECT_FORENSIC_AUDIT.md` (L519) | GeoJSON polygon layer size. |
| **Candidate Relocation Sites Count** | **2,998 discrete polygons** | `candidate_areas_metadata.json` / Step 9 | Filtered to $1–10\text{ ha}$, $\text{slope} \le 20^\circ$, ESA non-forest. |
| **Candidate Relocation Sites Total Area** | **8,095.52 hectares** | `candidate_areas_metadata.json` / Step 9 | Total gross area of 2,998 candidate polygons. |
| **Candidate Relocation Sites (Early Draft/Pre-LULC)** | *5,991 polygons* | `README.md` (L21) / Early Step 9 | Historical note: polygon count before ESA WorldCover exclusion. |
| **PMAY-G Housing Standard Norm** | **25.0 m² / household** | `configs/capacity.yaml` (L60) / MoRD GoI (2016) | Minimum built floor area including cooking area. |
| **PMAY-G Land Utilization Efficiency ($\eta$)** | **40% (0.40)** | `configs/capacity.yaml` (L76) | 40% net buildable; 60% reserved for roads, setbacks, drainage. |
| **Area per Person Assumption** | **6.25 m² / person** | `configs/capacity.yaml` (L65) | Derived as $25\text{ m}^2 / 4.0\text{ persons}$. |
| **Minimum Viable Plot Area** | **2,500 m² (0.25 ha)** | `configs/capacity.yaml` (L84) | Minimum site area to accommodate 10 households. |
| **Scale Protection Upper Bound** | **100.0 hectares** | `configs/capacity.yaml` / `PROJECT_FORENSIC_AUDIT.md` | Sites $>100\text{ ha}$ flagged as exceeding site scale. |
| **Sample 10 ha Site Capacity (CA-0001)** | **1,599 HH / 6,396 persons** | `decision_summary.json` (L255-256) | Usable area: $3.999\text{ ha}$ ($39,985\text{ m}^2$). |
| **Copernicus DEM Spatial Resolution** | **30 metres** ($\approx 29.11\text{m}$ grid) | `copernicus_glo30_rudraprayag.tif` | Ground pixel sampling distance in projected space. |
| **Pixel Area in Projected Metric Space** | **847.15 m²** | `candidate_areas_metadata.json` (L8) | Area of a single raster cell in `EPSG:32644`. |
| **District Total Surface Area** | **372,128.32 hectares** ($\approx 2,439\text{ km}^2$) | `lulc_summary.json` (L11) | Bounding box spatial extent of Rudraprayag. |
| **ESA WorldCover Ecological Exclusion Area** | **265,510.46 ha (71.35%)** | `lulc_summary.json` (L12-13) | Tree cover ($58.57\%$), snow ($11.93\%$), built-up ($0.46\%$), water ($0.39\%$). |
| **ESA WorldCover Ecological Permissible Area** | **106,617.86 ha (28.65%)** | `lulc_summary.json` (L14-15) | Grassland ($19.89\%$), bare soil ($3.18\%$), cropland ($0.69\%$), moss ($4.89\%$). |
| **Critical Infrastructure Facility Count** | **291 facilities** | `infrastructure_summary.json` / Phase 4 | 187 health, 72 education, 28 civic, 4 emergency. |
| **Health Facilities Breakdown** | **187 facilities** | `infrastructure_summary.json` (L16) | 127 subcentres, 24 hospitals, 18 clinics, 12 PHCs, 6 CHCs. |
| **Emergency Facilities Breakdown** | **4 facilities** | `infrastructure_summary.json` (L19) | 3 police stations, 1 fire station. |
| **Mean Habitation Distance to Health POI** | **1,848.9 metres** | `infrastructure_summary.json` (L39) | Average straight-line distance across 653 villages. |
| **Mean Habitation Distance to Hospital/CHC** | **4,921.6 metres** | `infrastructure_summary.json` (L40) | Average distance to full clinical facility. |
| **Mean Habitation Distance to School** | **12,250.1 metres** | `infrastructure_summary.json` (L41) | Average distance to secondary/higher school POI. |
| **Habitations within 5 km of Health Facility** | **646 of 653 (98.9%)** | `infrastructure_summary.json` (L42) | High local sub-centre coverage. |
| **Habitations within 60 min Hospital Drive** | **315 of 653 (48.2%)** | `infrastructure_summary.json` (L44) | Less than half within 1 hour clinical reach. |
| **Road Network Total Length** | **6,397.35 km** | `road_summary.json` (L9) | All OSM highway hierarchy segments in district buffer. |
| **Vehicular Road Network Length** | **4,756.84 km** | `road_summary.json` (L10) | Paved and unpaved vehicular driveable roads. |
| **Arterial Highway Length (Trunk + Primary)** | **620.25 km** | `road_summary.json` (L11) | NH-107, NH-07, and primary corridors. |
| **Road Network Graph Nodes / Edges** | **237,401 nodes / 238,234 edges** | `road_summary.json` (L12-13) | Topologically connected routing graph. |
| **Largest Connected Road Component** | **94.3%** (153,212 nodes) | `road_summary.json` (L18) | Giant connected component percentage. |
| **Assumed Road Travel Speeds** | **35 km/h** (Trunk), **20 km/h** (PMGSY), **3.5 km/h** (Footway) | `road_summary.json` (L25, 60, 104, 116) | Realistic mountain road impedance model. |
| **Mean Habitation Distance to Road** | **344.1 metres** | `road_summary.json` (L137) | Average distance from village centroid to road. |
| **Mean Travel Time to Arterial Highway** | **38.0 minutes** | `road_summary.json` (L138) | Mountain road graph travel impedance. |
| **Isolated Habitations Count** | **82 habitations** | `road_summary.json` (L140) | 71 severely remote + 11 graph-disconnected. |
| **Canonical Historical Disaster Events** | **22 events (1998–2024)** | `disaster_summary.json` / Phase 3 | Curated from NDMA/USDMA/literature (26 raw, 4 deduplicated). |
| **Total Recorded Fatalities (1998–2024)** | **6,913 fatalities** | `disaster_summary.json` (L9) | Includes June 2013 Kedarnath disaster losses. |
| **Total Affected Households in Disasters** | **3,637 households** | `disaster_summary.json` (L10) | Recorded historical household damage. |
| **Disaster Types Breakdown** | **10 Landslides, 5 Cloudbursts, 3 Debris Flows, 2 Riverine, 1 Flash Flood, 1 Rockfall** | `disaster_summary.json` (L16-21) | Exact hazard type breakdown. |
| **Habitations within 1 km of Past Disaster** | **33 habitations** | `disaster_summary.json` (L138) | Within 1 km chronic hazard buffer. |
| **Habitations within 2 km of Past Disaster** | **129 habitations** | `disaster_summary.json` (L139) | Within 2 km chronic hazard buffer. |
| **Chronic Exposure Habitations Count** | **26 habitations** | `disaster_summary.json` (L140) | Chronic historical co-occurrence. |
| **Demographic P75 Benchmark: Child Pop** | **15.10% (0.151)** | `priority_thresholds.yaml` (L253) | Upper tertile of 653 habitations. |
| **Demographic P75 Benchmark: SC Pop** | **24.60% (0.246)** | `priority_thresholds.yaml` (L265) | Upper tertile of 653 habitations. |
| **Demographic P75 Benchmark: Dependency** | **57.90% (0.579)** | `priority_thresholds.yaml` (L280) | Non-worker rate upper tertile. |
| **Demographic P75 Benchmark: Illiteracy** | **34.00% (0.340)** | `priority_thresholds.yaml` (L292) | Illiteracy rate upper tertile. |
| **High Vulnerability Flag Threshold** | **$\ge 2$ active flags of 4** | `priority_thresholds.yaml` (L305) | Highlights compounded socioeconomic stress. |
| **Slope Normalization Range** | **$0.0^\circ$ to $60.0^\circ$** | `derive_terrain_susceptibility.py` | Slope failure interval mapped to $[0.0, 1.0]$. |
| **TWI Normalization Range** | **$3.5$ to $13.5$** | `derive_flood_exposure.py` | Topographic wetness saturation interval. |
| **Multi-Hazard Factor Weights** | **0.5 Terrain / 0.5 Flood** | `derive_multihazard_score.py` | Equal-weight linear screening combination. |
| **Hazard Intensity Class 1 (Lower)** | **Score $< 0.35$** | `classify_multihazard.py` | Low multi-hazard exposure band. |
| **Hazard Intensity Class 2 (Moderate)** | **Score $0.35 \le M < 0.65$** | `classify_multihazard.py` | Moderate multi-hazard exposure band. |
| **Hazard Intensity Class 3 (Higher)** | **Score $M \ge 0.65$** | `classify_multihazard.py` | High / Very High multi-hazard exposure band. |
| **Red Zone Minimum Mapping Unit (MMU)** | **$\ge 5,000\text{ m}^2$ (~0.5 ha)** | `identify_candidate_zones.py` | Filters out isolated micro-pixel noise. |
| **Relocation Site Max Slope Limit** | **$\le 20.0^\circ$** | `identify_candidate_areas.py` | Upper slope limit for feasible settlement. |
| **Relocation Site Area Bounds (MMU)** | **$1.0\text{ ha}$ to $10.0\text{ ha}$** | `candidate_areas_metadata.json` (L25-26) | Minimum and maximum area constraints. |
| **Tier 1 Proximity Threshold** | **$\le 500.0\text{ metres}$** | `priority_thresholds.yaml` (L53) | Immediate attention radius with $\text{MH Class} \ge 2$. |
| **Tier 2 Proximity Threshold** | **$\le 2,000.0\text{ metres}$** | `priority_thresholds.yaml` (L74) | Short-term planning radius. |
| **Tier 3 Proximity Threshold** | **$\le 5,000.0\text{ metres}$** | `priority_thresholds.yaml` (L89) | Medium-term monitoring perimeter. |
| **Beyond Proximity Threshold** | **$> 5,000.0\text{ metres}$** | `priority_thresholds.yaml` (L104) | Routine monitoring perimeter. |
| **Backend Lifespan Data Preload Time** | **~1.8 seconds** | `PROJECT_FORENSIC_AUDIT.md` | In-memory loading of all spatial GeoPackages. |
| **Paginated Village Query Latency** | **$< 15\text{ ms}$** | `PROJECT_FORENSIC_AUDIT.md` | In-memory R-tree query performance. |
| **District Decision Summary Query Latency** | **$< 8\text{ ms}$** | `PROJECT_FORENSIC_AUDIT.md` | In-memory JSON response latency. |
| **Dynamic Recomputation Execution Time** | **~12–18 seconds** | `PROJECT_FORENSIC_AUDIT.md` | Background subprocess execution time. |
| **Full Raster Processing Pipeline Execution** | **~85.5 seconds** | `candidate_areas_metadata.json` (L56) | End-to-end execution of Steps 3–10. |
| **Automated Test Suite Coverage** | **18 / 18 tests passed (100%)** | `tests/test_api.py` / Pytest | Full endpoint and contract validation. |
| **Spatial Join Success Rate** | **653 / 653 villages (100.0%)** | `validate_habitation_baseline.py` | Exact code match rate (PCA to SHRUG). |
| **Total Cloud Hosting Cost** | **$< \$10 / \text{month}$** | `DEPLOYMENT.md` / `SCALABILITY_DEPLOYMENT.md` | Vercel Free + Render/Railway Starter. |
