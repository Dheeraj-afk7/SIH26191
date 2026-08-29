#!/usr/bin/env python3
"""
SIH26191 — Step 3B.1: DEM CRS Validation
==============================================================================
Validates that the raw DEM's coordinate reference system (CRS) matches the
storage CRS configured in configs/project.yaml, and that the configured
analysis CRS is a projected metric system suitable for distance / area work.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

PURPOSE
-------
This step confirms:
  1. The DEM carries an embedded CRS.
  2. The DEM's actual CRS matches configs → crs.storage_crs  (EPSG:4326).
  3. The configured storage CRS is geographic (lat/lon).
  4. The configured analysis CRS is projected.
  5. The analysis CRS uses metric (metre) linear units.

DESIGN NOTE
-----------
Storage/display CRS and metric analysis CRS are intentionally separate:
  EPSG:4326 is used for geographic storage and presentation,
  while the configured analysis CRS is reserved for operations
  requiring metric distance or area calculations.

SCOPE
-----
  * Validation ONLY — the DEM is opened in read-only mode.
  * No raster is written, modified, or reprojected.
  * All CRS values are read from project.yaml; nothing is hardcoded.

USAGE
-----
    python scripts/validate_dem_crs.py
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Third-party imports — fail early with a clear message if missing
# ---------------------------------------------------------------------------
try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML is not installed.  Run:  pip install pyyaml")
    sys.exit(1)

try:
    import rasterio
except ImportError:
    print("[ERROR] rasterio is not installed.  Run:  pip install rasterio")
    sys.exit(1)

try:
    from pyproj import CRS as ProjCRS
    PYPROJ_AVAILABLE = True
except ImportError:
    print("[WARN]  pyproj is not installed — axis/unit checks will be skipped.")
    print("        Run:  pip install pyproj")
    PYPROJ_AVAILABLE = False


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _sep(char: str = "=", width: int = 66) -> str:
    """Return a horizontal separator string."""
    return char * width


def _section(title: str) -> None:
    """Print a clearly delimited section header."""
    print(f"\n{_sep('-')}")
    print(f"  {title}")
    print(_sep('-'))


def _field(label: str, value, width: int = 34) -> None:
    """Print a labelled field in a consistent aligned format."""
    print(f"  {label:<{width}}: {value}")


def _result(label: str, ok: bool, detail: str = "") -> bool:
    """
    Print a [PASS] / [FAIL] line.

    Returns the same `ok` value so callers can accumulate it with AND logic.
    """
    tag  = "[PASS]" if ok else "[FAIL]"
    line = f"  {tag}  {label}"
    if detail:
        line += f"  ({detail})"
    print(line)
    return ok


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(root_dir: Path) -> dict:
    """Load and return configs/project.yaml as a dict."""
    config_path = root_dir / "configs" / "project.yaml"
    if not config_path.is_file():
        print(f"[FAIL] Configuration file not found: {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        print("[FAIL] project.yaml did not parse to a dict.")
        sys.exit(1)
    return cfg


def _require(cfg: dict, *keys: str) -> str:
    """
    Walk nested dict keys and return the value.
    Exits with a clear message if any key is missing or empty.
    """
    node = cfg
    path = ".".join(keys)
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            print(f"[FAIL] Required config key '{path}' is missing from project.yaml.")
            sys.exit(1)
        node = node[k]
    if node is None or str(node).strip() == "":
        print(f"[FAIL] Required config key '{path}' is empty in project.yaml.")
        sys.exit(1)
    return str(node).strip()


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------

def validate_crs(root_dir: Path, cfg: dict) -> bool:
    """
    Run all CRS validation checks and return True only if every check passes.
    """
    overall = True   # will be AND-ed with each individual check result

    # ------------------------------------------------------------------
    # Read values from config
    # ------------------------------------------------------------------
    dem_rel          = _require(cfg, "paths", "dem_raw")
    storage_crs_str  = _require(cfg, "crs", "storage_crs")
    analysis_crs_str = _require(cfg, "crs", "analysis_crs_metric")

    dem_path = root_dir / dem_rel

    # ------------------------------------------------------------------
    # Section 1 — Configuration summary
    # ------------------------------------------------------------------
    _section("1. CONFIGURATION (read from configs/project.yaml)")
    _field("paths.dem_raw",           dem_rel)
    _field("crs.storage_crs",         storage_crs_str)
    _field("crs.analysis_crs_metric", analysis_crs_str)

    # ------------------------------------------------------------------
    # Section 2 — DEM file check
    # ------------------------------------------------------------------
    _section("2. DEM FILE CHECK")

    file_ok = dem_path.is_file()
    _field("DEM path", dem_path)
    overall &= _result("DEM file exists", file_ok)

    if not file_ok:
        # Cannot proceed without the file
        return False

    # ------------------------------------------------------------------
    # Section 3 — Actual DEM CRS (rasterio, read-only)
    # ------------------------------------------------------------------
    _section("3. ACTUAL DEM CRS  (rasterio — read-only)")

    try:
        with rasterio.open(dem_path) as src:
            actual_crs = src.crs
    except Exception as e:
        print(f"\n[FAIL] rasterio could not open the DEM: {e}")
        return False

    has_crs = actual_crs is not None
    _field("Actual DEM CRS",          actual_crs if has_crs else "NOT SET")
    overall &= _result("DEM has an embedded CRS", has_crs)

    if not has_crs:
        return False   # remaining checks all depend on a valid CRS

    # Normalise actual CRS to a canonical authority string for comparison
    actual_crs_auth = actual_crs.to_epsg()   # returns int or None
    actual_crs_str  = f"EPSG:{actual_crs_auth}" if actual_crs_auth else str(actual_crs)

    # ------------------------------------------------------------------
    # Section 4 — CRS match: actual vs configured storage CRS
    # ------------------------------------------------------------------
    _section("4. CRS MATCH  (actual DEM vs configured storage CRS)")

    _field("Actual DEM CRS (canonical)",   actual_crs_str)
    _field("Configured storage CRS",       storage_crs_str)

    # Normalise configured storage CRS for comparison
    try:
        configured_storage_epsg = int(storage_crs_str.upper().replace("EPSG:", ""))
        crs_match = (actual_crs_auth == configured_storage_epsg)
    except (ValueError, AttributeError):
        # Fallback: string comparison
        crs_match = (actual_crs_str.upper() == storage_crs_str.upper())

    overall &= _result(
        "Actual DEM CRS matches configured storage CRS",
        crs_match,
        f"actual={actual_crs_str}, configured={storage_crs_str}",
    )

    # ------------------------------------------------------------------
    # Section 5 — pyproj deeper analysis (if available)
    # ------------------------------------------------------------------
    _section("5. CRS TYPE & UNIT ANALYSIS  (pyproj)")

    if not PYPROJ_AVAILABLE:
        print("  [SKIP] pyproj not available — install with:  pip install pyproj")
        print("         Axis and unit checks were not performed.")
    else:
        # ---- Storage CRS ----
        try:
            proj_storage = ProjCRS.from_user_input(storage_crs_str)
            is_geographic = proj_storage.is_geographic
            is_projected  = proj_storage.is_projected

            storage_type = (
                "geographic" if is_geographic else
                "projected"  if is_projected  else
                "other"
            )
            _field("Storage CRS type", storage_type)
            overall &= _result(
                "Storage CRS is geographic (lat/lon)",
                is_geographic,
                f"type={storage_type}",
            )

        except Exception as e:
            overall &= _result("Storage CRS pyproj parse", False, str(e))

        # ---- Analysis CRS ----
        try:
            proj_analysis = ProjCRS.from_user_input(analysis_crs_str)
            is_proj_analysis = proj_analysis.is_projected

            analysis_type = (
                "geographic" if proj_analysis.is_geographic else
                "projected"  if is_proj_analysis             else
                "other"
            )
            _field("Analysis CRS type", analysis_type)
            overall &= _result(
                "Analysis CRS is projected",
                is_proj_analysis,
                f"type={analysis_type}",
            )

            # Unit check — walk the axis list for the linear unit
            try:
                axes = proj_analysis.axis_info
                unit_names = [ax.unit_name.lower() for ax in axes]
                _field("Analysis CRS axis units", ", ".join(
                    f"{ax.name}: {ax.unit_name}" for ax in axes
                ))
                is_metric = any("metre" in u or "meter" in u for u in unit_names)
                overall &= _result(
                    "Analysis CRS uses metric units (metres)",
                    is_metric,
                    f"units={unit_names}",
                )
            except Exception as e:
                overall &= _result("Analysis CRS unit check", False, str(e))

        except Exception as e:
            overall &= _result("Analysis CRS pyproj parse", False, str(e))

    # ------------------------------------------------------------------
    # Section 6 — Design note (always printed)
    # ------------------------------------------------------------------
    _section("6. DESIGN NOTE — DUAL-CRS ARCHITECTURE")
    print(
        "  Storage/display CRS and metric analysis CRS are intentionally separate:\n"
        "  EPSG:4326 is used for geographic storage and presentation,\n"
        "  while the configured analysis CRS is reserved for operations\n"
        "  requiring metric distance or area calculations."
    )

    return overall


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Project root is one level above this script (scripts/ → root)
    root_dir = Path(__file__).resolve().parent.parent

    print(_sep("="))
    print("  SIH26191 — STEP 3B.1: DEM CRS VALIDATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    # Load project configuration
    print(f"\n  Config : configs/project.yaml")
    cfg = load_config(root_dir)
    print("  [OK]    Configuration loaded successfully.")

    # Run all validation checks
    passed = validate_crs(root_dir, cfg)

    # Final verdict
    print(f"\n{_sep('=')}")
    if passed:
        print("  CRS VALIDATION: PASS")
    else:
        print("  CRS VALIDATION: FAIL")
    print(_sep("="))

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
