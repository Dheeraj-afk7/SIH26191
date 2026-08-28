# Step 8D -- Habitation Baseline Validation Report

**Generated:** 2026-08-28T20:20:28Z  
**Project:** SIH26191 -- Rudraprayag District, Uttarakhand  
**File validated:** `data\processed\habitations\habitation_baseline.geojson`  

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Feature count | 653 |
| CRS | EPSG:32644 |
| Total population | 232,360 |
| Total households | 50,882 |
| SC population | 46,279 |
| ST population | 309 |
| Population coverage vs Census inhabited | 100.00% |

---

## Validation Checks

| # | Check | Status | Detail |
|---|-------|--------|--------|
| 1 | File exists | PASS | data\processed\habitations\habitation_baseline.geojson |
| 2 | CRS matches configured metric CRS | PASS | Actual: EPSG:32644 | Expected: EPSG:32644 |
| 3 | Feature count | PASS | Actual: 653 | Expected: 653 |
| 4 | No duplicate village_id | PASS | Duplicate count: 0 |
| 5 | No null geometries | PASS | Null geometry count: 0 |
| 6 | No null demographic fields | PASS | Nulls: households=0, tot_pop=0, pop_male=0, pop_female=0, pop_sc=0, pop_st=0 |
| 7 | No negative tot_pop | PASS | Negative population count: 0 |
| 8 | Population sum matches Census inhabited total | PASS | Baseline: 232,360 | Census inhabited: 232,360 |
| 9 | Household sum matches Census inhabited total | PASS | Baseline: 50,882 | Census inhabited: 50,882 |
| 10 | SC population matches Census | PASS | Baseline: 46,279 | Census: 46,279 |
| 11 | ST population matches Census | PASS | Baseline: 309 | Census: 309 |
| 12 | Population coverage >= 100% | PASS | 100.00% |
| 13 | SC population within total population | PASS |  |
| 14 | ST population within total population | PASS |  |

---

## Overall Status: **PASS**

> All validation checks passed.
> Proceed to Phase 8E: Hazard Exposure Overlay.

---

## Reference: Census Cross-Check Totals

| Metric | Census (inhabited) | Baseline |
|--------|-------------------|----------|
| Inhabited village records | 653 | 653 |
| Total population | 232,360 | 232,360 |
| Total households | 50,882 | 50,882 |
| SC population | 46,279 | 46,279 |
| ST population | 309 | 309 |

---

*This document is a decision-support output of the SIH26191 pipeline.*
*It does not constitute an official hazard zone declaration, evacuation order,*
*safety certification, or relocation authorization.*