# data/processed/hazards — Hazard Susceptibility Datasets

**Project:** SIH26191 — Intelligent Identification of Hazard-Based Red Zones,
Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations  
**Pilot District:** Rudraprayag District, Uttarakhand, India  
**Pipeline Step:** Step 4 — Terrain-Derived Landslide Susceptibility Proxy

---

## Mandatory Scientific Disclaimer

> **IMPORTANT:**  
> The datasets in this directory represent a **Terrain-Derived Landslide Susceptibility Proxy**
> and corresponding preliminary screening categories.
>
> **This layer is a terrain-derived susceptibility proxy and must not be interpreted as a landslide prediction, probability, engineering certification, or official hazard declaration.**
>
> It serves exclusively as an explainable, deterministic terrain decision-support layer. It must be integrated with downstream multi-factor evidence (geology, rainfall, drainage, land cover, road networks, historical landslide inventories, and in-situ geotechnical field validation) before any official spatial planning or hazard zone candidate identification can occur.

---

## 1. Input Datasets (Step 3 Terrain Derivatives)

| Dataset | Relative Path | CRS | Data Type | Units / Range | Role in Step 4 |
|---------|---------------|-----|-----------|---------------|----------------|
| **Slope** | `data/processed/terrain/slope_degrees.tif` | EPSG:32644 | Float32 | $0.0^\circ \text{ to } 79.45^\circ$ | **Primary Factor** — Topographic slope drives gravitational shear stress. |
| **Aspect** | `data/processed/terrain/aspect_degrees.tif` | EPSG:32644 | Float32 | $0.0^\circ \text{ to } 360.0^\circ$ (Flat: $-1.0$) | **Contextual Metadata** — Tracked with zero arbitrary hazard weighting. |

---

## 2. Output Datasets (Step 4 Hazards)

### 2.1 Continuous Terrain Susceptibility Proxy

- **Filename:** `terrain_susceptibility_proxy.tif`
- **Purpose:** Provide a continuous, normalized indicator of slope-driven terrain predisposition to instability.
- **Coordinate Reference System (CRS):** `EPSG:32644` (WGS 84 / UTM Zone 44N)
- **Data Type:** `Float32`
- **Raster Dimensions:** 1,854 columns $\times$ 2,458 rows (1 Band)
- **Pixel Resolution:** $\approx 29.11\text{ m} \times 29.11\text{ m}$
- **Value Range:** $[0.0000, 1.0000]$ (Dimensionless normalized score)
  - `0.0000`: Minimal slope contribution (flat terrain, $0.0^\circ$)
  - `1.0000`: Maximum slope predisposition saturation ($\ge 60.0^\circ$)
- **NoData Value / Handling:** `NaN` (Float32 NaN, exactly matching DEM NoData regions)
- **Compression:** LZW lossless compression
- **Transformation Formula:**
  $$\text{score} = \operatorname{clip}\left(\frac{\text{slope} - 0.0}{60.0 - 0.0}, 0.0, 1.0\right)$$

---

### 2.2 Terrain Susceptibility Screening Classes

- **Filename:** `terrain_susceptibility_classes.tif`
- **Purpose:** Provide standardized, transparent, explainable screening categories for decision-support and spatial query workflows.
- **Coordinate Reference System (CRS):** `EPSG:32644` (WGS 84 / UTM Zone 44N)
- **Data Type:** `UInt8`
- **Raster Dimensions:** 1,854 columns $\times$ 2,458 rows (1 Band)
- **Pixel Resolution:** $\approx 29.11\text{ m} \times 29.11\text{ m}$
- **NoData Value:** `255` (UInt8)
- **Compression:** LZW lossless compression

#### Class Code Definitions & Distribution

| Code | Screening Category Label | Score Range | Slope Range (Approx) | Pixel Count | % Valid Terrain | % Total Grid |
|:----:|:-------------------------|:-----------:|:--------------------:|:-----------:|:---------------:|:------------:|
| **1** | **Lower Terrain Susceptibility Indicator** | $[0.00, 0.35)$ | $< 21.0^\circ$ | 940,399 | 21.41% | 20.64% |
| **2** | **Moderate Terrain Susceptibility Indicator** | $[0.35, 0.65)$ | $21.0^\circ \text{ to } 39.0^\circ$ | 2,432,320 | 55.37% | 53.37% |
| **3** | **Higher Terrain Susceptibility Indicator** | $[0.65, 1.00]$ | $\ge 39.0^\circ$ | 1,019,998 | 23.22% | 22.38% |
| **255** | **NoData / Out of Analysis Extent** | — | — | 164,415 | — | 3.61% |
| **TOTAL** | — | — | — | **4,557,132** | **100.00%** | **100.00%** |

---

## 3. Methodological Principles

1. **Deterministic & Reproducible:** The continuous proxy and discrete classes are generated via explicit mathematical transformations defined in `configs/project.yaml`.
2. **Monotonicity:** Susceptibility score increases monotonically with slope steepness; higher slope never reduces susceptibility.
3. **No Arbitrary Factor Weights:** Aspect is documented contextually but assigned 0.0 weight to prevent arbitrary uncalibrated weighting.
4. **No Black-Box AI/ML:** No neural networks, random forests, or uncalibrated statistical models govern the spatial scores.

---

## 4. Known Scientific Limitations

Users and decision-makers must consider that this layer reflects **topographic steepness only**. It does NOT account for:
- Bedrock lithology, weathering, joint dip vs. slope face orientation
- Structural faults and thrust planes (e.g., Main Central Thrust zone)
- Colluvial / soil mantle depth and cohesion
- Subsurface pore-water pressure and drainage saturation
- Extreme monsoon precipitation / cloudburst events
- Land cover condition (forested vs. degraded/barren slopes)
- Road cutting, toe excavation, and anthropogenic slope destabilization
- Historical landslide occurrence records
- Ground-truth geotechnical field measurements

---

## 5. Multi-Hazard Integration Datasets (Step 6)

### 5.1 Continuous Multi-Hazard Screening Score
- **Filename:** `multihazard_score.tif`
- **Purpose:** Provide a combined, deterministic multi-hazard screening indicator integrating terrain-slope susceptibility and hydrological flood exposure.
- **CRS:** `EPSG:32644` (WGS 84 / UTM Zone 44N)
- **Data Type:** `Float32`
- **Dimensions:** 1,854 columns $\times$ 2,458 rows
- **Value Range:** $[0.1562, 0.8751]$ (Bounded $[0.0000, 1.0000]$)
- **NoData:** `NaN`
- **Formula:** $M = (0.50 \times T) + (0.50 \times F)$

### 5.2 Multi-Hazard Screening Classes
- **Filename:** `multihazard_classes.tif`
- **Purpose:** Discretized screening levels for regional risk screening and query workflows.
- **CRS:** `EPSG:32644`, Data Type: `UInt8`, NoData: `255`
- **Classes:**
  - Class 1: Lower Multi-Hazard Indicator ($[0.00, 0.35)$) — 1,964,406 px (44.72%)
  - Class 2: Moderate Multi-Hazard Indicator ($[0.35, 0.65)$) — 2,420,565 px (55.10%)
  - Class 3: Higher Multi-Hazard Indicator ($[0.65, 1.00]$) — 7,746 px (0.18%)

### 5.3 Explainability & Contribution Layers
- `terrain_contribution.tif` ($w_{\text{terrain}} \times T$, Float32, $[0.0000, 0.5000]$, Mean: 0.2534)
- `flood_contribution.tif` ($w_{\text{flood}} \times F$, Float32, $[0.0000, 0.5000]$, Mean: 0.1085)
- **Explainability Condition:** $\max(|C_{\text{terrain}} + C_{\text{flood}} - M|) = 0.00\text{e}+00$

---

## 6. Downstream Integration

This dataset is an intermediate decision-support product. In subsequent stages of the SIH26191 pipeline, it will be integrated with:
- Habitation footprint layers and settlement exposure (Step 8)
- Critical infrastructure and road vulnerability data
- Candidate relocation feasibility criteria (Step 9)
- Carrying capacity models (Step 10)

Under the project operating charter, **Step 6 outputs are intermediate screening indicators and do not declare official Red Zones or authorize relocation decisions.**

