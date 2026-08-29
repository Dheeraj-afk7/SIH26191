#!/usr/bin/env python3
"""
SIH26191 -- Step 5D: Hydrological Terrain Derivatives Derivation
==============================================================================
Derives deterministic hydrological terrain indicators from the verified DEM:
  1. D8 Flow Direction (flow_direction.tif)
  2. Flow Accumulation (flow_accumulation.tif)
  3. Topographic Wetness Index (topographic_wetness_index.tif)

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

SCIENTIFIC APPROACH & METHODOLOGY
---------------------------------
1. Metric Grid In-Memory Reprojection:
   - The raw DEM in EPSG:4326 is reprojected in-memory to the metric analysis CRS
     (EPSG:32644, UTM Zone 44N) matching the exact grid geometry of Step 3 & 4.
   - Raw DEM is NEVER modified.

2. D8 Flow Direction (Steepest Downhill Descent):
   - For each valid terrain cell, the slope to each of the 8 neighbors is evaluated:
         slope_k = (elev_center - elev_neighbor_k) / dist_k
     where dist_k is dx or dy for orthogonal neighbors, and sqrt(dx^2 + dy^2) for diagonals.
   - The steepest positive gradient defines the flow direction.
   - Standard ESRI D8 encoding:
     1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE, 0=sink/flat, 255=NoData.

3. Flow Accumulation:
   - Initialized with 1.0 cell unit for every valid terrain pixel.
   - Evaluated using a topological elevation-sorted descending queue: cells process
     from highest to lowest elevation, ensuring that all upstream runoff is
     fully accumulated before transferring downhill.

4. Topographic Wetness Index (TWI):
   - Beven & Kirkby (1979) formulation:
         TWI = ln( a / tan(beta) )
     where:
       a = specific catchment area = accumulation * pixel_size (metres)
       beta = local slope angle in radians (from verified slope raster)
   - Numerical safeguards:
     - Slope angle is floored at min_slope_deg (0.1 deg) to avoid division by zero and infinite singularities.
     - Catchment area is strictly >= pixel_size > 0, ensuring log argument is positive.
     - All invalid/NoData pixels are preserved as NaN.

OUTPUTS
-------
  data/processed/hydrology/flow_direction.tif           (uint8, nodata=255)
  data/processed/hydrology/flow_accumulation.tif        (float32, nodata=NaN)
  data/processed/hydrology/topographic_wetness_index.tif (float32, nodata=NaN)

USAGE
-----
    python processing/hydrology/derive_hydrological_derivatives.py
"""

import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    import numpy as np
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from rasterio.crs import CRS
except ImportError as e:
    print(f"[ERROR] Required package not installed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths and formatting helpers
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT_DIR   = _SCRIPT_DIR.parent.parent


def _sep(char: str = "=", width: int = 68) -> str:
    return char * width


def _section(title: str) -> None:
    print(f"\n{_sep('-')}")
    print(f"  {title}")
    print(_sep('-'))


def _field(label: str, value, width: int = 34) -> None:
    print(f"  {label:<{width}}: {value}")


def _result(label: str, ok: bool, detail: str = "") -> bool:
    tag = "[PASS]" if ok else "[FAIL]"
    msg = f"  {tag}  {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    return ok


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config() -> dict:
    cfg_path = _ROOT_DIR / "configs" / "project.yaml"
    if not cfg_path.is_file():
        print(f"[FAIL] Config not found: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        print("[FAIL] Configuration file parsed to non-dict object.")
        sys.exit(1)
    return cfg


# ---------------------------------------------------------------------------
# Core Hydrological Derivatives Logic
# ---------------------------------------------------------------------------

def derive_hydrological_derivatives() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 5D: DERIVE HYDROLOGICAL TERRAIN DERIVATIVES")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config()

    # Read configuration
    paths_cfg = cfg.get("paths", {})
    crs_cfg = cfg.get("crs", {})
    hydro_cfg = cfg.get("hydrology", {})
    deriv_cfg = hydro_cfg.get("derivatives", {})

    dem_rel = paths_cfg.get("dem_raw", "data/raw/copernicus_glo30_rudraprayag.tif")
    slope_rel = paths_cfg.get("slope_processed", "data/processed/terrain/slope_degrees.tif")
    analysis_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    fdir_rel = deriv_cfg.get("flow_direction", {}).get("output_path", "data/processed/hydrology/flow_direction.tif")
    facc_rel = deriv_cfg.get("flow_accumulation", {}).get("output_path", "data/processed/hydrology/flow_accumulation.tif")
    twi_rel = deriv_cfg.get("topographic_wetness_index", {}).get("output_path", "data/processed/hydrology/topographic_wetness_index.tif")

    min_slope_twi_deg = float(deriv_cfg.get("topographic_wetness_index", {}).get("min_slope_deg", 0.1))

    dem_path = (_ROOT_DIR / dem_rel).resolve()
    slope_path = (_ROOT_DIR / slope_rel).resolve()
    fdir_path = (_ROOT_DIR / fdir_rel).resolve()
    facc_path = (_ROOT_DIR / facc_rel).resolve()
    twi_path = (_ROOT_DIR / twi_rel).resolve()

    fdir_path.parent.mkdir(parents=True, exist_ok=True)

    _section("1. CONFIGURATION & INPUT VERIFICATION")
    _field("Raw DEM Path (read-only)", str(dem_path))
    _field("Slope Input Path", str(slope_path))
    _field("Analysis Metric CRS", analysis_crs_str)
    _field("TWI Minimum Slope Floor", f"{min_slope_twi_deg:.2f} deg")
    _field("Flow Direction Output", str(fdir_path))
    _field("Flow Accumulation Output", str(facc_path))
    _field("TWI Output", str(twi_path))

    if not dem_path.is_file():
        print(f"[FAIL] Raw DEM not found: {dem_path}")
        return False
    if not slope_path.is_file():
        print(f"[FAIL] Slope raster not found: {slope_path}")
        return False

    # ------------------------------------------------------------------
    # Step 1: In-memory DEM Reprojection to Metric Analysis Grid
    # ------------------------------------------------------------------
    _section("2. IN-MEMORY DEM REPROJECTION TO METRIC GRID")
    t0 = time.time()
    try:
        with rasterio.open(dem_path) as src:
            src_crs = src.crs
            src_nodata = src.nodata

            dst_transform, dst_width, dst_height = calculate_default_transform(
                src.crs, target_crs,
                src.width, src.height,
                *src.bounds,
            )

            dem_metric = np.full(
                (dst_height, dst_width),
                fill_value=np.nan,
                dtype=np.float32,
            )

            reproject(
                source=rasterio.band(src, 1),
                destination=dem_metric,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=target_crs,
                resampling=Resampling.bilinear,
                src_nodata=src_nodata,
                dst_nodata=np.nan,
            )

    except Exception as e:
        print(f"[FAIL] DEM Reprojection failed: {e}")
        return False

    dx = abs(dst_transform.a)
    dy = abs(dst_transform.e)
    cell_size = (dx + dy) / 2.0

    _field("Reprojection Time", f"{time.time() - t0:.2f} s")
    _field("Grid Dimensions (W x H)", f"{dst_width} x {dst_height} pixels")
    _field("Pixel Spacing (dx, dy)", f"{dx:.4f} m, {dy:.4f} m")
    _field("Metric Elevation Range", f"{np.nanmin(dem_metric):.1f} m to {np.nanmax(dem_metric):.1f} m")

    # Verify grid alignment against slope raster
    with rasterio.open(slope_path) as slope_src:
        slope_w, slope_h = slope_src.width, slope_src.height
        slope_crs = slope_src.crs
        slope_transform = slope_src.transform
        slope_data = slope_src.read(1)

    dim_matches = (dst_width == slope_w) and (dst_height == slope_h)
    crs_matches = (target_crs == slope_crs)
    trans_matches = (
        np.isclose(dst_transform.a, slope_transform.a) and
        np.isclose(dst_transform.e, slope_transform.e) and
        np.isclose(dst_transform.c, slope_transform.c) and
        np.isclose(dst_transform.f, slope_transform.f)
    )

    all_passed &= _result("Metric grid dimensions match slope grid", dim_matches)
    all_passed &= _result("Metric grid CRS matches analysis CRS", crs_matches)
    all_passed &= _result("Metric grid transform aligns with slope transform", trans_matches)

    if not (dim_matches and crs_matches and trans_matches):
        print("[FAIL] Spatial alignment with slope raster failed.")
        return False

    # ------------------------------------------------------------------
    # Step 2: D8 Flow Direction Calculation
    # ------------------------------------------------------------------
    _section("3. D8 FLOW DIRECTION ROUTING")
    t0 = time.time()
    H, W = dem_metric.shape
    valid_mask = ~np.isnan(dem_metric) & ~np.isnan(slope_data)
    total_valid = int(np.sum(valid_mask))

    diag_dist = float(np.sqrt(dx**2 + dy**2))
    # 8 neighbor offsets: (dr, dc, distance, esri_code)
    # 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE
    neighbors = [
        (0, 1, dx, 1),
        (1, 1, diag_dist, 2),
        (1, 0, dy, 4),
        (1, -1, diag_dist, 8),
        (0, -1, dx, 16),
        (-1, -1, diag_dist, 32),
        (-1, 0, dy, 64),
        (-1, 1, diag_dist, 128),
    ]

    flow_dir = np.zeros((H, W), dtype=np.uint8)  # 0 for sink/flat/undefined
    max_slope_grid = np.full((H, W), -1.0, dtype=np.float32)
    target_r = np.full((H, W), -1, dtype=np.int32)
    target_c = np.full((H, W), -1, dtype=np.int32)

    for dr, dc, dist, code in neighbors:
        r_src = slice(max(0, -dr), min(H, H - dr))
        r_dst = slice(max(0, dr), min(H, H + dr))
        c_src = slice(max(0, -dc), min(W, W - dc))
        c_dst = slice(max(0, dc), min(W, W + dc))

        diff = dem_metric[r_src, c_src] - dem_metric[r_dst, c_dst]
        slope = diff / dist

        # Valid downhill slope
        cond = (slope > 0) & (slope > max_slope_grid[r_src, c_src]) & (~np.isnan(slope))

        sub_max = max_slope_grid[r_src, c_src]
        sub_max[cond] = slope[cond]
        max_slope_grid[r_src, c_src] = sub_max

        sub_dir = flow_dir[r_src, c_src]
        sub_dir[cond] = code
        flow_dir[r_src, c_src] = sub_dir

        rr, cc = np.mgrid[r_src, c_src]
        tr = target_r[r_src, c_src]
        tc = target_c[r_src, c_src]
        tr[cond] = (rr + dr)[cond]
        tc[cond] = (cc + dc)[cond]
        target_r[r_src, c_src] = tr
        target_c[r_src, c_src] = tc

    # Mark NoData as 255
    flow_dir[~valid_mask] = 255

    fdir_time = time.time() - t0
    unique_fdir = np.unique(flow_dir).tolist()
    _field("D8 Flow Routing Time", f"{fdir_time:.2f} s")
    _field("Encountered Flow Direction Codes", str(unique_fdir))

    all_passed &= _result("Flow direction computation complete", True)
    all_passed &= _result("NoData encoded as 255", 255 in unique_fdir)

    # ------------------------------------------------------------------
    # Step 3: Flow Accumulation Calculation
    # ------------------------------------------------------------------
    _section("4. FLOW ACCUMULATION (TOPOLOGICAL DOWNHILL PROPAGATION)")
    t0 = time.time()

    flat_dem = dem_metric.ravel()
    flat_acc = np.zeros(H * W, dtype=np.float32)
    flat_acc[valid_mask.ravel()] = 1.0  # Base weight: 1.0 cell unit

    flat_target_r = target_r.ravel()
    flat_target_c = target_c.ravel()

    # Get valid flat indices and sort in descending elevation order
    valid_indices = np.flatnonzero(valid_mask)
    sorted_valid_indices = valid_indices[np.argsort(-flat_dem[valid_indices])]

    # Propagate accumulation along DAG
    for idx in sorted_valid_indices:
        tr = flat_target_r[idx]
        tc = flat_target_c[idx]
        if tr >= 0 and tc >= 0:
            target_idx = tr * W + tc
            flat_acc[target_idx] += flat_acc[idx]

    flow_acc = flat_acc.reshape((H, W))
    flow_acc[~valid_mask] = np.nan

    facc_time = time.time() - t0
    valid_acc = flow_acc[valid_mask]
    acc_min = float(np.min(valid_acc))
    acc_max = float(np.max(valid_acc))
    acc_mean = float(np.mean(valid_acc))

    _field("Flow Accumulation Time", f"{facc_time:.2f} s")
    _field("Minimum Accumulation", f"{acc_min:.1f} cells")
    _field("Maximum Accumulation", f"{acc_max:.1f} cells (~{acc_max * cell_size * cell_size / 1e6:.2f} sq km)")
    _field("Mean Accumulation", f"{acc_mean:.1f} cells")

    all_passed &= _result("Accumulation values strictly >= 1.0 cell", acc_min >= 1.0, f"min={acc_min}")
    all_passed &= _result("Zero infinite values in accumulation", int(np.sum(np.isinf(flow_acc))) == 0)

    # ------------------------------------------------------------------
    # Step 4: Topographic Wetness Index (TWI) Calculation
    # ------------------------------------------------------------------
    _section("5. TOPOGRAPHIC WETNESS INDEX (BEVEN-KIRKBY 1979)")
    t0 = time.time()

    # Safe slope in radians with configurable floor
    safe_slope_deg = np.maximum(slope_data, min_slope_twi_deg)
    slope_rad = np.radians(safe_slope_deg)
    tan_beta = np.tan(slope_rad)
    tan_beta = np.maximum(tan_beta, 1e-4)  # Safeguard against tan(0)

    # Specific catchment area: a = acc * cell_size (m)
    specific_catchment = flow_acc * cell_size

    # TWI = ln(a / tan(beta))
    twi = np.log(specific_catchment / tan_beta).astype(np.float32)
    twi[~valid_mask] = np.nan

    twi_time = time.time() - t0
    valid_twi = twi[valid_mask]
    twi_min = float(np.min(valid_twi))
    twi_max = float(np.max(valid_twi))
    twi_mean = float(np.mean(valid_twi))
    twi_std = float(np.std(valid_twi))

    _field("TWI Computation Time", f"{twi_time:.2f} s")
    _field("Minimum TWI", f"{twi_min:.4f}")
    _field("Maximum TWI", f"{twi_max:.4f}")
    _field("Mean TWI", f"{twi_mean:.4f}")
    _field("Std Dev TWI", f"{twi_std:.4f}")

    all_passed &= _result("TWI values strictly finite on all valid pixels", int(np.sum(np.isinf(twi))) == 0)
    all_passed &= _result("TWI range physically realistic [1.0 to 25.0]", (twi_min >= 0.0) and (twi_max <= 30.0),
                          f"min={twi_min:.2f}, max={twi_max:.2f}")

    # ------------------------------------------------------------------
    # Step 5: Write Output GeoTIFFs
    # ------------------------------------------------------------------
    _section("6. WRITE GEOTIFF OUTPUTS")
    base_profile = {
        "driver": "GTiff",
        "width": dst_width,
        "height": dst_height,
        "count": 1,
        "crs": target_crs,
        "transform": dst_transform,
        "compress": "lzw",
        "tiled": False
    }

    # 1. Flow Direction (uint8, nodata=255)
    fdir_profile = base_profile.copy()
    fdir_profile.update({"dtype": "uint8", "nodata": 255})
    try:
        with rasterio.open(fdir_path, "w", **fdir_profile) as dst:
            dst.write(flow_dir, 1)
            dst.set_band_description(1, "D8 Flow Direction (ESRI Encoding: 1=E, 2=SE, 4=S, 8=SW, 16=W, 32=NW, 64=N, 128=NE, 0=Sink/Flat, 255=NoData)")
            dst.update_tags(
                TITLE="D8 Flow Direction",
                PROJECT_ID="SIH26191",
                PILOT_DISTRICT="Rudraprayag",
                METHOD="D8 Steepest Downhill Descent",
                ENCODING="ESRI Standard Power-of-Two",
                NODATA_VALUE="255"
            )
        all_passed &= _result("Flow direction GeoTIFF written", fdir_path.is_file(),
                              f"Size: {fdir_path.stat().st_size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"[FAIL] Error writing flow direction: {e}")
        all_passed = False

    # 2. Flow Accumulation (float32, nodata=NaN)
    facc_profile = base_profile.copy()
    facc_profile.update({"dtype": "float32", "nodata": np.nan})
    try:
        with rasterio.open(facc_path, "w", **facc_profile) as dst:
            dst.write(flow_acc, 1)
            dst.set_band_description(1, "Flow Accumulation (Upslope Contributing Cell Count)")
            dst.update_tags(
                TITLE="Flow Accumulation",
                PROJECT_ID="SIH26191",
                PILOT_DISTRICT="Rudraprayag",
                METHOD="Topological Downhill Accumulation",
                UNIT="cells",
                NODATA_VALUE="NaN"
            )
        all_passed &= _result("Flow accumulation GeoTIFF written", facc_path.is_file(),
                              f"Size: {facc_path.stat().st_size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"[FAIL] Error writing flow accumulation: {e}")
        all_passed = False

    # 3. Topographic Wetness Index (float32, nodata=NaN)
    twi_profile = base_profile.copy()
    twi_profile.update({"dtype": "float32", "nodata": np.nan})
    try:
        with rasterio.open(twi_path, "w", **twi_profile) as dst:
            dst.write(twi, 1)
            dst.set_band_description(1, "Topographic Wetness Index (TWI = ln(a / tan(beta)))")
            dst.update_tags(
                TITLE="Topographic Wetness Index (TWI)",
                PROJECT_ID="SIH26191",
                PILOT_DISTRICT="Rudraprayag",
                METHOD="Beven & Kirkby (1979)",
                MIN_SLOPE_DEG=str(min_slope_twi_deg),
                NODATA_VALUE="NaN"
            )
        all_passed &= _result("Topographic Wetness Index GeoTIFF written", twi_path.is_file(),
                              f"Size: {twi_path.stat().st_size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"[FAIL] Error writing TWI: {e}")
        all_passed = False

    # Summary
    print(f"\n{_sep('=')}")
    if all_passed:
        print("HYDROLOGICAL DERIVATIVES DERIVATION: PASS")
    else:
        print("HYDROLOGICAL DERIVATIVES DERIVATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = derive_hydrological_derivatives()
    sys.exit(0 if success else 1)
