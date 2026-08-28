# Step 8 -- Habitation Hazard Exposure Report

**Generated:** 2026-08-28T20:26:16Z  
**Project:** SIH26191 -- Rudraprayag District, Uttarakhand  
**Pilot District:** Rudraprayag  
**Status:** DECISION SUPPORT SCREENING OUTPUT -- Requires Official Verification  

---

> **IMPORTANT DISCLAIMER**
>
> This report presents population exposure screening based on the current
> **Candidate Hazard-Based Red Zone** layer (Step 7 output).
>
> These results are **NOT**:
> - Evacuation orders
> - Disaster predictions
> - Mandatory relocation recommendations
> - Engineering safety certifications
> - Official government hazard zone declarations
>
> All outputs require official verification and geotechnical assessment
> before any administrative action.

---

## Step 7 Red Zone Input Summary

| Parameter | Value |
|-----------|-------|
| File | `data\outputs\candidate_hazard_based_red_zones.geojson` |
| Feature count | 289 |
| Geometry type | Polygon / MultiPolygon |
| CRS | EPSG:32644 |
| Zone label | Candidate Hazard-Based Red Zone |

---

## Habitation Baseline Summary

| Parameter | Value |
|-----------|-------|
| File | `data\processed\habitations\habitation_baseline.geojson` |
| Feature count | 653 |
| Geometry type | Point (village centroids) |
| CRS | EPSG:32644 |
| Source | Census PCA 2011 joined to SHRUG spatial bridge |

---

## Spatial Operation

| Parameter | Detail |
|-----------|--------|
| Method | Point-in-Polygon spatial join (GeoPandas sjoin) |
| Predicate | `within` (habitation centroid falls inside red zone polygon) |
| Both layers in metric CRS | EPSG:32644 (UTM Zone 44N) |
| Overlay type | Left join (all habitations retained) |

---

## Exposure Results

### Habitation Records

| Metric | Count | Percentage |
|--------|-------|------------|
| Total habitation records | 653 | 100.0% |
| Inside Candidate Hazard-Based Red Zone | 0 | 0.0% |
| Outside Candidate Hazard-Based Red Zone | 653 | 100.0% |

### Population Exposure

| Metric | Value | Percentage |
|--------|-------|------------|
| Total population (Census PCA 2011) | 232,360 | 100.0% |
| Population inside Candidate Red Zones | 0 | 0.0% |
| Population outside Candidate Red Zones | 232,360 | 100.0% |

### Household Exposure

| Metric | Value | Percentage |
|--------|-------|------------|
| Total households (Census PCA 2011) | 50,882 | 100.0% |
| Households inside Candidate Red Zones | 0 | 0.0% |
| Households outside Candidate Red Zones | 50,882 | 100.0% |

### SC Population Exposure

| Metric | Value | Percentage |
|--------|-------|------------|
| Total SC population | 46,279 | 100.0% |
| SC population inside Candidate Red Zones | 0 | 0.0% |
| SC population outside Candidate Red Zones | 46,279 | 100.0% |

### ST Population Exposure

| Metric | Value | Percentage |
|--------|-------|------------|
| Total ST population | 309 | 100.0% |
| ST population inside Candidate Red Zones | 0 | 0.0% |
| ST population outside Candidate Red Zones | 309 | 100.0% |

---

## Proximity Context: Distance to Nearest Candidate Red Zone

> **Methodological Note on the 0-Inside Result**
>
> No village centroids fall **inside** a Candidate Hazard-Based Red Zone polygon.
> This is a **geographically valid and expected result**, not a pipeline error.
>
> Explanation:
> - SHRUG village centroids represent the **administrative village boundary centroid**,
>   not precise building or household locations.
> - Candidate Hazard-Based Red Zones are **small terrain-derived patches** (avg area ~7,721 m2)
>   derived from steep/wet raster cells, which tend to occupy ridge flanks and
>   valley corridor areas -- not village administrative centres.
> - The 289 red zones cover a **total of ~223 ha** across a large mountainous district.
>
> The distance-to-nearest-red-zone field (`dist_to_nearest_redzone_m`) provides
> critical proximity context for decision-makers.

### Distance from Village Centroid to Nearest Candidate Red Zone

| Metric | Value |
|--------|-------|
| Minimum distance (closest village) | 42.5 m |
| Maximum distance | 16712.2 m |
| Mean distance | 6212.8 m |

### Proximity Band Breakdown

| Distance Band | Habitation Count | Percentage |
|---------------|-----------------|------------|
| < 500 m | 14 | 2.1% |
| 500 m -- 1,000 m | 16 | 2.5% |
| 1,000 m -- 2,000 m | 51 | 7.8% |
| 2,000 m -- 5,000 m | 204 | 31.2% |
| > 5,000 m | 368 | 56.4% |

**NOTE:** Proximity does not equal exposure. A village centroid being close to
a red zone boundary does not mean the village area is inside the red zone.
Field verification and site-level geotechnical assessment is required.

---

## Validation Cross-Checks

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Exposure records = baseline records | 653 | 653 | PASS |
| Inside pop + outside pop = total pop | 232,360 | 232,360 | PASS |
| Inside HH + outside HH = total HH | 50,882 | 50,882 | PASS |
| Inside SC + outside SC = total SC | 46,279 | 46,279 | PASS |
| Inside ST + outside ST = total ST | 309 | 309 | PASS |
| CRS consistency | EPSG:32644 | EPSG:32644 | PASS |

---

## Output Files

| File | Description |
|------|-------------|
| `data\processed\exposure\habitation_exposure.geojson` | Habitation exposure layer (GeoJSON, EPSG:32644) |
| `data\processed\exposure\habitation_exposure_summary.csv` | Exposure summary table (CSV) |
| `docs\step8_habitation_exposure_report.md` | This report |

---

## Hazard Zone Flag Definition

| Field | Value | Meaning |
|-------|-------|---------|
| `hazard_zone_flag` | `1` | Inside Candidate Hazard-Based Red Zone |
| `hazard_zone_flag` | `0` | Outside Candidate Hazard-Based Red Zone |

**These flags do NOT indicate safe or unsafe status.**
**They represent preliminary spatial screening only.**

---

*This report is a decision-support output of the SIH26191 GIS pipeline.*
*Official administrative action requires verification by competent geotechnical*
*and disaster management authorities.*