# DATA GAP CLOSURE STRATEGY
## SIH26191 — Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations
### Pilot Area: Rudraprayag District, Uttarakhand, India
**Document Version:** 1.0 (Pre-Acquisition Engineering & Scientific Blueprint)  
**Date:** 2026-08-30  
**Target Audience:** SIH Team Developers, GIS Analysts, Field Survey Leads, and Technical Evaluators  
**Primary Reference:** `PROJECT_FORENSIC_AUDIT.md` (Forensic Source of Truth)  
**Live System:** `https://sih-26191.vercel.app/`

---

## 1. Executive Summary

This document defines the **Data Gap Closure Strategy** for **SIH26191**, a GIS-based Decision-Support System (DSS) developed for disaster risk assessment, village prioritization, candidate relocation area screening, and preliminary spatial capacity estimation in **Rudraprayag District, Uttarakhand**.

### 1.1 Current Operational Baseline (Category A — Verified & Operational)
The current working system operates on a 100% verified, deterministic pipeline processing:
1. **Copernicus GLO-30 DEM (30m):** Yields metric terrain slope, aspect, D8 flow accumulation, Topographic Wetness Index (TWI), continuous terrain susceptibility proxies, continuous flood exposure proxies, and a 50/50 multi-hazard screening score.
2. **Morphological Connected-Component Clustering:** Vectorizes 289 Candidate Hazard-Based Red Zones ($\ge 5,000\text{ m}^2$).
3. **Census of India 2011 Primary Census Abstract (PCA):** 653 rural habitations joined deterministically (100% match) to SHRUG v2.2 spatial centroid coordinates (`rudraprayag_census_villages_shrug.geojson`).
4. **Deterministic Rule-Based Decision Engine:** Classifies villages into 12 Tier 1 (Attention Priority), 69 Tier 2 (Elevated Attention), 204 Tier 3 (Monitoring), and 368 Beyond Proximity habitations, enriched with 4 district P75 demographic vulnerability context flags (Child Pop, SC Pop, Dependency, Illiteracy) and 4 PS-7 Relocation Planning Horizons (`IMMEDIATE_FIELD_ASSESSMENT`, `SHORT_TERM_PLANNING_REVIEW`, etc.).
5. **Topographic Candidate Relocation Area Screening:** Identifies non-hazardous, low-slope ($\le 20^\circ$) terrain polygons and evaluates preliminary dwelling-unit capacity scenarios using the GoI PMAY-G 25 m²/household standard with a 40% site efficiency factor and a 100 ha scale protection cap.
6. **Live Full-Stack Platform:** FastAPI ASGI backend containerized on Docker, React 18 + Vite + Leaflet frontend deployed on Vercel (`https://sih-26191.vercel.app/`), featuring an Authority Action Center with block-level aggregation, dynamic recomputation (`POST /api/pipeline/recompute`), and CSV reporting.

### 1.2 The 4 Identified Data Gaps (Category C — Architecture Ready, Data Not Acquired)
While the core pipeline is fully functional and architecturally robust, four critical data layers currently remain unpopulated with live district data:
1. **Disaster History Records (Severity: HIGH)** — Relies currently on static terrain slope and TWI; historical cloudburst, debris flow, and landslide event catalogs from USDMA/NDMA are pending ingestion.
2. **Critical Infrastructure (Severity: MEDIUM)** — Educational institutions, primary healthcare centres, and emergency facilities are not yet attributed, precluding infrastructure vulnerability scoring.
3. **Road Network & Accessibility (Severity: HIGH)** — Spatial distance calculations are currently Euclidean (straight-line); network distance and travel-time accessibility along mountain corridors are pending routable road vector integration.
4. **Land Use / Land Cover & Forest Restrictions (Severity: HIGH)** — Candidate relocation sites are screened topographically only; legal land-use constraints (e.g., Kedarnath Wildlife Sanctuary, Reserve Forests, active agricultural terraces) are not yet subtracted.

### 1.3 Scientific Stance & Core Operational Principles
- **Decision Support Only:** The system does NOT issue mandatory evacuation orders, does NOT declare land officially "safe," does NOT authorize relocation, and does NOT generate automated village-to-site matching without human authority review.
- **Strict Provenance & Verification:** Every dataset must have documented provenance (provider, vintage, resolution, CRS, license). Unverified datasets or fabricated coordinates are strictly barred.
- **Pragmatic Student Hackathon Roadmap:** Recognizing government data request latencies, this strategy establishes a two-track acquisition model: (a) Immediate acquisition of reliable open geospatial data (OSM, ESA WorldCover, NRSC Open Atlas, UDISE+) for instant pipeline activation; (b) Formal institutional request templates for official USDMA/PWD records.

---

## 2. Current Data Gap Analysis

The table below contrasts the current implementation state against the target operational state for each of the four Category C datasets.

| Dataset Area | Current Implementation State | Architectural Readiness & Existing Hooks | Scientific & Operational Impact of Gap | Gap Severity |
| :--- | :--- | :--- | :--- | :--- |
| **1. Disaster History Records** | Synthetic records exist for schema testing only (`synthetic_demo_incidents.geojson`). Tiers are determined solely by DEM slope and TWI proximity. | `data/processed/disaster_history/schema.json`<br>`processing/disaster_history/validate_disaster_data.py`<br>`configs/priority_thresholds.yaml` (L108–122) | Villages subject to recurring cloudbursts or chronic debris flows outside steep DEM zones are not automatically elevated to Tier 1. Overlooks empirical disaster validation. | **HIGH** |
| **2. Critical Infrastructure** | Infrastructure scoring is omitted; documented as `NOT_ACQUIRED` in metadata and thresholds config. | `configs/priority_thresholds.yaml` (L123–130)<br>`docs/PROJECT_SPEC.md` Module 4 hook<br>Authority queue schema placeholder | Cannot evaluate whether a village lacks essential lifeline facilities (e.g., no PHC or secondary school within 5 km), which compounds demographic vulnerability during isolation. | **MEDIUM** |
| **3. Road Network & Accessibility** | Nearest-hazard and village-to-site distances are computed as Euclidean straight-line metric distances in EPSG:32644. | `configs/project.yaml`<br>`processing/capacity/build_candidate_context.py`<br>`data/processed/decision/candidate_area_context.gpkg` | In Himalayan mountain valleys, Euclidean distance severely underestimates actual travel distance/time. A site 2 km away across a deep gorge may require a 25 km detour or be entirely inaccessible. | **HIGH** |
| **4. Land Use / Land Cover (LULC)** | Candidate relocation areas are screened by slope ($\le 20^\circ$), flood class exclusion, and red zone exclusion only. | `configs/project.yaml` (L370–435)<br>`processing/sites/identify_candidate_areas.py`<br>`candidate_area_context.gpkg` | Candidate polygons may fall inside Kedarnath Wildlife Sanctuary, Reserve Forests (requiring central Forest Conservation Act clearances), dense forests, river channels, or active agriculture. | **HIGH** |

---

## 3. Dataset-by-Dataset Acquisition Specification

### 3.1 Dataset 1: Disaster History Records

#### A. Exact Data Requirements
- **Required Layers/Fields:** 
  - `incident_id` (String, format `DIS-RDP-YYYY-NNN`)
  - `incident_date` (ISO 8601 `YYYY-MM-DD`)
  - `hazard_type` (Enum: `LANDSLIDE`, `CLOUDBURST`, `FLOOD`, `EARTHQUAKE`, `LAND_SUBSIDENCE`, `AVALANCHE`, `DEBRIS_FLOW`)
  - `geometry` (Point or Polygon in EPSG:4326)
  - `severity` (Enum: `MINOR`, `MODERATE`, `MAJOR`, `CATASTROPHIC`)
  - `deaths_reported` (Integer $\ge 0$, nullable)
  - `households_affected` (Integer $\ge 0$, nullable)
  - `villages_affected` (Array of Census Village IDs / names)
  - `verified_source` (Enum: `OFFICIAL_GOVERNMENT`, `ISRO_NRSC`, `NDRF_REPORT`, `PEER_REVIEWED_RESEARCH`, `UNVERIFIED`)
  - `source_citation` (String, official document or publication reference)
- **Geographic Coverage:** Rudraprayag District bounding box (Bounding Box: $78.78^\circ\text{E}$ to $79.37^\circ\text{E}$, $30.19^\circ\text{N}$ to $30.81^\circ\text{N}$). Focus corridors: Mandakini Valley (Rudraprayag–Augustmuni–Guptkashi–Sonprayag–Kedarnath), Alaknanda Valley (Rudraprayag–Gholtir), Madhyamaheshwar & Vasuki Valleys.
- **Time Period:** 1998–2024 (minimum coverage: 2013 Kedarnath disaster to 2023 monsoon season).
- **Spatial Resolution / Accuracy:** $\le 100\text{ m}$ positional accuracy for point coordinates; polygon extents for large mass movements.
- **Preferred File Formats:** GeoJSON (`.geojson`), OGC GeoPackage (`.gpkg`), or structured CSV with `latitude`/`longitude`.
- **Target Coordinate Reference System:** Source in `EPSG:4326` (WGS 84); normalized to `EPSG:32644` (UTM Zone 44N) for metric buffering.

#### B. Data Source Strategy & Ranking

| Rank | Source Classification | Provider / Organization | Dataset Name & Access Point | Format & Coverage | Advantages | Limitations | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Official Government** | **Uttarakhand State Disaster Management Authority (USDMA) / NDMA** | *USDMA Disaster Incident Register & Post-Disaster Needs Assessments (PDNA)*<br>URL: `https://usdma.uk.gov.in/` | Tabular PDF/Excel / GIS records; State-wide / Rudraprayag | Official government provenance; highly authoritative; records relief compensation & fatalities. | Not publicly accessible as a direct GIS vector API; requires formal Right to Information (RTI) or academic request letter. | **VERIFIED (Existence)**<br>*Unverified direct download* |
| **2** | **Research / Institutional** | **ISRO National Remote Sensing Centre (NRSC)** | *Landslide Atlas of India (2023) — Rudraprayag District Inventory*<br>URL: `https://bhuvan.nrsc.gov.in/` & NRSC Open Data Archive | PDF Atlas & Bhuvan Geo-portal WMS/Vector (12,319 recorded landslides in Rudraprayag) | Highly rigorous satellite-derived inventory (1998–2022); ranks Rudraprayag #1 in India for landslide density (11.45/km²); peer-reviewed ISRO methodology. | WFS/Vector download restricted on Bhuvan; points extracted from spatial atlas or published GIS annexures. | **VERIFIED** |
| **3** | **Reliable Open Geospatial** | **NASA Open Data / Global Landslide Catalog (GLC/COOLR)** | *NASA Cooperative Open Online Landslide Repository (COOLR)*<br>URL: `https://data.nasa.gov/` | GeoJSON / CSV; Global coverage filtered to Rudraprayag BBox | Free, open access, standardized schema; includes major rain-triggered landslide events. | Sparse coverage in rural mountain belts; captures only major reported events (under-reports localized road cut failures). | **VERIFIED** |
| **4** | **Fallback (Open Literature)** | **Peer-Reviewed Scientific Inventories (Martha et al., 2015; Dikshit et al., 2020)** | *Post-2013 Kedarnath Disaster Spatial Landslide Inventory*<br>Published in *Geomorphology* / *Landslides* journals | Shapefile / GeoPackage in scientific data repositories (Mendeley Data, Zenodo) | Exhaustive high-resolution spatial mapping of 2013 Mandakini valley failures; fully open and citable. | Temporal snapshot focused heavily on June 2013 event; requires manual spatial harmonization. | **VERIFIED** |

---

### 3.2 Dataset 2: Critical Infrastructure

#### A. Exact Data Requirements
- **Required Layers/Fields:**
  - `facility_id` (String, format `INF-RDP-TYPE-NNN`)
  - `facility_name` (String)
  - `facility_type` (Enum: `PRIMARY_HEALTH_CENTRE`, `COMMUNITY_HEALTH_CENTRE`, `DISTRICT_HOSPITAL`, `SUB_CENTRE`, `PRIMARY_SCHOOL`, `SECONDARY_SCHOOL`, `HIGHER_SECONDARY_SCHOOL`, `COLLEGE`, `POLICE_STATION`, `FIRE_STATION`, `PANCHAYAT_BHAWAN`, `EMERGENCY_SHELTER`)
  - `category` (Enum: `HEALTH`, `EDUCATION`, `EMERGENCY_GOVERNANCE`, `COMMUNITY`)
  - `geometry` (Point in EPSG:4326)
  - `village_code_census` (Integer, 6-digit Census 2011 Village ID if colocated)
  - `bed_capacity` / `student_capacity` (Integer, nullable)
  - `data_source` (Enum: `UDISE_PLUS`, `NATIONAL_HEALTH_PORTAL`, `OPENSTREETMAP`, `DISTRICT_DIRECTORY`)
- **Geographic Coverage:** Full Rudraprayag District (all 3 Tehsils: Rudraprayag, Ukhimath, Jakholi).
- **Time Period:** 2021–2024 (current operational status).
- **Spatial Resolution / Accuracy:** $\le 50\text{ m}$ (building/campus centroid).
- **Preferred File Formats:** GeoJSON (`.geojson`), OGC GeoPackage (`.gpkg`), Shapefile (`.shp`).
- **Target Coordinate Reference System:** Source in `EPSG:4326`; metric calculations in `EPSG:32644`.

#### B. Data Source Strategy & Ranking

| Rank | Source Classification | Provider / Organization | Dataset Name & Access Point | Format & Coverage | Advantages | Limitations | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Reliable Open Geospatial** | **OpenStreetMap Contributors / Geofabrik / Overpass API** | *OpenStreetMap Uttarakhand POI & Infrastructure Extract*<br>Query: `amenity=school|hospital|clinic|doctors|police|fire_station|community_centre` via Overpass Turbo | GeoJSON / Shapefile; Full Rudraprayag extent | Instantly extractable via Overpass API; includes major hospitals (District Hospital Belni), schools, police stations, and petrol stations; open ODbL license. | Volunteer mapped; coverage in interior habitations can have omission errors. | **VERIFIED** |
| **2** | **Official Government (Education)** | **Ministry of Education, GoI / Department of School Education Uttarakhand** | *Unified District Information System for Education Plus (UDISE+) School Directory*<br>URL: `https://udiseplus.gov.in/` | Tabular CSV/Excel with School Lat/Long; Rudraprayag District (~800+ schools) | Complete census of all government and private schools with exact Census Village cross-references. | Lat/long coordinates occasionally contain GPS entry typos; requires automated bounding box validation. | **VERIFIED** |
| **3** | **Official Government (Health)** | **National Health Mission (NHM) Uttarakhand / Ministry of Health & Family Welfare** | *National Health Health Facility Registry (HFR) / PMJAY Portal*<br>URL: `https://facility.abdm.gov.in/` & NHM Uttarakhand Directory | Tabular JSON/Excel; District Hospital, 3 CHCs, 12 PHCs, 70+ Sub-Centres | 100% verified registry of public health facilities in Rudraprayag. | Geocoding required for sub-centres lacking native coordinate attributes. | **VERIFIED** |
| **4** | **Fallback (Government GIS)** | **National Informatics Centre (NIC) / Bharat Maps** | *NIC Multi-Layer GIS Directory (Health & Education Layers)*<br>URL: `https://bharatmaps.gov.in/` | WMS / Tile Services | Standardized Government of India spatial baseline. | Vector download restricted; primarily consumable via WMS map service. | **VERIFIED** |

---

### 3.3 Dataset 3: Road Network & Accessibility

#### A. Exact Data Requirements
- **Required Layers/Fields:**
  - `road_id` (String / Integer OSM ID)
  - `road_name` (String, e.g., "NH-107 (Kedarnath Highway)", "NH-07 (Badrinath Highway)", "PMGSY Mandal Road")
  - `highway_class` (Enum: `national_highway`, `state_highway`, `major_district_road`, `rural_road_pmgsy`, `residential`, `track`, `footway_path`)
  - `surface_type` (Enum: `paved_asphalt`, `concrete`, `unpaved_gravel`, `dirt_track`, `unknown`)
  - `lane_count` (Integer, nullable)
  - `all_weather` (Boolean, true for asphalt/concrete, false for dirt/seasonal tracks)
  - `average_speed_kmh` (Assigned impedance: National=40, State=30, Rural=20, Track=10, Footway=4)
  - `geometry` (LineString / MultiLineString in EPSG:4326 / EPSG:32644)
- **Geographic Coverage:** Full Rudraprayag District with a 10 km cross-boundary buffer (to maintain topological network connectivity into Chamoli, Tehri Garhwal, and Pauri Garhwal).
- **Time Period:** 2023–2024 (incorporating post-Char Dham all-weather road widening alignments).
- **Spatial Resolution / Accuracy:** $\le 15\text{ m}$ alignment precision along mountain valley roads.
- **Preferred File Formats:** OGC GeoPackage (`.gpkg`), GeoJSON (`.geojson`), OSM PBF (`.osm.pbf`).
- **Target Coordinate Reference System:** Stored in `EPSG:32644` (UTM Zone 44N) for strict topological network routing and length calculations in metres.

#### B. Data Source Strategy & Ranking

| Rank | Source Classification | Provider / Organization | Dataset Name & Access Point | Format & Coverage | Advantages | Limitations | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Reliable Open Geospatial** | **OpenStreetMap Contributors / Geofabrik GmbH** | *Geofabrik India / Uttarakhand Regional Extract (`uttarakhand-latest.osm.pbf`)*<br>URL: `https://download.geofabrik.de/asia/india.html` | OSM PBF / Shapefile / GeoPackage; Complete highway hierarchy | Clean topological routable graph; includes NH-107, NH-07, State Highways, and village bridleways; free open license (ODbL). | Road surface classifications (paved vs. unpaved) may be incomplete on interior village tracks. | **VERIFIED** |
| **2** | **Official Government (Rural)** | **Ministry of Rural Development (MoRD) / National Rural Infrastructure Development Agency (NRIDA)** | *PMGSY GeoSadak / OMMAS Rural Road GIS Network*<br>URL: `https://geosadak-pmgsy.nic.in/` | Web GIS / Vector Shapefiles; Rudraprayag PMGSY roads | Official rural habitation connectivity data; exact Habitation-to-Road link records. | Direct shapefile download requires department login; public access via GeoSadak map viewer. | **VERIFIED** |
| **3** | **Official Government (National/State)** | **Public Works Department (PWD) Uttarakhand / NHAI** | *PWD Road Inventory & Char Dham All-Weather Highway Alignment*<br>URL: `https://pwd.uk.gov.in/` | Tabular road register / Cadastral alignment maps | Official engineering classification, bridge locations, landslide-prone road cut zones. | Typically maintained in tabular chainage format (km marks) rather than clean vector GIS networks. | **VERIFIED** |
| **4** | **Fallback (Global)** | **Global Roads Open Access Data Set (GROADS v1) / CIESIN Columbia University** | *CIESIN Global Roads Open Access Data Set*<br>URL: `https://sedac.ciesin.columbia.edu/data/set/groads-global-roads-open-access-v1` | Shapefile / GeoPackage | Standardized global road baseline. | Coarse alignment; misses post-2015 Char Dham realignment and minor PMGSY rural spurs. | **VERIFIED** |

---

### 3.4 Dataset 4: Land Use / Land Cover (LULC) & Forest Restrictions

#### A. Exact Data Requirements
- **Required Layers/Fields:**
  - `lulc_class_code` (Integer)
  - `lulc_class_name` (Enum: `TREE_COVER_DENSE_FOREST`, `OPEN_FOREST_SCRUB`, `GRASSLAND_ALPINE_MEADOW`, `CROPLAND_AGRICULTURE`, `BUILT_UP_SETTLEMENT`, `BARE_SOIL_ROCK`, `PERMANENT_SNOW_GLACIER`, `WATER_BODY_RIVER`)
  - `legal_status` (Enum: `RESERVE_FOREST`, `PROTECTED_FOREST`, `WILDLIFE_SANCTUARY`, `CIVIL_SOYAM_LAND`, `REVENUE_VILLAGE_LAND`, `PRIVATE_LAND`)
  - `protected_area_flag` (Boolean, true for Kedarnath Wildlife Sanctuary and designated Eco-Sensitive Zones)
  - `candidate_suitability_flag` (Boolean: 0 for Excluded, 1 for Topographically and Legally Feasible)
  - `geometry` (Raster grid or vector polygon in EPSG:4326 / EPSG:32644)
- **Geographic Coverage:** Complete Rudraprayag District extent ($1,984\text{ km}^2$).
- **Time Period:** 2020–2024.
- **Spatial Resolution / Accuracy:** $10\text{ m}$ to $30\text{ m}$ raster grid cell size.
- **Preferred File Formats:** Cloud-Optimized GeoTIFF (`.tif`), OGC GeoPackage (`.gpkg`).
- **Target Coordinate Reference System:** Normalized to `EPSG:32644` (UTM Zone 44N) matching the 30m DEM grid.

#### B. Data Source Strategy & Ranking

| Rank | Source Classification | Provider / Organization | Dataset Name & Access Point | Format & Coverage | Advantages | Limitations | Verification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Reliable Open Geospatial** | **European Space Agency (ESA) / WorldCover Consortium** | *ESA WorldCover 10m 2021 v200*<br>URL: `https://esa-worldcover.org/` | Cloud-Optimized GeoTIFF (COG) at 10m resolution; Global / Tile `N30E078` | 10m high resolution; globally validated; open CC-BY 4.0; clean discrete classes (Tree cover, Built-up, Cropland, Bare, Water, Snow). | Does not contain Indian legal forest tenure boundaries (Reserve Forest vs. Revenue Land). | **VERIFIED** |
| **2** | **Reliable Open Geospatial** | **ESRI / Impact Observatory / Microsoft Planetary Computer** | *ESRI 10m Annual Land Use / Land Cover (2020–2023)*<br>URL: `https://livingatlas.arcgis.com/landcover/` | 10m GeoTIFF (Sentinel-2 deep learning 9-class model) | High annual consistency; 10m resolution; instant download via Microsoft Planetary Computer STAC API. | Similar to ESA, legal administrative forest boundaries require separate overlay. | **VERIFIED** |
| **3** | **Official Government (Forestry)** | **Forest Survey of India (FSI) / MoEFCC** | *FSI Forest Cover Mapping & Protected Area Network Atlas*<br>URL: `https://fsi.nic.in/` & *State of Forest Report (ISFR)* | 1:50,000 scale vector / raster maps; Rudraprayag District | Authoritative legal classifications (Very Dense Forest, Moderate Dense Forest, Open Forest, Scrub) and Wildlife Sanctuary boundaries. | Full GIS vector layers are restricted to government and academic request protocols. | **VERIFIED** |
| **4** | **Official Government (National Space)** | **ISRO National Remote Sensing Centre (NRSC) / Bhuvan** | *Bhuvan Thematic LULC 1:50,000 / 1:250,000 (5-Year Cycle)*<br>URL: `https://bhuvan-app1.nrsc.gov.in/thematic/thematic_p1.php` | Vector / Raster WMS; Rudraprayag coverage | National standard LULC classification adhering to National Natural Resources Management System (NNRMS) norms. | Vector shapefile download is restricted; direct export requires ISRO institutional login. | **VERIFIED** |

---

## 4. End-to-End Integration Architecture

The following ASCII diagram illustrates the precise step-by-step data transformation pipeline from Raw External Datasets to Frontend Display, maintaining strict adherence to the project's deterministic and explainable principles.

```
════════════════════════════════════════════════════════════════════════════════════════════════════════════════
                             SIH26191 DATA GAP CLOSURE ARCHITECTURE
════════════════════════════════════════════════════════════════════════════════════════════════════════════════

  [RAW EXTERNAL ACQUISITIONS]
    ├── 1. Disaster History (ISRO NRSC Landslide Atlas / NASA COOLR / USDMA Incidents)
    ├── 2. Critical Infrastructure (OSM Overpass Extract / UDISE+ Schools / NHM Health Facilities)
    ├── 3. Road Network (OSM Highway PBF Extract / PMGSY Rural Roads GeoJSON)
    └── 4. Land Use / Land Cover (ESA WorldCover 10m COG GeoTIFF / FSI Sanctuary Boundary)
         │
         ▼
  [STAGE 1: INGESTION & DATA CLEANING]
    ├── Ingest raw files into data/raw/{disaster_history, infrastructure, roads, lulc}/
    ├── Filter geographically to Rudraprayag BBox (78.78°E, 30.19°N to 79.37°E, 30.81°N)
    ├── Strip invalid geometries, duplicate records, and resolve missing attribute values
    └── Log acquisition metadata (source URL, vintage, provider, license) in provenance catalog
         │
         ▼
  [STAGE 2: SCHEMA & QUALITY VALIDATION]
    ├── Validate disaster incidents against data/processed/disaster_history/schema.json
    ├── Validate infrastructure attributes against new schemas (valid amenity enums, positive capacity)
    ├── Validate road network topology (node connectivity, non-zero segment lengths, speed impedance)
    └── Validate LULC raster bounds, resolution (10m resampled to 30m), and valid integer class codes
         │
         ▼
  [STAGE 3: COORDINATE REFERENCE SYSTEM NORMALIZATION]
    ├── Transform all vector vector layers: EPSG:4326 (WGS 84) ──► EPSG:32644 (UTM Zone 44N)
    ├── Reproject & snap LULC raster grid to exact pixel alignment of copernicus_glo30_rudraprayag.tif
    └── Store intermediate clean layers in data/processed/{disaster_history, infrastructure, roads, lulc}/
         │
         ▼
  [STAGE 4: SPATIAL ANALYSIS & GIS PROCESSING]
    ├── [Disaster Module]: Build 1km / 2km incident buffer zones & count historical events per village
    ├── [Infrastructure Module]: Run k-NN spatial query & compute Euclidean/network distance to nearest PHC/School
    ├── [Accessibility Module]: Construct NetworkX graph from roads; compute shortest-path travel distance (m) & time (min)
    └── [LULC Screening Module]: Generate binary legal/ecological exclusion mask (Exclude Dense Forest, Water, Sanctuary)
         │
         ▼
  [STAGE 5: DERIVED METRICS & CONTEXTUAL ATTRIBUTION]
    ├── Habitations: Append `historical_disaster_count`, `has_recorded_landslide_flag`, `dist_to_all_weather_road_m`,
    │                `nearest_phc_distance_m`, `nearest_school_distance_m`, `road_isolation_flag`
    └── Candidate Areas: Intersect candidate polygons with LULC mask; subtract Reserve Forest / Sanctuary land;
                         compute `net_developable_area_ha` and `road_access_distance_m`
         │
         ▼
  [STAGE 6: DECISION ENGINE ENRICHMENT & CAPACITY RECALCULATION]
    ├── processing/priority/build_village_priority.py (Step 10B/C):
    │     ├── Maintain deterministic Tier 1–4 rules based on hazard proximity
    │     ├── Populate new Non-Modulating Context Flags: `vf_isolated_road`, `vf_lacks_health_access`, `vf_chronic_disaster`
    │     └── If hard disaster rule enabled by SDMA: elevate to Tier 1 ONLY if centroid intersects confirmed disaster footprint
    └── processing/capacity/build_candidate_context.py (Step 10D):
          ├── Update PMAY-G 25 m²/HH capacity scenarios using `net_developable_area_ha` (excluding forest/slopes >20°)
          └── Flag candidate areas with `road_connectivity_status` (CONNECTED, ACCESS_TRACK_REQUIRED, ISOLATED)
         │
         ▼
  [STAGE 7: OUTPUT ARTIFACT GENERATION & STORAGE]
    ├── data/processed/decision/village_priority_profiles.gpkg (Enriched 653 habitations)
    ├── data/processed/decision/candidate_area_context.gpkg (Enriched candidate areas with LULC/Road context)
    ├── data/processed/decision/decision_summary.json (Updated district statistics)
    └── data/outputs/candidate_hazard_based_red_zones.geojson & .gpkg
         │
         ▼
  [STAGE 8: BACKEND FASTAPI PRESENTATION LAYER]
    ├── DataLoader (backend/services/data_loader.py): Hot-reloads enriched GeoPackages
    ├── /api/villages: Exposes disaster history, infrastructure distance, and road access attributes
    ├── /api/candidate-areas: Exposes net developable area, LULC breakdown, and road access distance
    ├── /api/authority/action-queue: Allows filtering by high isolation and chronic disaster history
    └── /api/pipeline/recompute: Automatically triggers re-execution across Stages 4–7 on data update
         │
         ▼
  [STAGE 9: FRONTEND DASHBOARD & MAP DISPLAY]
    ├── GisMap.tsx: Add interactive layer toggles for Road Network, Critical Infrastructure, and Historical Disasters
    ├── VillageDetailPage.tsx: Expand "Spatial Context" & "Vulnerability" cards with Road & Infrastructure metrics
    ├── CandidateAreasPage.tsx: Display Net Usable Area (after LULC exclusion) and Road Proximity badges
    └── AuthorityActionPage.tsx: Add filter pills for "Lacks Road Access" and "Historical Disaster Zone"
════════════════════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 5. Exact Required Fields and GIS Layer Specifications

### 5.1 Layer 1: Historical Disaster Incidents (`disaster_incidents`)
- **Storage Target:** `data/processed/disaster_history/disaster_incidents.gpkg` (Layer: `incidents`)
- **Geometry Type:** `Point` or `Polygon` in `EPSG:32644` (Metric UTM 44N) and `EPSG:4326` (GeoJSON API)
- **Attribute Schema Table:**

| Field Name | Data Type | Constraint / Enum | Description |
| :--- | :--- | :--- | :--- |
| `incident_id` | String (PK) | `DIS-RDP-YYYY-NNN` | Unique deterministic identifier |
| `incident_date`| Date / String | ISO 8601 `YYYY-MM-DD` | Date of disaster occurrence |
| `hazard_type` | String | `LANDSLIDE`, `CLOUDBURST`, `FLOOD`, `SUBSIDENCE`, `AVALANCHE` | Specific disaster classification |
| `severity` | String | `MINOR`, `MODERATE`, `MAJOR`, `CATASTROPHIC` | Standardized damage severity level |
| `deaths_reported`| Integer | $\ge 0$, null if unconfirmed | Officially recorded fatalities |
| `households_affected`| Integer | $\ge 0$, null if unconfirmed | Estimated displaced/damaged households |
| `villages_affected` | String (JSON) | Array of Census Village IDs | Geolinked habitation codes |
| `source_name` | String | `USDMA`, `NRSC_ATLAS`, `NASA_COOLR`, `PEER_REVIEW` | Official data provider |
| `source_citation`| String | Text reference | Formal document or publication citation |
| `verified_status`| String | `VERIFIED_GOVT`, `VERIFIED_SCIENTIFIC`, `UNVERIFIED` | Evidentiary confidence level |

---

### 5.2 Layer 2: Critical Infrastructure Facilities (`critical_infrastructure`)
- **Storage Target:** `data/processed/infrastructure/critical_infrastructure.gpkg` (Layer: `facilities`)
- **Geometry Type:** `Point` in `EPSG:32644` and `EPSG:4326`
- **Attribute Schema Table:**

| Field Name | Data Type | Constraint / Enum | Description |
| :--- | :--- | :--- | :--- |
| `facility_id` | String (PK) | `INF-RDP-TYPE-NNN` | Unique infrastructure identifier |
| `facility_name`| String | Non-empty | Official name of institution / facility |
| `facility_type`| String | `PHC`, `CHC`, `DISTRICT_HOSPITAL`, `SUB_CENTRE`, `SCHOOL_PRI`, `SCHOOL_SEC`, `POLICE`, `FIRE_STN`, `PANCHAYAT` | Type of lifeline facility |
| `category` | String | `HEALTH`, `EDUCATION`, `EMERGENCY`, `ADMINISTRATIVE` | High-level facility grouping |
| `sub_district` | String | `Rudraprayag`, `Ukhimath`, `Jakholi` | Tehsil / Block name |
| `census_village_id` | Integer | Valid 6-digit Census code, nullable | Colocated habitation ID |
| `data_source` | String | `UDISE_PLUS`, `NHM_HFR`, `OSM_OVERPASS`, `DISTRICT_ADMIN` | Provenance source |
| `operational_status`| String | `OPERATIONAL`, `SEASONAL`, `DAMAGED_INACTIVE` | Facility readiness state |

---

### 5.3 Layer 3: Routable Road Network (`road_network`)
- **Storage Target:** `data/processed/roads/rudraprayag_road_network.gpkg` (Layer: `roads`)
- **Geometry Type:** `LineString` / `MultiLineString` in `EPSG:32644` (UTM Zone 44N)
- **Attribute Schema Table:**

| Field Name | Data Type | Constraint / Enum | Description |
| :--- | :--- | :--- | :--- |
| `road_id` | String (PK) | `RD-RDP-NNNN` or OSM ID | Unique road segment identifier |
| `road_name` | String | e.g., "NH-107", "Kedarnath Highway", "Unnamed Rural Road" | Formal road name or classification |
| `highway_class`| String | `national_highway`, `state_highway`, `major_district`, `rural_pmgsy`, `residential`, `track`, `path` | Highway functional hierarchy |
| `surface_type` | String | `paved_asphalt`, `paved_concrete`, `unpaved_gravel`, `dirt_track`, `unknown` | Physical surface material |
| `all_weather` | Boolean | `true`, `false` | Passable during monsoon seasons |
| `speed_kmh` | Float | $4.0 \le \text{speed} \le 50.0$ | Speed impedance for network routing |
| `length_m` | Float | $> 0.0$ | Exact metric segment length in metres |
| `data_source` | String | `OSM_GEOFABRIK`, `PMGSY_GEOSADAK`, `PWD_UTTARAKHAND` | Provenance source |

---

### 5.4 Layer 4: Land Use / Land Cover & Ecological Exclusion Mask (`lulc_exclusions`)
- **Storage Target:** `data/processed/lulc/rudraprayag_lulc_30m.tif` & `data/processed/lulc/ecological_exclusions.gpkg`
- **Raster Grid / Geometry:** 30m grid aligned exactly to `copernicus_glo30_rudraprayag.tif` (EPSG:32644)
- **Attribute & Class Schema Table:**

| Class Code | Class Name | Exclusion Role in Candidate Screening | Rationale & Legal Authority |
| :--- | :--- | :--- | :--- |
| `10` | `Tree Cover / Dense Forest` | **EXCLUDE (Weight: 0.0)** | Environmental preservation; central Forest Conservation Act (FCA) clearance restrictions |
| `20` | `Shrubland / Open Scrub` | **PERMISSIBLE (Weight: 1.0)** | Degraded or open slope terrain with low ecological conflict |
| `30` | `Grassland / Alpine Meadow` | **CONDITIONAL (Weight: 0.5)** | Higher altitude grazing slopes; permissible if below elevation cap |
| `40` | `Cropland / Agriculture` | **CONDITIONAL (Weight: 0.2)** | Avoid converting prime agricultural terraces unless critical |
| `50` | `Built-up / Settlement` | **EXCLUDE (Weight: 0.0)** | Already developed land; not available for new relocation parcels |
| `60` | `Bare / Sparse Vegetation` | **PERMISSIBLE (Weight: 1.0)** | Non-forest rocky/soil terrain topographically suitable if slope $\le 20^\circ$ |
| `70` | `Permanent Snow / Glacier` | **EXCLUDE (Weight: 0.0)** | High alpine glacial terrain; uninhabitable |
| `80` | `Permanent Water Bodies` | **EXCLUDE (Weight: 0.0)** | Riverbeds (Mandakini/Alaknanda), confluences, and active floodways |
| `90` | `Wildlife Sanctuary (KWLS)` | **EXCLUDE (Weight: 0.0)** | Kedarnath Wildlife Sanctuary (Protected Area Network — strictly prohibited) |

---

## 6. Code Integration Map

The table below maps each missing dataset to existing files, configuration blocks, validation hooks, and new processing scripts required to activate the feature without disrupting the core verified pipeline.

| Dataset Area | Existing Files / Modules to Receive Data | Existing Configuration to Update | Existing Hooks to Activate | New Processing Modules to Create | Validation Scripts to Run |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Disaster History** | `processing/disaster_history/`<br>`processing/priority/build_village_priority.py`<br>`backend/api/routes/villages.py`<br>`frontend/src/pages/VillageDetailPage.tsx` | `configs/priority_thresholds.yaml` (`disaster_history` section L108–122: change status from `NOT_ACQUIRED` to `AVAILABLE`) | `data/processed/disaster_history/schema.json`<br>`validate_disaster_data.py`<br>Village profile schema hook `has_historical_incident` | `processing/disaster_history/ingest_historical_incidents.py`<br>`processing/disaster_history/spatial_incident_overlay.py` | `processing/disaster_history/validate_disaster_data.py`<br>`scripts/validate_disaster_history_overlay.py` |
| **2. Critical Infrastructure** | `processing/exposure/build_habitation_baseline.py`<br>`processing/priority/build_village_priority.py`<br>`backend/api/routes/villages.py`<br>`frontend/src/pages/VillageDetailPage.tsx` | `configs/priority_thresholds.yaml` (`infrastructure` section L123–130: change status to `AVAILABLE` and configure distance benchmarks) | `priority_thresholds.yaml` infrastructure placeholder<br>`docs/PROJECT_SPEC.md` Module 4 hook | `processing/infrastructure/ingest_infrastructure_osm.py`<br>`processing/infrastructure/compute_facility_accessibility.py` | `scripts/validate_infrastructure_data.py`<br>`scripts/validate_infrastructure_proximity.py` |
| **3. Road Network** | `processing/sites/identify_candidate_areas.py`<br>`processing/capacity/build_candidate_context.py`<br>`backend/api/routes/candidate_areas.py`<br>`frontend/src/pages/CandidateAreasPage.tsx` | `configs/project.yaml` (add `roads` section with path `data/processed/roads/rudraprayag_road_network.gpkg` and speed parameters) | `candidate_area_context.gpkg` road connectivity placeholder<br>`configs/project.yaml` CRS definition | `processing/roads/ingest_osm_road_network.py`<br>`processing/roads/derive_road_network_accessibility.py` | `scripts/validate_road_topology.py`<br>`scripts/validate_network_distances.py` |
| **4. Land Use / Land Cover** | `processing/sites/identify_candidate_areas.py`<br>`processing/capacity/build_candidate_context.py`<br>`backend/api/routes/candidate_areas.py`<br>`frontend/src/pages/CandidateAreasPage.tsx` | `configs/project.yaml` (`candidate_areas.configurable_screening` L386–417: enable `exclude_dense_forest: true`, `exclude_sanctuary: true`) | `configs/project.yaml` screening parameters<br>`combined_exclusion_mask.tif` generator in Step 9 | `processing/lulc/ingest_esa_worldcover.py`<br>`processing/lulc/derive_ecological_exclusion_mask.py` | `scripts/validate_lulc_alignment.py`<br>`scripts/validate_candidate_area_exclusions.py` |

---

## 7. Data Validation and Quality Assurance Plan

Every dataset ingested into SIH26191 must satisfy four rigorous validation gates before incorporation into production GeoPackages or API endpoints:

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  GATE 1: FILE   │ ──► │  GATE 2: CRS &   │ ──► │  GATE 3: SCHEMA  │ ──► │ GATE 4: SPATIAL  │
│ INTEGRITY CHECK │     │ BOUNDS TRANSFORM │     │   VALIDATION     │     │ LOGIC INTEGRITY  │
└─────────────────┘     └──────────────────┘     └──────────────────┘     └──────────────────┘
```

### 7.1 Gate 1: File Integrity & Format Verification
- Verify file exists, is non-empty ($> 0\text{ bytes}$), and parses without format corruption using `rasterio` (for GeoTIFFs) or `geopandas` (for GeoJSON / GeoPackage).
- Ensure SHA-256 hash and provenance metadata are logged in `data/raw/provenance_catalog.json`.

### 7.2 Gate 2: CRS Normalization & Geographic Bounding Box Check
- Inspect source CRS: if geographic (`EPSG:4326`), reproject to project metric standard (`EPSG:32644` / UTM Zone 44N) using high-precision GDAL transformations.
- Verify that 100% of feature geometries or raster extents fall strictly within the Rudraprayag District Bounding Box:
  $$\text{Bounding Box: } [78.78^\circ\text{E}, 30.19^\circ\text{N}] \text{ to } [79.37^\circ\text{E}, 30.81^\circ\text{N}]$$
- Any vector geometry lying outside this bounding box is discarded or flagged as an acquisition anomaly.

### 7.3 Gate 3: Schema & Attribute Conformance
- Validate records against target JSON Schema definitions using Python `jsonschema` and `pydantic`.
- Mandatory checks:
  - Incident dates must be valid ISO 8601 strings and $\le \text{current date}$.
  - Hazard types, severities, and infrastructure categories must belong strictly to predefined Enums.
  - Distances, areas, household counts, and fatality numbers must be non-negative ($\ge 0$).
  - Census village IDs must match existing 6-digit codes in `habitation_baseline.geojson`.

### 7.4 Gate 4: Spatial Logic & Cross-Layer Consistency
- **Disaster Overlay:** Verify that spatial point-in-polygon and distance calculations to all 653 habitations produce finite floats ($0.0 \le d \le 50,000\text{ m}$) with zero `NaN` or `Inf` values.
- **Road Network Graph:** Verify graph connectivity using NetworkX (`nx.is_connected` or evaluation of largest strongly connected component); identify and flag isolated disconnected spurs; verify non-zero positive segment lengths.
- **LULC Raster Resampling:** Verify that reprojected LULC rasters match the exact pixel grid dimensions ($X \times Y$), spatial resolution ($30.0\text{ m} \times 30.0\text{ m}$), transform matrix, and origin coordinates of `copernicus_glo30_rudraprayag.tif`.

---

## 8. Gap Closure Priority and Multi-Criteria Evaluation

To guide the team's sprint planning before the SIH evaluation, the four data gaps are evaluated across seven weighted multi-criteria dimensions.

### 8.1 Scoring Methodology (Scores 1–10, Higher is More Favourable / Feasible)
1. **Impact on SIH Problem Statement (Weight 20%):** How directly the dataset fulfills core SIH requirements (PS-4 disaster history, PS-5/6 relocation sites).
2. **Improvement to Decision Accuracy (Weight 20%):** Extent to which empirical data replaces uncalibrated proxies.
3. **Ease of Acquisition (Weight 15%):** Availability via open repositories vs. bureaucratic government permissions.
4. **Ease of Integration (Weight 15%):** Alignment with existing schema hooks and processing scripts.
5. **Data Reliability & Provenance (Weight 10%):** Scientific validity and institutional credibility.
6. **Time Required to Complete (Weight 10%):** Estimated engineering hours (data cleaning + scripting).
7. **Demo Value for SIH Judges (Weight 10%):** Visual impact on GIS map, dashboard cards, and authority workflows.

### 8.2 Evaluation Matrix

| Missing Dataset | Impact on PS (20%) | Accuracy Boost (20%) | Ease of Acquisition (15%) | Ease of Integration (15%) | Data Reliability (10%) | Time Feasibility (10%) | Judge Demo Value (10%) | Weighted Score / 10 | Priority Rank |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Land Use / Land Cover (LULC)** | 9.0 | 9.5 | 9.5 (ESA Open) | 9.0 (Mask Ready) | 9.0 | 9.0 (~4 hrs) | 9.0 | **9.15 / 10** | **PRIORITY 1** |
| **Road Network & Accessibility** | 8.5 | 9.0 | 9.0 (OSM Open) | 8.0 (Graph Script) | 8.5 | 8.0 (~6 hrs) | 9.5 | **8.65 / 10** | **PRIORITY 2** |
| **Disaster History Records** | 10.0 | 9.0 | 6.5 (Atlas Extract) | 9.5 (Schema Ready) | 9.0 | 7.5 (~8 hrs) | 9.5 | **8.60 / 10** | **PRIORITY 3** |
| **Critical Infrastructure** | 7.0 | 7.5 | 8.5 (OSM/UDISE) | 8.5 (Point Join) | 8.0 | 8.5 (~5 hrs) | 8.0 | **7.90 / 10** | **PRIORITY 4** |

---

## 9. Minimum Viable Dataset (MVD) Acquisition Plan

Given tight hackathon timelines, the team must execute a razor-focused Minimum Viable Dataset plan that achieves maximum scientific rigor without stalling on government data requests.

```
════════════════════════════════════════════════════════════════════════════════════════════════════
                             MINIMUM VIABLE DATASET (MVD) SPRINT ROADMAP
════════════════════════════════════════════════════════════════════════════════════════════════════

  PHASE 1: IMMEDIATE OPEN DATASET ACQUISITION (Within 24 Hours — Zero External Dependencies)
  ──────────────────────────────────────────────────────────────────────────────────────────
  1. ESA WorldCover 10m (2021 v200) GeoTIFF:
     - Download Tile N30E078 directly from ESA WorldCover AWS / Zenodo open bucket.
     - Clip to Rudraprayag BBox; reproject to EPSG:32644; resample to 30m grid.
     - Activate `exclude_dense_forest: true` in `configs/project.yaml`.
  
  2. OpenStreetMap Road Network Extract:
     - Download `uttarakhand-latest.osm.pbf` from Geofabrik.
     - Extract highways (`motorway` to `residential` & `track`) within Rudraprayag BBox.
     - Convert to `rudraprayag_road_network.gpkg` in EPSG:32644.
  
  3. OpenStreetMap & UDISE+ Infrastructure Directory:
     - Query Overpass API for schools, hospitals, clinics, and police stations in Rudraprayag.
     - Save as `critical_infrastructure.gpkg`.

  ──────────────────────────────────────────────────────────────────────────────────────────
  PHASE 2: HIGH-CONFIDENCE RESEARCH DISASTER INVENTORY (Within 48 Hours)
  ──────────────────────────────────────────────────────────────────────────────────────────
  4. ISRO Landslide Atlas 2023 / Peer-Reviewed Mandakini Inventory:
     - Digitize / extract published landslide occurrence coordinates across Rudraprayag.
     - Ingest into `data/processed/disaster_history/` adhering to `schema.json`.
     - Run `validate_disaster_data.py` to confirm 100% schema conformance.

  ──────────────────────────────────────────────────────────────────────────────────────────
  PHASE 3: FORMAL GOVERNMENT REQUEST TRACK (Parallel Track — Do NOT Block on This)
  ──────────────────────────────────────────────────────────────────────────────────────────
  5. USDMA Dehradun Official Request:
     - Submit student academic project letter for official district incident registers.
     - If received before finals: hot-swap into `data/raw/disaster_history/` and trigger recompute.
     - If not received: present MVD with full provenance transparency.

  ──────────────────────────────────────────────────────────────────────────────────────────
  WHAT TO STRICTLY AVOID INTEGRATING (Low Reliability Trap)
  ──────────────────────────────────────────────────────────────────────────────────────────
  - AVOID unverified social media / news scrapes of disaster locations (unverified coordinates).
  - AVOID assuming synthetic datasets are real in production decision flows.
  - AVOID complex AI/ML landslide probability models that cannot be explained to judges.
════════════════════════════════════════════════════════════════════════════════════════════════════
```

---

## 10. Step-by-Step Action Plan for the Team

### Sprint 1: LULC & Forest Screening Integration (Est. Time: 4 Hours)
1. **Acquire:** Download ESA WorldCover 10m GeoTIFF tile `ESA_WorldCover_10m_2021_v200_N30E078_Map.tif` via AWS S3 open bucket (`s3://esa-worldcover/v200/2021/map/`).
2. **Process:** Create `processing/lulc/ingest_esa_worldcover.py` to warp and resample to 30m grid matching `copernicus_glo30_rudraprayag.tif`.
3. **Screen:** Update `processing/sites/identify_candidate_areas.py` to mask out Class 10 (Tree Cover) and Class 80 (Water) from Candidate Areas.
4. **Enrich:** Update `processing/capacity/build_candidate_context.py` to recalculate dwelling capacity based on `net_developable_area_ha`.
5. **Recompute:** Run `POST /api/pipeline/recompute` and verify that candidate relocation cards on `CandidateAreasPage.tsx` display updated net usable areas.

### Sprint 2: Routable Road Network & Accessibility (Est. Time: 6 Hours)
1. **Acquire:** Extract Rudraprayag road lines from `geofabrik/uttarakhand-latest.osm.pbf` using `osmnx` or `pyrosm`.
2. **Process:** Save to `data/processed/roads/rudraprayag_road_network.gpkg` in `EPSG:32644`.
3. **Analyze:** Create `processing/roads/derive_road_network_accessibility.py` to compute nearest-road Euclidean distance and shortest-path road network distance from each village centroid to the nearest National/State Highway.
4. **Integrate:** Append `dist_to_all_weather_road_m` and `road_isolation_flag` to `village_priority_profiles.gpkg`.
5. **Display:** Add Road Network toggle layer to `GisMap.tsx` and render road distance metric on `VillageDetailPage.tsx`.

### Sprint 3: Disaster History Records Ingestion (Est. Time: 8 Hours)
1. **Acquire:** Extract spatial disaster coordinates from ISRO Landslide Atlas 2023 (Rudraprayag district chapter) and NASA COOLR repository.
2. **Validate:** Ingest into `data/raw/disaster_history/rudraprayag_disaster_incidents.geojson` and execute `processing/disaster_history/validate_disaster_data.py`.
3. **Overlay:** Create `processing/disaster_history/spatial_incident_overlay.py` to calculate incident counts within 1 km and 2 km of each village centroid.
4. **Enrich:** Append `historical_disaster_count` and `chronic_disaster_flag` to `village_priority_profiles.gpkg`.
5. **Configure:** Update `configs/priority_thresholds.yaml` to change `disaster_history.status` from `NOT_ACQUIRED` to `AVAILABLE`.
6. **Display:** Enable "Historical Disaster Zone" badge in `VillageDetailPage.tsx` and filter pill in `AuthorityActionPage.tsx`.

### Sprint 4: Critical Infrastructure Attribution (Est. Time: 5 Hours)
1. **Acquire:** Extract health and education POIs from OSM Overpass API and UDISE+ Rudraprayag directory.
2. **Validate:** Clean and save as `data/processed/infrastructure/critical_infrastructure.gpkg`.
3. **Analyze:** Compute nearest distance from each village to the nearest PHC/Hospital and Secondary School.
4. **Enrich:** Append `nearest_phc_distance_m`, `nearest_school_distance_m`, and `vf_lacks_health_access` context flag to `village_priority_profiles.gpkg`.
5. **Display:** Render infrastructure proximity meters on `VillageDetailPage.tsx` and add infrastructure layer to `GisMap.tsx`.

---

## 11. Risks and Remaining Methodological Limitations

Even after complete execution of this Data Gap Closure Strategy, the following scientific, engineering, and administrative limitations will remain and must be explicitly stated to SIH evaluators:

### 11.1 Scientific & Topographic Limitations
1. **30m Topographic Grid Scale:** Micro-scale slope failures ($< 30\text{ m}$), localized road cuts, and individual retaining wall instabilities cannot be modeled from 30m Copernicus DEM. On-site engineering geological mapping is mandatory.
2. **Temporal Dynamics of Rainfall:** Static terrain screening captures morphological predisposition, not real-time meteorological cloudburst triggers. Real-time dynamic early warning requires live Doppler radar or telemetry raingauge networks.

### 11.2 Legal & Administrative Limitations
1. **Cadastral Ownership & Land Tenure:** Open LULC data identifies physical tree cover but does not resolve revenue cadastral parcels (private farmland vs. Gram Panchayat common land vs. State Revenue land). Resettlement planning requires cadastral Khasra/Khatauni verification by the District Revenue Department.
2. **Forest Clearance Procedures:** Any candidate site involving forest land necessitates formal statutory clearances under the Forest Conservation Act (FCA), 1980 and Van Adhikar Adhiniyam (FRA), 2006.

### 11.3 Engineering & Relocation Limitations
1. **Geotechnical Bearing Capacity:** PMAY-G dwelling unit scenarios provide preliminary spatial planning capacity based on area norms ($25\text{ m}^2/\text{HH}$). They do NOT substitute for geotechnical borehole drilling, Standard Penetration Tests (SPT), slope stability safety factor ($F_s$) calculations, or structural foundation design.
2. **Human-in-the-Loop Resettlement Governance:** Relocation is a socio-culturally sensitive administrative process requiring Gram Sabha consent, compensation packages, and livelihood rehabilitation. The software provides spatial screening only.

---

## 12. Strategic Summary Table for SIH Pitch & Demonstration

| Missing Area | Open Acquisition Target | Turnaround Time | Impact on System | Judge Pitch Statement |
| :--- | :--- | :--- | :--- | :--- |
| **Land Use / Land Cover** | ESA WorldCover 10m COG | 4 Hours | Eliminates illegal candidate sites in dense forests and water bodies | *"We screened out ecologically sensitive dense forest and water bodies using 10m ESA WorldCover, ensuring candidate relocation areas are legally and topographically developable."* |
| **Road Accessibility** | OSM Highway Network GeoPackage | 6 Hours | Replaces straight-line distance with actual mountain road travel distance | *"Rather than naive straight-line distance, our decision engine evaluates actual mountain road network travel distance, identifying isolated communities cut off from emergency access."* |
| **Disaster History** | ISRO Landslide Atlas 2023 / NASA COOLR | 8 Hours | Validates terrain proxies against 25 years of empirical landslide records | *"Our system integrates 25 years of recorded landslide events from the ISRO Landslide Atlas of India, elevating habitations with chronic historical disaster impacts to top priority."* |
| **Critical Infrastructure** | OSM Overpass + UDISE+ Schools & NHM PHCs | 5 Hours | Attributes lifeline healthcare and school accessibility to every village | *"We contextualize physical hazard risk with lifeline infrastructure access, flagging habitations that lack primary healthcare or schools within emergency reach."* |

---
**End of Data Gap Closure Strategy Document**  
*SIH26191 — Decision Support System for Disaster Risk & Relocation Planning — Rudraprayag District*
