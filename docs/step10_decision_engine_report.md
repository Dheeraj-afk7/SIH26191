# Step 10 — Decision Engine, Priority & Standardized Outputs

**Generated (UTC):** 2026-08-29T06:41:59Z  
**Project:** SIH26191 — Rudraprayag District, Uttarakhand  
**Pipeline Version:** 1.0  
**Status:** DECISION SUPPORT SCREENING OUTPUT — Requires Official Verification
**Validation:** STEP 10 COMPLETE — 73 PASS, 0 NON-BLOCKING WARNING, 0 FAIL

---

## 1. Mandatory Decision-Support Disclaimer

> **MANDATORY DISCLAIMER**
>
> These outputs are PRELIMINARY DECISION-SUPPORT SCREENING RESULTS and do NOT
> constitute: official government relocation priority designations, engineering-
> certified hazard assessments, evacuation orders, mandatory relocation instructions,
> or official government Red Zone declarations.
>
> All outputs require official government review, field verification, and geotechnical
> assessment before any administrative action is taken.

---

## 2. Executive Summary

| Metric | Value |
|--------|-------|
| Total habitations | **653** |
| Total population | **232,360** |
| Total households | **50,882** |
| Candidate areas (Step 9) | **5** |
| Total candidate terrain | **361,307.9 ha** |
| Capacity status | **NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD** |

---

## 3. Classification Methodology

**Method:** Rule-based proximity × multi-hazard class classification  
**Primary dimension:** `nearest_hazard_distance_m` — Euclidean distance to nearest Candidate Hazard-Based Red Zone (Step 8)  
**Secondary dimension:** `mh_class_at_centroid` — Multi-Hazard Class at village centroid (sampled from Step 6 raster)  
**Hard flag:** `direct_zone_overlap` — centroid inside red zone polygon always assigns Tier 1  
**Thresholds:** Loaded from `configs/priority_thresholds.yaml`  

> **No AHP weights, MCDA weights, or composite vulnerability scores applied.**  
> Vulnerability indicators (literacy, SC/ST, children, non-workers) are included as CONTEXT FIELDS only.

### Tier Definitions

| Tier | Rule | Description |
|------|------|-------------|
| Tier 1 — Attention Priority | dist ≤ 500 m AND mh_class ≥ 2; OR direct overlap | Very close proximity + moderate-higher hazard class |
| Tier 2 — Elevated Attention | dist ≤ 2,000 m | Within elevated attention proximity |
| Tier 3 — Monitoring | dist ≤ 5,000 m | Within monitoring proximity band |
| Beyond Proximity | dist > 5,000 m | Outside monitoring proximity threshold |

---

## 4. Village Priority Distribution

| Tier | Villages | % | Population | Households |
|------|----------|---|------------|------------|
| Tier 1 — Attention Priority | 12 | 1.8% | 4,750 | 977 |
| Tier 2 — Elevated Attention | 69 | 10.6% | 23,012 | 4,674 |
| Tier 3 — Monitoring | 204 | 31.2% | 64,463 | 13,978 |
| Beyond Proximity — Lower Attention | 368 | 56.4% | 140,135 | 31,253 |

---

## 5. Tier 1 — Attention Priority Villages

| Village ID | Village Name | Distance to Red Zone | MH Class | Population | Households |
|------------|-------------|----------------------|----------|------------|------------|
| 42573 | Marora | 42 m | 2.0 | 208 | 49 |
| 42067 | Tarsali | 178 m | 2.0 | 98 | 20 |
| 42165 | Dungar semala | 311 m | 2.0 | 580 | 110 |
| 42320 | Narkota | 322 m | 2.0 | 357 | 83 |
| 42129 | Gadagu | 330 m | 2.0 | 601 | 117 |
| 42080 | Jaltalla | 349 m | 2.0 | 373 | 79 |
| 42086 | Kabiltha | 350 m | 2.0 | 341 | 62 |
| 42127 | Burua | 411 m | 2.0 | 386 | 71 |
| 42128 | Madali | 425 m | 2.0 | 5 | 2 |
| 42058 | Gaurikund | 469 m | 2.0 | 223 | 43 |
| 42118 | Gaundar | 486 m | 2.0 | 294 | 45 |
| 42574 | Mawana | 498 m | 2.0 | 1,284 | 296 |


> Village centroids are administrative reference points, NOT building footprints.
> Actual settlement extents may differ. Field verification is mandatory.

---

## 6. Vulnerability Indicators (Context Only)

The following indicators are derived from Census PCA 2011.  
**They are NOT used in tier assignment. No composite weight is applied.**

| Indicator | Mean | Min | Max | Valid Count |
|-----------|------|-----|-----|-------------|
| Illiteracy rate | 0.296 | 0.000 | 0.889 | 653 |
| Children 0–6 proportion | 0.127 | 0.000 | 0.375 | 653 |
| SC population proportion | 0.146 | 0.000 | 1.000 | 653 |
| ST population proportion | 0.001 | 0.000 | 0.125 | 653 |
| Non-worker proportion | 0.525 | 0.000 | 1.000 | 653 |

---

## 7. Candidate Topographically Feasible Areas (Context)

| Area ID | Area | Mean Slope | Dist to Red Zone | Nearest Village | Capacity Status |
|---------|------|------------|-----------------|----------------|-----------------|
| CA-0001 | 361,306.8 ha | 30.9° | 3250 m | Lamgondi | NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD |
| CA-0002 | 0.9 ha | 1.8° | 837 m | Gaundar | NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD |
| CA-0003 | 0.1 ha | 1.8° | 2339 m | Garuriya | NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD |
| CA-0004 | 0.1 ha | 54.6° | 15 m | Gaundar | NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD |
| CA-0005 | 0.1 ha | 0.0° | 14543 m | Chantikhal | NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD |


> **IMPORTANT:** CA-0001 covers ~361,307 ha (virtually all non-excluded terrain in the district).
> This is because configurable screening filters (slope threshold, minimum mapping unit) are
> NOT_CONFIGURED in `configs/project.yaml`.
> 
> **CA-0001 is a Preliminary unfiltered topographically feasible terrain extent — requires additional screening and field verification.**
> It must NOT be described as a relocation site, safe site, approved site, recommended site, or a discrete candidate site.
>
> **No Village → Candidate Area allocation has been generated.**
> No verified allocation methodology exists for this project.

---

## 8. Capacity Status

**Status:** `NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD`

No area-per-household or area-per-person planning standard has been provided.
Configure `configs/capacity.yaml` with a verified authority citation before
computing capacity estimates.

---

## 9. Missing / Blocked Indicators

| Indicator / Dataset | Status | Impact |
|--------------------|--------|--------|
| Historical disaster evidence (NDMA/SDMA/EM-DAT) | NOT ACQUIRED | Cannot confirm Tier 1 per spec (disaster history component absent) |
| Infrastructure vulnerability (schools, health centres) | NOT ACQUIRED | Infrastructure context not scored |
| Road accessibility | NOT ACQUIRED | Candidate area accessibility not assessable |
| LULC / forest cover | NOT ACQUIRED | Forest/protected area status of candidate areas unknown |
| Capacity planning standard | NOT CONFIGURED | No capacity estimate generated |
| Slope threshold for candidate areas | NOT_CONFIGURED | All slope gradients present in candidate areas |
| Minimum mapping unit for candidate areas | NOT_CONFIGURED | Very small and very large areas all retained |

---

## 10. Output Files

| File | Step | Purpose |
|------|------|---------|
| `data/processed/decision/village_priority_indicators.gpkg` | 10B | Vulnerability indicators attributed to all villages |
| `data/processed/decision/village_priority_profiles.gpkg` | 10C | Priority tier classification + all indicators |
| `data/processed/decision/candidate_area_context.gpkg` | 10D | Candidate areas with contextual descriptors |
| `data/processed/decision/decision_summary.json` | 10E | District-level summary statistics |
| `data/processed/decision/decision_metadata.json` | 10E | Processing provenance and methodology log |
| `docs/step10_decision_engine_report.md` | 10E | This report |

---

## 11. Scientific Limitations

1. **No disaster history** — Tier 1 cannot be confirmed by historical evidence.
2. **No infrastructure data** — Infrastructure vulnerability not scored.
3. **No road network** — Candidate area accessibility not determined.
4. **No LULC** — Forest / protected area status of candidate terrain unknown.
5. **Centroid-based proximity** — Village centroids are administrative reference points. Settlement extents may be closer to hazard terrain than centroid distances indicate.
6. **Equal-weight MH formula** — Terrain (0.5) + Flood (0.5) is an unvalidated baseline assumption.
7. **Census 2011 data** — Population data is approximately 15 years old.
8. **30m DEM resolution** — All spatial outputs limited to ~30m precision.
9. **CA-0001 = 361,307 ha** — Candidate area output is not yet meaningfully segmented.
10. **No capacity estimate** — Carrying capacity not computed.

---

*This report is a decision-support output of the SIH26191 GIS pipeline.*  
*Official administrative action requires verification by competent geotechnical*  
*and disaster management authorities.*
