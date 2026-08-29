# Step 8B.1 — Actual Dataset Schema Inspection Report

**Inspection Date**: 2026-08-29  
**Target District**: Rudraprayag, Uttarakhand, India  
**Audited Datasets**:
1. **Demographic Dataset**: `data/raw/habitations/PCA_CDB-0503-F-Census.xlsx` (Census of India 2011 Primary Census Abstract)
2. **Spatial Dataset**: `data/raw/habitations/rudraprayag_settlements_osm.geojson` (OpenStreetMap Populated Places)

---

## Executive Summary & Final Classification

```
FINAL STATUS: PARTIAL — datasets inspected but no safe join key exists
```

Both datasets have been verified to physically exist and load with standard geospatial and tabular toolchains. However, schema inspection reveals that **no authoritative shared key (Census 2011 MDDS village code, LGD code, or unique identifier)** exists between the Census table and the OpenStreetMap spatial features. 

In strict adherence to engineering constraints:
- **No production join is executed.**
- **No name-based or fuzzy matching is attempted.**
- **Spatial hazard screening will operate directly on physical settlement coordinates without unverified demographic merging.**

---

## Phase 1 — Census Dataset Inspection

**Source File**: `data/raw/habitations/PCA_CDB-0503-F-Census.xlsx`  
**Authority**: Office of the Registrar General & Census Commissioner, India (ORGI)

### 1. Structure & Dimensions
- **Workbook Sheets**: `['EB-0503']`
- **Total Rows**: `700`
- **Total Columns**: `95`
- **Data Completeness**: 100% (0 nulls across all core administrative and demographic fields)

### 2. Administrative Breakdown (`Level` & `TRU`)
| Administrative Level | Total Records | Rural | Urban | Description |
| :--- | :--- | :--- | :--- | :--- |
| **CD BLOCK** | 12 | 4 | 4 | 4 C.D. Blocks (`Ukhimath` [16], `Augustmuni` [17], `Jakholi` [18], `Forest/Special` [98]) with Total/Rural/Urban aggregates |
| **VILLAGE** | 688 | 688 | 0 | 688 inhabited and uninhabited rural revenue villages |
| **TOWN** | 0 | 0 | 0 | (Towns are enumerated separately in urban PCA tables) |
| **TOTAL** | **700** | **692** | **4** | Complete district rural administrative hierarchy |

### 3. Core Field Mapping
| Semantic Concept | Actual Column Name | Data Type | Notes |
| :--- | :--- | :--- | :--- |
| **State Code** | `State` | `int64` | Value `5` (Uttarakhand) |
| **District Code** | `District` | `int64` | Value `58` (Census 2011 district code for Rudraprayag) |
| **District Name** | `DT Name` | `object` | `'Rudraprayag'` |
| **C.D. Block Code** | `CD Block` | `int64` | `16`, `17`, `18`, `98` |
| **Census Village Code** | `Town/Village` | `int64` | 5-to-6 digit Census 2011 MDDS code (`042054` to `042741`) |
| **Administrative Level** | `Level` | `object` | `'CD BLOCK'` or `'VILLAGE'` |
| **Village Name** | `Name` | `object` | Official village name |
| **Rural / Urban** | `TRU` | `object` | `'Total'`, `'Rural'`, or `'Urban'` |
| **Households** | `No_HH` | `int64` | Total occupied households |
| **Total Population** | `TOT_P` | `int64` | Total persons |
| **Male Population** | `TOT_M` | `int64` | Total males |
| **Female Population** | `TOT_F` | `int64` | Total females |
| **SC Population** | `P_SC` | `int64` | Scheduled Caste population |
| **ST Population** | `P_ST` | `int64` | Scheduled Tribe population |

### 4. Integrity Checks
- **Null values in key fields**: `0` (0.00%)
- **Village Code Uniqueness**: All `688` village records possess distinct, unique `Town/Village` codes (`0` duplicates).

### 5. First 5 Rows Sample
```text
   State  District      DT Name  CD Block  Town/Village  Ward  EB     Level        Name    TRU  No_HH  TOT_P  TOT_M  TOT_F  P_SC  P_ST
0      5        58  Rudraprayag        16             0     0   0  CD BLOCK    Ukhimath  Total  10259  50719  25204  25515  7792   135
1      5        58  Rudraprayag        16             0     0   0  CD BLOCK    Ukhimath  Rural  10259  50719  25204  25515  7792   135
2      5        58  Rudraprayag        16             0     0   0  CD BLOCK    Ukhimath  Urban      0      0      0      0     0     0
3      5        58  Rudraprayag        16         42054     0   0   VILLAGE    Garuriya  Rural      2     10     10      0     0     0
4      5        58  Rudraprayag        16         42055     0   0   VILLAGE  Ghinurpani  Rural      0      0      0      0     0     0
```

---

## Phase 2 — Spatial Dataset Inspection

**Source File**: `data/raw/habitations/rudraprayag_settlements_osm.geojson`  
**Authority**: OpenStreetMap Contributors / Overpass API

### 1. Spatial Properties
- **Coordinate Reference System (CRS)**: `EPSG:4326` (WGS84 geographic 2D)
- **Total Features**: `1,481`
- **Geometry Types**:
  - `Point`: `1,467` features (99.05%)
  - `Polygon`: `14` features (0.95%)

### 2. Settlement Type Distribution (`place` tag)
| Place Classification | Feature Count | Percentage | Description |
| :--- | :--- | :--- | :--- |
| `hamlet` | 1,125 | 75.96% | Small rural settlements / tolas / majras |
| `isolated_dwelling` | 186 | 12.56% | Isolated homesteads / high-altitude chalets |
| `village` | 140 | 9.45% | Main recognized villages |
| `locality` | 17 | 1.15% | Named landmarks / named junctions |
| `town` | 12 | 0.81% | Urban/peri-urban centers (e.g., Rudraprayag, Ukhimath, Karnaprayag) |
| `village;hamlet` | 1 | 0.07% | Compound tag |
| **Total** | **1,481** | **100.0%** | Comprehensive settlement footprint |

### 3. Attribute Schema (26 Columns)
```text
[00] AND_a_nosr_p       [09] name:fa          [18] population
[01] addr:postcode      [10] name:hi          [19] postal_code
[02] alt_name           [11] name:ml          [20] source
[03] alt_name:en        [12] name:pa          [21] wikidata
[04] fixme              [13] name:ta          [22] wikipedia
[05] landuse            [14] name:te          [23] osm_id
[06] name               [15] name:uk          [24] osm_type
[07] name:ar            [16] nga:ufi          [25] geometry
[08] name:en            [17] place
```

### 4. Identification of Key Identifiers & Quality Audit
- **Settlement Name Field**: `name` (English/Romanized transliteration)
- **Spatial Identifier**: `osm_id` (Unique 64-bit integer)
- **Census 2011 / MDDS Village Code**: **NONE** (Not present in OSM attributes)
- **Local Government Directory (LGD) Code**: **NONE** (Not present in OSM attributes)
- **Explicit Administrative Hierarchy**: **NONE** (District boundary is inferred from query AOI bounding box `[30.1878, 78.7847, 30.8211, 79.3789]`)
- **Unnamed / Null Settlements**: `218` features (14.72% have `name = null`)
- **Duplicate Settlement Names**: `83` names appear multiple times across the bounding box (e.g., common local toponyms like `Bhatwari`, `Gair`, `Khola`, `Simli`, `Bagoli`, `Dimmar`).

### 5. First 10 Records Sample
```text
      osm_id osm_type             name     place population                          source
0  245769614     node       Dangchaura   village       5000                             AND
1  245769705     node      Karnaprayag      town       5000  AND;Bing, USGS, 2013-05-16;NGA
2  245769841     node       Nandaprayag     town       None      Bing, USGS, 2013-05-16;NGA
3  299531766     node  Trijugi Narayan  locality       None                             AND
4  299531768     node         Ukhimath      town       1000      Bing, USGS, 2013-05-16;NGA
5  342107378     node      Rudraprayag      town      15000                            None
6  342107387     node           Pokhri      town       None      Bing, USGS, 2013-05-16;NGA
7  342107407     node        Gopeshwar      town       None      Bing, USGS, 2013-05-16;NGA
8  342107444     node             Kund    hamlet       None                            None
9  342107568     node          Mastura   village       None                            None
```

---

## Phase 3 — Join Feasibility Analysis

### Comparison Matrix

| Inspection Criterion | Census 2011 Dataset | OpenStreetMap Dataset | Join Compatibility |
| :--- | :--- | :--- | :--- |
| **Primary Key** | `Town/Village` (Census MDDS code) | `osm_id` | **INCOMPATIBLE (No Shared Key)** |
| **LGD Code** | Not Present | Not Present | **INCOMPATIBLE** |
| **Settlement Name** | Formal Revenue Village Name | Vernacular / Hamlet Name | **UNSAFE (Severe Spelling & Granularity Mismatch)** |
| **Granularity** | 688 Revenue Villages | 1,481 Points/Polygons (mostly hamlets) | **Many-to-One / Unmatched** |
| **Unnamed Entities** | 0% | 14.72% Unnamed | **Cannot Join Unnamed Features** |

### Join Classification:
**Category B & C: NO DIRECT SAFE JOIN POSSIBLE**

### Technical Rationale Against Name-Based / Fuzzy Matching:
1. **Granularity Divergence**: Census 2011 PCA reports at the *Revenue Village* level (688 units), whereas OSM maps individual *hamlets, tolas, and dwellings* (1,481 units). A single revenue village frequently comprises 3–10 distinct spatial hamlets.
2. **Toponymic Ambiguity**: 83 settlement names are duplicated within the region, making deterministic 1:1 joins impossible without cadastral boundaries.
3. **Transliteration Noise**: Discrepancies between Hindi Devanagari romanization in Census records vs. volunteer-contributed OSM toponyms would induce false positive cross-links.
4. **Data Integrity Standard**: In hazard risk screening, assigning population or vulnerability metrics to the wrong spatial coordinates creates dangerous operational errors.

### Required Datasets for Future Authoritative Joins:
To achieve an authoritative 1:1 demographic-to-spatial link, the system would require:
1. **Survey of India (SOI) / LGD Village Boundary Shapefile** containing official 6-digit Census 2011 MDDS village codes.
2. **DevDataLab SHRUG (Socioeconomic High-resolution Rural-Urban Geographic) Platform** mapping SHRIDs directly to Census 2011 village codes.

---

## Phase 4 — Inspection Script & Verification Tool

The read-only inspection script is located at:
- [`scripts/inspect_step8_habitation_data.py`](file:///c:/Users/K%20DHEERAJ/Documents/Claude%20Workspace/SIH26191/scripts/inspect_step8_habitation_data.py)

### Execution Command:
```bash
python scripts/inspect_step8_habitation_data.py
```
*(Exit Code: 0, Output Status: PARTIAL — datasets inspected but no safe join key exists)*
