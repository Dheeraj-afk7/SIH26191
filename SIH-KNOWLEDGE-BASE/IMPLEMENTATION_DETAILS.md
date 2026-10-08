# Implementation Details: SIH26191

## Repository & Directory Structure

```
SIH26191/
├── backend/                             # FastAPI Python REST Application
│   ├── api/
│   │   └── routes/                      # 12 Modular API Route Controllers
│   │       ├── authority.py             # SDMA Action Queue, Block Summary, CSV Exporter
│   │       ├── candidate_areas.py       # Candidate Relocation Sites (BBox & capacity queries)
│   │       ├── decision.py              # District-level decision summaries & metadata
│   │       ├── disasters.py             # Historical disaster incidents & exposure stats
│   │       ├── hazards.py               # Hazard raster metadata & availability flags
│   │       ├── infrastructure.py        # Critical facilities (health, education, emergency)
│   │       ├── lulc.py                  # ESA WorldCover 10m land cover class breakdown
│   │       ├── pipeline.py              # Dynamic recomputation execution triggers & polling
│   │       ├── roads.py                 # Routable road network segments & graph metrics
│   │       ├── system.py                # Health checks, CRS metadata, provenance
│   │       ├── villages.py              # 653 habitation profiles, filters, single dossiers
│   │       └── zones.py                 # 289 Candidate Red Zone GeoJSON
│   ├── core/
│   │   └── config.py                    # Pydantic Settings & YAML loader
│   ├── services/
│   │   └── data_loader.py               # In-memory spatial cache (GeoPandas & R-tree sindex)
│   └── main.py                          # Application entry point, CORS, lifespan preloader
│
├── frontend/                            # React 18 + TypeScript + Vite Dashboard
│   ├── src/
│   │   ├── components/                  # Reusable UI cards, tables, tooltips, layouts
│   │   │   ├── layout/                  # AppShell, Header, Sidebar, DisclaimerBanner
│   │   │   ├── map/                     # GisMap (Leaflet), MapLegend, layer toggles
│   │   │   └── shared/                  # KPICard, InfoTooltip, PriorityBadge, StatusBadge
│   │   ├── config/                      # API endpoints, map bounds, tier constants
│   │   ├── hooks/                       # TanStack React Query data-fetching hooks
│   │   ├── pages/                       # 9 Dedicated Router Views
│   │   │   ├── AuthorityActionPage.tsx  # SDMA Action Queue & Block Aggregations
│   │   │   ├── CandidateAreasPage.tsx   # Relocation Site Explorer & PMAY-G Capacities
│   │   │   ├── DashboardPage.tsx        # Executive KPIs & Priority Distribution Chart
│   │   │   ├── MapPage.tsx              # Fullscreen Multi-Layer Leaflet GIS Viewer
│   │   │   ├── MethodologyPage.tsx      # Transparent Mathematical Disclosures
│   │   │   ├── PipelineRecomputePage.tsx# Dynamic Operator Execution Interface
│   │   │   ├── SystemStatusPage.tsx     # Provenance & Dataset Integrity Audit
│   │   │   ├── VillageDetailPage.tsx    # Single-Village Deep-Dive Dossier
│   │   │   └── VillageExplorerPage.tsx  # Habitation Directory & Filterable Table
│   │   ├── services/                    # Axios API client functions
│   │   ├── types/                       # Strict TypeScript interfaces matching backend
│   │   └── utils/                       # Formatters, coordinate reprojections, color helpers
│   ├── Dockerfile                       # Multi-stage production Nginx container
│   ├── nginx.conf                       # Nginx reverse proxy configuration
│   └── package.json                     # Frontend dependencies
│
├── processing/                          # Deterministic Python GIS Processing Pipeline
│   ├── capacity/                        # Step 10D: PMAY-G capacity calculations
│   │   └── build_candidate_context.py   # Computes household & population capacity scenarios
│   ├── disaster_history/                # Phase B / Phase 3: Historical disaster validator
│   │   └── build_disaster_layer.py      # Literature-curated deduplication & spatial buffering
│   ├── exposure/                        # Step 8: Spatial joins & habitation baselines
│   │   ├── build_habitation_baseline.py # Exact 100% Census PCA + SHRUG centroid join
│   │   └── habitation_exposure_overlay.py # Point-in-polygon & nearest red zone distances
│   ├── hazards/                         # Step 4: Terrain susceptibility proxy rasters
│   │   ├── derive_terrain_susceptibility.py   # Linear normalized slope scaling [0-1]
│   │   └── classify_terrain_susceptibility.py # Classes 1, 2, 3 thresholding
│   ├── hydrology/                       # Step 5: D8 Flow & Topographic Wetness Index
│   │   ├── derive_hydrological_derivatives.py # D8 flow direction, accumulation, TWI
│   │   ├── derive_flood_exposure.py           # Linear normalized TWI scaling [0-1]
│   │   └── classify_flood_exposure.py         # Classes 1, 2, 3 thresholding
│   ├── infrastructure/                  # Phase 4: Critical facility routing & overlay
│   │   └── ingest_critical_infrastructure.py  # Health/education distance calculations
│   ├── lulc/                            # Phase 1: ESA WorldCover 10m raster processing
│   │   └── filter_landcover.py          # Tree cover, built-up, snow, water exclusion
│   ├── multihazard/                     # Step 6: Multi-Hazard Index composite
│   │   ├── derive_multihazard_score.py  # M = 0.5*Terrain + 0.5*Flood
│   │   └── classify_multihazard.py      # Low, Moderate, Higher intensity bands
│   ├── priority/                        # Step 10: Relocation decision engine & summaries
│   │   ├── build_village_priority.py    # Deterministic Tiers 1-4, P75 flags, Horizons
│   │   └── generate_decision_summary.py # District JSON & Markdown summary reports
│   ├── redzones/                        # Step 7: Morphological clustering & vectorization
│   │   └── identify_candidate_zones.py  # 8-connectivity clustering -> 289 RZ polygons
│   ├── roads/                           # Phase 2: Routable road network graph
│   │   └── ingest_road_network.py       # NetworkX Dijkstra mountain travel time routing
│   ├── sites/                           # Step 9: Candidate relocation area extraction
│   │   └── identify_candidate_areas.py  # Slope <= 20° & exclusion masking (2,998 sites)
│   └── terrain/                         # Step 3: Copernicus DEM gradient derivation
│       ├── derive_slope.py              # Metric slope in degrees in EPSG:32644
│       └── derive_aspect.py             # Compass aspect bearing in degrees (0-360°)
│
├── configs/                             # Central Declarative YAML Configurations
│   ├── capacity.yaml                    # PMAY-G 25 m²/HH norm, 40% efficiency, 100 ha cap
│   ├── priority_thresholds.yaml         # Proximity cutoffs, P75 benchmarks, Horizons
│   ├── project.yaml                     # Master CRS (EPSG:32644), file paths, parameters
│   └── road_network.yaml                # Mountain highway class speeds & graph parameters
│
├── data/
│   ├── raw/                             # Immutable raw inputs (Copernicus DEM, Census, SHRUG)
│   ├── processed/                       # Derived GeoTIFF rasters, intermediate GPKGs
│   └── outputs/                         # Final GeoPackages & GeoJSONs served to API
│
├── docs/                                # Technical reports, forensic audits, traceability matrices
├── tests/                               # Automated Pytest suite
│   └── test_api.py                      # 18 Comprehensive endpoint contract assertions
├── Dockerfile.backend                   # Production Python FastAPI container
├── docker-compose.yml                   # Multi-container full-stack compose
└── requirements.txt                     # Pinned Python GIS & ASGI dependencies
```

---

## Important Classes & Functions

### 1. In-Memory Data Store (`backend/services/data_loader.py`)
- **`DataLoader` Class:**
  - `load_all()`: Invoked on backend lifespan startup (`@asynccontextmanager`). Preloads `village_priority_profiles.gpkg` (653 features), `candidate_hazard_based_red_zones.geojson` (289 features), `candidate_area_context.gpkg` (2,998 features), `critical_infrastructure.geojson` (291 features), `historical_disaster_inventory.geojson` (22 features), and `arterial_roads.geojson` into memory.
  - Automatically initializes R-tree spatial indexing (`.sindex`) on all GeoDataFrames for $\mathcal{O}(\log N)$ spatial lookups.

### 2. Dynamic Pipeline Recomputation Runner (`backend/api/routes/pipeline.py`)
- **`_run_job(job_id, steps, operator_note)`:**
  - Background worker thread invoked by `POST /api/pipeline/recompute`.
  - Sequentially executes requested pipeline scripts (`build_village_priority.py`, `build_candidate_context.py`, `generate_decision_summary.py`) via `subprocess.run` with a 300-second timeout ceiling.
  - Captures `stdout` and `stderr` tail logs per step.
  - Automatically calls `data_store.load_all()` upon completion to hot-reload in-memory spatial caches without server downtime.

### 3. Authority Action Queue Controller (`backend/api/routes/authority.py`)
- **`get_action_queue(tiers, high_vuln_only, limit)`:** Queries in-memory village profiles, filters by priority tier (default: Tier 1 and Tier 2), applies high-vulnerability filter ($\ge 2$ $P_{75}$ flags), and sorts by `nearest_hazard_distance_m` ascending.
- **`get_block_summary()`:** Aggregates village risk counts by Sub-District Tehsil ID (`shrug_subdist_id`), computing total population, Tier 1 immediate counts, Tier 2 short-term counts, and at-risk population totals per block.
- **`download_priority_report(tiers)`:** Generates a streaming CSV response (`StreamingResponse`) with administrative legal disclaimer headers for direct download.

### 4. Rule-Based Classification Logic (`processing/priority/build_village_priority.py`)
- Evaluates spatial distance $d$ and multi-hazard class at centroid to deterministically assign priority tiers:
  ```python
  def classify_priority(row):
      if row['direct_zone_overlap']:
          return 'Tier1_AttentionPriority', 'IMMEDIATE_FIELD_ASSESSMENT'
      elif row['nearest_hazard_distance_m'] <= 500.0 and row['mh_class_at_centroid'] >= 2:
          return 'Tier1_AttentionPriority', 'IMMEDIATE_FIELD_ASSESSMENT'
      elif row['nearest_hazard_distance_m'] <= 2000.0:
          return 'Tier2_ElevatedAttention', 'SHORT_TERM_PLANNING_REVIEW'
      elif row['nearest_hazard_distance_m'] <= 5000.0:
          return 'Tier3_Monitoring', 'MEDIUM_TERM_MONITORING'
      else:
          return 'BeyondProximity', 'ROUTINE_MONITORING'
  ```

---

## Core Data Schemas

### 1. Village Priority Profile Schema (`village_priority_profiles.gpkg`)
- `village_id` (int): 6-digit Census 2011 Village ID
- `village_name` (str): Transliterated revenue village name
- `tot_pop` (int): Total population
- `households` (int): Total household count
- `nearest_hazard_distance_m` (float): Metric Euclidean distance in metres to nearest Candidate Red Zone
- `nearest_zone_id` (str): Identifier of nearest red zone (e.g., `RZ-220`)
- `mh_class_at_centroid` (float): Multi-Hazard Screening Class ($1.0, 2.0, 3.0$) at centroid
- `priority_tier` (str): `Tier1_AttentionPriority` | `Tier2_ElevatedAttention` | `Tier3_Monitoring` | `BeyondProximity`
- `priority_tier_display` (str): Human-readable tier label
- `relocation_horizon` (str): `IMMEDIATE_FIELD_ASSESSMENT` | `SHORT_TERM_PLANNING_REVIEW` | `MEDIUM_TERM_MONITORING` | `ROUTINE_MONITORING`
- `planning_horizon_years` (str): `"0-1"`, `"1-3"`, `"3-10"`, `"10+"`
- `recommended_action` (str): Actionable administrative guidance
- `priority_reason` (str): Plain-language rule explanation
- `vf_high_child_pop` (bool): Child proportion $> 15.1\%$
- `vf_high_sc` (bool): SC proportion $> 24.6\%$
- `vf_high_dependency` (bool): Non-worker rate $> 57.9\%$
- `vf_high_illiteracy` (bool): Illiteracy rate $> 34.0\%$
- `vulnerability_flag_count` (int): Number of active flags ($0–4$)
- `dist_to_nearest_health_facility_m` (float): Metric distance to nearest health POI
- `dist_to_nearest_disaster_m` (float): Metric distance to historical disaster epicenter
- `dist_to_nearest_road_m` (float): Metric distance to road network
- `travel_time_to_arterial_min` (float): Estimated mountain driving time in minutes

### 2. Candidate Area Context Schema (`candidate_area_context.gpkg`)
- `area_id` (str): Unique site identifier (e.g., `CA-0001` to `CA-2998`)
- `area_hectares` (float): Gross polygon area ($1.0–10.0\text{ ha}$)
- `mean_slope` (float): Mean terrain slope in degrees ($\le 20.0^\circ$)
- `usable_area_m2` (float): Gross area $\times 0.40$ (net buildable area)
- `usable_area_ha` (float): Net buildable area in hectares
- `estimated_household_capacity` (int): $\lfloor \text{usable\_area\_m2} / 25.0 \rfloor$ (PMAY-G norm)
- `estimated_population_capacity` (int): $\text{households} \times 4.0\text{ persons}$
- `capacity_status` (str): `PRELIMINARY_DWELLING_UNIT_SCENARIO`
- `dominant_land_cover` (str): ESA WorldCover class (Grassland, Cropland, Bare vegetation, Moss/lichen)
- `road_accessibility_category` (str): `HIGHLY_ACCESSIBLE` | `MODERATELY_ACCESSIBLE` | `REMOTE` | `SEVERELY_REMOTE` | `ISOLATED_GRAPH_DISCONNECTED`
- `dist_to_nearest_redzone_m` (float): Buffer distance to nearest red zone polygon

---

## Important Implementation Decisions

1. **Metric UTM 44N (`EPSG:32644`) for Spatial Calculations:**
   - Geographic coordinates (`EPSG:4326` degrees) distort metric slope and distance in mountainous regions. Reprojecting all inputs to UTM Zone 44N ensures true Cartesian metric distance and slope gradient accuracy.
2. **In-Memory Cache vs. External Relational Database:**
   - Given a district scope ($653$ villages, $289$ red zones), storing preloaded GeoDataFrames in Python memory with R-tree indexing avoids network latency, eliminates database server crashes during hackathon presentations, and delivers response times $<15\text{ ms}$.
3. **Declarative YAML Decoupling:**
   - Hardcoding cutoffs (e.g., 500m buffer) in Python code makes administrative auditing impossible. Storing all rules in YAML (`configs/`) allows operators to modify parameters and trigger dynamic recomputation without code edits.
