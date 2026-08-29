# processing/hazards — Hazard Susceptibility Processing Module

**Project:** SIH26191 — Intelligent Identification of Hazard-Based Red Zones,
Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations  
**Pilot District:** Rudraprayag District, Uttarakhand, India  
**Pipeline Step:** Step 4 — Terrain-Derived Landslide Susceptibility Proxy

---

## 1. Purpose & Scope

The purpose of this module is to generate a **Terrain-Derived Landslide Susceptibility Proxy**
and corresponding **Screening Categories** using verified terrain derivative layers.

This module provides a scientific, deterministic, explainable, and reproducible
terrain screening indicator to serve as decision-support evidence in subsequent pipeline stages.

---

## 2. Terrain Variables & Scientific Role

| Terrain Variable | Status | Role in Susceptibility Proxy | Scientific Justification |
|------------------|--------|-----------------------------|---------------------------|
| **Slope Angle** | Available (`data/processed/terrain/slope_degrees.tif`) | **PRIMARY Factor** | Gravitational driving shear stress increases monotonically with slope angle. Steep slopes in the Himalayas are a primary physical predisposing condition for mass wasting and slope failure. |
| **Aspect** | Available (`data/processed/terrain/aspect_degrees.tif`) | **Contextual / Informational** | Slope orientation influences solar insolation and localized moisture retention. However, without empirical, district-validated historical landslide inventories and geological dip-slope interaction data, assigning arbitrary hazard weights to compass directions would be scientifically indefensible. Aspect is therefore tracked for contextual awareness with **zero arbitrary hazard weight**. |

### Scientific Rules Enforced:
1. **Slope is the Primary Factor:** Slope steepness drives the continuous susceptibility scoring function.
2. **No Arbitrary Aspect Weighting:** Compass aspect is preserved contextually but not assigned speculative hazard weights.
3. **Monotonicity:** Higher slope angles never produce a lower susceptibility score.
4. **No Black-Box Models:** No machine learning, neural networks, or uncalibrated statistical regressions are used.
5. **No Probability Claims:** The proxy represents relative terrain steepness predisposition, NOT a temporal probability or guarantee of failure.

---

## 3. Mathematical Methodology

### 3.1 Continuous Proxy Transformation
The slope measurement in degrees $\theta \in [0^\circ, 90^\circ]$ is transformed into a continuous screening score $S \in [0.0, 1.0]$ via a deterministic, monotonic piecewise-linear function configured in `configs/project.yaml`:

$$S(\theta) = \operatorname{clip}\left(\frac{\theta - \theta_{\min}}{\theta_{\max} - \theta_{\min}}, 0.0, 1.0\right)$$

Where:
- $\theta_{\min} = 0.0^\circ$ (baseline flat terrain)
- $\theta_{\max} = 60.0^\circ$ (saturation slope angle where steepness predisposition reaches maximum score 1.0)
- For invalid / NoData pixels: $S = \text{NaN}$

### 3.2 Transparent Screening Categories
The continuous score $S$ is partitioned into transparent screening categories configured in `configs/project.yaml`:

| Class Code | Category Label | Score Range ($S$) | Approximate Slope ($\theta$) | Geomorphic & Screening Description |
|:----------:|:---------------|:-----------------:|:-----------------------------:|:------------------------------------|
| **1** | **Lower Terrain Susceptibility Indicator** | $[0.00, 0.35)$ | $< 21.0^\circ$ | Valley floors, gentle terraces, and low-gradient terrain where topographic slope contributes relatively less gravitational driving stress. |
| **2** | **Moderate Terrain Susceptibility Indicator** | $[0.35, 0.65)$ | $21.0^\circ \le \theta < 39.0^\circ$ | Moderate valley flanks and hillside slopes common throughout the middle Himalayas; requires contextual evaluation with other evidence. |
| **3** | **Higher Terrain Susceptibility Indicator** | $[0.65, 1.00]$ | $\ge 39.0^\circ$ | Steep to precipitous escarpments, gorges, and high-relief slopes where gravitational shear stress is high. |
| **255** | **NoData / Out of Extent** | — | — | Unmapped or invalid pixels propagated from source DEM. |

---

## 4. Input & Output Datasets

### Inputs (Read-Only)
- `data/processed/terrain/slope_degrees.tif` (EPSG:32644, Float32, degrees)
- `data/processed/terrain/aspect_degrees.tif` (EPSG:32644, Float32, degrees / sentinel)

### Outputs Generated
- `data/processed/hazards/terrain_susceptibility_proxy.tif` (EPSG:32644, Float32, continuous range $[0.0, 1.0]$)
- `data/processed/hazards/terrain_susceptibility_classes.tif` (EPSG:32644, UInt8, class codes 1, 2, 3, NoData=255)

---

## 5. What This Output Represents vs. What It Does NOT Represent

### ✅ What It Represents:
- A transparent, reproducible spatial proxy of terrain-slope predisposition to instability.
- An objective metric terrain screening input for multi-factor decision-support analysis.

### ❌ What It Does NOT Represent:
- **NOT a landslide prediction or forecast.**
- **NOT a statistical probability of failure.**
- **NOT a declaration of "safe" or "unsafe" land.**
- **NOT an engineering certification or geotechnical site assessment.**
- **NOT an official government Hazard-Based Red Zone.**

---

## 6. Known Limitations & Missing Factors

This Step 4 output is strictly derived from 30 m digital elevation geometry. It currently does NOT incorporate:
1. **Lithology & Bedrock Geology** (rock mass strength, joint orientation, weathering grade)
2. **Structural Geology** (fault lines, shear zones, thrust planes)
3. **Soil Overburden Thickness & Cohesion**
4. **Hydrology & Drainage Networks** (pore-water pressure, spring heads, seepage lines)
5. **Precipitation Triggers** (monsoon rainfall intensity, cloudburst thresholds)
6. **Land Cover & Vegetation Root Cohesion** (dense forest vs. barren/degraded slopes)
7. **Anthropogenic Disturbances** (unsupported road cuts, toe excavation, quarrying)
8. **Historical Landslide Inventories** (verified past failure locations)
9. **Site-Specific Geotechnical In-Situ Testing**

---

## 7. Position in Overall Pipeline

```
Raw Copernicus DEM (GLO-30)
          ↓ (Step 3)
Metric Terrain Processing (EPSG:32644)
          ↓
  Slope & Aspect Rasters
          ↓ (Step 4)
Terrain-Derived Landslide Susceptibility Proxy & Classes (CURRENT STEP)
          ↓ (Future Steps)
Integration with Flood Exposure, Habitation Exposure & Multi-Factor Evidence
          ↓
Candidate Hazard-Based Red Zones (Subject to Human & Official Review)
```

> **CRITICAL RULE:** Step 4 output alone must NEVER be used to authorize relocations or declare red zones.
