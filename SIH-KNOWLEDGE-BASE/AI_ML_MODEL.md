# AI / ML & Deterministic Decision Engine: SIH26191

## Core Modeling Paradigm: Deterministic Physics-Based GIS & Rule Engine

> **Mandatory Scientific Stance:** In accordance with `PROJECT_SPEC.md` Section 2.4 and `PROJECT_FORENSIC_AUDIT.md`, core spatial hazard screening, red zone identification, village prioritization, and relocation site feasibility are governed by **deterministic, physics-based, and explainable rule-based spatial algorithms**.
>
> Uncalibrated black-box Machine Learning models (such as deep neural networks or opaque random forests) were **intentionally excluded from safety-critical classification paths** to prevent hallucinations, guarantee 100% reproducibility, and ensure that district administrators can transparently justify life-safety decisions to local communities and disaster authorities.

---

## 1. Primary Algorithmic Components

### Module A: Physical Terrain Gradient & Aspect Derivation
- **Model Type:** Deterministic 2D Finite-Difference Elevation Gradient Operator.
- **Model Architecture:** Metric spatial convolution computing partial derivatives of elevation ($\partial z / \partial x, \partial z / \partial y$) across a $30\text{m}$ digital elevation grid in projected UTM Zone 44N space (`EPSG:32644`):
  $$\text{Slope}_{\text{rad}} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right), \quad \text{Slope}_{\text{deg}} = \text{Slope}_{\text{rad}} \times \frac{180}{\pi}$$
  $$\text{Aspect}_{\text{math}} = \text{atan2}\left(-\frac{\partial z}{\partial y}, \frac{\partial z}{\partial x}\right), \quad \text{Aspect}_{\text{geo}} = (90 - \text{deg}(\text{Aspect}_{\text{math}})) \pmod{360}$$
- **Input:** Copernicus GLO-30 DEM 32-bit floating-point elevation raster.
- **Output:** Continuous slope raster (`slope_degrees.tif`) and compass aspect raster (`aspect_degrees.tif`).
- **Inference Process:** Deterministic grid convolution executed via `rasterio` and `numpy`.

---

### Module B: D8 Hydrological Accumulation & Topographic Wetness Index (TWI)
- **Model Type:** Deterministic D8 Downhill Flow Routing & Beven-Kirkby Hydrological Model (Beven & Kirkby, 1979).
- **Model Architecture:**
  - **D8 Flow Direction:** Assigns drainage to the steepest downward slope among 8 adjacent grid neighbors ($2^0$ to $2^7$ bit-encoding).
  - **Topological Flow Accumulation:** Ingests elevation-sorted grid queue to accumulate upstream contributing area ($a = \text{pixels} \times \text{cell\_size}_m$).
  - **Topographic Wetness Index (TWI):**
    $$\text{TWI} = \ln\left(\frac{a}{\tan\beta}\right)$$
    Where $\beta = \max(\text{Slope}_{\text{rad}}, 0.1^\circ \times \frac{\pi}{180})$ (numerical singularity safeguard).
- **Input:** GLO-30 DEM and metric slope raster.
- **Output:** Flow direction, flow accumulation, and Topographic Wetness Index rasters (`topographic_wetness_index.tif`).
- **Inference Process:** Topologically sorted recursive upstream area accumulation.

---

### Module C: Continuous Multi-Hazard Proxy & Intensity Grading
- **Model Type:** Multi-Factor Linear Weighted Overlay Proxy Model.
- **Model Architecture:**
  - **Terrain Susceptibility Proxy ($T$):** Continuous linear scaling of slope over the critical failure interval $[0^\circ, 60^\circ]$:
    $$T(\theta) = \text{clip}\left(\frac{\theta - 0.0^\circ}{60.0^\circ - 0.0^\circ}, 0.0, 1.0\right)$$
  - **Flood Exposure Proxy ($F$):** Continuous linear scaling of TWI over empirical saturation range $[3.5, 13.5]$:
    $$F(\text{TWI}) = \text{clip}\left(\frac{\text{TWI} - 3.5}{13.5 - 3.5}, 0.0, 1.0\right)$$
  - **Multi-Hazard Score ($M$):** Equal-weight multi-hazard synthesis:
    $$M(x,y) = 0.5 \cdot T(x,y) + 0.5 \cdot F(x,y)$$
  - **Intensity Band Classification:**
    - Class 1 (Lower Intensity): $M < 0.35$
    - Class 2 (Moderate Intensity): $0.35 \le M < 0.65$
    - Class 3 (Higher / Very High Intensity): $M \ge 0.65$
- **Input:** Slope and TWI rasters.
- **Output:** Continuous multi-hazard score raster (`multihazard_score.tif`) and discrete 3-tier classification raster (`multihazard_classes.tif`).

---

### Module D: Morphological Image Segmentation & Red Zone Polygonization
- **Model Type:** Binary Connected-Component Labeling with Minimum Mapping Unit (MMU) Filter.
- **Model Architecture:**
  - Isolates binary raster mask where $\text{Multi-Hazard Class} == 3$.
  - Applies 8-neighbor connectivity structuring element ($3 \times 3$ kernel) via `scipy.ndimage.label`.
  - Filters micro-clusters below the Minimum Mapping Unit: $\text{Area} < 5,000\text{ m}^2$ (~0.5 ha, ~6 pixels).
  - Vectorizes contiguous clusters into OGC polygon geometries with zonal summary statistics.
- **Input:** Multi-hazard class raster and continuous score raster.
- **Output:** 289 Candidate Hazard-Based Red Zone polygons (`candidate_hazard_based_red_zones.geojson`).

---

### Module E: Deterministic Relocation Priority Decision Engine
- **Model Type:** Rule-Based Expert Decision Logic Engine.
- **Model Architecture:**
  - Evaluates spatial point-in-polygon containment and nearest-boundary Euclidean distance ($d$) in metric space.
  - Applies hard safety constraints and proximity thresholds stored in `configs/priority_thresholds.yaml`:
    ```python
    if direct_zone_overlap == True:
        tier = "Tier1_AttentionPriority"
        horizon = "IMMEDIATE_FIELD_ASSESSMENT"  # 0-1 years
    elif nearest_hazard_distance_m <= 500.0 and mh_class_at_centroid >= 2:
        tier = "Tier1_AttentionPriority"
        horizon = "IMMEDIATE_FIELD_ASSESSMENT"  # 0-1 years
    elif nearest_hazard_distance_m <= 2000.0:
        tier = "Tier2_ElevatedAttention"
        horizon = "SHORT_TERM_PLANNING_REVIEW"   # 1-3 years
    elif nearest_hazard_distance_m <= 5000.0:
        tier = "Tier3_Monitoring"
        horizon = "MEDIUM_TERM_MONITORING"       # 3-10 years
    else:
        tier = "BeyondProximity"
        horizon = "ROUTINE_MONITORING"           # 10+ years
    ```
- **Input:** Habitation centroid coordinates, candidate red zone polygons, multi-hazard rasters.
- **Output:** Prioritized habitation profiles (`village_priority_profiles.gpkg`): 12 Tier 1, 69 Tier 2, 204 Tier 3, 368 Beyond Proximity habitations.

---

### Module F: PMAY-G Rural Housing Spatial Capacity Model
- **Model Type:** Normative Architectural Capacity Scenario Model.
- **Model Architecture:**
  - Evaluates gross polygon area ($A$) of candidate topographically feasible sites ($\text{slope} \le 20^\circ$, hazard-excluded, ESA WorldCover non-forest).
  - Applies $40\%$ net buildable site utilization efficiency ($\eta = 0.40$):
    $$\text{Usable Area } (m^2) = A \times 0.40$$
  - Applies Ministry of Rural Development PMAY-G housing norm ($25\text{ m}^2/\text{HH}$):
    $$\text{Estimated Households} = \left\lfloor \frac{\text{Usable Area}}{25.0\text{ m}^2/\text{HH}} \right\rfloor$$
    $$\text{Estimated Population} = \text{Estimated Households} \times 4.0\text{ persons/HH}$$
  - Scale Protection Rule: If $A > 100.0\text{ ha}$, capacity is not calculated (`AREA_EXCEEDS_SITE_PLANNING_SCALE`).
- **Input:** Candidate site polygons and `configs/capacity.yaml`.
- **Output:** Attributed candidate area capacity context (`candidate_area_context.gpkg`).

---

## 2. Optional AI/ML / RAG SOP Assistant Component
- **Model Type:** Retrieval-Augmented Generation (RAG) Architecture (LangChain / Vector Store / LLM).
- **Purpose:** Standard Operating Procedure (SOP) Q&A assistant for explaining disaster mitigation guidelines, PMAY-G schemes, and project metadata.
- **Model Architecture:** Text embedding model + Vector Store indexing structured Markdown knowledge documents + Chat LLM generator.
- **Safety Boundary:** The RAG assistant operates strictly as an informational user interface. **It has ZERO write access to spatial rasters, priority scoring tables, or site allocation databases.** It never governs safety-critical decisions.

---

## 3. Training & Optimization Specifications

- **Training Methodology:** Not applicable. (Physics-based terrain modeling and rule-based decision trees; no model fitting or weight optimization required).
- **Loss Function:** Not applicable.
- **Optimizer:** Not applicable.
- **Hyperparameters:** Declarative physical thresholds stored in YAML configuration files:
  - Slope hazard interval: $[0.0^\circ, 60.0^\circ]$
  - TWI saturation interval: $[3.5, 13.5]$
  - Multi-hazard class thresholds: Lower ($<0.35$), Moderate ($0.35–0.65$), Higher ($\ge 0.65$)
  - Minimum Mapping Unit (MMU) for Red Zones: $5,000\text{ m}^2$
  - Candidate relocation site slope limit: $\le 20.0^\circ$
  - Candidate relocation site area bounds: $1.0\text{ ha}$ to $10.0\text{ ha}$
  - Relocation buffer thresholds: $500\text{m}$ (Tier 1), $2,000\text{m}$ (Tier 2), $5,000\text{m}$ (Tier 3)
  - PMAY-G standard: $25.0\text{ m}^2/\text{HH}$, $40\%$ efficiency, $4.0\text{ persons/HH}$
- **Training Procedure:** Not applicable.

---

## 4. Evaluation, Baselines & Comparison

- **Evaluation Metrics:**
  - Spatial Join Match Rate: $100\%$ ($653/653$ Census villages matched to SHRUG centroids).
  - Deterministic Classification Consistency: $100\%$ (Zero unclassified or ambiguous villages).
  - API Contract Test Pass Rate: $100\%$ ($18/18$ Pytest assertions passed in automated test suite).
  - Physical Conservation Check: $C_{\text{terrain}} + C_{\text{flood}} == M(x,y)$ verified across $>3.5\text{M}$ pixels within float32 precision.
- **Baselines & Comparison:**
  - *Vs. Uninterpretable Machine Learning (Random Forest / CNN):* ML models require thousands of ground-truth landslide polygons for local training, frequently suffer from spatial overfitting, and function as opaque black boxes that cannot be audited during administrative appeals. The deterministic GIS pipeline provides transparent, audit-ready formulas.
  - *Vs. Ad-Hoc Political Relocation Planning:* Replaces subjective post-disaster representations with standardized, reproducible spatial metrics across all 653 habitations.
- **Why Selected Approach Was Used:** Legal, ethical, and administrative necessity. Disaster management authorities require explainable, legally defensible justifications before investing public funds in infrastructure relocation or advising community resettlement.
