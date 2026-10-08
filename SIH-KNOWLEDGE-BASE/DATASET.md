# Datasets: SIH26191

This document provides a comprehensive inventory and data sheet for all datasets ingested and processed within the SIH26191 platform.

---

## 1. Copernicus GLO-30 Digital Elevation Model (DEM)

- **Dataset Name:** Copernicus Global Digital Elevation Model (GLO-30)
- **Source / Provider:** European Space Agency (ESA) / Copernicus Open Access Data Hub
- **Purpose:** Primary digital elevation surface used to calculate terrain slopes, aspect bearings, D8 hydrological flow accumulation, and Topographic Wetness Index (TWI).
- **Size on Disk:** 19.05 MB (single GeoTIFF tile)
- **Number of Samples / Records / Pixels:** Raster grid covering Rudraprayag District ($>3.5\text{M}$ active pixels; spatial bounding box: $78.78^\circ\text{E}$ to $79.37^\circ\text{E}$, $30.19^\circ\text{N}$ to $30.81^\circ\text{N}$).
- **Features / Channels:** Single-band 32-bit floating-point elevation in metres above sea level (elevation range across district: ~400m in river valleys to ~6,900m at Kedarnath/Chaukhamba peaks).
- **Labels / Classes:** Continuous physical elevation surface.
- **Data Format:** GeoTIFF (`.tif`), Cloud-Optimized GeoTIFF.
- **Train / Validation / Test Split:** Not applicable (Deterministic physical terrain modeling; no ML split).
- **Preprocessing:** Reprojected from geographic WGS 84 (`EPSG:4326`) to projected metric coordinate system UTM Zone 44N (`EPSG:32644`) with bilinear interpolation to enable metric gradient calculations in metres.
- **Cleaning:** NoData void checking and artifact clipping at administrative district boundaries.
- **Feature Engineering:** Derivation of metric slope in degrees, compass aspect in degrees, D8 flow direction, D8 flow accumulation, Topographic Wetness Index ($\text{TWI} = \ln(a / \tan\beta)$), and linear normalized continuous terrain susceptibility proxies ($T \in [0.0, 1.0]$).
- **Data Augmentation:** Not applicable (Physical elevation data).
- **Data Limitations:** 30-meter grid resolution cannot resolve micro-topographic features such as roadside retaining wall fractures, localized slope cuts $<30\text{m}$, or building foundation cut-slopes.
- **Licensing / Source Information:** Open access under the Copernicus open data policy.
- **Why the Dataset Was Selected:** High vertical accuracy ($\sim 2\text{ m}$ relative error), modern 2021 release vintage, free open global availability, and superior hydrological consistency over older SRTM 30m and ASTER GDEM.

---

## 2. Primary Census Abstract (PCA) 2011 — Rudraprayag District

- **Dataset Name:** Primary Census Abstract (PCA) 2011 — Rudraprayag District (District Code: 0503)
- **Source / Provider:** Office of the Registrar General & Census Commissioner of India, Ministry of Home Affairs, Government of India.
- **Purpose:** Provides official socio-demographic baseline statistics for all rural revenue habitations across Rudraprayag District.
- **Size on Disk:** 318 KB (Excel spreadsheet `PCA_CDB-0503-F-Census.xlsx`).
- **Number of Samples / Records:** 653 rural revenue village records (District totals: 232,360 persons, 50,882 households).
- **Features:** 
  - `village_id` (6-digit official Census Village Code)
  - `village_name` (Standardized revenue village name)
  - `TOT_P` (Total population)
  - `No_HH` (Total households)
  - `P_06` (Child population aged 0–6)
  - `P_ILL` (Illiterate population)
  - `TOT_SC` (Total Scheduled Caste population)
  - `TOT_ST` (Total Scheduled Tribe population)
  - `MAIN_WORK_P` (Main working population)
  - `MARG_WORK_P` (Marginal working population)
  - `NON_WORK_P` (Non-working population)
- **Labels / Classes:** Continuous demographic counts and proportions.
- **Data Format:** Tabular Excel (`.xlsx`), joined to GeoPackage attributes.
- **Train / Validation / Test Split:** Not applicable (Deterministic administrative population census).
- **Preprocessing:** Code-based joining using the unique 6-digit Census Village ID to spatial geometries; computation of demographic rates (`child_proportion`, `illiteracy_rate`, `sc_proportion`, `st_proportion`, `non_worker_rate`).
- **Cleaning:** Strict validation verifying that $\text{TOT\_P} == \text{P\_MALES} + \text{P\_FEMALES}$ and that all 653 records successfully bind to spatial geometries with zero missing values.
- **Feature Engineering:** District-wide upper-tertile ($P_{75}$) benchmarking:
  - `vf_high_child_pop`: Child proportion $> 15.1\%$
  - `vf_high_sc`: SC proportion $> 24.6\%$
  - `vf_high_dependency`: Non-worker rate $> 57.9\%$
  - `vf_high_illiteracy`: Illiteracy rate $> 34.0\%$
  - Composite flag count ($0$ to $4$).
- **Data Augmentation:** Not applicable.
- **Data Limitations:** 2011 Census vintage (~15 years old); does not account for post-2013 Kedarnath disaster population out-migration, demographic shifts, or recent infrastructure expansion.
- **Licensing / Source Information:** Government of India Open Data (Open Government Data License - India).
- **Why the Dataset Was Selected:** It is the only legally recognized, official village-level population census in India covering every revenue settlement in the district.

---

## 3. Socio-Economic High-Resolution Rural-Urban Geographic Platform (SHRUG) v2.2

- **Dataset Name:** SHRUG v2.2 Village Centroids & Spatial Crosswalk
- **Source / Provider:** Development Data Lab (Asher et al., 2021)
- **Purpose:** Serves as the precise geometric spatial bridge linking Census 2011 village ID codes to geographic point coordinates.
- **Size on Disk:** 408 KB (`rudraprayag_census_villages_shrug.geojson`) + crosswalk tables (>300 MB).
- **Number of Samples / Records:** 653 point centroids corresponding 1:1 with Rudraprayag Census 2011 villages.
- **Features:** 
  - `shrid` (SHRUG unique settlement identifier)
  - `village_id` (Census 2011 Village ID)
  - `village_name` (Standardized transliterated name)
  - `subdistrict_id` / `shrug_subdist_id` (Tehsil classification: Ukhimath, Augustmuni, Jakholi)
  - `geometry` (Point: longitude, latitude in EPSG:4326).
- **Labels / Classes:** Point vector geometries.
- **Data Format:** GeoJSON (`.geojson`) and OGC GeoPackage (`.gpkg`).
- **Train / Validation / Test Split:** Not applicable.
- **Preprocessing:** Extracted for Rudraprayag district bounding box; joined against Census 2011 PCA codes; reprojected to UTM Zone 44N (`EPSG:32644`) for Euclidean distance calculations.
- **Cleaning:** Verified 100% spatial join match rate ($653/653$ villages resolved without orphan records).
- **Feature Engineering:** Nearest-neighbor spatial distance to candidate red zones, health facilities, schools, and roads.
- **Data Augmentation:** Not applicable.
- **Data Limitations:** Centroids represent single administrative point coordinates rather than full multi-hectare village parcel footprints.
- **Licensing / Source Information:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Why the Dataset Was Selected:** Gold-standard academic crosswalk bridging Indian administrative censuses to open GIS geometries.

---

## 4. ESA WorldCover 10m 2021 v200 Land Cover

- **Dataset Name:** ESA WorldCover 10m 2021 v200 (Tile: `ESA_WorldCover_10m_2021_v200_N30E078`)
- **Source / Provider:** European Space Agency (ESA) / VITO Remote Sensing
- **Purpose:** Ecological and land-cover screening to subtract environmental constraints (dense forests, snow, water bodies, existing built-up land) from candidate relocation areas.
- **Size on Disk:** Raster tile (~15 MB subset)
- **Number of Samples / Records / Pixels:** 10m resolution raster resampled to 30m grid covering total district area ($372,128.32\text{ ha}$).
- **Features / Classes:**
  - `10`: Tree cover ($217,938.16\text{ ha}$, $58.57\%$ of district) $\rightarrow$ **EXCLUDED**
  - `20`: Shrubland ($0.08\text{ ha}$, $<0.01\%$) $\rightarrow$ **PERMISSIBLE**
  - `30`: Grassland ($74,003.07\text{ ha}$, $19.89\%$) $\rightarrow$ **PERMISSIBLE**
  - `40`: Cropland ($2,557.37\text{ ha}$, $0.69\%$) $\rightarrow$ **PERMISSIBLE**
  - `50`: Built-up ($1,706.33\text{ ha}$, $0.46\%$) $\rightarrow$ **EXCLUDED**
  - `60`: Bare / sparse vegetation ($11,851.52\text{ ha}$, $3.18\%$) $\rightarrow$ **PERMISSIBLE**
  - `70`: Snow and ice ($44,396.93\text{ ha}$, $11.93\%$) $\rightarrow$ **EXCLUDED**
  - `80`: Permanent water bodies ($1,469.04\text{ ha}$, $0.39\%$) $\rightarrow$ **EXCLUDED**
  - `100`: Moss and lichen ($18,205.81\text{ ha}$, $4.89\%$) $\rightarrow$ **PERMISSIBLE**
- **District Ecological Exclusion Breakdown:** $265,510.46\text{ ha}$ ($71.35\%$) excluded; $106,617.86\text{ ha}$ ($28.65\%$) permissible.
- **Data Format:** GeoTIFF (`.tif`).
- **Train / Validation / Test Split:** Not applicable.
- **Preprocessing:** Resampled to matching 30m grid of DEM and reprojected to `EPSG:32644`.
- **Cleaning:** Mapped to binary ecological exclusion mask.
- **Feature Engineering:** Spatial intersection and dominant land-cover classification per candidate relocation polygon.
- **Data Augmentation:** Not applicable.
- **Data Limitations:** 10m satellite classification snapshot from 2021; does not substitute for official statutory Forest Department cadastre boundaries or private land ownership titles.
- **Licensing / Source Information:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Why the Dataset Was Selected:** Globally validated 10m land cover providing the highest resolution open ecological baseline available in the Himalayas.

---

## 5. OpenStreetMap Critical Infrastructure POIs

- **Dataset Name:** OpenStreetMap Critical Infrastructure Extract — Rudraprayag District
- **Source / Provider:** OpenStreetMap Contributors (queried via Overpass API / Geofabrik)
- **Purpose:** Ingests health, educational, and emergency infrastructure to evaluate community isolation and emergency access.
- **Size on Disk:** ~1.2 MB (GeoJSON)
- **Number of Samples / Records:** 291 critical facilities across the district:
  - Healthcare Facilities (187 total): 127 subcentres, 24 hospitals, 18 clinics, 12 PHCs, 6 CHCs.
  - Educational Institutions (72 total): 33 higher education, 20 schools, 19 universities/colleges.
  - Civic & Administrative (28 total): 22 government offices, 2 community centres, 1 post office, 3 other civic.
  - Emergency Facilities (4 total): 3 police stations, 1 fire station.
- **Features:** `facility_id`, `facility_name`, `facility_category`, `broad_type`, `explicitly_evidenced_emergency_capability`, `potential_emergency_receiving_facility`, `geometry` (Point).
- **Labels / Classes:** Categorical infrastructure types.
- **Data Format:** GeoJSON (`.geojson`) and OGC GeoPackage (`.gpkg`).
- **Train / Validation / Test Split:** Not applicable.
- **Preprocessing:** Spatial attribution and distance calculation to all 653 habitations.
- **Cleaning:** Deduplication of co-located POI nodes and validation of coordinates within district boundaries.
- **Feature Engineering:** Mean distance to health facility ($1,848.9\text{ m}$), mean distance to hospital/CHC ($4,921.6\text{ m}$), mean distance to school ($12,250.1\text{ m}$).
- **Data Augmentation:** Not applicable.
- **Data Limitations:** Crowdsourced open data; does not represent an exhaustive administrative census of all rural primary schools.
- **Licensing / Source Information:** Open Database License (ODbL 1.0).
- **Why the Dataset Was Selected:** Most accessible, structured open vector dataset of healthcare and civic amenities.

---

## 6. OpenStreetMap Routable Road Network

- **Dataset Name:** OpenStreetMap Mountain Highway & Rural Road Hierarchy Extract
- **Source / Provider:** OpenStreetMap Contributors (Geofabrik extract)
- **Purpose:** Evaluates vehicular accessibility, isolation categories, and shortest-path mountain travel times.
- **Size on Disk:** ~8.5 MB (`osm_roads_rudraprayag.geojson`)
- **Number of Samples / Records:** 3,914 road segments totaling **6,397.35 km** ($4,756.84\text{ km}$ vehicular; $620.25\text{ km}$ arterial). Topological graph contains 237,401 nodes and 238,234 edges (largest connected component: $94.3\%$).
- **Features / Highway Classes:**
  - `trunk` (NH-107 / NH-07): 285 segments, $510.66\text{ km}$, speed: $35\text{ km/h}$
  - `primary`: 28 segments, $109.58\text{ km}$, speed: $30\text{ km/h}$
  - `secondary`: 50 segments, $134.95\text{ km}$, speed: $25\text{ km/h}$
  - `tertiary` (PMGSY): 307 segments, $927.74\text{ km}$, speed: $20\text{ km/h}$
  - `unclassified`: 1,147 segments, $2,534.16\text{ km}$, speed: $18\text{ km/h}$
  - `residential` / `service`: 393 segments, $201.12\text{ km}$, speed: $15\text{ km/h}$
  - `track` / `path` / `footway`: 1,690 segments, $1,975.37\text{ km}$, speed: $3.5–10\text{ km/h}$
- **Data Format:** GeoJSON (`.geojson`), OGC GeoPackage (`.gpkg`), Pickled NetworkX Graph (`road_graph.pickle`).
- **Train / Validation / Test Split:** Not applicable.
- **Preprocessing:** Built topologically connected metric graph in `EPSG:32644`; assigned mountain impedance speeds.
- **Cleaning:** Pruned disconnected micro-components and resolved multi-line segment overlaps.
- **Feature Engineering:** Calculated travel time to arterial highways (mean village travel time: $38.0\text{ min}$) and categorized habitations: Moderately Accessible ($249$), Remote ($180$), Highly Accessible ($142$), Severely Remote ($71$), Isolated ($11$).
- **Data Augmentation:** Not applicable.
- **Data Limitations:** Does not account for dynamic monsoon roadblocks or real-time debris obstructions.
- **Licensing / Source Information:** Open Database License (ODbL 1.0).
- **Why the Dataset Was Selected:** Only comprehensive open vector dataset capturing the complete road hierarchy from National Highways to rural PMGSY spurs in Uttarakhand.

---

## 7. Literature-Curated Historical Disaster Registry

- **Dataset Name:** Rudraprayag Historical Disaster & Landslide Incident Inventory (1998–2024)
- **Source / Provider:** Curated from NDMA, USDMA bulletins, ISRO Bhuvan Landslide Atlas, NIDM Post-Disaster Needs Assessments, and peer-reviewed journals (*Geomorphology*, *Natural Hazards*, *Current Science*).
- **Purpose:** Provides verified empirical evidence of past disaster locations to establish chronic risk exposure perimeters.
- **Size on Disk:** ~150 KB (`historical_disaster_inventory.geojson`)
- **Number of Samples / Records:** 22 canonical verified disaster events (deduplicated from 26 raw literature records; 4 duplicate pairs merged). Total recorded fatalities: **6,913**; affected households: **3,637**.
- **Features:** `canonical_incident_id`, `incident_year` (1998–2024), `hazard_type` (10 Landslides, 5 Cloudbursts, 3 Debris Flows, 2 Riverine Floods, 1 Flash Flood, 1 Rockfall), `fatalities`, `households_affected`, `evidence_level`, `source_provider`, `coordinate_uncertainty`, `geometry` (Point).
- **Labels / Classes:** Event severity and disaster hazard types.
- **Data Format:** GeoJSON (`.geojson`) and JSON summary.
- **Train / Validation / Test Split:** Not applicable.
- **Preprocessing:** Spatial georeferencing to `EPSG:32644` and derivation of $1\text{ km}$ and $2\text{ km}$ proximity buffers around historical disaster epicenters.
- **Cleaning:** Strict deduplication logging spatial offsets ($24\text{ m}$ to $73\text{ m}$) and temporal co-occurrence.
- **Feature Engineering:** Identification of chronic exposure habitations (33 villages within $1\text{ km}$; 129 villages within $2\text{ km}$; 26 chronic exposure villages).
- **Data Augmentation:** Not applicable.
- **Data Limitations:** Curated secondary literature snapshot; does not represent an automated real-time official telemetry feed from USDMA.
- **Licensing / Source Information:** Literature compiled under academic fair-use and public disaster report citations.
- **Why the Dataset Was Selected:** Fulfills the strict PS-4 requirement for empirical disaster history integration using verified, citable scientific records without fabricating synthetic events.

---

## 8. PMAY-G Rural Housing Standard Configuration

- **Dataset / Standard Name:** Pradhan Mantri Awaas Yojana - Gramin (PMAY-G) Operational Guidelines
- **Source / Provider:** Ministry of Rural Development (MoRD), Government of India (2016)
- **Purpose:** Authoritative national planning standard for calculating preliminary dwelling-unit and household capacity scenarios on candidate relocation sites.
- **Specification / Parameters:**
  - Minimum built floor area norm: **$25.0\text{ m}^2$ per household**
  - Site efficiency factor ($\eta$): **$0.40$** ($40\%$ net buildable land utilization; $60\%$ reserved for setbacks, roads, and drainage)
  - Average household size: **$4.0$ persons per household** (conservative planning assumption vs. Census average of $4.57$)
  - Minimum viable site area: **$2,500\text{ m}^2$** ($0.25\text{ ha}$, minimum 10 HH)
  - Scale protection cap: **$100\text{ ha}$** (polygons $>100\text{ ha}$ flagged as `AREA_EXCEEDS_SITE_PLANNING_SCALE`)
- **Data Format:** Declarative YAML configuration (`configs/capacity.yaml`).
- **Why the Standard Was Selected:** Officially gazetted Government of India rural housing scheme norm, providing an explainable, citable basis for spatial carrying capacity scenarios.
