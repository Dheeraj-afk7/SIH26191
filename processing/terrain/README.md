# processing/terrain — Terrain Processing Module

**Project:** SIH26191 — Intelligent Identification of Hazard-Based Red Zones,
Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable
Habitations
**Pilot:** Rudraprayag District, Uttarakhand, India

---

## Purpose

This module derives terrain layers from the verified raw DEM for use in
downstream decision-support analysis. All processing is deterministic,
reproducible, and read-only with respect to the raw DEM.

---

## Input

| Item | Value |
|------|-------|
| Raw DEM | `data/raw/copernicus_glo30_rudraprayag.tif` |
| DEM source | Copernicus GLO-30 (~30 m nominal resolution) |
| Raw DEM CRS | EPSG:4326 (WGS 84, geographic) |
| DEM status | **Read-only — must never be modified** |

The DEM path is read dynamically from `configs/project.yaml → paths.dem_raw`.
It is never hardcoded inside processing scripts.

---

## CRS Strategy

The raw DEM is stored in EPSG:4326 (decimal degrees). Terrain derivatives
(slope, aspect) require metric pixel spacing for scientifically valid gradient
calculations. The pipeline therefore:

1. Reprojects the raw DEM in-memory to the configured analysis CRS
   (`configs/project.yaml → crs.analysis_crs_metric`, default: **EPSG:32644**
   — WGS 84 / UTM Zone 44N).
2. Performs all gradient calculations in metric pixel space.
3. Saves derived outputs with the **analysis CRS** embedded in the output
   raster metadata (EPSG:32644).

> **Important:** Slope calculated by treating degree-spacing as metres would
> be scientifically incorrect. The reprojection step is mandatory.

---

## Derived Outputs

All derived outputs are written to `data/processed/terrain/`.

| Layer | File | Unit | CRS |
|-------|------|------|-----|
| Slope | `slope_degrees.tif` | degrees (0–90) | EPSG:32644 |
| Aspect | `aspect_degrees.tif` | degrees (0–360) | EPSG:32644 |

### Slope Convention
- Range: 0° (flat) to 90° (vertical cliff).
- Calculated from the gradient magnitude of the metric-reprojected DEM.
- NoData regions propagated from the source DEM.

### Aspect Convention
- 0° / 360° = North
- 90° = East
- 180° = South
- 270° = West
- Flat / undefined terrain is represented as −1 (or NoData where appropriate).
  See `derive_aspect.py` for the documented handling choice.

---

## Processing Rules

| Rule | Description |
|------|-------------|
| **Read-only raw DEM** | No script in this module writes to `data/raw/`. |
| **No overwrite of raw data** | Outputs go exclusively to `data/processed/terrain/`. |
| **Config-driven paths** | All file paths and CRS values are read from `configs/project.yaml`. |
| **Metric CRS for calculations** | Gradient operations use EPSG:32644, not raw degree spacing. |
| **Metadata preservation** | Output rasters include correct CRS, transform, and NoData. |
| **Deterministic** | Same input → same output. No stochastic steps. |
| **No hazard classification** | This module produces terrain geometry layers only. |

---

## Suitability Statement

Outputs from this module are **decision-support terrain layers**. They are:

✅ Suitable for:
- Pilot-scale terrain screening
- Regional slope and aspect characterisation
- Decision-support input to hazard zone candidate identification

❌ NOT sufficient for:
- Parcel-level engineering design
- Geotechnical site certification
- Guaranteed site safety determination
- Any legally certified terrain accuracy claim

---

## Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| `derive_slope.py` | `processing/terrain/` | Compute slope_degrees.tif |
| `derive_aspect.py` | `processing/terrain/` | Compute aspect_degrees.tif |

---

## Running

```bash
python processing/terrain/derive_slope.py
python processing/terrain/derive_aspect.py
```

Validate outputs:

```bash
python scripts/validate_terrain_outputs.py
```
