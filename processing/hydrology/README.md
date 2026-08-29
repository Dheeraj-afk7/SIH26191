# Hydrology Processing Module — Step 5

## Purpose
The `processing/hydrology` module provides the deterministic hydrological screening foundation for the **SIH26191** decision-support pipeline in Rudraprayag District, Uttarakhand, India. It computes standardized, reproducible, physics-based topographic hydrological indicators from the verified Digital Elevation Model (Copernicus GLO-30) to evaluate relative terrain predisposition to runoff concentration, drainage convergence, and potential flood exposure.

---

## Input Datasets
All processing is strictly configuration-driven (`configs/project.yaml`) and utilizes verified datasets:
1. **Raw Digital Elevation Model (Copernicus GLO-30)**:
   - Path: `data/raw/copernicus_glo30_rudraprayag.tif`
   - Access: Strictly **READ-ONLY** (never modified).
   - In-memory metric reprojection to EPSG:32644 (UTM Zone 44N, ~29.11 m resolution).
2. **Derived Slope Raster (Step 3)**:
   - Path: `data/processed/terrain/slope_degrees.tif`
   - CRS: EPSG:32644.
   - Purpose: Local slope angle ($\beta$) for Topographic Wetness Index calculation.

---

## Methodology & Formulations

### 1. D8 Flow Direction (`flow_direction.tif`)
- **Method**: Standard 8-direction deterministic steepest downhill descent (O'Callaghan & Mark, 1984; Jenson & Domingue, 1988).
- **Metric Distance Calculation**: Uses true metric distances for orthogonal ($dx, dy$) and diagonal ($\sqrt{dx^2 + dy^2}$) neighbors.
- **Encoding (ESRI standard)**:
  - $1 = \text{East } (0, +1)$
  - $2 = \text{Southeast } (+1, +1)$
  - $4 = \text{South } (+1, 0)$
  - $8 = \text{Southwest } (+1, -1)$
  - $16 = \text{West } (0, -1)$
  - $32 = \text{Northwest } (-1, -1)$
  - $64 = \text{North } (-1, 0)$
  - $128 = \text{Northeast } (-1, +1)$
  - $0 = \text{Local sink / flat / edge termination}$
  - $255 = \text{NoData}$

### 2. Flow Accumulation (`flow_accumulation.tif`)
- **Method**: Topological elevation-sorted downhill cell accumulation.
- **Unit**: Count of contributing grid cells (where each cell starts with an initial weight of 1.0).
- **Physical Meaning**: Cumulative upslope area contributing overland drainage to each cell.

### 3. Topographic Wetness Index (`topographic_wetness_index.tif`)
- **Method**: Beven & Kirkby (1979) Topographic Wetness Index (TWI):
  $$\text{TWI} = \ln\left(\frac{a}{\tan\beta}\right)$$
  where:
  - $a = \text{Specific catchment area} = \text{Accumulation} \times \text{cell\_size}$ (in metres)
  - $\beta = \text{Slope angle in radians}$
- **Numerical Safeguards**:
  - Slope floor $\beta_{\min} = 0.1^\circ$ (configured in `project.yaml`) prevents division by zero ($\tan 0 = 0$) and infinite singularities.
  - Accumulation is strictly $\ge 1.0$, ensuring $a > 0$ and $\ln(\cdot)$ is strictly real and finite.
  - NoData pixels from the source DEM are preserved as `NaN`.

### 4. Terrain-Derived Flood Exposure Proxy (`flood_exposure_proxy.tif`)
- **Formula**:
  $$F(\text{TWI}) = \text{clip}\left(\frac{\text{TWI} - \text{TWI}_{\min}}{\text{TWI}_{\max} - \text{TWI}_{\min}}, 0.0, 1.0\right)$$
  where $\text{TWI}_{\min} = 3.5$ (dry shedding crests) and $\text{TWI}_{\max} = 13.5$ (major river channels and confluences).
- **Properties**: Strictly continuous, monotonic, and bounded within $[0.0000, 1.0000]$.

### 5. Transparent Screening Categories (`flood_exposure_classes.tif`)
- **Class 1 (Lower Indicator)**: Score $[0.00, 0.35)$ ($\text{TWI} < 7.00$) — Ridge tops, steep slopes, low catchment area.
- **Class 2 (Moderate Indicator)**: Score $[0.35, 0.65)$ ($\text{TWI } 7.00 - 10.00$) — Concave hollows, secondary tributaries, lower valley slopes.
- **Class 3 (Higher Indicator)**: Score $[0.65, 1.00]$ ($\text{TWI} \ge 10.00$) — Main river corridors (Alaknanda, Mandakini), floodplains, channel confluences.
- **NoData (255)**: Outside administrative boundary / DEM NoData.

---

## Output Datasets

| Output File | Location | Format | Dtype | NoData | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `flow_direction.tif` | `data/processed/hydrology/` | GeoTIFF | `uint8` | 255 | D8 steepest descent flow directions |
| `flow_accumulation.tif` | `data/processed/hydrology/` | GeoTIFF | `float32` | NaN | Cumulative upslope contributing cell count |
| `topographic_wetness_index.tif` | `data/processed/hydrology/` | GeoTIFF | `float32` | NaN | Beven-Kirkby Topographic Wetness Index |
| `flood_exposure_proxy.tif` | `data/processed/hazards/` | GeoTIFF | `float32` | NaN | Normalized continuous flood exposure score [0.0 - 1.0] |
| `flood_exposure_classes.tif` | `data/processed/hazards/` | GeoTIFF | `uint8` | 255 | 3-tier preliminary screening classification (1, 2, 3) |

---

## Scientific Limitations & Explicit Non-Claims

> [!WARNING]
> **MANDATORY GOVERNANCE & NON-PREDICTIVE DISCLAIMER**:
> This module produces **TERRAIN-DERIVED SCREENING INDICATORS** for intermediate spatial decision support.
> 
> **Explicit Non-Claims**:
> 1. **NOT a Flood Prediction or Forecast**: This layer does NOT predict when, where, or if a flood event will occur.
> 2. **NOT a Flood Inundation Probability**: Does not model hydrodynamic flood frequencies (e.g. 25-yr, 50-yr, 100-yr return periods).
> 3. **NOT an Official Flood Hazard Zone**: Does not substitute for Central Water Commission (CWC) or State Disaster Management Authority (SDMA) official flood plain zonation.
> 4. **NOT an Authorization for Relocation or Evacuation**: Cannot be used unilaterally to enforce red zones or habitational displacement.

### Missing Critical Hydrological Factors:
1. **Dynamic Precipitation**: Real-time or forecasted monsoon rainfall intensity, cloudburst triggers, or snowmelt dynamics.
2. **Hydraulic Parameters**: River cross-sections, Manning's roughness ($n$), bankfull discharge, stage-discharge rating curves.
3. **Upstream Infrastructure**: Hydroelectric dam releases, barrages (e.g. Srinagar dam upstream/downstream impacts), culverts, drainage bottlenecks.
4. **Soil & Subsurface Hydrology**: Infiltration capacity, hydraulic conductivity, soil moisture saturation dynamics.
5. **Observed Inundation Records**: Historical flood event footprints (e.g. June 2013 Kedarnath disaster inundation surveys).
6. **Hydrodynamic Modeling**: 1D/2D Saint-Venant hydraulic wave propagation modeling (HEC-RAS, TUFLOW, etc.).
