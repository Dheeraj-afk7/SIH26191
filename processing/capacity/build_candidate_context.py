#!/usr/bin/env python3
"""
SIH26191 -- Step 10D: Candidate Area Contextual Enrichment
============================================================

Enriches Candidate Topographically Feasible Area polygons (Step 9 output)
with contextual descriptor fields and sets capacity status.

Pilot   : Rudraprayag District, Uttarakhand, India
Project : SIH26191

MANDATORY DISCLAIMER
--------------------
Outputs are PRELIMINARY DECISION-SUPPORT CANDIDATES requiring field
verification. Not an official site authorization or safety certification.
Geotechnical and infrastructure assessment required before any relocation
action.

NO Village → Candidate Area assignments are generated.
No allocation methodology has been verified for this project.

CAPACITY STATUS
---------------
capacity_status = "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD"
No area-per-household or area-per-person standard has been provided.
See configs/capacity.yaml for configuration requirements.

INPUTS
------
  data/outputs/candidate_topographically_feasible_areas_attributed.geojson
  configs/capacity.yaml

OUTPUTS
-------
  data/processed/decision/candidate_area_context.gpkg

USAGE
-----
  python processing/capacity/build_candidate_context.py
"""

import sys
import io
import json
import datetime
import pathlib
import warnings
from typing import Optional

import numpy as np
import pandas as pd
import geopandas as gpd
import yaml

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

_CONFIG_CAPACITY = _ROOT / "configs" / "capacity.yaml"
_INPUT_AREAS = _ROOT / "data" / "outputs" / "candidate_topographically_feasible_areas_attributed.geojson"
_OUTPUT_DIR = _ROOT / "data" / "processed" / "decision"

_METRIC_CRS_EPSG = 32644

_DISCLAIMER = (
    "PRELIMINARY DECISION-SUPPORT CANDIDATE — Requires field verification, "
    "geotechnical assessment, legal land-use review, and official administrative "
    "authorization before any relocation action. NOT a safe site certification."
)

_CAPACITY_STATUS = "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD"

_CAPACITY_STATUS_CONFIGURED = "PRELIMINARY_DWELLING_UNIT_SCENARIO"

# Maximum area for site-level capacity estimation.
# Areas > 100 ha are terrain screening zones, not individual settlement sites.
# Applying capacity formulas to a 3,500 ha polygon produces meaningless numbers
# (e.g., 567,000 HH -- more than the district population of 232,360).
# Capacity estimates are only meaningful at site planning scale (<=100 ha).
MAX_CAPACITY_AREA_HA = 100.0

_CAPACITY_NOTE = (
    "Spatial capacity estimate requires an authoritative planning standard "
    "(e.g., NDMA guidelines, IS code, State Housing Board standard) specifying "
    "area per household or per person. Configure configs/capacity.yaml with a "
    "verified planning standard before computing capacity estimates."
)

_NOT_ALLOCATED = (
    "PRELIMINARY DWELLING-UNIT SCENARIO — Not an official site authorization. "
    "Village → Candidate Area assignments must not be "
    "inferred from this output."
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _banner(text: str) -> None:
    print()
    print("=" * 72)
    print(f"  {text}")
    print("=" * 72)


def _section(text: str) -> None:
    print(f"\n--- {text} ---")


def _load_yaml(path: pathlib.Path, label: str) -> Optional[dict]:
    if not path.exists():
        print(f"  WARNING: {label} not found: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    print(f"  Loaded {label}: {path.name}")
    return cfg


# ---------------------------------------------------------------------------
# Context label derivation
# ---------------------------------------------------------------------------

def _slope_context(mean_slope: float) -> str:
    """Categorical description of mean slope."""
    if pd.isna(mean_slope):
        return "Unknown"
    if mean_slope < 15.0:
        return "Gentle terrain (mean slope < 15 degrees)"
    elif mean_slope < 30.0:
        return "Moderate terrain (mean slope 15-30 degrees)"
    else:
        return "Steep terrain (mean slope >= 30 degrees)"


def _terrain_susc_context(mean_ts: float) -> str:
    """Categorical from mean terrain susceptibility score."""
    if pd.isna(mean_ts):
        return "Unknown"
    if mean_ts < 0.35:
        return "Lower terrain susceptibility indicator (score < 0.35)"
    elif mean_ts < 0.65:
        return "Moderate terrain susceptibility indicator (score 0.35-0.65)"
    else:
        return "Higher terrain susceptibility indicator (score >= 0.65)"


def _flood_context(mean_flood: float) -> str:
    """Categorical from mean flood exposure proxy score."""
    if pd.isna(mean_flood):
        return "Unknown"
    if mean_flood < 0.35:
        return "Lower terrain-derived flood exposure (score < 0.35)"
    elif mean_flood < 0.65:
        return "Moderate terrain-derived flood exposure (score 0.35-0.65)"
    else:
        return "Higher terrain-derived flood exposure (score >= 0.65)"


def _hazard_buffer_context(dist_m: float) -> str:
    """Categorical from distance to nearest red zone."""
    if pd.isna(dist_m):
        return "Unknown"
    if dist_m <= 500.0:
        return "Within 500m of Candidate Red Zone boundary"
    elif dist_m <= 2000.0:
        return "500m to 2km from nearest Candidate Red Zone"
    else:
        return f"Beyond 2km from nearest Candidate Red Zone ({dist_m/1000:.1f}km)"


def _area_scale_context(area_ha: float) -> str:
    """Categorical area scale label."""
    if pd.isna(area_ha):
        return "Unknown"
    if area_ha > 10000.0:
        return (
            "VERY_LARGE_UNFILTERED_TERRAIN_SCREEN — This polygon represents "
            "a large contiguous terrain area. Configurable filters (slope threshold, "
            "minimum mapping unit) are NOT_CONFIGURED. This is NOT a discrete "
            "relocation site recommendation."
        )
    elif area_ha > 100.0:
        return (
            "Large terrain cluster (> 100 ha). Minimum mapping unit filter "
            "NOT_CONFIGURED — sub-areas may vary in suitability."
        )
    elif area_ha > 10.0:
        return "Moderate terrain cluster (10-100 ha)."
    else:
        return "Small terrain cluster (< 10 ha)."


def _count_not_configured(screening_basis: str) -> int:
    """Count NOT_CONFIGURED parameters from screening_basis string."""
    if not isinstance(screening_basis, str):
        return 0
    return screening_basis.count("NOT_CONFIGURED")


# ---------------------------------------------------------------------------
# Phase D — Preliminary Spatial Capacity Estimation (PS-6)
# ---------------------------------------------------------------------------

def compute_capacity(
    area_m2: float,
    cap_cfg: dict,
) -> dict:
    """
    Compute a preliminary spatial capacity estimate for a candidate area
    based on configured planning standard (capacity.yaml).

    MANDATORY DISCLAIMER
    --------------------
    Outputs are PRELIMINARY PLANNING SCENARIOS ONLY.
    NOT engineering-certified carrying capacity.
    Engineering surveys, geotechnical assessment, land ownership verification,
    and legal clearances are required before any site is used for actual
    relocation planning.

    PLANNING STANDARD APPLIED (when configured)
    --------------------------------------------
    Pradhan Mantri Awaas Yojana — Gramin (PMAY-G)
    Ministry of Rural Development, Government of India.
    Minimum house size: 25 m² per household.
    Source: PMAY-G Operational Guidelines (2016), MoRD GoI.

    Parameters
    ----------
    area_m2 : float — total area of the candidate polygon in m²
    cap_cfg : dict — loaded capacity.yaml

    Returns
    -------
    dict with capacity estimate fields
    """
    area_per_hh = cap_cfg.get("area_per_household_m2")
    eff_factor = cap_cfg.get("site_efficiency_factor", 0.40)
    avg_hh_size = cap_cfg.get("avg_household_size", 4.0)
    min_viable_m2 = cap_cfg.get("minimum_viable_plot_m2", 2500.0)
    out_cfg = cap_cfg.get("output", {})
    std_cfg = cap_cfg.get("planning_standard", {})
    disclaimer = out_cfg.get(
        "disclaimer", "PRELIMINARY SPATIAL CAPACITY ESTIMATE. Not engineering-certified."
    ).strip()

    if area_per_hh is None:
        return {
            "capacity_status": _CAPACITY_STATUS,
            "capacity_planning_note": out_cfg.get("planning_note", _CAPACITY_NOTE).strip(),
            "capacity_planning_standard": "NOT_CONFIGURED",
            "capacity_planning_standard_citation": "NOT_CONFIGURED",
            "usable_area_m2": None,
            "usable_area_ha": None,
            "site_efficiency_factor": None,
            "estimated_household_capacity": None,
            "estimated_population_capacity": None,
            "capacity_density_hh_per_ha": None,
            "avg_household_size_assumed": None,
            "capacity_disclaimer": disclaimer,
        }

    area_ha = float(area_m2) / 10000.0

    # -- Area scale check: capacity meaningless at terrain-zone scale ------
    if area_ha > MAX_CAPACITY_AREA_HA:
        return {
            "capacity_status": "AREA_EXCEEDS_SITE_PLANNING_SCALE",
            "capacity_planning_note": (
                f"Area {area_ha:,.0f} ha exceeds the {MAX_CAPACITY_AREA_HA:.0f} ha site planning "
                "threshold. This polygon represents a terrain screening zone, not an "
                "individual settlement site. Subdivision planning and detailed survey "
                "required before capacity estimation is meaningful."
            ),
            "capacity_planning_standard": out_cfg.get("planning_standard_name", "PMAY-G 25m2/HH"),
            "capacity_planning_standard_citation": "N/A -- area exceeds site planning scale",
            "usable_area_m2": None,
            "usable_area_ha": None,
            "site_efficiency_factor": None,
            "estimated_household_capacity": None,
            "estimated_population_capacity": None,
            "capacity_density_hh_per_ha": None,
            "avg_household_size_assumed": None,
            "capacity_viable": False,
            "capacity_disclaimer": disclaimer,
        }

    # -- Compute usable area (total area * efficiency factor) --------------
    usable_area_m2 = float(area_m2) * float(eff_factor)
    usable_area_ha = usable_area_m2 / 10000.0

    # Household capacity
    estimated_hh = int(usable_area_m2 / float(area_per_hh))

    # Population capacity
    estimated_pop = int(estimated_hh * float(avg_hh_size))

    # Density
    density_hh_per_ha = (estimated_hh / usable_area_ha) if usable_area_ha > 0 else None

    # Viability check
    viable = usable_area_m2 >= float(min_viable_m2) and estimated_hh >= 10

    # Planning standard name for display
    std_name = out_cfg.get(
        "planning_standard_name",
        f"PMAY-G {area_per_hh} m²/HH (MoRD, GoI)"
    )

    return {
        "capacity_status": _CAPACITY_STATUS_CONFIGURED,
        "capacity_planning_note": out_cfg.get("planning_note", "").strip(),
        "capacity_planning_standard": std_name,
        "capacity_planning_standard_citation": std_cfg.get("citation", "").strip(),
        "usable_area_m2": round(usable_area_m2, 1),
        "usable_area_ha": round(usable_area_ha, 3),
        "site_efficiency_factor": float(eff_factor),
        "estimated_household_capacity": estimated_hh,
        "estimated_population_capacity": estimated_pop,
        "capacity_density_hh_per_ha": round(density_hh_per_ha, 1) if density_hh_per_ha else None,
        "avg_household_size_assumed": float(avg_hh_size),
        "capacity_viable": viable,
        "capacity_disclaimer": disclaimer,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> dict:
    _banner("SIH26191 — Step 10D: Candidate Area Contextual Enrichment")
    t_start = datetime.datetime.utcnow()
    print(f"  Started: {t_start.strftime('%Y-%m-%dT%H:%M:%SZ')}")

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Output directory: {_OUTPUT_DIR.relative_to(_ROOT)}")

    # ── Load capacity config ──────────────────────────────────────────────
    _section("Loading capacity configuration")
    cap_cfg = _load_yaml(_CONFIG_CAPACITY, "capacity.yaml")
    capacity_configured = False

    if cap_cfg:
        cfg_status = cap_cfg.get("status", "NOT_CONFIGURED")
        out_cfg = cap_cfg.get("output", {})
        area_per_hh = cap_cfg.get("area_per_household_m2")
        capacity_configured = (cfg_status == "CONFIGURED" and area_per_hh is not None)
        print(f"  Capacity config status: {cfg_status}")
        print(f"  area_per_household_m2: {area_per_hh}")
        if capacity_configured:
            print(f"  Planning standard: {cap_cfg.get('planning_standard', {}).get('scheme', 'N/A')}")
            print(f"  Site efficiency factor: {cap_cfg.get('site_efficiency_factor', 0.40)}")
        else:
            print(f"  Capacity NOT configured — all areas will carry NOT_ESTIMATED status")
    else:
        print("  capacity.yaml not found or unreadable — capacity status = NOT_ESTIMATED")

    # ── Load candidate areas ──────────────────────────────────────────────
    _section("Loading candidate areas (Step 9C attributed output)")
    if not _INPUT_AREAS.exists():
        raise FileNotFoundError(
            f"Candidate areas not found: {_INPUT_AREAS}\n"
            "Ensure Step 9 has completed successfully."
        )

    areas_gdf = gpd.read_file(str(_INPUT_AREAS))
    print(f"  Loaded: {len(areas_gdf)} candidate area features")
    print(f"  CRS: {areas_gdf.crs}")
    print(f"  Columns: {list(areas_gdf.columns)}")

    # Schema inspection — identify which Step 9C fields are present
    step9_expected = [
        "area_id", "area_label", "area_m2", "area_hectares", "pixel_count",
        "screening_basis", "mean_slope", "max_slope", "min_slope",
        "mean_terrain_susceptibility", "mean_flood_exposure_proxy",
        "mean_multihazard_score", "dist_to_nearest_redzone_m",
        "nearest_redzone_id", "nearest_habitation_m",
        "nearest_village_name", "nearest_village_id", "nearest_village_pop",
    ]
    found = [c for c in step9_expected if c in areas_gdf.columns]
    missing = [c for c in step9_expected if c not in areas_gdf.columns]
    print(f"  Step 9C fields found: {len(found)}/{len(step9_expected)}")
    if missing:
        print(f"  Step 9C fields missing: {missing}")

    # Ensure metric CRS
    if areas_gdf.crs is None:
        areas_gdf = areas_gdf.set_crs(epsg=_METRIC_CRS_EPSG)
    elif areas_gdf.crs.to_epsg() != _METRIC_CRS_EPSG:
        areas_gdf = areas_gdf.to_crs(epsg=_METRIC_CRS_EPSG)

    # ── Add contextual fields ─────────────────────────────────────────────
    _section("Adding contextual descriptor fields")

    # Slope context
    if "mean_slope" in areas_gdf.columns:
        areas_gdf["slope_context"] = areas_gdf["mean_slope"].apply(_slope_context)
        print(f"  slope_context: derived from mean_slope")
    else:
        areas_gdf["slope_context"] = "Unknown — mean_slope field not available"
        print("  slope_context: UNAVAILABLE (mean_slope missing)")

    # Terrain susceptibility context
    if "mean_terrain_susceptibility" in areas_gdf.columns:
        areas_gdf["terrain_context"] = areas_gdf["mean_terrain_susceptibility"].apply(
            _terrain_susc_context
        )
        print("  terrain_context: derived from mean_terrain_susceptibility")
    else:
        areas_gdf["terrain_context"] = "Unknown — mean_terrain_susceptibility not available"
        print("  terrain_context: UNAVAILABLE")

    # Flood exposure context
    if "mean_flood_exposure_proxy" in areas_gdf.columns:
        areas_gdf["flood_context"] = areas_gdf["mean_flood_exposure_proxy"].apply(
            _flood_context
        )
        print("  flood_context: derived from mean_flood_exposure_proxy")
    else:
        areas_gdf["flood_context"] = "Unknown — mean_flood_exposure_proxy not available"
        print("  flood_context: UNAVAILABLE")

    # Hazard buffer context
    if "dist_to_nearest_redzone_m" in areas_gdf.columns:
        areas_gdf["hazard_buffer_context"] = areas_gdf["dist_to_nearest_redzone_m"].apply(
            _hazard_buffer_context
        )
        print("  hazard_buffer_context: derived from dist_to_nearest_redzone_m")
    else:
        areas_gdf["hazard_buffer_context"] = "Unknown — dist_to_nearest_redzone_m not available"
        print("  hazard_buffer_context: UNAVAILABLE")

    # Area scale context
    if "area_hectares" in areas_gdf.columns:
        areas_gdf["area_scale_context"] = areas_gdf["area_hectares"].apply(_area_scale_context)
        print("  area_scale_context: derived from area_hectares")
    else:
        areas_gdf["area_scale_context"] = "Unknown — area_hectares not available"
        print("  area_scale_context: UNAVAILABLE")

    # Screening completeness
    if "screening_basis" in areas_gdf.columns:
        areas_gdf["not_configured_count"] = areas_gdf["screening_basis"].apply(
            _count_not_configured
        )
        areas_gdf["screening_completeness"] = areas_gdf["not_configured_count"].apply(
            lambda n: (
                f"PARTIAL — {n} configurable screening filter(s) NOT_CONFIGURED "
                f"(slope_max_deg, redzone_buffer_m, flood_class2_exclusion, "
                f"mh_class2_exclusion, elevation_max_m, minimum_area_m2)"
                if n > 0 else "COMPLETE — all configured filters applied"
            )
        )
        areas_gdf = areas_gdf.drop(columns=["not_configured_count"], errors="ignore")
        print("  screening_completeness: derived from screening_basis")
    else:
        areas_gdf["screening_completeness"] = (
            "PARTIAL — screening_basis field not available; "
            "completeness cannot be determined"
        )

    # ── Phase D: Capacity estimation (PS-6) ──────────────────────────────
    _section("Phase D — Preliminary spatial capacity estimation (PMAY-G standard)")

    cap_records = []
    for _, row in areas_gdf.iterrows():
        area_m2 = row.get("area_m2", 0) or 0
        cap = compute_capacity(float(area_m2), cap_cfg or {})
        cap_records.append(cap)

    cap_df = pd.DataFrame(cap_records)
    for col in cap_df.columns:
        areas_gdf[col] = cap_df[col].values

    if capacity_configured:
        print(f"  Planning standard: PMAY-G 25 m²/HH (MoRD, GoI)")
        print(f"  Site efficiency factor: {cap_cfg.get('site_efficiency_factor', 0.40)}")
        total_hh = cap_df["estimated_household_capacity"].sum()
        total_pop = cap_df["estimated_population_capacity"].sum()
        print(f"  Total estimated household capacity (all areas): {total_hh:,} HH")
        print(f"  Total estimated population capacity (all areas): {total_pop:,} persons")
    else:
        print(f"  capacity_status: {_CAPACITY_STATUS}")

    # Allocation status (always NOT_GENERATED)
    areas_gdf["allocation_status"] = _NOT_ALLOCATED
    print("  allocation_status: NOT_ALLOCATED (no verified methodology)")

    # Infrastructure and access notes
    if "road_accessibility_status" not in areas_gdf.columns or areas_gdf["road_accessibility_status"].isnull().all():
        areas_gdf["road_accessibility_status"] = (
            "NOT_ASSESSED — Road network dataset not acquired. "
            "Area accessibility by road cannot be determined from current data."
        )
    if "dominant_land_cover" in areas_gdf.columns:
        areas_gdf["lulc_status"] = "ESA_WORLDCOVER_EVALUATED — Screened against Tree cover, Snow/Ice, Water Bodies, and Built-up"
    else:
        areas_gdf["lulc_status"] = (
            "NOT_ASSESSED — Land use / land cover dataset not acquired. "
            "Forest, agricultural, or protected area status cannot be determined."
        )

    # Step 10 disclaimer
    areas_gdf["step10_disclaimer"] = _DISCLAIMER

    # ── Print summary ─────────────────────────────────────────────────────
    _section("Candidate area summary")
    for _, row in areas_gdf.iterrows():
        area_id = row.get("area_id", "N/A")
        area_ha = row.get("area_hectares", np.nan)
        slope = row.get("mean_slope", np.nan)
        dist_rz = row.get("dist_to_nearest_redzone_m", np.nan)
        near_vill = row.get("nearest_village_name", "N/A")
        near_pop = row.get("nearest_village_pop", "N/A")
        slope_ctx = row.get("slope_context", "N/A")
        cap_status_row = row.get("capacity_status", "N/A")
        est_hh = row.get("estimated_household_capacity", None)
        est_pop = row.get("estimated_population_capacity", None)
        print(f"\n  {area_id}:")
        print(f"    Area:           {area_ha:,.1f} ha" if not pd.isna(area_ha) else "    Area: N/A")
        print(f"    Mean slope:     {slope:.2f} deg ({slope_ctx})" if not pd.isna(slope) else "    Mean slope: N/A")
        print(f"    Dist to red zone: {dist_rz:.0f} m" if not pd.isna(dist_rz) else "    Dist to red zone: N/A")
        print(f"    Nearest village: {near_vill} (pop: {near_pop})")
        if est_hh is not None:
            usable_ha = row.get("usable_area_ha", np.nan)
            print(f"    Capacity: ~{est_hh:,} HH / ~{est_pop:,} persons"
                  f" | Usable area: {usable_ha:.2f} ha [PMAY-G 25m²/HH, eff=40%]")
        else:
            print(f"    Capacity: {cap_status_row}")

    # ── Save ──────────────────────────────────────────────────────────────
    _section("Saving candidate_area_context.gpkg")

    # Preserve all existing Step 9C columns + new context columns
    # Do NOT drop any Step 9C fields
    out_path = _OUTPUT_DIR / "candidate_area_context.gpkg"
    areas_gdf.to_file(str(out_path), driver="GPKG", layer="candidate_area_context")
    sz = out_path.stat().st_size
    print(f"\n  Saved: {out_path.relative_to(_ROOT)} ({sz:,} bytes)")
    print(f"  Features: {len(areas_gdf)} | CRS: {areas_gdf.crs}")
    print(f"  Total columns: {len(areas_gdf.columns)}")

    t_end = datetime.datetime.utcnow()
    elapsed = (t_end - t_start).total_seconds()

    _banner(f"Step 10D Complete ({elapsed:.1f}s)")
    print(f"  {out_path.relative_to(_ROOT)}")
    print(f"\n  DISCLAIMER: {_DISCLAIMER}")

    return {
        "output_path": str(out_path),
        "n_areas": len(areas_gdf),
        "capacity_configured": capacity_configured,
        "capacity_standard": (
            cap_cfg.get("output", {}).get("planning_standard_name", "NOT_CONFIGURED")
            if cap_cfg else "NOT_CONFIGURED"
        ),
        "total_estimated_household_capacity": (
            int(areas_gdf["estimated_household_capacity"].sum())
            if capacity_configured and "estimated_household_capacity" in areas_gdf.columns
            else None
        ),
        "total_estimated_population_capacity": (
            int(areas_gdf["estimated_population_capacity"].sum())
            if capacity_configured and "estimated_population_capacity" in areas_gdf.columns
            else None
        ),
        "allocation_status": "NOT_GENERATED",
        "elapsed_seconds": round(elapsed, 2),
        "generated_utc": t_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
