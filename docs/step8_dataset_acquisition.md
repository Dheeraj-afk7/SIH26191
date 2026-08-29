# Step 8A.1 — Actual Dataset Acquisition Report

**Acquisition Date**: 2026-08-29  
**Target Region**: Rudraprayag District, Uttarakhand, India  
**Acquisition Status**: **PASS — Both demographic AND spatial datasets physically downloaded and successfully opened.**

---

## 1. Demographic Dataset

| Field | Detail |
| :--- | :--- |
| **1. Dataset Name** | Primary Census Abstract C.D. Block wise, Uttarakhand - District Rudraprayag - 2011 (`PCA_CDB-0503`) |
| **2. Authority** | Office of the Registrar General & Census Commissioner, India (ORGI), Ministry of Home Affairs, Government of India |
| **3. Official Source** | Census of India Digital Library / NADA Study Catalog 40739 (`https://censusindia.gov.in/nada/index.php/catalog/40739`) |
| **4. Download URL** | `https://censusindia.gov.in/nada/index.php/catalog/40739/download/44370/PCA_CDB-0503-F-Census.xlsx` |
| **5. Access / Download Method** | Automated HTTP GET via Python `urllib.request` with standard TLS configuration and custom user-agent. |
| **6. Local Filename** | `PCA_CDB-0503-F-Census.xlsx` |
| **7. Local Path** | `data/raw/habitations/PCA_CDB-0503-F-Census.xlsx` (Absolute: `C:\Users\K DHEERAJ\Documents\Claude Workspace\SIH26191\data\raw\habitations\PCA_CDB-0503-F-Census.xlsx`) |
| **8. File Size** | 317,621 bytes (~310.2 KB) |
| **9. Download Date** | 2026-08-29T01:06:04+05:30 |
| **10. Verification Result** | **PASSED** — Valid OpenXML Excel format (`PK\x03\x04`), successfully loaded via `openpyxl` (read-only mode) and `pandas.read_excel`. Contains sheet `EB-0503` with 95 census demographic attribute columns. |
| **11. Limitations** | Decennial census data vintage 2011. Does not contain explicit native GIS polygon/point coordinates inside the spreadsheet; represents tabular block/village-level administrative hierarchies. |

---

## 2. Spatial Habitation Dataset

| Field | Detail |
| :--- | :--- |
| **1. Dataset Name** | OpenStreetMap Populated Places & Settlements for Rudraprayag District |
| **2. Authority** | OpenStreetMap Foundation (OSMF) / OpenStreetMap Community Contributors |
| **3. Official Source** | OpenStreetMap Database / Overpass API Service (`https://overpass-api.de/`) |
| **4. Download URL** | `https://overpass-api.de/api/interpreter` (Query filtered for `place IN ['village', 'town', 'hamlet', 'isolated_dwelling', 'suburb', 'locality']` within Rudraprayag bounding box `[30.1878, 78.7847, 30.8211, 79.3789]`) |
| **5. Access / Download Method** | Automated Overpass QL API query executed via Python `urllib.request`, converted to standard GeoJSON FeatureCollection. |
| **6. Local Filename** | `rudraprayag_settlements_osm.geojson` |
| **7. Local Path** | `data/raw/habitations/rudraprayag_settlements_osm.geojson` (Absolute: `C:\Users\K DHEERAJ\Documents\Claude Workspace\SIH26191\data\raw\habitations\rudraprayag_settlements_osm.geojson`) |
| **8. File Size** | 531,262 bytes (~518.8 KB) |
| **9. Download Date** | 2026-08-29T01:10:32+05:30 |
| **10. Verification Result** | **PASSED** — Valid GeoJSON FeatureCollection, loaded via `geopandas.read_file()`. Contains 1,481 spatial features (1,467 Points, 14 Polygons) in CRS `EPSG:4326` (WGS84). |
| **11. Limitations** | Open community-sourced mapping dataset licensed under ODbL. While highly localized and spatially precise for terrain/flood exposure, settlement naming and attribution may vary from official Survey of India MDDS village boundary codes. |

---

## 3. Physical File Audit & Command Output

The acquisition and loadability verification was validated using `scripts/verify_step8_downloads.py`:

```text
======================================================================
PHASE 4 — DOWNLOAD VERIFICATION AUDIT
======================================================================
Timestamp: 2026-08-29T01:10:52.507643
Habitations Directory: C:\Users\K DHEERAJ\Documents\Claude Workspace\SIH26191\data\raw\habitations

File Name: PCA_CDB-0503-F-Census.xlsx
Relative Path: data/raw/habitations/PCA_CDB-0503-F-Census.xlsx
Absolute Path: C:\Users\K DHEERAJ\Documents\Claude Workspace\SIH26191\data\raw\habitations\PCA_CDB-0503-F-Census.xlsx
File Extension: .xlsx
Physically Exists: True
File Size (bytes): 317621
Last Modified: 2026-08-29T01:06:04.554866
Open Status: SUCCESS (Workbook loaded, sheets: ['EB-0503'], preview rows: 5)
----------------------------------------------------------------------
File Name: rudraprayag_settlements_osm.geojson
Relative Path: data/raw/habitations/rudraprayag_settlements_osm.geojson
Absolute Path: C:\Users\K DHEERAJ\Documents\Claude Workspace\SIH26191\data\raw\habitations\rudraprayag_settlements_osm.geojson
File Extension: .geojson
Physically Exists: True
File Size (bytes): 531262
Last Modified: 2026-08-29T01:10:32.490123
Open Status: SUCCESS (GeoDataFrame loaded, features: 1481, CRS: EPSG:4326)
----------------------------------------------------------------------

======================================================================
FINAL STATUS: PASS
Both demographic AND spatial datasets physically downloaded and successfully opened.
======================================================================
```

---

## 4. Strict Protocol Compliance
- [x] Raw data directory `data/raw/habitations/` created and maintained.
- [x] Official Government of India Census dataset acquired directly without modification.
- [x] Real spatial settlement dataset acquired covering Rudraprayag without synthetic coordinates.
- [x] Both files physically exist and open successfully with production geospatial/data libraries.
- [x] Exposure analysis, schema merging, and joins deferred to subsequent authorized steps.
