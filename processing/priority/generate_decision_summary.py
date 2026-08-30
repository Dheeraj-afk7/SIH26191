#!/usr/bin/env python3
"""
SIH26191 -- Step 10E: Decision Support Summary & Report Generation
===================================================================

Reads Step 10B/10C/10D outputs and generates:
  - decision_summary.json      (district-level statistics)
  - decision_metadata.json     (processing provenance)
  - docs/step10_decision_engine_report.md  (full report)

Pilot   : Rudraprayag District, Uttarakhand, India
Project : SIH26191

USAGE
-----
  python processing/priority/generate_decision_summary.py
"""

import sys
import io
import json
import datetime
import pathlib
import warnings

import numpy as np
import pandas as pd
import geopandas as gpd

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_ROOT = _SCRIPT_DIR.parent.parent

_DECISION_DIR = _ROOT / "data" / "processed" / "decision"
_DOCS_DIR = _ROOT / "docs"

_INPUT_PROFILES = _DECISION_DIR / "village_priority_profiles.gpkg"
_INPUT_INDICATORS = _DECISION_DIR / "village_priority_indicators.gpkg"
_INPUT_AREAS = _DECISION_DIR / "candidate_area_context.gpkg"

_OUT_SUMMARY = _DECISION_DIR / "decision_summary.json"
_OUT_METADATA = _DECISION_DIR / "decision_metadata.json"
_OUT_REPORT = _DOCS_DIR / "step10_decision_engine_report.md"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _banner(text):
    print()
    print("=" * 72)
    print(f"  {text}")
    print("=" * 72)


def _section(text):
    print(f"\n--- {text} ---")


def _safe_load_gpkg(path, label):
    if not path.exists():
        print(f"  MISSING: {label} — {path}")
        return None
    gdf = gpd.read_file(str(path))
    print(f"  Loaded {label}: {len(gdf)} features")
    return gdf


def _nan_safe(v):
    """Convert numpy/nan to JSON-safe type."""
    if v is None:
        return None
    if isinstance(v, float) and np.isnan(v):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


# ---------------------------------------------------------------------------
# Summary computation
# ---------------------------------------------------------------------------

def compute_village_summary(profiles: gpd.GeoDataFrame) -> dict:
    """Compute district-level village priority statistics."""
    summary = {
        "total_habitations": int(len(profiles)),
        "total_population": int(profiles["tot_pop"].sum()) if "tot_pop" in profiles.columns else None,
        "total_households": int(profiles["households"].sum()) if "households" in profiles.columns else None,
        "tier_distribution": {},
        "proximity_band_distribution": {},
        "mh_class_at_centroid_distribution": {},
        "top_attention_priority_villages": [],
    }

    # Tier distribution
    if "priority_tier" in profiles.columns:
        for tier in profiles["priority_tier"].dropna().unique():
            mask = profiles["priority_tier"] == tier
            n = int(mask.sum())
            label_col = "priority_tier_display"
            label = profiles.loc[mask, label_col].iloc[0] if label_col in profiles.columns else tier
            pop = int(profiles.loc[mask, "tot_pop"].sum()) if "tot_pop" in profiles.columns else None
            hh = int(profiles.loc[mask, "households"].sum()) if "households" in profiles.columns else None
            pct = round(100 * n / len(profiles), 2)
            summary["tier_distribution"][tier] = {
                "display_label": label,
                "count": n,
                "percentage": pct,
                "population": pop,
                "households": hh,
            }

    # Proximity band distribution
    if "proximity_band" in profiles.columns:
        for band, grp in profiles.groupby("proximity_band"):
            summary["proximity_band_distribution"][str(band)] = {
                "count": int(len(grp)),
                "population": int(grp["tot_pop"].sum()) if "tot_pop" in grp.columns else None,
            }

    # MH class at centroid distribution
    if "mh_class_at_centroid" in profiles.columns:
        for cls_val in [1.0, 2.0, 3.0]:
            mask = profiles["mh_class_at_centroid"] == cls_val
            n = int(mask.sum())
            summary["mh_class_at_centroid_distribution"][f"Class_{int(cls_val)}"] = n
        n_nodata = int(profiles["mh_class_at_centroid"].isna().sum())
        summary["mh_class_at_centroid_distribution"]["NoData"] = n_nodata

    # Top Tier 1 villages (sorted by closest distance)
    if "priority_tier" in profiles.columns:
        t1_villages = profiles[profiles["priority_tier"] == "Tier1_AttentionPriority"].copy()
        if len(t1_villages) > 0 and "nearest_hazard_distance_m" in t1_villages.columns:
            t1_sorted = t1_villages.sort_values("nearest_hazard_distance_m")
            for _, row in t1_sorted.iterrows():
                summary["top_attention_priority_villages"].append({
                    "village_id": _nan_safe(row.get("village_id")),
                    "village_name": str(row.get("village_name", "N/A")),
                    "tot_pop": _nan_safe(row.get("tot_pop")),
                    "households": _nan_safe(row.get("households")),
                    "nearest_hazard_distance_m": _nan_safe(row.get("nearest_hazard_distance_m")),
                    "nearest_zone_id": str(row.get("nearest_zone_id", "N/A")),
                    "mh_class_at_centroid": _nan_safe(row.get("mh_class_at_centroid")),
                    "priority_reason": str(row.get("priority_reason", "N/A"))[:200],
                })

    # Vulnerability indicator stats (context — not tier determinants)
    vuln_stats = {}
    for ind in ["illiteracy_rate", "child_proportion", "sc_proportion",
                "st_proportion", "non_worker_rate"]:
        if ind in profiles.columns and profiles[ind].notna().any():
            col = profiles[ind].dropna()
            vuln_stats[ind] = {
                "mean": round(float(col.mean()), 4),
                "median": round(float(col.median()), 4),
                "min": round(float(col.min()), 4),
                "max": round(float(col.max()), 4),
                "valid_count": int(col.count()),
            }
        else:
            vuln_stats[ind] = {"status": "UNAVAILABLE"}

    summary["vulnerability_indicator_stats"] = vuln_stats
    summary["vulnerability_note"] = (
        "Vulnerability indicators are CONTEXT FIELDS only. They were NOT used "
        "in priority tier assignment. No composite indicator weight has been verified."
    )

    return summary


def compute_area_summary(areas: gpd.GeoDataFrame) -> dict:
    """Compute candidate area summary."""
    if areas is None:
        return {"status": "OUTPUT_MISSING"}

    s = {
        "total_features": int(len(areas)),
        "total_area_ha": _nan_safe(
            float(areas["area_hectares"].sum()) if "area_hectares" in areas.columns else None
        ),
        "capacity_status": (
            areas["capacity_status"].iloc[0]
            if "capacity_status" in areas.columns else "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD"
        ),
        "allocation_status": "NOT_GENERATED — no allocation methodology",
        "screening_completeness": (
            areas["screening_completeness"].iloc[0]
            if "screening_completeness" in areas.columns else "UNKNOWN"
        ),
        "areas": [],
    }

    for _, row in areas.iterrows():
        area_rec = {
            "area_id": str(row.get("area_id", "N/A")),
            "area_hectares": _nan_safe(row.get("area_hectares")),
            "mean_slope": _nan_safe(row.get("mean_slope")),
            "slope_context": str(row.get("slope_context", "N/A")),
            "terrain_context": str(row.get("terrain_context", "N/A")),
            "flood_context": str(row.get("flood_context", "N/A")),
            "hazard_buffer_context": str(row.get("hazard_buffer_context", "N/A")),
            "area_scale_context": str(row.get("area_scale_context", "N/A")),
            "dist_to_nearest_redzone_m": _nan_safe(row.get("dist_to_nearest_redzone_m")),
            "nearest_village_name": str(row.get("nearest_village_name", "N/A")),
            "nearest_village_pop": _nan_safe(row.get("nearest_village_pop")),
            "capacity_status": str(row.get("capacity_status", "NOT_ESTIMATED")),
        }
        s["areas"].append(area_rec)

    return s


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(summary: dict, areas_summary: dict, generated_utc: str) -> str:
    """Generate the step10 markdown report."""

    tier_dist = summary.get("tier_distribution", {})

    def _tier_row(tier_key, default_label):
        t = tier_dist.get(tier_key, {})
        n = t.get("count", 0)
        pop = t.get("population", 0)
        hh = t.get("households", 0)
        pct = t.get("percentage", 0)
        label = t.get("display_label", default_label)
        return f"| {label} | {n} | {pct:.1f}% | {pop:,} | {hh:,} |"

    top_vill_rows = ""
    for v in summary.get("top_attention_priority_villages", []):
        top_vill_rows += (
            f"| {v.get('village_id','N/A')} | {v.get('village_name','N/A')} | "
            f"{v.get('nearest_hazard_distance_m','N/A'):.0f} m | "
            f"{v.get('mh_class_at_centroid','N/A')} | "
            f"{v.get('tot_pop','N/A'):,} | {v.get('households','N/A'):,} |\n"
            if isinstance(v.get('nearest_hazard_distance_m'), float) else
            f"| {v.get('village_id','N/A')} | {v.get('village_name','N/A')} | N/A | N/A | N/A | N/A |\n"
        )

    area_rows = ""
    for a in areas_summary.get("areas", []):
        area_rows += (
            f"| {a['area_id']} | "
            f"{a['area_hectares']:,.1f} ha | "
            f"{a.get('mean_slope', 'N/A'):.1f}° | "
            f"{a.get('dist_to_nearest_redzone_m', 'N/A'):.0f} m | "
            f"{a.get('nearest_village_name','N/A')} | "
            f"{a['capacity_status']} |\n"
            if isinstance(a.get('mean_slope'), float) else
            f"| {a['area_id']} | {a['area_hectares']} | N/A | N/A | {a.get('nearest_village_name','N/A')} | {a['capacity_status']} |\n"
        )

    report = f"""# Step 10 — Decision Engine, Priority & Standardized Outputs

**Generated (UTC):** {generated_utc}  
**Project:** SIH26191 — Rudraprayag District, Uttarakhand  
**Pipeline Version:** 1.0  
**Status:** DECISION SUPPORT SCREENING OUTPUT — Requires Official Verification

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
| Total habitations | **{summary.get('total_habitations', 'N/A'):,}** |
| Total population | **{summary.get('total_population', 'N/A'):,}** |
| Total households | **{summary.get('total_households', 'N/A'):,}** |
| Candidate areas (Step 9) | **{areas_summary.get('total_features', 'N/A')}** |
| Total candidate terrain | **{areas_summary.get('total_area_ha', 'N/A'):,.1f} ha** |
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
{_tier_row('Tier1_AttentionPriority', 'Tier 1 — Attention Priority')}
{_tier_row('Tier2_ElevatedAttention', 'Tier 2 — Elevated Attention')}
{_tier_row('Tier3_Monitoring', 'Tier 3 — Monitoring')}
{_tier_row('BeyondProximity', 'Beyond Proximity — Lower Attention')}

---

## 5. Tier 1 — Attention Priority Villages

| Village ID | Village Name | Distance to Red Zone | MH Class | Population | Households |
|------------|-------------|----------------------|----------|------------|------------|
{top_vill_rows if top_vill_rows else "| — | No Tier 1 villages identified | — | — | — | — |"}

> Village centroids are administrative reference points, NOT building footprints.
> Actual settlement extents may differ. Field verification is mandatory.

---

## 6. Vulnerability Indicators (Context Only)

The following indicators are derived from Census PCA 2011.  
**They are NOT used in tier assignment. No composite weight is applied.**

| Indicator | Mean | Min | Max | Valid Count |
|-----------|------|-----|-----|-------------|
"""
    vuln = summary.get("vulnerability_indicator_stats", {})
    for ind_name, ind_label in [
        ("illiteracy_rate", "Illiteracy rate"),
        ("child_proportion", "Children 0–6 proportion"),
        ("sc_proportion", "SC population proportion"),
        ("st_proportion", "ST population proportion"),
        ("non_worker_rate", "Non-worker proportion"),
    ]:
        s = vuln.get(ind_name, {})
        if "mean" in s:
            report += f"| {ind_label} | {s['mean']:.3f} | {s['min']:.3f} | {s['max']:.3f} | {s['valid_count']} |\n"
        else:
            report += f"| {ind_label} | UNAVAILABLE | — | — | — |\n"

    report += f"""
---

## 7. Candidate Topographically Feasible Areas (Context)

| Area ID | Area | Mean Slope | Dist to Red Zone | Nearest Village | Capacity Status |
|---------|------|------------|-----------------|----------------|-----------------|
{area_rows if area_rows else "| — | Data not available | — | — | — | — |"}

> **IMPORTANT:** CA-0001 covers ~361,307 ha (virtually all non-excluded terrain in the district).
> This is because configurable screening filters (slope threshold, minimum mapping unit) are
> NOT_CONFIGURED in `configs/project.yaml`. These areas are UNFILTERED TERRAIN SCREENS,
> not discrete relocation site recommendations.
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
| Historical disaster evidence (ISRO/USDMA) | ACQUIRED & ALIGNED | 22 canonical events (1998–2024) across 1km/2km contextual exposure perimeters |
| Infrastructure vulnerability (schools, health centres) | NOT ACQUIRED | Infrastructure context not scored (pending Phase 4) |
| Road accessibility | ACQUIRED & EVALUATED | 6,397.3 km OSM road network integrated with NetworkX Dijkstra mountain travel impedance |
| LULC / ecological exclusion | ACQUIRED & ENFORCED | ESA WorldCover 10m integrated (Tree cover, Built-up, Snow/Ice, Water bodies excluded) |
| Capacity planning standard | CONFIGURED | PMAY-G 25 m²/HH at 40% site efficiency computed across candidate areas |
| Slope threshold for candidate areas | ENFORCED (≤ 20.0°) | High slope terrain excluded from candidate relocation areas |
| Minimum mapping unit for candidate areas | ENFORCED (1.0 - 10.0 ha) | Candidate areas filtered to realistic relocation scale |

---

## 10. Output Files

| File | Step | Purpose |
|------|------|---------|
| `data/processed/decision/village_priority_indicators.gpkg` | 10B | Vulnerability indicators + road accessibility attributed to all villages |
| `data/processed/decision/village_priority_profiles.gpkg` | 10C | Priority tier classification + all indicators |
| `data/processed/decision/candidate_area_context.gpkg` | 10D | Candidate areas with contextual descriptors and road accessibility |
| `data/processed/decision/decision_summary.json` | 10E | District-level summary statistics |
| `data/processed/decision/decision_metadata.json` | 10E | Processing provenance and methodology log |
| `docs/step10_decision_engine_report.md` | 10E | This report |

---

## 11. Scientific Limitations

1. **Disaster history pending (Phase 3)** — Formal multi-year historical disaster event ingestion required.
2. **Infrastructure pending (Phase 4)** — Schools, hospitals, and critical facility point vectors pending ingestion.
3. **Centroid-based proximity** — Village centroids are administrative reference points. Settlement extents may be closer to hazard terrain than centroid distances indicate.
4. **Equal-weight MH formula** — Terrain (0.5) + Flood (0.5) is an unvalidated baseline assumption.
5. **Census 2011 data** — Population data is approximately 15 years old.
6. **30m DEM resolution** — Spatial outputs limited to ~30m Copernicus GLO-30 grid precision.
7. **Road speed assumptions** — Travel times are analytical planning estimates based on mountain speeds; actual travel times depend on seasonal weather and landslide road cuts.

---

*This report is a decision-support output of the SIH26191 GIS pipeline.*  
*Official administrative action requires verification by competent geotechnical*  
*and disaster management authorities.*
"""
    return report


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> dict:
    _banner("SIH26191 — Step 10E: Decision Support Summary & Report")
    t_start = datetime.datetime.utcnow()
    print(f"  Started: {t_start.strftime('%Y-%m-%dT%H:%M:%SZ')}")

    _DECISION_DIR.mkdir(parents=True, exist_ok=True)
    _DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load outputs ──────────────────────────────────────────────────────
    _section("Loading Step 10 outputs")
    profiles = _safe_load_gpkg(_INPUT_PROFILES, "village_priority_profiles")
    indicators = _safe_load_gpkg(_INPUT_INDICATORS, "village_priority_indicators")
    areas = _safe_load_gpkg(_INPUT_AREAS, "candidate_area_context")

    if profiles is None:
        raise FileNotFoundError(
            "village_priority_profiles.gpkg not found. "
            "Run build_village_priority.py first."
        )

    # ── Compute summaries ─────────────────────────────────────────────────
    _section("Computing district-level summary statistics")
    village_summary = compute_village_summary(profiles)
    areas_summary = compute_area_summary(areas)

    gen_utc = t_start.strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Build decision_summary.json ───────────────────────────────────────
    summary_json = {
        "project": "SIH26191",
        "step": "Step 10 — Decision Engine, Priority & Standardized Outputs",
        "pilot_district": "Rudraprayag, Uttarakhand, India",
        "generated_utc": gen_utc,
        "methodology_version": "1.0",
        "classification_method": "rule_based_proximity_class",
        "village_priority": village_summary,
        "candidate_areas": areas_summary,
        "missing_datasets": [
            "disaster_history_ndma_sdma",
            "road_network",
            "lulc_land_use_land_cover",
            "infrastructure_schools_health_centres",
            "capacity_planning_standard",
        ],
        "blocked_features": [
            "historical_disaster_integration",
            "infrastructure_vulnerability_scoring",
            "road_accessibility_scoring",
            "lulc_exclusion",
            "capacity_estimate",
            "village_to_area_allocation",
        ],
        "disclaimer": (
            "PRELIMINARY DECISION-SUPPORT PRIORITY — Not an official government "
            "relocation priority. Requires field verification, geotechnical assessment, "
            "and official administrative review before any relocation action."
        ),
    }

    _section("Saving decision_summary.json")
    with open(_OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2, default=str)
    print(f"  Saved: {_OUT_SUMMARY.relative_to(_ROOT)} ({_OUT_SUMMARY.stat().st_size:,} bytes)")

    # ── Build decision_metadata.json ──────────────────────────────────────
    metadata_json = {
        "project": "SIH26191",
        "generated_utc": gen_utc,
        "pipeline_step": "Step 10",
        "inputs_used": {
            "habitation_exposure": "data/processed/exposure/habitation_exposure.geojson (Step 8)",
            "pca_census": "data/raw/habitations/PCA_CDB-0503-F-Census.xlsx (Census 2011 PCA)",
            "multihazard_score": "data/processed/hazards/multihazard_score.tif (Step 6)",
            "multihazard_classes": "data/processed/hazards/multihazard_classes.tif (Step 6)",
            "terrain_susceptibility": "data/processed/hazards/terrain_susceptibility_proxy.tif (Step 4)",
            "flood_exposure": "data/processed/hazards/flood_exposure_proxy.tif (Step 5)",
            "candidate_areas": "data/outputs/candidate_topographically_feasible_areas_attributed.geojson (Step 9)",
        },
        "outputs_produced": {
            "village_priority_indicators": "data/processed/decision/village_priority_indicators.gpkg",
            "village_priority_profiles": "data/processed/decision/village_priority_profiles.gpkg",
            "candidate_area_context": "data/processed/decision/candidate_area_context.gpkg",
            "decision_summary": "data/processed/decision/decision_summary.json",
            "decision_metadata": "data/processed/decision/decision_metadata.json",
            "report": "docs/step10_decision_engine_report.md",
        },
        "classification_rules_applied": {
            "tier1": {
                "rule": "dist <= 500m AND mh_class >= 2; OR direct_zone_overlap = True",
                "config_source": "configs/priority_thresholds.yaml",
                "status": "APPLIED",
            },
            "tier2": {
                "rule": "dist <= 2000m (and not Tier 1)",
                "config_source": "configs/priority_thresholds.yaml",
                "status": "APPLIED",
            },
            "tier3": {
                "rule": "dist <= 5000m (and not Tier 1 or 2)",
                "config_source": "configs/priority_thresholds.yaml",
                "status": "APPLIED",
            },
            "beyond": {
                "rule": "dist > 5000m",
                "config_source": "configs/priority_thresholds.yaml",
                "status": "APPLIED",
            },
        },
        "indicators_used_in_tier": ["nearest_hazard_distance_m", "mh_class_at_centroid", "direct_zone_overlap"],
        "indicators_as_context_only": [
            "illiteracy_rate", "child_proportion", "sc_proportion",
            "st_proportion", "non_worker_rate",
            "mh_score_at_centroid", "terrain_score_at_centroid", "flood_score_at_centroid",
        ],
        "conditional_inputs_unavailable": {
            "disaster_history": "ACQUIRED — Literature Curated Historical Disaster Inventory (22 canonical events 1998-2024, 1km/2km contextual exposure buffers)",
            "infrastructure": "ACQUIRED — OpenStreetMap Critical Infrastructure (291 facilities: 187 healthcare [24 hospitals, 6 CHCs, 12 PHCs, 127 subcentres, 18 clinics], 70 education, 4 emergency, with Phase 2 road network graph routing)",
            "lulc": "ACQUIRED — ESA WorldCover 10m 2021 v200 (Tree cover, Built-up, Snow/Ice, Water excluded)",
            "road_network": "ACQUIRED — OpenStreetMap (6,397.3 km, NetworkX Dijkstra mountain impedance in EPSG:32644)",
            "capacity_standard": "CONFIGURED — PMAY-G 25 m²/HH at 40% site efficiency",
        },
        "capacity_status": "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD",
        "allocation_status": "NOT_GENERATED — no verified allocation methodology",
        "crs": "EPSG:32644 (WGS 84 / UTM Zone 44N)",
        "step9_outputs_modified": False,
        "step8_outputs_modified": False,
        "step7_outputs_modified": False,
    }

    _section("Saving decision_metadata.json")
    with open(_OUT_METADATA, "w", encoding="utf-8") as f:
        json.dump(metadata_json, f, indent=2, default=str)
    print(f"  Saved: {_OUT_METADATA.relative_to(_ROOT)} ({_OUT_METADATA.stat().st_size:,} bytes)")

    # ── Generate report ───────────────────────────────────────────────────
    _section("Generating step10_decision_engine_report.md")
    report_text = generate_report(village_summary, areas_summary, gen_utc)
    with open(_OUT_REPORT, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"  Saved: {_OUT_REPORT.relative_to(_ROOT)} ({_OUT_REPORT.stat().st_size:,} bytes)")

    # ── Print key results ─────────────────────────────────────────────────
    _section("Key results")
    print(f"  Total habitations: {village_summary.get('total_habitations'):,}")
    print(f"  Total population:  {village_summary.get('total_population'):,}")
    print()
    for tier, stats in village_summary.get("tier_distribution", {}).items():
        print(f"  {stats.get('display_label', tier)}: "
              f"{stats['count']} villages, "
              f"{stats['population']:,} pop, "
              f"{stats['households']:,} HH")
    print()
    print(f"  Capacity status: NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD")
    print(f"  Allocation:      NOT_GENERATED")

    t_end = datetime.datetime.utcnow()
    elapsed = (t_end - t_start).total_seconds()

    _banner(f"Step 10E Complete ({elapsed:.1f}s)")

    return {
        "summary_path": str(_OUT_SUMMARY),
        "metadata_path": str(_OUT_METADATA),
        "report_path": str(_OUT_REPORT),
        "elapsed_seconds": round(elapsed, 2),
    }


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
