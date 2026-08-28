# Step 8 -- Habitation Hazard Exposure & Proximity Screening Report

**Generated:** 2026-08-28T20:34:16Z  
**Project:** SIH26191 -- Rudraprayag District, Uttarakhand  
**Pilot District:** Rudraprayag  
**Status:** DECISION SUPPORT SCREENING OUTPUT -- Requires Official Verification  

---

## 1. Decision-Support Disclaimer

> **DECISION-SUPPORT DISCLAIMER**
>
> These outputs are preliminary GIS-based decision-support screening results
> and do not constitute disaster prediction, engineering safety certification,
> evacuation instruction, or mandatory relocation recommendation.
>
> Official administrative action requires verification by competent geotechnical
> and disaster management authorities.

---

## 2. Executive Summary & Key Findings

### A. Direct Overlap
Direct centroid-based overlap analysis found that **0 habitation centroids** were located inside the current Candidate Hazard-Based Red Zone polygons.

### B. Proximity Screening
Proximity screening identified multiple habitation centroids near Candidate Hazard-Based Red Zones, including **14 within 500 m** and the nearest identified habitation at approximately **42.5 m**.

### C. Methodological Limitation
Village centroid locations represent reference points for habitations and do not represent complete settlement extents, building footprints, or individual household locations. Accordingly, the absence of direct centroid overlap should not be interpreted as evidence that no population or infrastructure is potentially affected.

---

## 3. Dataset Inputs & Geometry Overview

| Dataset | File Path | Features | Geometry Type | CRS |
|---------|-----------|----------|---------------|-----|
| Habitation Baseline | `data\processed\habitations\habitation_baseline.geojson` | 653 | Point (Village Centroids) | EPSG:32644 |
| Step 7 Red Zones | `data\outputs\candidate_hazard_based_red_zones.geojson` | 289 | Polygon / MultiPolygon | EPSG:32644 |

---

## 4. Direct Centroid-Based Overlap Results

| Demographic Metric | Total Inhabited Baseline | Direct Overlap (Inside) | Outside Red Zone Polygons |
|--------------------|-------------------------|-------------------------|---------------------------|
| Habitation Records | 653 | **0 (0.0%)** | 653 (100.0%) |
| Total Population (TOT_P) | 232,360 | **0 (0.0%)** | 232,360 (100.0%) |
| Total Households (No_HH) | 50,882 | **0 (0.0%)** | 50,882 (100.0%) |
| SC Population (P_SC) | 46,279 | **0 (0.0%)** | 46,279 (100.0%) |
| ST Population (P_ST) | 309 | **0 (0.0%)** | 309 (100.0%) |

---

## 5. Proximity Screening Results

To provide rigorous decision-support context beyond single-point centroids, Euclidean distances from each village centroid to the boundary of the nearest Candidate Hazard-Based Red Zone were computed in metric CRS (EPSG:32644).

### Distance Statistics

- **Minimum Distance (Closest Village Centroid):** 42.5 m (Village: Marora, ID: 42573)
- **Maximum Distance:** 16712.2 m
- **Mean Distance:** 6212.8 m
- **Median Distance:** 5613.5 m

### Proximity Band Breakdown

| Proximity Band | Habitations | % Habitations | Population | % Population | Households | % Households |
|----------------|------------|---------------|------------|--------------|------------|--------------|
| Inside Candidate Hazard-Based Red Zone | 0 | 0.00% | 0 | 0.00% | 0 | 0.00% |
| Within 500 m | 14 | 2.14% | 5,305 | 2.28% | 1,088 | 2.14% |
| 500 m to 1 km | 16 | 2.45% | 4,858 | 2.09% | 985 | 1.94% |
| 1 km to 2 km | 51 | 7.81% | 17,599 | 7.57% | 3,578 | 7.03% |
| 2 km to 5 km | 204 | 31.24% | 64,463 | 27.74% | 13,978 | 27.47% |
| 5 km to 10 km | 255 | 39.05% | 93,965 | 40.44% | 21,145 | 41.56% |
| Beyond 10 km | 113 | 17.30% | 46,170 | 19.87% | 10,108 | 19.87% |

### Nearest Habitations to Candidate Hazard-Based Red Zones (< 500 m)

| Village Code | Village Name | Nearest Zone ID | Distance (m) | Population | Households |
|--------------|--------------|-----------------|--------------|------------|------------|
| 42573 | Marora | RZ-220 | 42.5 m | 208 | 49 |
| 42067 | Tarsali | RZ-018 | 178.5 m | 98 | 20 |
| 42070 | Khat | RZ-078 | 257.7 m | 271 | 54 |
| 42165 | Dungar semala | RZ-048 | 310.8 m | 580 | 110 |
| 42320 | Narkota | RZ-250 | 321.5 m | 357 | 83 |
| 42129 | Gadagu | RZ-152 | 330.5 m | 601 | 117 |
| 42080 | Jaltalla | RZ-045 | 349.1 m | 373 | 79 |
| 42086 | Kabiltha | RZ-261 | 349.6 m | 341 | 62 |
| 42081 | Chaumasi | RZ-177 | 379.1 m | 284 | 57 |
| 42127 | Burua | RZ-091 | 410.6 m | 386 | 71 |
| 42128 | Madali | RZ-174 | 425.1 m | 5 | 2 |
| 42058 | Gaurikund | RZ-008 | 468.8 m | 223 | 43 |
| 42118 | Gaundar | RZ-145 | 486.4 m | 294 | 45 |
| 42574 | Mawana | RZ-220 | 497.6 m | 1,284 | 296 |

---

## 6. Output Schema & Standardized Fields

| Field Name | Type | Description |
|------------|------|-------------|
| `village_id` | Integer | Census 2011 Town/Village identifier code |
| `village_name` | String | Official Census village name |
| `tot_pop` | Integer | Total village population (Census PCA 2011) |
| `households` | Integer | Number of households (Census PCA 2011) |
| `pop_sc` | Integer | Scheduled Caste population |
| `pop_st` | Integer | Scheduled Tribe population |
| `direct_zone_overlap` | Boolean | True if centroid directly intersects Candidate Red Zone |
| `hazard_zone_flag` | Integer | 1 = Inside, 0 = Outside (backward compatibility) |
| `hazard_zone_label` | String | Standardized textual overlap label |
| `nearest_hazard_distance_m` | Float | Distance in meters to nearest Candidate Red Zone (EPSG:32644) |
| `proximity_band` | String | Descriptive proximity category (7 standard bands) |
| `nearest_zone_id` | String | Identifier of the closest Candidate Red Zone polygon |
| `geometry` | Geometry | Point centroid in metric CRS (EPSG:32644) |

---

## 7. Validation Cross-Checks

| Check Description | Expected | Actual | Status |
|-------------------|----------|--------|--------|
| Total Exposure Records | 653 | 653 | PASS |
| Direct Overlap + Outside Population = Total Pop | 232,360 | 232,360 | PASS |
| Direct Overlap + Outside Households = Total HH | 50,882 | 50,882 | PASS |
| Proximity Band Record Sum = Total Habitations | 653 | 653 | PASS |
| Proximity Band Population Sum = Total Population | 232,360 | 232,360 | PASS |
| Coordinate Reference System | EPSG:32644 | EPSG:32644 | PASS |

---

*This report is a decision-support output of the SIH26191 GIS pipeline.*
*Official administrative action requires verification by competent geotechnical*
*and disaster management authorities.*