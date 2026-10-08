# 🏔️ SIH26191 — Disaster Decision-Support Platform

## Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment & Relocation Needs for Vulnerable Habitations

<div align="center">

[![Live Demo](https://img.shields.io/badge/🌐_Live_Demo-sih--26191.vercel.app-4F46E5?style=for-the-badge)](https://sih-26191.vercel.app/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/SIH_2026-Problem_SIH26191-FF6B35?style=for-the-badge)](https://sih.gov.in/)

**Smart India Hackathon 2026 · Problem Statement SIH26191**
**Pilot District:** Rudraprayag, Uttarakhand, India
**Target Users:** USDMA / SDMA / NDRF / District Magistrate & DDMA Planners

</div>

---

## 👨‍💻 About This Project — My Personal Walkthrough

> *This section is specifically written to explain what I built, how I built it, what decisions I made, and why — for interviewers, judges, and anyone evaluating this project.*

### What Problem Did I Solve?

Rudraprayag district in Uttarakhand is one of India's most disaster-prone mountain regions — recurring landslides, flash floods, and cloudbursts repeatedly destroy lives and infrastructure. The core problem with disaster management in such regions has historically been **reactive**: authorities wait for a disaster to happen, then respond. My goal was to flip this model to **proactive, data-driven, spatial planning**.

The SIH26191 problem statement asked me to:
1. Identify hazard-based **red zones** (areas at serious risk of landslide/flood events)
2. Assess the **carrying capacity** of candidate safe relocation sites
3. Determine which habitations need **immediate relocation** vs. long-term monitoring

**The core challenge:** Do all of this with *deterministic, explainable* GIS methods — no black-box AI — because the outputs inform real government decisions about where 653 habitations and their populations should live.

---

### How I Approached the Solution

I designed a full-stack, end-to-end GIS Decision Support System from scratch. Here is my thought process:

**Step 1 — Understand the data landscape.** I identified all publicly available authoritative datasets for the Rudraprayag district:
- **ESA Copernicus GLO-30 DEM** (30m Digital Elevation Model) — the terrain foundation
- **Census 2011 Primary Census Abstract (PCA)** — demographic data for all habitations
- **SHRUG v2.2 (Development Data Lab)** — georeferenced village centroids to locate habitations on the map
- **ESA WorldCover 10m** — land cover classification (forests, built-up, water bodies)
- **OpenStreetMap Overpass API** — roads, health centers, schools
- **NDMA/USDMA/ISRO Bhuvan** — historical disaster incident records

**Step 2 — Design the processing pipeline.** I broke the GIS analysis into 10 deterministic, modular steps (each in its own Python module under `processing/`), making the logic auditable and rerunnable.

**Step 3 — Build a REST API.** I wrapped all processed outputs in a FastAPI backend with 12 modular routers, serving GeoJSON and JSON to the frontend.

**Step 4 — Build the GIS dashboard.** I built a React 18 + TypeScript + Vite + Leaflet frontend with 9 dedicated views, giving SDMA planners a full command center.

---

## 🧠 The GIS Processing Pipeline — How I Did the Science

This is the technical heart of the project. Each module lives in `processing/` and produces deterministic outputs.

### Step 1: Terrain Derivatives (`processing/terrain/`)
- Loaded the **Copernicus GLO-30 DEM** (30m resolution) for Rudraprayag district
- Reprojected everything to **UTM Zone 44N (EPSG:32644)** — a metric coordinate system essential for accurate distance and area calculations in meters
- Computed:
  - **Slope (degrees)** — the primary landslide susceptibility indicator
  - **Aspect (degrees)** — slope-facing direction (N/S/E/W exposure)
  - **Profile & Plan Curvature** — terrain concavity affecting water flow concentration

### Step 2: Hydrology (`processing/hydrology/`)
- Ran **D8 flow direction** algorithm on the DEM to model how water drains across terrain
- Computed **flow accumulation** rasters — identifying channels where runoff concentrates
- Calculated the **Topographic Wetness Index (TWI)**: `TWI = ln(flow_accumulation / tan(slope))` — higher TWI = more flood-prone areas
- Used TWI as the **flood exposure proxy** since real-time discharge data was unavailable

### Step 3: Hazard Scoring (`processing/hazards/` + `processing/multihazard/`)
- **Landslide Susceptibility:** Slope >= 35 degrees = Very High, 25-35 = Higher, 15-25 = Moderate, <15 = Low
- **Flood Exposure:** TWI percentile thresholds to classify flood risk zones
- **Multi-Hazard Index (MHI):** Combined both proxies using a **50/50 weighted overlay** into 4 final classes: Low, Moderate, Higher, Very High
- Stored as a 30m raster `multihazard_classes.tif`

### Step 4: Red Zone Extraction (`processing/redzones/`)
- Applied **morphological filtering** (closing + erosion operations from `scipy.ndimage`) to remove isolated noise pixels
- **Vectorized** contiguous Very High/Higher hazard pixels into polygons using `rasterio.features`
- Applied a **1 ha Minimum Mapping Unit (MMU)** threshold — polygons smaller than 1 ha are discarded as noise
- Result: **289 Candidate Hazard-Based Red Zone polygons**

### Step 5: Habitation Baseline & Exposure (`processing/exposure/`)
- Loaded **653 Census 2011 habitations** by joining Census PCA data with **SHRUG v2.2 village centroids** — this was the key spatial bridge
- Computed **Euclidean distance** from each habitation centroid to the nearest red zone polygon (in meters, in UTM 44N)
- Computed **Euclidean distance** to nearest OSM road, health center, and school
- Enriched each habitation with the **Multi-Hazard class** at its location

### Step 6: Vulnerability Composite Index (`processing/exposure/`)
- For each of the 653 habitations, I computed a **socio-demographic vulnerability score** from 5 Census indicators:
  - Illiteracy rate
  - Child proportion (0-6 age group / total population)
  - SC/ST proportion (socially marginalized communities)
  - Non-worker rate (economically inactive population)
  - Female ratio
- Benchmarked each indicator against the **district-wide 75th percentile** (upper tertile) to flag statistically vulnerable habitations

### Step 7: Relocation Horizon Classification (`processing/priority/`)
Built a **rule-based decision engine** — no ML, fully explainable — using thresholds from `configs/priority_thresholds.yaml`:

| Tier | Criteria | Action |
|------|----------|--------|
| **Tier 1 — Immediate Field Assessment** | Distance to red zone <= 500m AND MH class = Very High | Urgent survey required |
| **Tier 2 — Short-Term Planning Review** | Distance <= 1,000m OR MH class = Higher | Planning review needed |
| **Tier 3 — Medium-Term Monitoring** | Distance <= 3,000m OR Moderate hazard | Routine monitoring |
| **Beyond Proximity** | All others | Low immediate concern |

The **vulnerability flags act as context** (not tier-modifiers) — they add weight to human decision-making without auto-escalating tier.

### Step 8: Relocation Site Screening (`processing/sites/`)
- Created a **feasible area mask** by excluding:
  - All pixels with slope > 20 degrees (unstable for construction)
  - 500m buffer around all 289 red zones (too close to hazards)
  - Water bodies and dense forest from ESA WorldCover
- Applied **1-10 ha MMU** filter — sites must be big enough to house families but not unrealistically large
- Result: **5,991 Candidate Topographically Feasible Relocation Site polygons**

### Step 9: PMAY-G Capacity Modeling (`processing/capacity/`)
- For every feasible site, estimated the number of households it can accommodate
- Formula: `capacity = (site_area_m2 * 0.40) / 25`
  - **25 m2/household** = Government of India PMAY-G (Pradhan Mantri Awaas Yojana - Gramin) standard
  - **0.40 (40% net buildable efficiency)** = accounts for roads, common areas, setbacks — prevents over-allocation
  - **Capped at 100 ha** to prevent unrealistic macro-scale claims

---

## 🏗️ System Architecture

```
+--------------------------------------------------------------------------+
|                          DATA INGESTION LAYER                            |
|  Copernicus GLO-30 DEM | Census 2011 PCA | SHRUG v2.2 | ESA WorldCover  |
|  OSM Overpass (Roads, Infra) | NDMA/USDMA Disaster Records              |
+-----------------------------------+--------------------------------------+
                                    v
+--------------------------------------------------------------------------+
|                    PYTHON GIS PROCESSING PIPELINE                        |
|  processing/terrain/    --> Slope, Aspect, Curvature, TWI               |
|  processing/hazards/    --> Hazard Intensity Classes (4-level)           |
|  processing/multihazard/--> 50/50 Weighted MHI Raster                   |
|  processing/redzones/   --> 289 Red Zone Polygons (morphological filter) |
|  processing/exposure/   --> 653 Habitation baseline + proximity distances|
|  processing/priority/   --> Tier 1/2/3 classification engine            |
|  processing/sites/      --> 5,991 Feasible Relocation Site polygons     |
|  processing/capacity/   --> PMAY-G household capacity per site          |
+-----------------------------------+--------------------------------------+
                                    v
+--------------------------------------------------------------------------+
|                FASTAPI BACKEND REST SERVICE (Port 8000)                  |
|  12 Modular Routers | In-memory GeoPandas cache | GeoJSON responses      |
|  Streaming CSV export | Dynamic pipeline recompute trigger               |
+-----------------------------------+--------------------------------------+
                                    v
+--------------------------------------------------------------------------+
|          REACT 18 + VITE GIS COMMAND CENTER FRONTEND (Port 3000)        |
|  Interactive Leaflet GIS Map | Village Explorer | Authority Action Queue |
|  PMAY-G Capacity Explorer | Dynamic Pipeline Recompute | 9 Page Views    |
+--------------------------------------------------------------------------+
```

---

## 🛠️ Tech Stack — Every Choice Explained

### Backend
| Technology | Version | Why I Chose It |
|---|---|---|
| **Python** | 3.10+ | The undisputed leader for GIS/data science. GeoPandas, Rasterio, SciPy all require it |
| **FastAPI** | >=0.111 | Async-first, auto-generates OpenAPI docs at `/docs`, Pydantic validation built in |
| **GeoPandas** | >=0.14 | Core spatial DataFrame library — reads/writes GPKG, GeoJSON, does spatial joins |
| **Rasterio** | >=1.3 | Standard Python library for reading/writing GeoTIFF rasters |
| **Shapely** | >=2.0 | 2D geometric operations — buffers, intersections, area calculations |
| **NumPy / SciPy** | >=1.26 / >=1.11 | Raster array math, morphological filtering for red zone extraction |
| **PyProj** | >=3.6 | Coordinate reference system transformations (WGS84 to/from UTM 44N) |
| **PyYAML** | >=6.0 | Loads YAML config files for explainable, auditable thresholds |
| **Uvicorn** | >=0.30 | ASGI server for FastAPI — production-grade async HTTP |
| **Pydantic Settings** | >=2.3 | Type-safe environment variable + settings management |
| **Pytest** | >=8.2 | 18 automated API endpoint tests |

### Frontend
| Technology | Version | Why I Chose It |
|---|---|---|
| **React 18** | ^18.3 | Industry-standard UI library, Concurrent Mode for smooth GIS rendering |
| **TypeScript** | ^5.6 | Strict typing for GeoJSON API contracts — catches bugs at compile time |
| **Vite** | ^6.0 | Ultra-fast bundler/dev server — HMR in milliseconds |
| **Leaflet + react-leaflet** | 1.9.4 / 4.2.1 | Lightweight, battle-tested web GIS library for multi-layer overlays |
| **TanStack React Query** | ^5.62 | Server state management — handles loading/error/caching for all 20 API endpoints |
| **Recharts** | ^2.14 | SVG charts for tier breakdowns, vulnerability distributions |
| **proj4** | ^2.21 | Client-side coordinate reprojection (UTM 44N to WGS84 for Leaflet) |
| **Tailwind CSS** | ^3.4 | Utility-first CSS for rapid, consistent styling |
| **React Router DOM** | ^6.28 | Client-side routing for 9 page views |
| **Lucide React** | ^0.468 | Clean, consistent SVG icon set |

### DevOps & Deployment
| Technology | Purpose |
|---|---|
| **Docker + Docker Compose** | Full-stack containerization (backend + frontend + Nginx) |
| **Nginx** | Reverse proxy — serves built React SPA, proxies `/api/*` to FastAPI |
| **Vercel** | Frontend static deployment (`sih-26191.vercel.app`) |
| **Render / Railway** | Backend cloud deployment |
| **Ruff** | Python linter — enforces code quality |

---

## 📁 Repository Structure

```
SIH26191/
├── backend/                      # FastAPI Python REST Application
│   ├── api/routes/               # 12 Modular API Route Handlers
│   │   ├── authority.py          # SDMA action queue, block aggregation, CSV export
│   │   ├── candidate_areas.py    # 5,991 relocation sites + PMAY-G capacities
│   │   ├── decision.py           # District-wide decision summary KPIs
│   │   ├── disasters.py          # Historical disaster incidents (NDMA/USDMA)
│   │   ├── hazards.py            # Hazard raster metadata
│   │   ├── infrastructure.py     # OSM critical facilities (health, education)
│   │   ├── lulc.py               # ESA WorldCover land-cover summary
│   │   ├── pipeline.py           # Dynamic recomputation endpoint
│   │   ├── roads.py              # OSM transport network
│   │   ├── system.py             # Health checks, provenance metadata
│   │   ├── villages.py           # 653 habitation profiles + filters
│   │   └── zones.py              # 289 Candidate Red Zone GeoJSON
│   ├── core/config.py            # Pydantic settings + YAML loader
│   ├── services/data_loader.py   # In-memory GeoPandas spatial cache
│   └── main.py                   # App factory, CORS, lifespan, router registration
│
├── frontend/src/
│   ├── components/               # Reusable UI: cards, tables, map overlays, tooltips
│   ├── config/                   # API endpoints, map defaults, tier color schemes
│   ├── hooks/                    # TanStack React Query data-fetching hooks
│   ├── pages/                    # 9 Primary GIS & Decision Support Views
│   │   ├── DashboardPage.tsx     # Executive KPIs & Risk Summary
│   │   ├── MapPage.tsx           # Fullscreen Multi-Layer Leaflet GIS Map
│   │   ├── VillageExplorerPage.tsx   # Searchable/filterable habitation table
│   │   ├── VillageDetailPage.tsx     # Single habitation deep-dive dossier
│   │   ├── CandidateAreasPage.tsx    # Relocation site explorer + capacities
│   │   ├── AuthorityActionPage.tsx   # SDMA Action Queue + CSV export
│   │   ├── PipelineRecomputePage.tsx # Operator recompute interface
│   │   ├── MethodologyPage.tsx       # Algorithm explainability disclosures
│   │   └── SystemStatusPage.tsx      # Data provenance + gap register
│   ├── services/                 # Axios API client functions
│   ├── types/                    # TypeScript GeoJSON + API interface definitions
│   └── utils/                    # Coordinate reprojection, tier color helpers
│
├── processing/                   # Deterministic Python GIS Pipeline (Steps 1-10)
│   ├── terrain/                  # Copernicus DEM -> Slope, Aspect, Curvature
│   ├── hydrology/                # D8 Flow Direction, Flow Accumulation, TWI
│   ├── hazards/                  # Terrain susceptibility + flood exposure classes
│   ├── multihazard/              # 50/50 weighted MHI composite raster
│   ├── redzones/                 # Morphological filter + vectorize -> 289 polygons
│   ├── exposure/                 # 653 habitation spatial joins + proximity distances
│   ├── priority/                 # Tier 1/2/3 rule-based classification engine
│   ├── sites/                    # Slope mask + exclusions -> 5,991 feasible sites
│   ├── capacity/                 # PMAY-G 25m2/HH capacity per site
│   ├── infrastructure/           # OSM facilities overlay
│   ├── roads/                    # OSM road network proximity
│   └── disaster_history/         # NDMA/USDMA incident schema validator
│
├── configs/                      # Explainable YAML Threshold Configuration
│   ├── capacity.yaml             # PMAY-G 25m2/HH, 40% efficiency, 100ha cap
│   ├── hazard_thresholds.yaml    # Slope/TWI cutoffs for hazard classes
│   ├── priority_thresholds.yaml  # Tier 1/2/3 distance + MH class rules
│   └── site_criteria.yaml        # Slope <=20deg, 1-10ha, MMU, exclusion buffers
│
├── data/
│   ├── raw/                      # Immutable authoritative source data
│   ├── processed/                # Intermediate GeoTIFFs, GPKGs, GeoJSONs
│   └── outputs/                  # Final decision layers served to API
│
├── docs/                         # Engineering + audit documentation
├── tests/test_api.py             # 18 Pytest endpoint + contract tests
├── docker-compose.yml            # Full-stack Docker orchestration
├── Dockerfile.backend            # Production FastAPI container
├── requirements.txt              # Pinned Python dependencies
└── DEPLOYMENT.md                 # Cloud deployment guide
```

---

## 🌐 REST API Reference

Backend auto-generates interactive Swagger docs at **`/docs`** (when running locally: http://localhost:8000/docs).

| Method | Endpoint | What It Returns |
|--------|----------|-----------------|
| `GET` | `/api/health` | System health + data load status |
| `GET` | `/api/metadata` | Project provenance + data source registry |
| `GET` | `/api/decision/summary` | District KPIs: Tier counts, at-risk population, totals |
| `GET` | `/api/villages` | 653 habitation profiles (filter by tier, name, subdistrict) |
| `GET` | `/api/villages/{id}` | Full habitation dossier: demographics, hazard distance, vulnerability flags |
| `GET` | `/api/red-zones` | 289 Candidate Red Zone polygons as GeoJSON |
| `GET` | `/api/candidate-areas` | 5,991 Feasible Relocation Sites with PMAY-G capacity |
| `GET` | `/api/candidate-areas/{id}` | Single site: slope, area, estimated household capacity |
| `GET` | `/api/hazards` | Hazard raster metadata + intensity class definitions |
| `GET` | `/api/infrastructure` | OSM health centers + educational facilities (GeoJSON) |
| `GET` | `/api/infrastructure/summary` | Count breakdown by facility type |
| `GET` | `/api/disasters` | Verified historical disaster incidents (GeoJSON) |
| `GET` | `/api/disasters/summary` | Incidents by type and decade |
| `GET` | `/api/roads` | OSM road network segments (GeoJSON) |
| `GET` | `/api/roads/summary` | Total road length + classification breakdown |
| `GET` | `/api/lulc/summary` | ESA WorldCover land cover class distribution |
| `POST` | `/api/pipeline/recompute` | Operator trigger: re-runs classification pipeline |
| `GET` | `/api/authority/action-queue` | Prioritized SDMA action list ordered by urgency |
| `GET` | `/api/authority/block-summary` | Block/sub-district aggregation of Tier 1 & 2 risk |
| `GET` | `/api/authority/report.csv` | Full village action report as streaming CSV download |

---

## 💻 Frontend GIS Command Center — 9 Views

1. **Executive Dashboard (`/dashboard`)** — District-level KPIs: total habitations screened (653), Tier 1/2/3 counts, at-risk population, quick navigation
2. **Interactive GIS Map (`/map`)** — Multi-layer Leaflet viewer: DEM hillshade, 289 Red Zones, 5,991 Relocation Sites, 653 Habitations, Roads, Infrastructure, Disaster markers with synchronized layer controls
3. **Village Priority Explorer (`/villages`)** — Filterable/searchable table of all 653 habitations, sortable by hazard distance, vulnerability score, population, tier
4. **Village Detail Dossier (`/villages/:id`)** — Deep-dive into any habitation: exact hazard proximity, socio-demographic breakdown, vulnerability flag triggers, recommended admin actions
5. **Candidate Relocation Sites (`/candidate-areas`)** — Interactive explorer for 5,991 feasible sites with slope, area (ha), and PMAY-G dwelling-unit capacity
6. **Authority Action Center (`/authority-action`)** — SDMA command view with actionable planning horizons, block-level risk (Ukhimath, Augustmuni, Jakholi), one-click CSV report export
7. **Dynamic Pipeline Recompute (`/recompute`)** — Operator panel to re-run classification pipeline, inspect step logs, verify updated metadata
8. **Methodology & Explainability (`/methodology`)** — Full algorithmic disclosures: mathematical formulas, threshold rationale, scientific bounds, data sources
9. **Data Status & Gap Register (`/status`)** — Data provenance dashboard: acquired datasets, known limitations, gap tracking

---

## 🚀 Running the Project Locally

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and npm
- *(Optional)* Docker & Docker Compose

### Method A: Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Dheeraj-afk7/SIH26191.git
cd SIH26191

# 2. Set up Python virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install Python GIS dependencies
pip install -r requirements.txt

# 4. Start the FastAPI backend (Port 8000)
python -m backend.main
# --> API: http://localhost:8000
# --> Swagger UI: http://localhost:8000/docs
```

```bash
# In a new terminal — start the React frontend
cd frontend
npm install
npm run dev
# --> Frontend: http://localhost:3000
```

### Method B: Docker Compose (One-Click)

```bash
docker-compose up --build -d
# --> Frontend: http://localhost
# --> API Docs: http://localhost:8000/docs
# --> Health:   http://localhost:8000/api/health

# Stop everything:
docker-compose down
```

### Method C: Run the Test Suite

```bash
pytest
# Expected: 18 passed — covers all API contracts, spatial responses, and error handling
```

---

## ☁️ Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for full cloud instructions:
- **Backend** — Render / Railway (Python 3 environment, Uvicorn process)
- **Frontend** — Vercel (Vite static build, `VITE_API_BASE_URL` env var)
- **Self-hosted** — Docker Compose + Nginx reverse proxy

**Live demo:** https://sih-26191.vercel.app/

---

## ⚖️ Scientific Ethics & Hard Constraints

This project operates under a strict, non-negotiable integrity framework:

1. **Decision-Support Only** — All outputs (hazard zones, relocation tiers) are **preliminary decision-support indicators**. They do NOT constitute official government declarations, statutory red zones, or mandatory eviction orders.

2. **On-Ground Surveys are Mandatory** — Candidate relocation sites are classified on topographic slope (<=20 degrees) and hazard exclusion only. **Geotechnical surveys, bedrock evaluations, and legal cadastral clearances are required** before any construction.

3. **No Uncalibrated Black-Box AI** — Every spatial decision is **deterministic, rule-based, and explainable**. I deliberately avoided ML classifiers for life-safety outputs — every threshold is documented in the YAML config files.

4. **Data Transparency** — The platform explicitly distinguishes verified data from gaps. No synthetic data is used for safety-critical inputs. Known data gaps are tracked in the Data Gap Register.

---

## 📊 Key Numbers at a Glance

| Metric | Value |
|--------|-------|
| Total habitations screened | **653** |
| Candidate Red Zone polygons | **289** |
| Candidate Relocation Site polygons | **5,991** |
| DEM resolution | **30m (Copernicus GLO-30)** |
| Land cover resolution | **10m (ESA WorldCover)** |
| API endpoints | **20** |
| Automated test cases | **18** |
| Frontend views | **9** |
| Processing pipeline modules | **13** |
| CRS used for GIS computation | **UTM Zone 44N (EPSG:32644)** |
| PMAY-G standard applied | **25 m2/household, 40% buildable efficiency** |

---

## 📖 Documentation Links

| Document | Purpose |
|---|---|
| [PROJECT_SPEC.md](docs/PROJECT_SPEC.md) | Problem statement spec + scientific constraints |
| [PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md) | Visual UI tour with 14 screenshot walkthroughs |
| [PROJECT_FORENSIC_AUDIT.md](PROJECT_FORENSIC_AUDIT.md) | 62KB full-codebase forensic audit — every file, every function |
| [DATA_GAP_CLOSURE_STRATEGY.md](docs/DATA_GAP_CLOSURE_STRATEGY.md) | Authoritative data acquisition roadmap |
| [ps_requirement_traceability_matrix.md](docs/ps_requirement_traceability_matrix.md) | Problem statement to code traceability matrix |
| [post_step13_ps_compliance_audit.md](docs/post_step13_ps_compliance_audit.md) | PS compliance evaluation + verification |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Cloud deployment + Docker guide |

---

## 👤 About the Developer

Built for **Smart India Hackathon 2026** (Problem SIH26191) by **K Dheeraj**.

**Data Sources Acknowledged:**
- ESA Copernicus / Sentinel Hub (DEM + Land Cover)
- Development Data Lab — SHRUG v2.2 Village Centroids
- Office of the Registrar General & Census Commissioner of India (Census 2011)
- OpenStreetMap Contributors
- ISRO Bhuvan — Landslide Atlas of India
- NDMA / USDMA — Historical Disaster Records

---

*All geospatial analysis uses open, authoritative public datasets. No proprietary or personally identifiable data is used.*
