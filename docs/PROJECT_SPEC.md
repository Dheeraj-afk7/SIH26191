# PROJECT SPECIFICATION — SIH26191

## Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations

> **Smart India Hackathon 2026**
> Last updated: 2026-08-27 (rev 2 — spec corrections applied)
> Pilot area: Rudraprayag District, Uttarakhand, India

---

## 1. Core Objective

Build a GIS-enabled decision-support application that:

1. Identifies candidate multi-hazard zones.
2. Identifies vulnerable and exposed habitations.
3. Assesses population and infrastructure vulnerability.
4. Integrates historical disaster evidence.
5. Prioritizes habitations for:
   - **Immediate** relocation
   - **Short-Term** relocation
   - **Medium-Term** relocation
6. Identifies **Candidate Topographically Feasible Sites** for relocation.
7. Produces a **Preliminary Spatial Capacity Estimate** (planning scenario only, not engineering-certified).
8. Provides actionable, explainable decision support.
9. Supports dynamic recalculation when new relevant data is supplied.
10. Keeps core spatial analysis and safety-critical decision logic **deterministic and explainable**. AI is not a core dependency and must never govern safety-critical outputs.

---

## 2. Mandatory Scientific Rules

These rules are **non-negotiable** and must be respected in all code, outputs, UI labels, and documentation.

### 2.1 Hazard Claims

| Rule | Reason |
|------|--------|
| **Do NOT** claim to predict exact landslides | Landslide prediction is an unsolved scientific problem at the exact site level |
| **Do NOT** claim to predict exact floods | Flood prediction requires hydrological models outside this scope |
| **Do NOT** label outputs as official government "Red Zones" | Only authorized government bodies can issue official designations |
| **Do NOT** claim candidate zones are guaranteed dangerous | All outputs are *candidate* or *susceptibility* indicators |
| Always label hazard outputs as **"Candidate Hazard-Based Red Zone"** or **"Candidate Hazard Zone"** | Terminology must make non-official status unambiguous |

### 2.2 Relocation Claims

| Rule | Reason |
|------|--------|
| **Do NOT** claim candidate relocation sites are guaranteed safe | Site safety requires field surveys and official geotechnical assessment |
| **Do NOT** automatically authorize relocation | The software may calculate and recommend; it must **never** independently authorize relocation |
| Always label sites as **"Candidate Topographically Feasible Site"** | Never use language implying guaranteed safety |
| All relocation outputs must be labelled **"Decision Support — Requires Official Verification"** | Legal and ethical responsibility |

### 2.3 Data Integrity

| Rule | Reason |
|------|--------|
| **Do NOT** invent datasets | All inputs must be real, citable open data sources |
| **Do NOT** invent government APIs | Use only publicly documented APIs or offline data |
| **Do NOT** fabricate historical disaster data | Historical data must be sourced from NDMA, SDMA, or peer-reviewed sources |
| **Do NOT** fabricate population data | Population data must be sourced from Census of India or equivalent |
| **Do NOT** invent infrastructure data | Use only verified, available infrastructure datasets (e.g., OSM, government surveys) |
| **Do NOT** claim live real-time prediction | The MVP demonstrates data-in → validate → recalculate → updated outputs; no live government API is assumed |

### 2.4 Algorithmic Scope

| Rule | Reason |
|------|--------|
| **Do NOT** add ML models unless explicitly requested | ML adds opacity; core spatial reasoning must remain explainable |
| Core spatial reasoning must remain **explainable** | Administrators must be able to explain decisions to communities |
| AI is **not a core dependency** | The system must be fully functional without any AI/LLM component |
| An RAG/LLM SOP assistant may be added later as an **optional, non-safety-critical** feature | Must be clearly isolated from spatial scoring logic |
| AI/LLM/RAG must **never** govern spatial scores, priority tiers, or site selections | Safety-critical outputs must be deterministic and auditable |
| TOPSIS is an **optional** ranking method, not a mandatory dependency | Core priority must work with rule-based scoring alone |

---

## 3. Core Modules

### Module 1 — Landslide Susceptibility

**Inputs:** DEM (slope, aspect, curvature), lithology, land use/land cover, rainfall isohyets, NDVI.
**Method:** Weighted overlay of susceptibility factors. No ML.
**Output:** Raster — Landslide Susceptibility Index (LSI) [0–1], classified into Low / Medium / High / Very High.
**Caveats:** This is a susceptibility *estimate*, not a prediction.

---

### Module 2 — Flood Exposure

**Inputs:** DEM (elevation, flow accumulation, TWI), river network, historical flood extents (if available).
**Method:** Topographic Wetness Index + distance-to-waterbody + historical overlay.
**Output:** Raster — Flood Exposure Score [0–1], classified into Low / Medium / High.
**Caveats:** Does not account for dam operations, monsoon intensity variability.

---

### Module 3 — Multi-Hazard Candidate Zones

**Inputs:** LSI raster (Module 1), Flood Exposure raster (Module 2).
**Method:** Combined weighted overlay → Multi-Hazard Index (MHI).
**Output:** Raster and vector polygons labelled **"Candidate Hazard-Based Red Zone"** / **"Candidate Hazard Zone"**, classified into Low / Medium / High / Very High.
**Caveats:** Candidate zones only — not official government designations. No legal authority implied.

---

### Module 4 — Habitation Exposure and Vulnerability

**Inputs:** Revenue village / habitation point data, Census population data, MHI (Module 3), and infrastructure data where **verified and available** (e.g., schools, health centres, roads from OSM or government surveys).
**Method:** Spatial join of habitation points to MHI; population exposure scoring; infrastructure exposure scoring (only for datasets that are actually obtained and validated); vulnerability composite index.
**Output:** Scored habitation table + GeoJSON layer.
**Caveats:** Infrastructure vulnerability is included explicitly. Only use infrastructure datasets that have been acquired and verified. Do not invent or proxy infrastructure data.

---

### Module 5 — Relocation Priority

**Inputs:** Habitation vulnerability scores (Module 4), **verified historical disaster evidence** (required input where available, not optional validation), community accessibility.
**Method:** Explainable priority scoring using configurable thresholds and hard safety rules:
  - **Tier 1 (Immediate):** Meets hard safety rule — e.g., Very High MHI AND High vulnerability AND confirmed historical disaster impact
  - **Tier 2 (Short-Term):** High MHI AND Medium-High vulnerability (configurable threshold)
  - **Tier 3 (Medium-Term):** Medium MHI AND lower vulnerability (configurable threshold)
  - Thresholds are stored in `configs/priority_thresholds.yaml` and must be explicitly justified.
  - **Do NOT use arbitrary percentile cutoffs** (e.g., "top 15% = Immediate"). Every tier boundary must be explainable.
  - TOPSIS may be used as an **optional** secondary ranking within a tier, not as the primary classification method.
**Output:** Prioritized habitation list + GeoJSON layer with per-habitation score breakdown.
**Caveats:** Outputs require official government review before any relocation action. Disaster history is a required scoring input where verified data exists.

---

### Module 6 — Candidate Topographically Feasible Site Selection

**Inputs:** DEM (slope < threshold), distance from candidate hazard zones, land use, road accessibility.
**Method:** Multi-criteria suitability analysis (raster-based Boolean and scoring).
**Output:** Polygons labelled **"Candidate Topographically Feasible Site"** with per-criterion suitability scores.
**Caveats:** Sites are *candidate* locations only, identified on topographic and land-use criteria. They are **not guaranteed safe**. Field surveys, geotechnical assessment, and legal clearance are required before any site is used for relocation.

---

### Module 7 — Preliminary Spatial Capacity Estimate

**Inputs:** Candidate Topographically Feasible Site polygons (Module 6), population to be relocated (Module 5).
**Method:** Area-based capacity estimate using configurable planning assumptions (e.g., area per household). All assumptions are treated as **explicit planning scenarios**, documented in `configs/capacity.yaml`, and must be verified before implementation.
**Output:** Capacity table per candidate site; demand-vs-supply summary labelled **"Preliminary Spatial Capacity Estimate"**.
**Caveats:** This output satisfies the SIH carrying-capacity requirement at MVP level. It is **not engineering-certified carrying capacity**. Any population-per-area figure must be presented with its documented assumptions. Engineering surveys are required before actual use.

---

## 4. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| GIS Processing | Python: rasterio, geopandas, shapely, numpy, scipy | Core spatial pipeline |
| Backend API | FastAPI + uvicorn | Serves processed GeoJSON/JSON results |
| Frontend | React + Leaflet | Interactive GIS map |
| Data formats | GeoTIFF (rasters), GeoJSON (vectors), CSV | Interoperable open formats |
| Config | YAML via pydantic-settings | Parameterized, reproducible |

### Explicitly excluded (do not introduce without approval):

- PostgreSQL / PostGIS
- GeoServer
- Kafka / Redis / Celery
- Cloud infrastructure (AWS, GCP, Azure)
- Complex microservices
- ML models (scikit-learn, PyTorch, TensorFlow)
- RAG / LLM inference *(may be added later as an optional, non-safety-critical SOP assistant — requires explicit approval)*
- Any paid API

---

## 5. Data Sources (Open, Citable)

| Dataset | Source | Format |
|---------|--------|--------|
| Digital Elevation Model | **Preferred candidate:** Copernicus GLO-30 (30m, open access). Alternatives: SRTM 30m, Cartosat-1 (ISRO Bhuvan). Final selection after acquisition and validation. | GeoTIFF |
| Land Use / Land Cover | ISRO Bhuvan LULC / NLSMA | GeoTIFF |
| River network | OpenStreetMap / WRIS India | Shapefile / GeoJSON |
| Administrative boundaries | Census of India / Survey of India | Shapefile |
| Population | Census of India 2011 (village-level) | CSV / Shapefile |
| Historical disaster events | NDMA / EM-DAT / SDMA Uttarakhand | CSV |
| Rainfall | IMD gridded data | NetCDF / GeoTIFF |
| Geology / Lithology | GSI (Geological Survey of India) | Shapefile |

> **Note:** All datasets must be downloaded, cited, and placed in `data/raw/`. Do not fabricate or interpolate missing data without documenting assumptions.

---

## 6. Configuration Parameters (`configs/`)

All scoring weights and thresholds must be stored in YAML config files so they can be adjusted without changing code. Examples:

- `configs/hazard_weights.yaml` — weights for landslide susceptibility factors
- `configs/priority_thresholds.yaml` — score thresholds for Tier 1/2/3
- `configs/site_selection.yaml` — slope threshold, distance buffers for site selection
- `configs/capacity.yaml` — area-per-household assumption, population density limits

---

## 7. Output Labelling Requirements

All map layers, report outputs, and UI elements must carry one of the following disclaimers as appropriate:

> *"Candidate zone — requires official geotechnical and administrative verification before any relocation action."*

> *"Decision support only — not an official government Red Zone designation."*

> *"Preliminary capacity estimate — engineering surveys required."*

---

## 8. Pilot Scope

- **District:** Rudraprayag, Uttarakhand *(provisional primary pilot — subject to data availability confirmation)*
- **Coordinate Reference System:** WGS84 (EPSG:4326) for storage; UTM Zone 44N (EPSG:32644) for metric calculations
- **Bounding box:** Do **not** hardcode an approximate bounding box. The pilot extent will be derived from the administrative boundary dataset once acquired and validated.
- **Architecture must remain geographically generalizable** — district, state, CRS, and all spatial extents must be config-driven, not hardcoded.

---

## 9. Problem Statement Compliance Checklist

The application must explicitly address all of the following SIH26191 requirements:

| Requirement | Module(s) | Status |
|-------------|-----------|--------|
| Multi-hazard zone identification | Module 1, 2, 3 | Planned |
| Dynamic updating (new data → recalculate → updated outputs) | All modules + Backend | Planned |
| Vulnerable habitation identification | Module 4 | Planned |
| Population vulnerability assessment | Module 4 | Planned |
| Infrastructure vulnerability assessment | Module 4 | Planned |
| Disaster history integration (required input, not optional) | Module 5 | Planned |
| Immediate / Short-Term / Medium-Term relocation prioritization | Module 5 | Planned |
| Candidate alternative relocation sites | Module 6 | Planned |
| Preliminary spatial carrying capacity estimate | Module 7 | Planned |
| Actionable, explainable decision support | All modules + Frontend | Planned |
| Optional justified AI layer (non-safety-critical) | Future phase | Optional |

---

## 10. Human-in-the-Loop Requirement

- The software may **calculate, score, and recommend**.
- It must **never independently authorize relocation**.
- Every output that could inform a relocation decision must include a visible disclaimer requiring official government review and community consent before any action is taken.
- This rule applies to all code, APIs, UI labels, and exported reports.

---

## 11. Dynamic Update Contract

The MVP must demonstrate this data flow:

```
new data / updated input
  → input validation (schema, CRS, completeness check)
  → recalculation of affected module(s)
  → updated hazard / vulnerability / priority outputs
  → updated map layers served via API
```

- **Do NOT** claim live real-time prediction.
- **Do NOT** assume live government API feeds.
- Dynamic update means: a user or operator supplies a new dataset file, the pipeline validates and reprocesses it, and the outputs update accordingly.

---

## 12. Open Questions for Future Phases

- Integration of real-time IMD rainfall alerts (when API access is confirmed).
- Community participation data input mechanism.
- Final reporting format (PDF export? QGIS project?).
- Multi-district scalability testing.
- Formal accuracy validation protocol.
- Optional RAG/LLM SOP assistant specification (if approved).
