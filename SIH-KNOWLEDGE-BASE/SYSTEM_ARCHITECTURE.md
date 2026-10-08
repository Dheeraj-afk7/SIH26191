# System Architecture: SIH26191

## High-Level System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    DATA INGESTION LAYER                                │
│  • Copernicus GLO-30 DEM (30m raster, ESA Open Access)                                │
│  • Census of India 2011 Primary Census Abstract (PCA Excel)                           │
│  • DDL SHRUG v2.2 Village Centroids (653 habitations)                                  │
│  • ESA WorldCover 10m Land Cover (2021 v200, Tile N30E078)                            │
│  • OpenStreetMap (OSM) Infrastructure POIs (291 health, education & civic facilities)  │
│  • OpenStreetMap Highway Network (6,397.35 km routable mountain road network)         │
│  • Literature-Curated Disaster Registry (22 canonical events 1998–2024, NDMA/USDMA)   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        GEOSPATIAL PROCESSING & SCREENING PIPELINE                      │
│                                (processing/ Modules)                                   │
│  ├── terrain/           → Slope (deg), Aspect (deg) in EPSG:32644 (UTM Zone 44N)       │
│  ├── hydrology/         → D8 Flow Direction, Accumulation, Topographic Wetness Index   │
│  ├── hazards/           → Normalized Terrain Proxy [0-1] & Flood Exposure Proxy [0-1]  │
│  ├── multihazard/       → 50/50 Multi-Hazard Score: M(x,y) = 0.5*Terrain + 0.5*Flood   │
│  ├── redzones/          → Morphological 8-Connectivity Clustering → 289 Red Zones      │
│  ├── exposure/          → 100% Code-Join (Census PCA + SHRUG) → 653 Habitations Baseline│
│  ├── lulc/              → Ecological Masking (Tree cover, Built-up, Snow/Water excluded)│
│  ├── roads/             → NetworkX Dijkstra Mountain Routing & Isolation Classification│
│  ├── sites/             → Slope <= 20° & Exclusion Masking → 2,998 Candidate Sites     │
│  ├── capacity/          → PMAY-G 25 m²/HH Norm with 40% Efficiency & 100 ha Scale Cap  │
│  └── priority/          → Rule-Based Decision Engine: Tiers 1–4, P75 Flags & Horizons  │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                            DATA PERSISTENCE & CACHING LAYER                            │
│  • Final Derived Vectors: OGC GeoPackages (.gpkg) & GeoJSONs in data/outputs/ & data/   │
│  • Aggregated Summaries: decision_summary.json, decision_metadata.json, summaries      │
│  • Configuration Store: YAML parameter files (project.yaml, priority_thresholds.yaml)  │
│  • In-Memory Cache: FastAPI DataLoader with GeoPandas DataFrames & Shapely Spatial Tree│
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               FASTAPI REST BACKEND SERVICE                             │
│                                  (backend/ Python ASGI)                                │
│  • Lifespan In-Memory Preloader (DataLoader.load_all)                                  │
│  • 12 Modular API Route Controllers:                                                   │
│      - /api/system          - /api/decision        - /api/villages                     │
│      - /api/red-zones       - /api/candidate-areas - /api/hazards                      │
│      - /api/infrastructure  - /api/disasters       - /api/roads                        │
│      - /api/lulc            - /api/pipeline        - /api/authority                    │
│  • Asynchronous Process Executor: POST /api/pipeline/recompute via Python subprocess   │
│  • Streaming CSV Exporter: GET /api/authority/report.csv                               │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     REACT 18 + VITE GIS COMMAND CENTER FRONTEND                        │
│                                  (frontend/src/)                                       │
│  • TanStack React Query Data Fetching & Caching                                        │
│  • Leaflet & React-Leaflet GIS Multi-Layer Map Engine (Canvas / SVG Vector Rendering)   │
│  • 9 Dedicated Views:                                                                  │
│      1. Executive Dashboard (/dashboard)       2. Interactive GIS Map (/map)           │
│      3. Village Priority Explorer (/villages)  4. Village Detail Dossier (/villages/:id)│
│      5. Candidate Areas Explorer (/candidate)  6. Authority Action Center (/authority)  │
│      7. Pipeline Recomputation (/pipeline)     8. Methodology Disclosures (/methodology)│
│      9. System Provenance Status (/status)                                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Major Components & Responsibilities

### 1. Frontend Client Layer
- **Technology:** React 18, Vite, TypeScript, Tailwind CSS, Leaflet GIS, TanStack Query, Lucide Icons.
- **Responsibilities:**
  - Rendering interactive GIS layers with client-side bounding box filtering and layer opacity controls.
  - Displaying executive KPI summaries, risk tier bar charts, and demographic breakdown widgets.
  - Enabling tabular search, sorting, and pagination across 653 habitations and 2,998 candidate areas.
  - Rendering deep-dive village profiles with "Why This Classification?" rule explainability cards.
  - Providing the SDMA Authority Action Center with sub-district risk aggregations and direct CSV downloads.
  - Monitoring operator-triggered pipeline recomputations with live polling status bars and diagnostic log tails.

### 2. Backend API Microservice Layer
- **Technology:** Python 3.10+, FastAPI, Uvicorn ASGI server, Pydantic, GeoPandas, Pandas, Shapely.
- **Responsibilities:**
  - Serves as the high-throughput, stateless REST interface between frontend clients and spatial datasets.
  - Preloads spatial datasets into memory on startup (`DataLoader.load_all()`) using R-tree spatial indexes (`sindex`) for sub-millisecond query responses.
  - Implements CORS middleware and route grouping across 12 domain controllers.
  - Executes dynamic background pipeline recomputation jobs via asynchronous threading and subprocess invocation.
  - Streams dynamic CSV reports directly to clients with administrative disclaimer headers.

### 3. Geospatial Processing Pipeline
- **Technology:** Python GIS Stack: `rasterio`, `geopandas`, `shapely`, `numpy`, `scipy`, `networkx`.
- **Responsibilities:**
  - Ingests raw satellite rasters and census tables.
  - Handles coordinate reference system reprojections from geographic `EPSG:4326` to metric `EPSG:32644` (UTM Zone 44N).
  - Derives continuous mathematical terrain and hydrological gradients.
  - Performs connected-component image segmentation, morphological filtering, and polygon vectorization.
  - Computes spatial point-in-polygon joins and nearest-neighbor Euclidean distance vectors.
  - Evaluates topological shortest path travel times across mountain road graphs using Dijkstra's algorithm.
  - Applies deterministic classification rules and PMAY-G dwelling capacity scenario models.

### 4. Persistence & Configuration Layer
- **Data Formats:** OGC GeoPackage (`.gpkg`), GeoJSON (`.geojson`), Cloud-Optimized GeoTIFF (`.tif`), JSON, CSV.
- **Configuration:** YAML files (`configs/project.yaml`, `configs/priority_thresholds.yaml`, `configs/capacity.yaml`, `configs/road_network.yaml`) read via `pydantic-settings` and `PyYAML`.
- **Responsibilities:**
  - Maintains immutable raw source data (`data/raw/`).
  - Stores intermediate derived terrain rasters (`data/processed/`).
  - Persists production-ready vector decision layers (`data/outputs/` and `data/processed/decision/`).
  - Encapsulates all threshold parameters outside the codebase for transparent explainability and dynamic updating.

---

## AI/ML Components & Decision Engine Architecture
- **Scientific Stance:** The core spatial screening and priority engine is **strictly deterministic, rule-based, and explainable**.
- **No Black-Box AI in Safety-Critical Paths:** To ensure absolute administrative auditability and prevent algorithmic hallucinations in life-safety classifications, core priority tiers are determined by explicit mathematical rules:
  $$\text{Tier 1} \iff (\text{direct\_zone\_overlap} == \text{True}) \lor (\text{dist} \le 500\text{ m} \land \text{MH\_Class} \ge 2)$$
  $$\text{Tier 2} \iff (\text{dist} \le 2000\text{ m}) \land (\text{not Tier 1})$$
  $$\text{Tier 3} \iff (\text{dist} \le 5000\text{ m}) \land (\text{not Tier 1 or 2})$$
  $$\text{Beyond Proximity} \iff \text{dist} > 5000\text{ m}$$
- **Optional Non-Safety AI Layer:** An optional RAG / LLM standard operating procedure assistant (such as this knowledge base) operates strictly as an informational assistant and **never** alters spatial scores, priority classifications, or site feasibility selections.

---

## Input / Output of Major Pipeline Steps

| Step | Script / Module | Primary Inputs | Primary Outputs | Key Output Format |
| :--- | :--- | :--- | :--- | :--- |
| **Step 3** | `terrain/derive_slope.py`<br>`terrain/derive_aspect.py` | `copernicus_glo30_rudraprayag.tif` (30m DEM) | `slope_degrees.tif`<br>`aspect_degrees.tif` | GeoTIFF (EPSG:32644) |
| **Step 4** | `hazards/derive_terrain_susceptibility.py` | `slope_degrees.tif` | `terrain_susceptibility_proxy.tif`<br>`terrain_susceptibility_classes.tif` | GeoTIFF [0.0–1.0] |
| **Step 5** | `hydrology/derive_hydrological_derivatives.py`<br>`hydrology/derive_flood_exposure.py` | `copernicus_glo30_rudraprayag.tif`<br>`slope_degrees.tif` | `flow_direction.tif`<br>`flow_accumulation.tif`<br>`topographic_wetness_index.tif`<br>`flood_exposure_proxy.tif` | GeoTIFF [0.0–1.0] |
| **Step 6** | `multihazard/derive_multihazard_score.py` | `terrain_susceptibility_proxy.tif`<br>`flood_exposure_proxy.tif` | `multihazard_score.tif` ($0.5T + 0.5F$)<br>`multihazard_classes.tif` | GeoTIFF [0.0–1.0] |
| **Step 7** | `redzones/identify_candidate_zones.py` | `multihazard_classes.tif`<br>`multihazard_score.tif` | `candidate_hazard_based_red_zones.geojson` (289 polygons, area $\ge 5,000\text{ m}^2$) | GeoJSON & GPKG |
| **Step 8** | `exposure/build_habitation_baseline.py`<br>`exposure/habitation_exposure_overlay.py` | `PCA_CDB-0503-F-Census.xlsx`<br>`rudraprayag_census_villages_shrug.geojson`<br>`candidate_hazard_based_red_zones.geojson` | `habitation_baseline.geojson` (653 villages)<br>`habitation_exposure.geojson` (distances & zone IDs) | GeoJSON & GPKG |
| **Step 9** | `sites/identify_candidate_areas.py`<br>`lulc/filter_landcover.py` | `slope_degrees.tif`<br>`multihazard_classes.tif`<br>`rudraprayag_worldcover_30m.tif` | `candidate_topographically_feasible_areas_attributed.geojson` (2,998 polygons, $1–10\text{ ha}$, slope $\le 20^\circ$) | GeoJSON & GPKG |
| **Step 10** | `priority/build_village_priority.py`<br>`capacity/build_candidate_context.py`<br>`priority/generate_decision_summary.py` | `habitation_exposure.geojson`<br>`candidate_areas_attributed.geojson`<br>`priority_thresholds.yaml`<br>`capacity.yaml` | `village_priority_profiles.gpkg`<br>`candidate_area_context.gpkg`<br>`decision_summary.json`<br>`decision_metadata.json` | GPKG & JSON |
| **Phases 1–4** | `roads/ingest_road_network.py`<br>`infrastructure/ingest_critical_infrastructure.py`<br>`disaster_history/build_disaster_layer.py` | `osm_roads_rudraprayag.geojson`<br>`critical_infrastructure.geojson`<br>`historical_disaster_inventory.geojson` | `arterial_roads.geojson`<br>`critical_infrastructure.geojson`<br>`disaster_incidents.geojson` | GeoJSON & JSON Summaries |

---

## API Catalog & Route Specifications

The FastAPI service exposes 12 modular route controllers:

| Method | Endpoint | Description | Input Parameters | Return Format |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | API root discovery & catalog | None | JSON object |
| `GET` | `/api/health` | System health probe & dataset cache load status | None | `{"status": "ok", "datasets_loaded": {...}}` |
| `GET` | `/api/metadata` | Project provenance, CRS, and disclaimer metadata | None | JSON object |
| `GET` | `/api/decision/summary` | District-wide KPIs, population counts, tier breakdown | None | JSON object |
| `GET` | `/api/decision/metadata` | Decision engine rule specifications and provenance | None | JSON object |
| `GET` | `/api/villages` | Query 653 habitation profiles | `priority_tier`, `name`, `limit`, `offset` | GeoJSON FeatureCollection |
| `GET` | `/api/villages/{id}` | Single village dossier with full demographic breakdown | `id` (int, Census ID) | GeoJSON Feature (1 feature) |
| `GET` | `/api/red-zones` | Candidate Hazard-Based Red Zones (289 polygons) | None | GeoJSON FeatureCollection |
| `GET` | `/api/candidate-areas` | Candidate Relocation Areas with PMAY-G capacities | `bbox`, `min_area_ha`, `max_area_ha`, `limit`, `offset` | GeoJSON FeatureCollection |
| `GET` | `/api/candidate-areas/{id}` | Single candidate area profile & slope statistics | `id` (str, e.g., CA-0001) | GeoJSON Feature (1 feature) |
| `GET` | `/api/hazards` | Hazard raster metadata & disk file availability flags | None | JSON object |
| `GET` | `/api/infrastructure` | Critical facilities (health, education, emergency) | `category`, `limit` | GeoJSON FeatureCollection |
| `GET` | `/api/infrastructure/summary` | Infrastructure facility counts & accessibility stats | None | JSON object |
| `GET` | `/api/disasters` | Canonical historical disaster records (22 incidents) | None | GeoJSON FeatureCollection |
| `GET` | `/api/disasters/summary` | Disaster totals, fatalities, and decades breakdown | None | JSON object |
| `GET` | `/api/roads` | Routable road network segments | `highway_class`, `limit` | GeoJSON FeatureCollection |
| `GET` | `/api/roads/summary` | Road network length ($6,397\text{ km}$) & graph statistics | None | JSON object |
| `GET` | `/api/lulc/summary` | ESA WorldCover 10m land cover class breakdown | None | JSON object |
| `POST` | `/api/pipeline/recompute` | Operator trigger to execute pipeline recomputation | `{"steps": [...], "operator_note": "..."}` | `{"job_id": "...", "status": "QUEUED"}` |
| `GET` | `/api/pipeline/status/{id}`| Poll execution status and log tail of recompute job | `id` (str, Job ID) | JSON object with step logs |
| `GET` | `/api/pipeline/steps` | List available recomputable pipeline steps | None | JSON list of steps |
| `GET` | `/api/authority/action-queue`| SDMA priority action queue sorted by hazard distance | `tiers`, `high_vuln_only`, `limit` | JSON object with distance-sorted list |
| `GET` | `/api/authority/block-summary`| Sub-district block aggregation of risk tiers | None | JSON list of sub-districts |
| `GET` | `/api/authority/report.csv` | Export complete priority action report as CSV | `tiers` (str) | Streaming CSV file download |

---

## Deployment Architecture
1. **Local Development Setup:**
   - Backend: Python 3.10+ virtual environment (`.venv`), running `uvicorn backend.main:app --port 8000`.
   - Frontend: Node.js 18+, Vite development server running on `http://localhost:3000` (or `5173`).
2. **Containerized Orchestration (Docker Compose):**
   - `Dockerfile.backend`: Multi-stage Python 3.11-slim container with GDAL/GEOS system libraries.
   - Frontend Container: Multi-stage Node 18 build serving static production assets via Nginx reverse proxy.
   - `docker-compose.yml`: Binds full stack on port 80 (Frontend) and port 8000 (Backend API).
3. **Cloud Production Deployment:**
   - **Frontend:** Hosted on Vercel CDN (`https://sih-26191.vercel.app/`).
   - **Backend:** Hosted on containerized ASGI cloud instances (Render / Railway) configured via `Procfile` (`web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT`).

---

## Security & Governance Architecture
- **Stateless Microservice:** The backend maintains no persistent user session state; data modifications are restricted to operator-triggered pipeline recomputations.
- **CORS Protection:** Configurable origins in `backend/core/config.py` restricting unauthorized cross-origin requests.
- **Input Validation:** Strict Pydantic model validation on all incoming JSON payloads and query parameters.
- **Audit Trailing:** Operator recomputation triggers require an explicit `operator_note` and generate timestamped execution logs with unique UUID job IDs.
- **Mandatory Disclaimers:** All API responses and UI views carry explicit non-official decision-support disclaimers to prevent illegal or unverified administrative action.
