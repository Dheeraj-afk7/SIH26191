#!/usr/bin/env python3
"""
SIH26191 -- Step 10B + 10C: Village Vulnerability Attribution & Priority Classification
========================================================================================

Pilot   : Rudraprayag District, Uttarakhand, India
Project : SIH26191

MANDATORY DISCLAIMER
--------------------
All outputs are PRELIMINARY DECISION-SUPPORT CLASSIFICATIONS only.
They do NOT constitute:
  - Official government relocation priority designations
  - Engineering-certified hazard assessments
  - Evacuation orders or notices
  - Mandatory relocation instructions
  - Official government Red Zone declarations
All outputs require official government review before any administrative action.

METHODOLOGY
-----------
Priority classification uses a deterministic RULE-BASED approach derived
exclusively from VERIFIED EXISTING DATA:

  PRIMARY DIMENSION:
    nearest_hazard_distance_m — Euclidean distance (m) from village centroid
    to nearest Candidate Hazard-Based Red Zone boundary. Source: Step 8.

  SECONDARY DIMENSION:
    mh_class_at_centroid — Multi-Hazard Screening Class (1/2/3) sampled from
    multihazard_classes.tif at the village centroid location. Source: Step 6.

  HARD FLAG:
    direct_zone_overlap — True if centroid directly intersects a red zone
    polygon. Source: Step 8. Always assigns Tier 1 regardless of distance.

  NO AHP, MCDA, or uncalibrated composite weights are applied.
  Vulnerability indicators (literacy, SC/ST, children, non-workers) are
  output as CONTEXT FIELDS only. They are NOT used in tier assignment.
  Indicator weights have not been scientifically verified.

CONFIGURABLE THRESHOLDS
-----------------------
All thresholds are loaded from configs/priority_thresholds.yaml.
Re-run this script after updating thresholds to regenerate outputs.

INPUTS (verified)
-----------------
  data/processed/exposure/habitation_exposure.geojson  (Step 8 output)
  data/raw/habitations/PCA_CDB-0503-F-Census.xlsx       (Census PCA 2011)
  data/processed/hazards/multihazard_score.tif          (Step 6 output)
  data/processed/hazards/multihazard_classes.tif        (Step 6 output)
  data/processed/hazards/terrain_susceptibility_proxy.tif (Step 4 output)
  data/processed/hazards/flood_exposure_proxy.tif       (Step 5 output)
  configs/priority_thresholds.yaml                      (Step 10 config)

OUTPUTS
-------
  data/processed/decision/village_priority_indicators.gpkg  (Step 10B)
  data/processed/decision/village_priority_profiles.gpkg    (Step 10C)

USAGE
-----
  python processing/priority/build_village_priority.py
"""

import sys
import io
import json
import datetime
import pathlib
import warnings
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import yaml

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent   # processing/priority/
_ROOT = _SCRIPT_DIR.parent.parent                        # project root

_CONFIG_MAIN = _ROOT / "configs" / "project.yaml"
_CONFIG_PRIORITY = _ROOT / "configs" / "priority_thresholds.yaml"
_OUTPUT_DIR = _ROOT / "data" / "processed" / "decision"

_METRIC_CRS_EPSG = 32644

_DISCLAIMER = (
    "PRELIMINARY DECISION-SUPPORT PRIORITY — Not an official government "
    "relocation priority. Requires field verification, geotechnical assessment, "
    "and official administrative review before any relocation action."
)

_METHODOLOGY_NOTE = (
    "Rule-based classification using verified proximity distance (Step 8) and "
    "multi-hazard class at centroid (Step 6 raster sample). No AHP or MCDA "
    "weights applied. Vulnerability indicators are context fields only."
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


def _load_yaml(path: pathlib.Path, label: str) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required config not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    print(f"  Loaded {label}: {path.name}")
    return cfg


def _inspect_gdf(gdf: gpd.GeoDataFrame, label: str) -> None:
    geom_types = gdf.geometry.geom_type.unique().tolist()
    print(f"  [{label}] {len(gdf)} features | CRS: {gdf.crs} | Geometry: {geom_types}")
    print(f"  [{label}] Columns ({len(gdf.columns)}): {list(gdf.columns)}")


# ---------------------------------------------------------------------------
# Phase 10B — Input loading
# ---------------------------------------------------------------------------

def load_habitation_exposure(path: pathlib.Path) -> gpd.GeoDataFrame:
    """Load habitation exposure GeoDataFrame with field validation."""
    _section("Loading habitation exposure (Step 8 output)")
    if not path.exists():
        raise FileNotFoundError(f"Habitation exposure not found: {path}")

    gdf = gpd.read_file(str(path))
    _inspect_gdf(gdf, "habitation_exposure")

    required_fields = [
        "village_id", "village_name", "tot_pop", "households",
        "pop_sc", "pop_st", "nearest_hazard_distance_m",
        "proximity_band", "direct_zone_overlap",
    ]
    missing = [f for f in required_fields if f not in gdf.columns]
    if missing:
        raise ValueError(
            f"Required fields missing from habitation_exposure: {missing}\n"
            f"Available: {list(gdf.columns)}"
        )

    print(f"  Schema validation: PASS — all {len(required_fields)} required fields present")
    print(f"  Total population: {gdf['tot_pop'].sum():,}")
    print(f"  Total households: {gdf['households'].sum():,}")

    # Reproject to metric CRS if needed
    if gdf.crs is None:
        print("  WARNING: CRS not set — assuming EPSG:32644")
        gdf = gdf.set_crs(epsg=_METRIC_CRS_EPSG)
    elif gdf.crs.to_epsg() != _METRIC_CRS_EPSG:
        print(f"  Reprojecting from EPSG:{gdf.crs.to_epsg()} to EPSG:{_METRIC_CRS_EPSG}")
        gdf = gdf.to_crs(epsg=_METRIC_CRS_EPSG)

    return gdf


def load_pca_census(path: pathlib.Path) -> Tuple[Optional[pd.DataFrame], dict, list]:
    """
    Load PCA Census 2011 Excel.

    Returns
    -------
    (villages_df, available_cols_map, unavailable_cols_list)
    villages_df is None if file not found.
    """
    _section("Loading PCA Census 2011")

    target_cols = {
        "Town/Village": "join_key",
        "TOT_P":        "total_population_pca",
        "P_06":         "children_under6",
        "P_LIT":        "literate_population",
        "P_ILL":        "illiterate_population",
        "P_SC":         "sc_population_pca",
        "P_ST":         "st_population_pca",
        "NON_WORK_P":   "non_worker_population",
    }

    if not path.exists():
        print(f"  WARNING: PCA Census file not found: {path}")
        print("  Vulnerability indicators cannot be computed from PCA.")
        return None, {}, list(target_cols.keys())

    df = pd.read_excel(str(path), sheet_name=0)
    print(f"  Loaded: {len(df)} rows, {len(df.columns)} columns")

    if "Level" not in df.columns:
        print("  WARNING: 'Level' column missing — cannot filter to village level")
        return None, {}, list(target_cols.keys())

    villages = df[df["Level"] == "VILLAGE"].copy()
    print(f"  Village-level rows: {len(villages)}")

    available = {}
    unavailable = []
    for col in target_cols:
        if col in villages.columns:
            available[col] = target_cols[col]
        else:
            unavailable.append(col)
            print(f"  WARNING: PCA column '{col}' not found")

    print(f"  PCA columns available: {list(available.keys())}")
    if unavailable:
        print(f"  PCA columns unavailable: {unavailable}")

    return villages, available, unavailable


def sample_rasters_at_centroids(
    gdf: gpd.GeoDataFrame,
    raster_paths: Dict[str, pathlib.Path],
) -> Dict[str, List[float]]:
    """
    Sample multiple rasters at village centroid locations.

    Parameters
    ----------
    gdf : GeoDataFrame with Point geometry in EPSG:32644
    raster_paths : {output_field_name: raster_path}

    Returns
    -------
    dict: {field_name: list_of_float_or_nan}
    """
    _section("Sampling hazard rasters at village centroids")

    # Extract (x, y) coordinate pairs
    coords = [(float(geom.x), float(geom.y)) for geom in gdf.geometry]
    results: Dict[str, List[float]] = {}

    for field_name, raster_path in raster_paths.items():
        if not raster_path.exists():
            print(f"  SKIP: {field_name} — raster not found: {raster_path.name}")
            results[field_name] = [np.nan] * len(gdf)
            continue

        with rasterio.open(str(raster_path)) as src:
            nodata_val = src.nodata
            dtype = src.dtypes[0]
            sampled_raw = list(src.sample(coords))

        values: List[float] = []
        nodata_count = 0

        for raw in sampled_raw:
            v = float(raw[0])
            is_nodata = False

            if np.isnan(v):
                is_nodata = True
            elif nodata_val is not None:
                # Float comparison with tolerance for float nodata
                if abs(v - float(nodata_val)) < 0.5:
                    is_nodata = True

            if is_nodata:
                values.append(np.nan)
                nodata_count += 1
            else:
                values.append(v)

        valid_count = len(values) - nodata_count
        print(
            f"  {field_name}: {valid_count}/{len(gdf)} valid, "
            f"{nodata_count} NoData (raster: {raster_path.name})"
        )
        results[field_name] = values

    return results


# ---------------------------------------------------------------------------
# Phase 10B — Vulnerability computation
# ---------------------------------------------------------------------------

def compute_vulnerability_indicators(
    gdf: gpd.GeoDataFrame,
    pca_villages: Optional[pd.DataFrame],
    pca_available: dict,
) -> Tuple[gpd.GeoDataFrame, List[str], List[str]]:
    """
    Join PCA additional columns and compute vulnerability indicators.

    Indicators derived:
      illiteracy_rate    = P_ILL / TOT_P
      child_proportion   = P_06  / TOT_P
      sc_proportion      = pop_sc / tot_pop   (pop_sc already in exposure)
      st_proportion      = pop_st / tot_pop   (pop_st already in exposure)
      non_worker_rate    = NON_WORK_P / TOT_P

    All rates are clipped to [0.0, 1.0].
    Villages with TOT_P = 0 receive NaN for all rates.

    NOTE: These indicators are CONTEXT FIELDS only.
    They are NOT used to determine priority tier.
    No composite weight is applied.
    """
    _section("Computing vulnerability indicators from Census PCA 2011")

    result = gdf.copy()
    computed: List[str] = []
    unavailable: List[str] = []

    # ── Join PCA additional columns ──────────────────────────────────────
    pca_extra_cols = [c for c in ["P_06", "P_LIT", "P_ILL", "NON_WORK_P"]
                      if c in pca_available]

    join_status_col = []

    if pca_villages is not None and "Town/Village" in pca_available and pca_extra_cols:
        fetch_cols = ["Town/Village"] + pca_extra_cols
        pca_subset = pca_villages[fetch_cols].copy()
        pca_subset = pca_subset.rename(columns={"Town/Village": "_pca_vid"})
        pca_subset["_pca_vid"] = pca_subset["_pca_vid"].astype(int)

        # Merge (left join — keep all habitations)
        result["_join_key"] = result["village_id"].astype(int)
        n_before = len(result)
        result = result.merge(
            pca_subset,
            left_on="_join_key",
            right_on="_pca_vid",
            how="left",
        )
        result = result.drop(columns=["_join_key", "_pca_vid"], errors="ignore")
        assert len(result) == n_before, "Merge changed row count — check for duplicate PCA keys"

        matched = result["P_ILL"].notna().sum() if "P_ILL" in result.columns else \
                  result["P_06"].notna().sum() if "P_06" in result.columns else 0
        print(f"  PCA join: {matched}/{len(result)} villages matched")
        join_status_col = ["JOINED" if not pd.isna(result.at[i, pca_extra_cols[0]])
                           else "NOT_FOUND_IN_PCA"
                           for i in result.index]
    else:
        print("  PCA join: skipped (file unavailable or required columns missing)")
        join_status_col = ["PCA_UNAVAILABLE"] * len(result)
        for col in pca_extra_cols:
            if col not in result.columns:
                result[col] = np.nan

    result["pca_join_status"] = join_status_col

    # ── Compute rates ─────────────────────────────────────────────────────
    # Use tot_pop already in exposure as denominator (verified field)
    # Safe denominator: zero population → NaN
    pop_denom = result["tot_pop"].where(result["tot_pop"] > 0, np.nan)

    def _safe_rate(num_col: str, out_col: str, label: str) -> None:
        if num_col in result.columns and result[num_col].notna().any():
            with np.errstate(divide="ignore", invalid="ignore"):
                result[out_col] = (result[num_col] / pop_denom).clip(0.0, 1.0)
            valid = result[out_col].notna().sum()
            print(f"  {label}: {valid} valid values (range "
                  f"{result[out_col].min():.3f}–{result[out_col].max():.3f})")
            computed.append(out_col)
        else:
            result[out_col] = np.nan
            print(f"  {label}: UNAVAILABLE — source column '{num_col}' not found or all NaN")
            unavailable.append(out_col)

    _safe_rate("P_ILL",      "illiteracy_rate",  "Illiteracy rate (P_ILL/TOT_P)")
    _safe_rate("P_06",       "child_proportion", "Child proportion (P_06/TOT_P)")
    _safe_rate("NON_WORK_P", "non_worker_rate",  "Non-worker rate (NON_WORK_P/TOT_P)")

    # SC and ST proportions — use columns already present in exposure
    if "pop_sc" in result.columns and result["pop_sc"].notna().any():
        with np.errstate(divide="ignore", invalid="ignore"):
            result["sc_proportion"] = (result["pop_sc"] / pop_denom).clip(0.0, 1.0)
        valid = result["sc_proportion"].notna().sum()
        print(f"  SC proportion (pop_sc/tot_pop): {valid} valid values")
        computed.append("sc_proportion")
    else:
        result["sc_proportion"] = np.nan
        print("  SC proportion: UNAVAILABLE — pop_sc column missing")
        unavailable.append("sc_proportion")

    if "pop_st" in result.columns and result["pop_st"].notna().any():
        with np.errstate(divide="ignore", invalid="ignore"):
            result["st_proportion"] = (result["pop_st"] / pop_denom).clip(0.0, 1.0)
        valid = result["st_proportion"].notna().sum()
        print(f"  ST proportion (pop_st/tot_pop): {valid} valid values")
        computed.append("st_proportion")
    else:
        result["st_proportion"] = np.nan
        print("  ST proportion: UNAVAILABLE — pop_st column missing")
        unavailable.append("st_proportion")

    # Drop raw PCA fetch columns (rates are retained)
    drop_cols = [c for c in ["P_06", "P_LIT", "P_ILL", "NON_WORK_P"] if c in result.columns]
    result = result.drop(columns=drop_cols, errors="ignore")

    print(f"\n  Computed indicators:   {computed}")
    print(f"  Unavailable indicators: {unavailable}")

    return result, computed, unavailable


# ---------------------------------------------------------------------------
# Phase 10C — Priority classification
# ---------------------------------------------------------------------------

def classify_priority(
    row: pd.Series,
    thresholds: dict,
) -> Tuple[str, str, str]:
    """
    Apply rule-based priority classification to a single village.

    Parameters
    ----------
    row : pandas Series with required fields
    thresholds : loaded priority_thresholds.yaml dict

    Returns
    -------
    (priority_tier, priority_reason, applied_rule_string)
    """
    dist = row.get("nearest_hazard_distance_m", np.nan)
    mh_raw = row.get("mh_class_at_centroid", np.nan)
    overlap = bool(row.get("direct_zone_overlap", False))
    zone_id = row.get("nearest_zone_id", "N/A")

    try:
        dist = float(dist)
    except (TypeError, ValueError):
        dist = np.nan

    # Resolve MH class
    mh_class: Optional[int] = None
    mh_valid = False
    if not (pd.isna(mh_raw) if isinstance(mh_raw, float) else mh_raw is None):
        try:
            mh_int = int(float(mh_raw))
            if mh_int in (1, 2, 3):
                mh_class = mh_int
                mh_valid = True
        except (TypeError, ValueError):
            pass

    mh_ctx = f"MH Class {mh_class}" if mh_valid else "MH class unavailable (NoData)"

    # ── HARD RULE: direct centroid overlap ─────────────────────────────
    if overlap:
        return (
            thresholds["tier1"]["label"],
            (f"HARD RULE: Village centroid directly overlaps Candidate Hazard-Based "
             f"Red Zone polygon. Village sits within red zone boundary. "
             f"({mh_ctx} at centroid)"),
            "direct_zone_overlap = True (hard safety rule)"
        )

    # ── Distance guard ─────────────────────────────────────────────────
    if np.isnan(dist):
        return (
            "Unknown",
            "nearest_hazard_distance_m is NaN — classification not possible",
            "CLASSIFICATION_ERROR: distance field is NaN"
        )

    t1_dist = float(thresholds["tier1"]["max_distance_m"])
    t1_class = int(thresholds["tier1"]["min_mh_class"])
    t2_dist = float(thresholds["tier2"]["max_distance_m"])
    t3_dist = float(thresholds["tier3"]["max_distance_m"])

    # ── Tier 1: proximity + MH class condition ─────────────────────────
    if dist <= t1_dist:
        if mh_valid and mh_class >= t1_class:
            return (
                thresholds["tier1"]["label"],
                (f"Centroid within {t1_dist:.0f}m of Candidate Red Zone "
                 f"(distance: {dist:.0f}m, nearest: {zone_id}) AND "
                 f"{mh_ctx} at centroid (rule: MH Class ≥ {t1_class}). "
                 f"Close proximity with moderate-higher hazard terrain at centroid."),
                f"dist ≤ {t1_dist:.0f}m AND mh_class ≥ {t1_class}"
            )
        elif not mh_valid:
            # Close proximity, but MH class unavailable — conservative: Tier 2
            return (
                thresholds["tier2"]["label"],
                (f"Centroid within {t1_dist:.0f}m of Candidate Red Zone "
                 f"(distance: {dist:.0f}m, nearest: {zone_id}) but {mh_ctx}. "
                 f"Cannot confirm Tier 1 MH class condition. "
                 f"Assigned Tier 2 (conservative — avoids unverified elevation)."),
                f"dist ≤ {t1_dist:.0f}m; mh_class = NoData (conservative Tier 2)"
            )
        else:
            # mh_class = 1: close proximity but Lower MH class at centroid
            # Falls through to Tier 2 (mh_class 1 does not satisfy tier1 condition)
            pass

    # ── Tier 2: within medium proximity ────────────────────────────────
    if dist <= t2_dist:
        # Check if this is a downgrade from tier1 proximity (dist ≤ 500m but class=1)
        if dist <= t1_dist and mh_valid and mh_class < t1_class:
            reason_extra = (
                f" Note: within {t1_dist:.0f}m threshold but "
                f"{mh_ctx} (Lower class — below Tier 1 class threshold ≥ {t1_class})."
            )
        else:
            reason_extra = ""
        return (
            thresholds["tier2"]["label"],
            (f"Centroid within {t2_dist:.0f}m of Candidate Red Zone "
             f"(distance: {dist:.0f}m, nearest: {zone_id}). "
             f"{mh_ctx} at centroid.{reason_extra}"),
            f"dist ≤ {t2_dist:.0f}m"
        )

    # ── Tier 3: monitoring distance ─────────────────────────────────────
    if dist <= t3_dist:
        return (
            thresholds["tier3"]["label"],
            (f"Centroid within {t3_dist:.0f}m of Candidate Red Zone "
             f"(distance: {dist:.0f}m, nearest: {zone_id}). "
             f"{mh_ctx} at centroid. Within monitoring proximity band."),
            f"dist ≤ {t3_dist:.0f}m"
        )

    # ── Beyond proximity ────────────────────────────────────────────────
    return (
        thresholds["beyond"]["label"],
        (f"Centroid beyond {t3_dist:.0f}m from nearest Candidate Red Zone "
         f"(distance: {dist:.0f}m, nearest: {zone_id}). "
         f"{mh_ctx} at centroid. Outside monitoring proximity band."),
        f"dist > {t3_dist:.0f}m"
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main() -> dict:
    _banner("SIH26191 — Step 10B + 10C: Village Vulnerability & Priority")
    t_start = datetime.datetime.utcnow()
    print(f"  Started: {t_start.strftime('%Y-%m-%dT%H:%M:%SZ')}")

    # ── Output directory ─────────────────────────────────────────────────
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Output directory: {_OUTPUT_DIR.relative_to(_ROOT)}")

    # ── Load configs ──────────────────────────────────────────────────────
    _section("Loading configurations")
    _load_yaml(_CONFIG_MAIN, "project.yaml")  # validate exists
    thresholds = _load_yaml(_CONFIG_PRIORITY, "priority_thresholds.yaml")

    print(f"  Tier 1: dist ≤ {thresholds['tier1']['max_distance_m']}m "
          f"AND mh_class ≥ {thresholds['tier1']['min_mh_class']}")
    print(f"  Tier 2: dist ≤ {thresholds['tier2']['max_distance_m']}m")
    print(f"  Tier 3: dist ≤ {thresholds['tier3']['max_distance_m']}m")
    print(f"  Beyond: dist > {thresholds['tier3']['max_distance_m']}m")

    # ── Define input paths ────────────────────────────────────────────────
    paths = {
        "hab_exposure": _ROOT / "data/processed/exposure/habitation_exposure.geojson",
        "pca_census":   _ROOT / "data/raw/habitations/PCA_CDB-0503-F-Census.xlsx",
        "mh_score":     _ROOT / "data/processed/hazards/multihazard_score.tif",
        "mh_class":     _ROOT / "data/processed/hazards/multihazard_classes.tif",
        "terrain":      _ROOT / "data/processed/hazards/terrain_susceptibility_proxy.tif",
        "flood":        _ROOT / "data/processed/hazards/flood_exposure_proxy.tif",
    }

    _section("Input file verification")
    all_found = True
    for name, p in paths.items():
        status = "FOUND" if p.exists() else "MISSING"
        if status == "MISSING" and name in ("hab_exposure", "mh_class", "mh_score"):
            all_found = False
        print(f"  {status:7s}: {name} → {p.relative_to(_ROOT)}")

    if not all_found:
        raise FileNotFoundError(
            "Critical input files missing. Cannot proceed. "
            "Ensure Steps 4–8 have been completed."
        )

    # =========================================================================
    # PHASE 10B — Village Vulnerability Attribution
    # =========================================================================
    _banner("Phase 10B — Village Vulnerability Attribution")

    # 1. Load habitation exposure
    hab_gdf = load_habitation_exposure(paths["hab_exposure"])
    n_villages = len(hab_gdf)

    # 2. Sample rasters at centroids
    raster_fields = {
        "mh_score_at_centroid":    paths["mh_score"],
        "mh_class_at_centroid":    paths["mh_class"],
        "terrain_score_at_centroid": paths["terrain"],
        "flood_score_at_centroid": paths["flood"],
    }
    raster_samples = sample_rasters_at_centroids(hab_gdf, raster_fields)

    for field, values in raster_samples.items():
        hab_gdf[field] = values

    # Clean mh_class: valid values are 1, 2, 3; nodata=255 → NaN
    if "mh_class_at_centroid" in hab_gdf.columns:
        def _clean_class(v):
            if pd.isna(v):
                return np.nan
            iv = int(round(float(v)))
            return float(iv) if iv in (1, 2, 3) else np.nan

        hab_gdf["mh_class_at_centroid"] = hab_gdf["mh_class_at_centroid"].apply(_clean_class)

        _section("MH class distribution at village centroids")
        for cls in [1, 2, 3]:
            n = (hab_gdf["mh_class_at_centroid"] == float(cls)).sum()
            print(f"  Class {cls}: {n} villages ({100*n/n_villages:.1f}%)")
        n_nodata = hab_gdf["mh_class_at_centroid"].isna().sum()
        print(f"  NoData:  {n_nodata} villages ({100*n_nodata/n_villages:.1f}%)")

    # 3. Load PCA Census
    pca_villages, pca_available, pca_unavailable = load_pca_census(paths["pca_census"])

    # 4. Compute vulnerability indicators
    indicators_gdf, computed_ind, unavail_ind = compute_vulnerability_indicators(
        hab_gdf, pca_villages, pca_available
    )

    # 5. Add metadata fields
    indicators_gdf["data_source"] = (
        "Census PCA 2011 (SHRUG spatial bridge join) + "
        "Step 6 raster sampling (multihazard_classes.tif, "
        "multihazard_score.tif, terrain_susceptibility_proxy.tif, "
        "flood_exposure_proxy.tif)"
    )
    indicators_gdf["step10b_methodology"] = _METHODOLOGY_NOTE
    indicators_gdf["step10b_disclaimer"] = _DISCLAIMER
    indicators_gdf["computed_indicators"] = "; ".join(computed_ind) if computed_ind else "NONE"
    indicators_gdf["unavailable_indicators"] = "; ".join(unavail_ind) if unavail_ind else "NONE"

    # 6. Select output columns (ordered, existing only)
    ind_cols = [
        "village_id", "village_name", "tot_pop", "households",
        "pop_sc", "pop_st",
        # Vulnerability indicators (context only)
        "illiteracy_rate", "child_proportion", "sc_proportion",
        "st_proportion", "non_worker_rate",
        # Raster samples
        "mh_score_at_centroid", "mh_class_at_centroid",
        "terrain_score_at_centroid", "flood_score_at_centroid",
        # Proximity (Step 8)
        "nearest_hazard_distance_m", "proximity_band",
        "nearest_zone_id", "direct_zone_overlap", "hazard_zone_label",
        # Identifiers
        "shrid2",
        # Metadata
        "pca_join_status", "data_source",
        "computed_indicators", "unavailable_indicators",
        "step10b_methodology", "step10b_disclaimer",
        "geometry",
    ]
    ind_cols = [c for c in ind_cols if c in indicators_gdf.columns]
    indicators_out = indicators_gdf[ind_cols].copy()

    # 7. Save
    _section("Saving village_priority_indicators.gpkg")
    out_ind_path = _OUTPUT_DIR / "village_priority_indicators.gpkg"
    indicators_out.to_file(str(out_ind_path), driver="GPKG", layer="village_priority_indicators")
    sz = out_ind_path.stat().st_size
    print(f"  Saved: {out_ind_path.relative_to(_ROOT)} ({sz:,} bytes)")
    print(f"  Features: {len(indicators_out)} | CRS: {indicators_out.crs}")

    # =========================================================================
    # PHASE 10C — Village Priority Classification
    # =========================================================================
    _banner("Phase 10C — Rule-Based Village Priority Classification")

    print("  Applying rule-based classification to each village...")
    print("  (Rules loaded from configs/priority_thresholds.yaml)")

    tiers: List[str] = []
    reasons: List[str] = []
    rules: List[str] = []

    for _, row in indicators_gdf.iterrows():
        tier, reason, rule = classify_priority(row, thresholds)
        tiers.append(tier)
        reasons.append(reason)
        rules.append(rule)

    profiles_gdf = indicators_gdf.copy()
    profiles_gdf["priority_tier"] = tiers
    profiles_gdf["priority_reason"] = reasons
    profiles_gdf["priority_applied_rule"] = rules

    # Tier display labels
    tier_labels = {
        thresholds["tier1"]["label"]:  thresholds["tier1"]["display_label"],
        thresholds["tier2"]["label"]:  thresholds["tier2"]["display_label"],
        thresholds["tier3"]["label"]:  thresholds["tier3"]["display_label"],
        thresholds["beyond"]["label"]: thresholds["beyond"]["display_label"],
        "Unknown": "Unknown — classification error",
    }
    profiles_gdf["priority_tier_display"] = (
        profiles_gdf["priority_tier"].map(tier_labels).fillna("Unknown")
    )

    # Disaster history status
    dh = thresholds.get("disaster_history", {})
    profiles_gdf["disaster_history_status"] = dh.get("status", "NOT_ACQUIRED")
    profiles_gdf["disaster_history_note"] = dh.get("note", "")

    # Methodology status
    profiles_gdf["methodology_status"] = _METHODOLOGY_NOTE
    profiles_gdf["step10c_disclaimer"] = _DISCLAIMER

    # ── Print tier distribution ───────────────────────────────────────────
    _section("Priority tier distribution")
    tier_summary = {}
    for tier in [
        thresholds["tier1"]["label"],
        thresholds["tier2"]["label"],
        thresholds["tier3"]["label"],
        thresholds["beyond"]["label"],
        "Unknown",
    ]:
        mask = profiles_gdf["priority_tier"] == tier
        n = int(mask.sum())
        if n == 0:
            continue
        pop = int(profiles_gdf.loc[mask, "tot_pop"].sum())
        hh = int(profiles_gdf.loc[mask, "households"].sum())
        label = tier_labels.get(tier, tier)
        print(f"  {label}:")
        print(f"    Villages: {n}  |  Population: {pop:,}  |  Households: {hh:,}")
        tier_summary[tier] = {"count": n, "population": pop, "households": hh,
                               "display_label": label}

    # ── Select output columns ─────────────────────────────────────────────
    prof_cols = [
        "village_id", "village_name", "tot_pop", "households",
        "pop_sc", "pop_st",
        # Vulnerability context
        "illiteracy_rate", "child_proportion", "sc_proportion",
        "st_proportion", "non_worker_rate",
        # Hazard context
        "mh_score_at_centroid", "mh_class_at_centroid",
        "terrain_score_at_centroid", "flood_score_at_centroid",
        # Proximity
        "nearest_hazard_distance_m", "proximity_band",
        "nearest_zone_id", "direct_zone_overlap", "hazard_zone_label",
        # Priority classification
        "priority_tier", "priority_tier_display",
        "priority_reason", "priority_applied_rule",
        # Status
        "disaster_history_status", "disaster_history_note",
        "pca_join_status", "methodology_status",
        "step10c_disclaimer",
        # Identifiers
        "shrid2",
        "geometry",
    ]
    prof_cols = [c for c in prof_cols if c in profiles_gdf.columns]
    profiles_out = profiles_gdf[prof_cols].copy()

    # ── Save ─────────────────────────────────────────────────────────────
    _section("Saving village_priority_profiles.gpkg")
    out_prof_path = _OUTPUT_DIR / "village_priority_profiles.gpkg"
    profiles_out.to_file(str(out_prof_path), driver="GPKG", layer="village_priority_profiles")
    sz = out_prof_path.stat().st_size
    print(f"  Saved: {out_prof_path.relative_to(_ROOT)} ({sz:,} bytes)")
    print(f"  Features: {len(profiles_out)} | CRS: {profiles_out.crs}")

    # ── Timing ────────────────────────────────────────────────────────────
    t_end = datetime.datetime.utcnow()
    elapsed = (t_end - t_start).total_seconds()

    _banner(f"Step 10B + 10C Complete ({elapsed:.1f}s)")
    print(f"  {out_ind_path.relative_to(_ROOT)}")
    print(f"  {out_prof_path.relative_to(_ROOT)}")
    print()
    print(f"  DISCLAIMER: {_DISCLAIMER}")

    return {
        "indicators_path": str(out_ind_path),
        "profiles_path": str(out_prof_path),
        "n_villages": n_villages,
        "tier_summary": tier_summary,
        "computed_indicators": computed_ind,
        "unavailable_indicators": unavail_ind,
        "elapsed_seconds": round(elapsed, 2),
        "generated_utc": t_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2))
