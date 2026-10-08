# Results & Quantitative Evaluation: SIH26191

## Experimental Setup & Pilot Environment
- **Pilot Geographic District:** Rudraprayag District, Uttarakhand, India (Total Area: $372,128.32\text{ ha} \approx 2,439\text{ km}^2$).
- **Coordinate Reference System:** Evaluated in projected metric space WGS 84 / UTM Zone 44N (`EPSG:32644`).
- **Demographic Scope:** 653 rural revenue habitations from Census 2011 Primary Census Abstract (232,360 residents, 50,882 households).
- **Hazard Surface:** $30\text{m}$ grid derived from Copernicus GLO-30 DEM ($>3.5\text{M}$ active raster cells).
- **Execution Environment:** Windows / Linux containerized environment; Python 3.10+ ASGI backend with GeoPandas and Rasterio.

---

## Quantitative Evaluation Results

### 1. Village Priority Classification & At-Risk Population Breakdown

| Priority Tier | Planning Horizon (PS-7) | Horizon Years | Village Count | Percentage of Villages | At-Risk Population | At-Risk Households |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Tier 1 — Attention Priority** | `IMMEDIATE_FIELD_ASSESSMENT` | 0–1 yr | **12** | 1.84% | **4,750** | **977** |
| **Tier 2 — Elevated Attention** | `SHORT_TERM_PLANNING_REVIEW` | 1–3 yr | **69** | 10.57% | **23,012** | **4,674** |
| **Tier 3 — Monitoring** | `MEDIUM_TERM_MONITORING` | 3–10 yr | **204** | 31.24% | **64,463** | **13,978** |
| **Beyond Proximity** | `ROUTINE_MONITORING` | 10+ yr | **368** | 56.36% | **140,135** | **31,253** |
| **Total District Baseline** | — | — | **653** | **100.00%** | **232,360** | **50,882** |

> **Key Finding:** Exactly **81 habitations** ($12.41\%$) representing **27,762 residents** and **5,651 households** fall within active planning attention tiers (Tier 1 & Tier 2), providing SDMA authorities with a clear, manageable target for near-term field surveys.

---

### 2. Top 12 Attention Priority Habitations (Tier 1 Drill-Down)

All 12 Tier 1 habitations strictly satisfy the proximity rule ($d \le 500\text{m}$ to Candidate Red Zone with $\text{MH Class} \ge 2$ at centroid):

| Village ID | Village Name | Population | Households | Nearest Hazard Distance ($m$) | Nearest Red Zone ID | Centroid MH Class | Key Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **42573** | **Marora** | 208 | 49 | **42.5 m** | RZ-220 | Class 2 | Extreme proximity to active hazard polygon |
| **42067** | **Tarsali** | 98 | 20 | **178.5 m** | RZ-018 | Class 2 | High-steepness valley flank proximity |
| **42165** | **Dungar semala** | 580 | 110 | **310.8 m** | RZ-048 | Class 2 | Within 500m screening perimeter |
| **42320** | **Narkota** | 357 | 83 | **321.5 m** | RZ-250 | Class 2 | Adjacent to major red zone cluster |
| **42129** | **Gadagu** | 601 | 117 | **330.5 m** | RZ-152 | Class 2 | Valley channel and slope hazard exposure |
| **42080** | **Jaltalla** | 373 | 79 | **349.1 m** | RZ-045 | Class 2 | Moderate terrain susceptibility at centroid |
| **42086** | **Kabiltha** | 341 | 62 | **349.6 m** | RZ-261 | Class 2 | High slope proximity |
| **42127** | **Burua** | 386 | 71 | **410.6 m** | RZ-091 | Class 2 | Within 500m hazard envelope |
| **42128** | **Madali** | 5 | 2 | **425.1 m** | RZ-174 | Class 2 | Small isolated hamlet in hazard buffer |
| **42058** | **Gaurikund** | 223 | 43 | **468.8 m** | RZ-008 | Class 2 | Famous Kedarnath gateway, chronic history |
| **42118** | **Gaundar** | 294 | 45 | **486.4 m** | RZ-145 | Class 2 | Madhyamaheshwar valley flank |
| **42574** | **Mawana** | 1,284 | 296 | **497.6 m** | RZ-220 | Class 2 | High population concentration near RZ-220 |

---

### 3. Habitation Hazard Proximity Distribution

| Distance Band | Village Count | Population | Cumulative Population | Cumulative Percentage |
| :--- | :--- | :--- | :--- | :--- |
| **Within 500 m** | 14 | 5,305 | 5,305 | 2.28% |
| **500 m to 1 km** | 16 | 4,858 | 10,163 | 4.37% |
| **1 km to 2 km** | 51 | 17,599 | 27,762 | 11.95% |
| **2 km to 5 km** | 204 | 64,463 | 92,225 | 39.69% |
| **5 km to 10 km** | 255 | 93,965 | 186,190 | 80.13% |
| **Beyond 10 km** | 113 | 46,170 | 232,360 | 100.00% |

---

### 4. Demographic Vulnerability Context Benchmarks ($P_{75}$)

Computed across all 653 Census 2011 habitations in Rudraprayag District:

| Vulnerability Dimension | Mean Value | Median ($P_{50}$) | Upper Tertile ($P_{75}$) Cutoff | Max Observed | Villages Flagged ($\ge P_{75}$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Child Population Rate (`P_06 / TOT_P`)** | 12.67% | 12.67% | **15.10%** | 37.50% | 164 villages |
| **Scheduled Caste Rate (`TOT_SC / TOT_P`)** | 14.65% | 3.85% | **24.60%** | 100.00% | 164 villages |
| **Non-Worker Dependency Rate** | 52.48% | 51.70% | **57.90%** | 100.00% | 164 villages |
| **Illiteracy Rate (`P_ILL / TOT_P`)** | 29.62% | 29.46% | **34.00%** | 88.89% | 164 villages |
| **Scheduled Tribe Rate (`TOT_ST / TOT_P`)** | 0.08% | 0.00% | **0.00%** | 12.50% | *Omitted (ST absent)* |

---

### 5. Candidate Relocation Sites & Capacity Modeling Results

- **Candidate Topographically Feasible Sites:** **2,998 discrete polygons** (filtered to $1.0–10.0\text{ ha}$, $\text{slope} \le 20^\circ$, hazard-excluded, ESA WorldCover non-forest).
- **Total Feasible Land Area:** **8,095.52 hectares**.
- **PMAY-G Dwelling Capacity Scenario:**
  - Standard applied: $25.0\text{ m}^2/\text{HH}$ built floor area with $40\%$ net buildable site utilization efficiency ($\eta = 0.40$).
  - Sample site capacity (e.g., $10.0\text{ ha}$ polygon): Usable area $= 4.0\text{ ha}$ ($39,985\text{ m}^2$) $\rightarrow$ **1,599 households** ($\approx 6,396\text{ persons}$).
  - Scale protection constraint: Polygons $>100\text{ ha}$ are flagged as `AREA_EXCEEDS_SITE_PLANNING_SCALE` to prevent macro-scale over-estimation.

---

### 6. Infrastructure, Road Accessibility & Disaster Exposure Metrics

- **Critical Infrastructure (291 facilities):**
  - Mean distance to nearest health facility: **$1,848.9\text{ m}$** ($646/653$ habitations within $5\text{ km}$).
  - Mean distance to nearest Hospital / CHC: **$4,921.6\text{ m}$** ($315/653$ habitations within $60\text{ min}$ drive).
  - Mean distance to nearest secondary/higher school: **$12,250.1\text{ m}$** ($36/653$ habitations within $3\text{ km}$).
- **Road Network ($6,397.35\text{ km}$ total length):**
  - Mean distance from habitation to nearest road: **$344.1\text{ m}$**.
  - Mean travel time to arterial highway: **$38.0\text{ minutes}$**.
  - Isolation Classification: Moderately Accessible ($249$), Remote ($180$), Highly Accessible ($142$), Severely Remote ($71$), Isolated ($11$).
- **Historical Disaster History (22 canonical events, 1998–2024):**
  - Habitations within $1\text{ km}$ of past disaster epicenter: **33 villages**.
  - Habitations within $2\text{ km}$ of past disaster epicenter: **129 villages**.
  - Habitations with chronic historical exposure: **26 villages**.

---

## Runtime, Latency & Computational Performance

| Operation / Endpoint | Scope / Dataset Size | Execution Time / Latency | Memory Footprint |
| :--- | :--- | :--- | :--- |
| **Backend Lifespan Startup (`load_all`)** | 653 villages, 289 red zones, 2,998 sites, 291 POIs, 22 disasters | **~1.8 seconds** | ~180 MB RAM |
| **`GET /api/villages` (Paginated)** | 25 GeoJSON features with attributes | **< 15 ms** | In-memory cache |
| **`GET /api/decision/summary`** | Full district aggregation statistics | **< 8 ms** | In-memory JSON |
| **`GET /api/candidate-areas`** | GeoJSON query with BBox spatial index | **< 45 ms** | R-tree indexed |
| **`GET /api/authority/report.csv`** | Dynamic CSV streaming (81 Tier 1/2 rows) | **< 25 ms** | In-memory buffer |
| **`POST /api/pipeline/recompute`** | Full pipeline re-execution (Steps 10B–10E) | **~12–18 seconds** | Subprocess thread |
| **Full Raster Processing Pipeline (Steps 3–10)** | District-scale 30m rasters ($>3.5\text{M}$ cells) | **~85.5 seconds** | ~1.2 GB peak RAM |

---

## Hardware Requirements
- **Minimum Development / Demonstration:**
  - CPU: Dual-Core x86_64 / ARM64 (e.g., Intel i3 / Apple M1)
  - RAM: 4 GB RAM
  - Storage: 2 GB free disk space (includes all raw and processed rasters)
- **Production Server Deployment:**
  - Container: 1 vCPU, 1 GB RAM (e.g., Render Free/Starter tier or AWS t4g.micro)
  - Client: Modern web browser (Chrome, Firefox, Edge, Safari) with WebGL/Canvas support.

---

## Limitations of the Evaluation
1. **Absence of Real-Time Ground Truth Validation:** Official post-disaster geotechnical drilling logs and slope inclinometer datasets are not publicly released by USDMA for academic benchmarking.
2. **Census Vintage Gap:** Demographic baseline relies on the 2011 Census of India; dynamic population changes over the last decade are unrepresented.
3. **Centroid vs Footprint Approximation:** Proximity calculations are derived from administrative settlement reference centroids rather than high-resolution building polygon footprints.
