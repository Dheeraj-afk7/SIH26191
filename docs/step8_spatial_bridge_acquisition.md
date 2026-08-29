# Step 8B.2 — Census-Code-Linked Spatial Village Data Acquisition & Diagnostic Join Report

**Acquisition Date**: 2026-08-29  
**Target District**: Rudraprayag, Uttarakhand, India  
**Bridge Source**: Development Data Lab — Socioeconomic High-resolution Rural-Urban Geographic Platform for India (SHRUG v2.2)  
**Verification Tool**: `scripts/diagnose_shrug_join.py` / Python 3.12 GeoPandas Stack  

---

## Executive Summary & Final Status

```
FINAL STATUS: PASS
A real spatial dataset was downloaded and a reliable code-based link to Census villages was demonstrated.
```

To bridge official 2011 Census demographic statistics with physical GIS geometry without relying on fuzzy or name-based joins, authoritative spatial keys from the **SHRUG (Development Data Lab)** platform were downloaded, verified, and structured into a production-grade spatial village bridge.

### Key Milestones Achieved:
1. **Zero Fuzzy Matching**: Every spatial feature is linked via the official 2011 Census 6-digit MDDS village code (`pc11_village_id` = `Town/Village`).
2. **High Village Match Rate**: **653 out of 688** Census village codes (94.91%) match 1:1 with spatial centroid points.
3. **100.00% Population Coverage**: All 35 unmatched census villages in the rural abstract are officially recorded as uninhabited (`TOT_P = 0`, `No_HH = 0`). The 653 matched villages cover **232,360 out of 232,360 rural residents (100.00%)** in Rudraprayag District.
4. **Zero Spatial Duplicates & Zero Spatial Outliers**: 0 duplicate village codes in spatial data; 0 spatial features outside the district.

---

## 1. Dataset Acquisition & Physical Verification

| Property | Detail |
| :--- | :--- |
| **Dataset Name** | SHRUG PC11 Rural Location Keys & Spatial Centroids (`rudraprayag_census_villages_shrug.geojson`) |
| **Authority** | Development Data Lab (Asher, Lunt, Matsuura, Novosad, 2021; World Bank Economic Review) |
| **Source URL** | `https://shrug-assets-ddl.s3.amazonaws.com/media/private/2.2.pakora/shrug-pc-keys-csv.zip` & `shrug-shrid-keys-csv.zip` |
| **Local File Path** | `data/raw/habitations/rudraprayag_census_villages_shrug.geojson` (Absolute: `C:\Users\K DHEERAJ\Documents\Claude Workspace\SIH26191\data\raw\habitations\rudraprayag_census_villages_shrug.geojson`) |
| **Physical Existence** | `True` |
| **File Size** | `408,409 bytes` (~398.8 KB) |
| **Format & CRS** | GeoJSON / `EPSG:4326` (WGS84 2D Geographic Coordinates) |
| **Geometry Type** | `Point` (`653` valid 2D spatial centroids) |

---

## 2. GeoPandas Schema & Attribute Audit

The dataset opens natively in GeoPandas. Complete column definitions (18 columns total):

```text
[00] shrid2                (dtype: object)   -> SHRUG v2.2 unique geographic unit identifier
[01] pc11_state_id         (dtype: int32)    -> Census 2011 State code (5 = Uttarakhand)
[02] pc11_district_id      (dtype: int32)    -> Census 2011 District code (58 = Rudraprayag)
[03] pc11_subdistrict_id   (dtype: float64)  -> Census 2011 Sub-district / Tehsil code
[04] pc11_village_id       (dtype: int32)    -> Census 2011 MDDS Village Code (Primary Join Key)
[05] pc11_land_area        (dtype: float64)  -> Village land area (sq km)
[06] pc11_pca_tot_p        (dtype: float64)  -> Total population cross-reference
[07] latitude              (dtype: float64)  -> WGS84 Latitude centroid
[08] longitude             (dtype: float64)  -> WGS84 Longitude centroid
[09] area_laea             (dtype: float64)  -> Equal-area projected land area
[10] high_quality          (dtype: int32)    -> Geometric boundary fidelity flag
[11] polysource            (dtype: object)   -> Source polygon lineage description
[12] state_name            (dtype: object)   -> State name string ('uttarakhand')
[13] district_name         (dtype: object)   -> District name string ('rudraprayag')
[14] subdistrict_name      (dtype: object)   -> Sub-district name string ('ukhimath', 'jakholi', etc.)
[15] village_name          (dtype: object)   -> Census village name
[16] place_name            (dtype: object)   -> Vernacular place name
[17] geometry              (dtype: geometry) -> Shapely Point(x=longitude, y=latitude)
```

### First 5 Records Sample:
```text
   pc11_village_id                  shrid2    village_name   latitude  longitude
0            42054  11-05-058-00290-042054        garuriya  30.720419  79.065656
1            42058  11-05-058-00290-042058       gaurikund  30.662653  79.025902
2            42059  11-05-058-00290-042059      mundkatiya  30.651491  79.010643
3            42060  11-05-058-00290-042060           tausi  30.682969  78.973308
4            42061  11-05-058-00290-042061  trijuginarayan  30.648060  78.987190
```

---

## 3. Diagnostic Join Test Results

A strict integer-code comparison was performed between the official Census 2011 Excel table (`PCA_CDB-0503-F-Census.xlsx`, column `Town/Village`) and the spatial bridge (`pc11_village_id`).

### Join Metrics:
| Metric | Value | Notes |
| :--- | :--- | :--- |
| **Census Village Records** | `688` | All records where `Level == 'VILLAGE'` in PCA Excel |
| **Spatial Village Features** | `653` | All records for Rudraprayag in SHRUG spatial bridge |
| **Matching Census Village Codes** | **653** | **94.91% match rate** on exact MDDS integer codes |
| **Unmatched Census Identifiers** | `35` | `5.09%` (All 35 are uninhabited with 0 population) |
| **Unmatched Spatial Identifiers** | `0` | `0.00%` (Zero orphan spatial records) |
| **Duplicate Spatial Identifiers** | `0` | `0.00%` (100% unique primary keys) |

### Population Coverage Analysis:
- **Total Census Rural Population**: `232,360` persons
- **Population in Matched 653 Villages**: `232,360` persons (**100.00%**)
- **Population in Unmatched 35 Villages**: `0` persons (**0.00%**)
- **Uninhabited Status**: All 35 unmatched census records have `TOT_P = 0` and `No_HH = 0` (e.g., high-altitude forest ranges, shrines, and unpopulated pastures such as *Tungnath, Chopta, Baniyakund, Dogalbhita, Ghinurpani, Rambara*).

---

## 4. Actual Diagnostic Command Output

```text
$ python scripts/diagnose_shrug_join.py
================================================================================
STEP 8B.2: CENSUS-CODE-LINKED SPATIAL VILLAGE DATA INSPECTION & JOIN TEST
================================================================================
Timestamp: 2026-08-29T01:41:52.038318

--- 1. SPATIAL DATASET PHYSICAL INSPECTION ---
Spatial File: C:\Users\K DHEERAJ\Documents\Claude Workspace\SIH26191\data\raw\habitations\rudraprayag_census_villages_shrug.geojson
File Exists: True
File Size: 408409 bytes
Last Modified: 2026-08-29T01:41:33.546776

--- 2. GEOPANDAS LOAD & SCHEMA AUDIT ---
Total Feature Count: 653
CRS: EPSG:4326
Geometry Types:
Point    653
All Column Names (18 total):
   [00] shrid2 (dtype: object)
   [01] pc11_state_id (dtype: int32)
   [02] pc11_district_id (dtype: int32)
   [03] pc11_subdistrict_id (dtype: float64)
   [04] pc11_village_id (dtype: int32)
   [05] pc11_land_area (dtype: float64)
   [06] pc11_pca_tot_p (dtype: float64)
   [07] latitude (dtype: float64)
   [08] longitude (dtype: float64)
   [09] area_laea (dtype: float64)
   [10] high_quality (dtype: int32)
   [11] polysource (dtype: object)
   [12] state_name (dtype: object)
   [13] district_name (dtype: object)
   [14] subdistrict_name (dtype: object)
   [15] village_name (dtype: object)
   [16] place_name (dtype: object)
   [17] geometry (dtype: geometry)

--- 3. IDENTIFIER INTEGRITY AUDIT ---
Identified Census Code Column: 'pc11_village_id' (Present: True)
Total Features: 653
Unique 'pc11_village_id' values: 653
Duplicate 'pc11_village_id' values: 0
Null 'pc11_village_id' values: 0
Valid Geometries Count: 653

First 5 Records:
   pc11_village_id                  shrid2    village_name   latitude  longitude
0            42054  11-05-058-00290-042054        garuriya  30.720419  79.065656
1            42058  11-05-058-00290-042058       gaurikund  30.662653  79.025902
2            42059  11-05-058-00290-042059      mundkatiya  30.651491  79.010643
3            42060  11-05-058-00290-042060           tausi  30.682969  78.973308
4            42061  11-05-058-00290-042061  trijuginarayan  30.648060  78.987190

--- 4. DIAGNOSTIC JOIN TEST ---
Census Village Records in Excel ('Level' == 'VILLAGE'): 688
Spatial Village Records in Dataset: 653
Matching Census-Spatial Village Codes: 653 (94.91%)
Unmatched Census Identifiers: 35 (5.09%)
Unmatched Spatial Identifiers: 0
Duplicate Identifiers in Spatial Data: 0

--- 5. UNMATCHED CENSUS VILLAGE ANALYSIS ---
Total Census Population in Rudraprayag: 232,360 persons
Population in 653 Matched Villages: 232,360 persons (100.00%)
Population in 35 Unmatched Villages: 0 persons (0.00%)
Uninhabited (TOT_P == 0) Unmatched Villages: 35 out of 35 (100.0%)

================================================================================
FINAL STATUS: PASS
A real spatial dataset was downloaded and a reliable code-based link to Census villages was demonstrated.
================================================================================
```

---

## 5. Architectural Compliance & Next Steps
- [x] Real spatial bridge dataset downloaded and verified on disk.
- [x] Code-based linkage validated (no name matching, no fuzzy heuristic).
- [x] 100.00% rural population coverage verified.
- [x] Diagnostic join test completed without modifying raw source files or generating final exposure products prematurely.
