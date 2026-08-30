# Step 9 — Candidate Topographically Feasible Area Identification Report

**Generated (UTC):** 2026-08-30T07:09:30Z  
**Project:** SIH26191 — Rudraprayag District, Uttarakhand  
**Pipeline Version:** 1.0  
**Status:** DECISION SUPPORT SCREENING OUTPUT — Requires Official Verification

---

## 1. Mandatory Decision-Support Disclaimer

> **MANDATORY DISCLAIMER**
>
> Preliminary decision-support candidate requiring field verification. Not an official site authorization or safety certification. Geotechnical and infrastructure assessment required before any relocation action.

---

## 2. Executive Summary

Step 9 applied a deterministic terrain-based screening pipeline to identify
**Candidate Topographically Feasible Areas** across Rudraprayag District.
All configurable screening parameters were set to `null` (NOT CONFIGURED) and
were explicitly skipped. Only deterministic exclusions based on the verified
Step 4–7 pipeline outputs were applied.

| Metric | Value |
|--------|-------|
| Candidate area features (9B base) | **5,991** |
| Total candidate terrain area | **16,342.3 ha** |
| Largest single candidate area | **10.0 ha** |
| Smallest single candidate area | **10,166 m²** |
| Pixel area | 847.15 m² (29.11 m × 29.11 m) |
| CRS | EPSG:32644 (WGS 84 / UTM Zone 44N) |
| Step 9C attribution | Completed |
| Demographic attribution | AVAILABLE (Census PCA 2011) |

---

## 3. Applied vs Skipped Screening Parameters

| Parameter | Value / Status | Classification |
|-----------|---------------|----------------|
| `exclude_mh_class_3` | APPLIED: 7746 pixels excluded | APPLIED |
| `exclude_flood_class_3` | APPLIED: 124137 pixels excluded | APPLIED |
| `exclude_redzone_pixels` | APPLIED: 2634 pixels excluded | APPLIED |
| `exclude_nodata` | APPLIED: 164415 pixels excluded | APPLIED |
| `slope_max_deg` | APPLIED: 20.0 deg, 3548200 pixels excluded | APPLIED |
| `redzone_buffer_m` | NOT_CONFIGURED | NOT_CONFIGURED |
| `exclude_flood_class_2` | NOT_CONFIGURED | NOT_CONFIGURED |
| `exclude_mh_class_2` | NOT_CONFIGURED | NOT_CONFIGURED |
| `elevation_max_m` | NOT_CONFIGURED | NOT_CONFIGURED |
| `minimum_area_m2` | APPLIED: 10000.0 m2 | APPLIED |
| `maximum_area_m2` | APPLIED: 100000.0 m2 | APPLIED |

---

## 4. Deterministic Exclusions Applied

The following exclusions were always applied regardless of configurable parameters:

| Exclusion | Basis | Source Layer |
|-----------|-------|-------------|
| Multi-Hazard Class 3 (Higher) | Internally consistent with Step 7 red zone generation | `multihazard_classes.tif` |
| Flood Exposure Class 3 (Higher) | TWI ≥ 10.0 (valley bottoms, drainage confluences) | `flood_exposure_classes.tif` |
| Step 7 Candidate Red Zone pixels | Pixels already in candidate hazard-based red zones | `candidate_redzone_raster.tif` |
| NoData pixels | Any pixel where required inputs have NoData | All required rasters |

---

## 5. Habitation Demographics Check

**Status:** `DEMOGRAPHIC_ATTRIBUTION_AVAILABLE: Exact code-based Census 2011 PCA join confirmed.`  
**nearest_village_pop included:** Yes  

The habitation dataset (`habitation_exposure.geojson`) was inspected before Step 9C.
Geometry source: SHRUG v2.2 spatial centroids (Development Data Lab).
Join method: Exact integer code match (Census Town/Village = SHRUG pc11_village_id).
Village centroid points represent administrative reference locations, NOT building footprints.
Proximity calculations are centroid-to-centroid Euclidean distances in EPSG:32644.

---

## 6. Output Files

| File | Step | Purpose |
|------|------|---------|
| `data/processed/sites/combined_exclusion_mask.tif` | 9A | Combined exclusion mask (0=candidate, 1=excluded, 255=NoData) |
| `data/processed/sites/candidate_area_raster.tif` | 9B | Labeled cluster raster (cluster_id per pixel, 0=background) |
| `data/outputs/candidate_topographically_feasible_areas_base.gpkg` | 9B | Base vector output (no attribution) |
| `data/outputs/candidate_topographically_feasible_areas_base.geojson` | 9B | Base GeoJSON |
| `data/outputs/candidate_topographically_feasible_areas_attributed.gpkg` | 9C | Attributed vector (zonal stats + proximity) |
| `data/outputs/candidate_topographically_feasible_areas_attributed.geojson` | 9C | Attributed GeoJSON |
| `data/outputs/candidate_areas_metadata.json` | 9A-9C | Processing metadata and parameter log |
| `docs/step9_candidate_areas_report.md` | 9A-9C | This report |

---

## 7. Major Limitations

1. **No slope screening applied** (`slope_max_deg = null`). All slope gradients that are not excluded by MH/Flood Class 3 remain as candidate terrain. Field surveys must assess actual slope suitability.
2. **No road accessibility screening** (roads dataset not acquired). Candidate areas may be topographically suitable but logistically inaccessible.
3. **No LULC / forest exclusion** (dataset not acquired). Candidate areas may include forest land, protected areas, or agricultural land.
4. **No river buffer exclusion** (river network dataset not acquired). TWI-based flood Class 3 exclusion is a partial proxy only.
5. **No minimum mapping unit filter** (`minimum_area_m2 = null`). All contiguous clusters are retained including very small areas potentially unsuitable for habitation.
6. **30 m DEM resolution** limits spatial precision. Candidate area boundaries are indicative at approximately 30 m scale.
7. **Village centroids are administrative reference points**, not building footprints. Proximity distances are Euclidean, not routable path distances.
8. **This output does NOT replace field surveys**, geotechnical assessment, legal land-use review, or government authorization.

---

*This report is a decision-support output of the SIH26191 GIS pipeline.*
*Official administrative action requires verification by competent geotechnical*
*and disaster management authorities.*
