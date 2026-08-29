# processing/multihazard — Multi-Hazard Integration Module

**Project:** SIH26191 — Intelligent Identification of Hazard-Based Red Zones,
Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations  
**Pilot District:** Rudraprayag District, Uttarakhand, India  
**Pipeline Step:** Step 6 — Transparent Multi-Hazard Integration

---

## 1. Purpose & Scope

The purpose of this module is to integrate two upstream deterministic screening proxies:
1. **Terrain-Derived Landslide Susceptibility Proxy** ($T \in [0.0, 1.0]$) from Step 4
2. **Terrain-Derived Flood Exposure Proxy** ($F \in [0.0, 1.0]$) from Step 5

into a single unified **Multi-Hazard Screening Indicator** ($M \in [0.0, 1.0]$), accompanied by transparent **Screening Classes** and pixel-level **Contribution / Explainability Layers**.

This output serves as an intermediate, transparent decision-support indicator for multi-hazard terrain screening.

---

## 2. Inputs & Data Provenance

| Input Layer | Pipeline Step | Source Dataset | CRS | Resolution | Data Type | Value Range |
|-------------|---------------|----------------|-----|------------|-----------|-------------|
| `data/processed/hazards/terrain_susceptibility_proxy.tif` | Step 4 | Metric Slope (Copernicus GLO-30 DEM) | EPSG:32644 | ~29.11 m | Float32 | $[0.0000, 1.0000]$ |
| `data/processed/hazards/flood_exposure_proxy.tif` | Step 5 | Topographic Wetness Index (TWI) | EPSG:32644 | ~29.11 m | Float32 | $[0.0000, 1.0000]$ |

Both layers are strictly verified as spatially co-registered on an identical metric grid ($1854 \times 2458$ pixels) with identical NoData masks (4,392,717 valid terrain pixels).

---

## 3. Integration Methodology & Mathematical Formulation

### 3.1 Linear Weighted Combination
The multi-hazard screening score $M(x, y)$ at any spatial location $(x, y)$ is calculated using a deterministic linear weighted combination:

$$M(x, y) = \big(w_{\text{terrain}} \times T(x, y)\big) + \big(w_{\text{flood}} \times F(x, y)\big)$$

Where:
- $M(x, y)$: Continuous Multi-Hazard Screening Score $\in [0.0, 1.0]$
- $T(x, y)$: Terrain-Derived Landslide Susceptibility Proxy $\in [0.0, 1.0]$
- $F(x, y)$: Terrain-Derived Flood Exposure Proxy $\in [0.0, 1.0]$
- $w_{\text{terrain}}$: Configured weight for terrain susceptibility ($0.5$)
- $w_{\text{flood}}$: Configured weight for flood exposure ($0.5$)

### 3.2 Weighting Scheme & Methodological Rationale
- **Configured Weights:** $w_{\text{terrain}} = 0.5$, $w_{\text{flood}} = 0.5$ (configured dynamically in `configs/project.yaml`).
- **Constraint:** $w_{\text{terrain}} + w_{\text{flood}} = 1.00$ strictly enforced and validated.
- **Scientific Justification for Equal Weights:**  
  In the absence of empirical, multi-decadal historical disaster loss inventories calibrated for Rudraprayag District, assigning subjective or unequal weights would introduce unscientific bias and false precision. An equal-weight formulation is established as an explicit, transparent, uncalibrated screening baseline.

### 3.3 NoData Policy
If either input raster contains a NoData value ($\text{NaN}$) at pixel $(x, y)$, the resulting multi-hazard score is assigned $\text{NaN}$ (and class code `255`), strictly preserving invalid/unmapped extents.

---

## 4. Transparent Classification Scheme

The continuous score $M$ is partitioned into transparent screening categories configured in `configs/project.yaml`:

| Class Code | Category Label | Score Range ($M$) | Screening Interpretation |
|:----------:|:---------------|:-----------------:|:--------------------------|
| **1** | **Lower Multi-Hazard Indicator** | $[0.00, 0.35)$ | Lower combined topographic slope and hydrological convergence predisposition. |
| **2** | **Moderate Multi-Hazard Indicator** | $[0.35, 0.65)$ | Moderate combined slope steepness or intermediate hydrological accumulation. |
| **3** | **Higher Multi-Hazard Indicator** | $[0.65, 1.00]$ | High combined terrain susceptibility (steep escarpments/flanks) and/or high flood convergence (valley corridors/alluvial confluences). |
| **255** | **NoData / Out of Extent** | — | Unmapped or invalid pixels propagated from upstream DEM mask. |

---

## 5. Explainability & Contribution Layers

To guarantee 100% transparency and auditability, Step 6 generates individual component contribution layers:

1. **Terrain Contribution Layer:**  
   $$C_{\text{terrain}}(x, y) = w_{\text{terrain}} \times T(x, y)$$  
   Path: `data/processed/hazards/terrain_contribution.tif`

2. **Flood Contribution Layer:**  
   $$C_{\text{flood}}(x, y) = w_{\text{flood}} \times F(x, y)$$  
   Path: `data/processed/hazards/flood_contribution.tif`

### Verification of Explainability
For every valid pixel $(x, y)$:
$$C_{\text{terrain}}(x, y) + C_{\text{flood}}(x, y) = M(x, y) \quad (\pm 10^{-6}\text{ numerical tolerance})$$

Any user or planner querying a specific grid cell can immediately see the exact relative driving factors behind its multi-hazard screening indicator.

---

## 6. Generated Output Datasets

| Dataset Path | Driver / Format | CRS | Dimensions | Resolution | Data Type | NoData | Description |
|--------------|-----------------|-----|------------|------------|-----------|--------|-------------|
| `data/processed/hazards/multihazard_score.tif` | GTiff | EPSG:32644 | $1854 \times 2458$ | ~29.11 m | Float32 | `nan` | Continuous combined multi-hazard screening score $[0.0, 1.0]$ |
| `data/processed/hazards/multihazard_classes.tif` | GTiff | EPSG:32644 | $1854 \times 2458$ | ~29.11 m | UInt8 | `255` | Classified multi-hazard screening levels (1, 2, 3) |
| `data/processed/hazards/terrain_contribution.tif` | GTiff | EPSG:32644 | $1854 \times 2458$ | ~29.11 m | Float32 | `nan` | Spatial contribution of terrain susceptibility $[0.0, 0.5]$ |
| `data/processed/hazards/flood_contribution.tif` | GTiff | EPSG:32644 | $1854 \times 2458$ | ~29.11 m | Float32 | `nan` | Spatial contribution of flood exposure $[0.0, 0.5]$ |

---

## 7. What This Output Represents vs. What It Does NOT Represent

### ✅ What It Represents:
- A transparent, reproducible, and explainable decision-support indicator combining morphological landslide susceptibility and hydrological flow accumulation.
- An objective spatial screening baseline for comparing multi-hazard terrain exposure across Rudraprayag District.

### ❌ What It Does NOT Represent:
- **NOT an official government hazard map or Red Zone.**
- **NOT a disaster prediction or real-time early warning.**
- **NOT a guarantee of landslide failure or flood inundation.**
- **NOT a declaration of land as "safe" or "unsafe".**
- **NOT an evacuation order or relocation authorization.**

---

## 8. Scientific Assumptions & Limitations

1. **Morphometric Foundation:** Derived entirely from a static 30 m digital elevation model (Copernicus GLO-30).
2. **Missing Dynamic & Subsurface Factors:** Does not account for real-time monsoon rainfall intensity, cloudbursts, soil pore-water pressure, lithology, bedrock bedding planes, structural faults, river hydraulic channel geometries, or vegetative cover.
3. **Linearity Assumption:** Uses linear additive combination; non-linear cascading hazard interactions (e.g., landslide-dammed lake outburst floods) require specialized hydrodynamic and numerical geotechnical simulation.
4. **Intermediate Status:** Final Candidate Hazard-Based Red Zones require downstream multi-criteria thresholding, spatial aggregation, and contextual habitation analysis (Steps 7–8).
