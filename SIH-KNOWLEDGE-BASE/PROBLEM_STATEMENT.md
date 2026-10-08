# Problem Statement: SIH26191

## Official Problem Statement Details
- **Problem Statement ID:** 26191
- **Title:** Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations
- **Organization:** Ministry of Home Affairs (MoHA)
- **Department:** National Disaster Response Force (NDRF), Disaster Management Division
- **Category:** Software
- **Theme:** Disaster Management

---

## Official Problem Statement Description
> **Background:** India's disaster-prone regions face recurring hazards such as landslides, floods, coastal erosion, and cloudbursts. Vulnerable habitations often remain in unsafe zones, leading to repeated loss of lives and property. Current relocation efforts are largely reactive, initiated after disasters strike, rather than proactively planned.
>
> **Description:** The initiative seeks to develop an Intelligent, GIS-enabled decision support platform. This platform will dynamically identify and update multi-hazard Red Zones (areas unsuitable for permanent habitation), assess the carrying capacity of safer alternative sites, and prioritize vulnerable habitations for relocation. The system will integrate hazard intensity, population vulnerability, and disaster history to guide evidence-based decisions.
>
> **Expected Solution:** A robust, AI-driven GIS platform that maps and updates hazard-based Red Zones in real time, assesses suitability and carrying capacity of safer relocation sites, prioritizes vulnerable habitations for immediate, short-term, and medium-term relocation, and provides actionable insights to State Disaster Management Authorities for proactive planning.

---

## Traceable Functional Requirements (PS-1 to PS-9)

| Requirement ID | Requirement Scope | System Implementation & Status |
| :--- | :--- | :--- |
| **PS-1** | **Dynamically identify and update multi-hazard Red Zones** | Ingests 30m DEM derivatives, morphological 8-connectivity clustering, and provides operator-triggered dynamic recomputation via `POST /api/pipeline/recompute`. |
| **PS-2** | **Integrate hazard intensity** | Calculates continuous terrain susceptibility proxies (slope) and flood exposure proxies (TWI), classifying them into Low, Moderate, and High/Very High intensity bands. |
| **PS-3** | **Integrate population vulnerability** | Ingests Census 2011 PCA demographics across 653 habitations; computes child population, SC population, dependency, and illiteracy flags benchmarked at district $P_{75}$. |
| **PS-4** | **Integrate disaster history** | Curates 22 canonical historical disaster incidents (1998–2024; 6,913 fatalities) from NDMA, USDMA, and peer-reviewed literature, computing $1\text{ km}$ and $2\text{ km}$ exposure perimeters. |
| **PS-5** | **Assess suitability of safer alternative sites** | Multi-criteria spatial exclusion of hazard zones, steep slopes ($> 20^\circ$), water bodies, and dense forest, yielding 2,998 candidate feasible polygons ($1–10\text{ ha}$). |
| **PS-6** | **Assess carrying capacity of safer alternative sites** | Applies GoI PMAY-G $25\text{ m}^2/\text{HH}$ standard with $40\%$ net buildable efficiency and a $100\text{ ha}$ scale protection cap to model dwelling-unit and population capacity scenarios. |
| **PS-7** | **Prioritize vulnerable habitations for Immediate / Short-Term / Medium-Term relocation** | Categorizes habitations into 4 deterministic tiers mapped to official planning horizons: Immediate (0–1 yr), Short-Term (1–3 yr), Medium-Term (3–10 yr), and Routine (10+ yr). |
| **PS-8** | **Provide actionable insights to State Disaster Management Authorities** | Dedicated SDMA Authority Action Center with distance-sorted urgency queues, Sub-District Block aggregations (Ukhimath, Augustmuni, Jakholi), and downloadable CSV reports. |
| **PS-9** | **Support proactive planning (not purely reactive)** | Delivers a complete district-wide pre-disaster baseline screening of all 653 habitations before monsoon triggers. |

---

## Mandatory System Constraints & Scientific Bounds
1. **Decision Support Only (Non-Authorizing Stance):**
   - The platform provides *decision support, screening, and prioritization indicators*.
   - It **NEVER** independently authorizes relocation or issues mandatory evacuation orders.
   - All outputs legally require official administrative review, on-ground geotechnical site testing, and community consent.
2. **Deterministic & Explainable Core Logic (No Black-Box AI in Safety Decisions):**
   - Core spatial decision logic must remain 100% deterministic, rule-based, and auditable.
   - Machine Learning / AI must **never** govern safety-critical life-safety classifications or spatial scoring.
3. **Data Authenticity (No Fabricated Datasets):**
   - All spatial and demographic inputs must originate from verified, citable public datasets (e.g., Copernicus DEM, Census 2011, SHRUG, OpenStreetMap, ESA WorldCover, official disaster records).
   - The system strictly distinguishes between acquired data and acknowledged data gaps.
4. **No Real-Time IoT Sensor Hallucinations:**
   - The platform performs deterministic pre-disaster spatial screening. It does not claim live real-time IoT ground-sensor telemetry or unverified meteorological rainfall prediction feeds.
   - "Dynamic updating" follows the contract: *Data In $\rightarrow$ Input Validation $\rightarrow$ Pipeline Recalculation $\rightarrow$ Output Refresh*.
5. **Standardized Terminology:**
   - Hazard outputs are strictly labeled **"Candidate Hazard-Based Red Zones"** (not official statutory red zones).
   - Relocation sites are labeled **"Candidate Topographically Feasible Sites"** (not "safe zones").
   - Capacity figures are labeled **"Preliminary Spatial Capacity Estimates"** (not engineering-certified carrying capacity).

---

## Expected Deliverables
1. **Automated GIS Processing Pipeline:** Python scripts (`rasterio`, `geopandas`, `shapely`, `numpy`, `scipy`) transforming raw satellite rasters and census tables into analysis-ready GeoPackages and GeoJSON layers.
2. **FastAPI REST API Microservice:** 12 modular route controllers serving district KPIs, habitation dossiers, red zones, candidate relocation areas, infrastructure layers, disaster records, block summaries, and CSV reports.
3. **Interactive Frontend Web Application:** React 18 + TypeScript + Vite + Tailwind CSS + Leaflet GIS application providing 9 dedicated views: Dashboard, Map, Village Explorer, Village Detail, Candidate Areas, Authority Action Center, Pipeline Recomputation, Methodology, and System Status.
4. **Configuration & Rule Engine:** Declarative YAML files (`configs/project.yaml`, `configs/priority_thresholds.yaml`, `configs/capacity.yaml`, `configs/road_network.yaml`) enabling transparent parameter tuning without modifying core source code.
5. **Audited Engineering Documentation:** Complete traceability matrices, forensic audit reports, data gap closure roadmaps, and automated test suites (`pytest`).

---

## Problems with Existing Approaches
1. **Purely Reactive Disaster Response:** Post-disaster relief funds and temporary tin-shed shelters are deployed only after habitations are destroyed, resulting in recurring casualties and cyclical economic losses.
2. **Subjective & Ad-Hoc Relocation Prioritization:** Relocation lists are often compiled based on ad-hoc political representations or post-event visibility rather than district-scale multi-criteria spatial screening.
3. **Siloed & Fragmented Data:** Terrain slope, flood risk, census demographics, disaster history, road networks, and land use exist in disparate government departments (Revenue, PWD, Forest, USDMA, Health) without unified spatial synthesis.
4. **Absence of Alternative Site Capacity Modeling:** Relief authorities lack standardized spatial mechanisms to estimate how many displaced households a prospective relocation site can practically accommodate under national housing norms (PMAY-G).
5. **Black-Box or Impractical AI Models:** Academic research frequently proposes uninterpretable neural network classifiers or requires high-density live telemetry sensor networks that do not exist across rugged Himalayan districts.

---

## Specific Gap Being Addressed
The SIH26191 platform bridges the gap between **raw geospatial data** and **administrative disaster governance** in high-hazard mountain districts. 

By systematically coupling:
- 30m Digital Elevation Model physics (slope gradient, D8 flow accumulation, Topographic Wetness Index),
- Demographic exposure from 653 Census 2011 habitations,
- Empirical multi-year disaster registries (22 events, 1998–2024),
- Mountain road network routing impedance ($6,397\text{ km}$),
- Land-cover ecological exclusions (ESA WorldCover 10m), and
- National rural housing capacity standards (MoRD PMAY-G $25\text{ m}^2/\text{HH}$),

the system provides an **end-to-end, glass-box, proactive decision-support platform** that enables SDMA and DDMA planners to identify vulnerable villages, prioritize them across actionable multi-year timelines, and screen viable relocation terrain prior to the onset of the monsoon season.
