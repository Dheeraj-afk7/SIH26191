# SIH Judge & Evaluator Q&A Knowledge Base: SIH26191

This file contains concise, exact, project-specific answers to likely questions from SIH evaluators, judges, and professors.

---

## Basic Project Questions

## Q: What is the core title and objective of project SIH26191?
**Answer:**
- **Title:** Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Relocation Needs for Vulnerable Habitations.
- **Objective:** Build a GIS decision-support system shifting disaster management from reactive relief to proactive pre-disaster spatial planning in Rudraprayag, Uttarakhand.
- **Outcome:** Screens 653 habitations into 4 priority horizons and identifies 2,998 candidate relocation sites with PMAY-G capacity.

## Q: Who are the target users and primary stakeholders?
**Answer:**
- State Disaster Management Authorities (USDMA / SDMA) and District Magistrates (DDMA).
- National Disaster Response Force (NDRF) and Ministry of Home Affairs (MoHA).
- Tehsil Planners, Block Development Officers (BDOs), and Rural Housing Agencies (PMAY-G).

## Q: Why was Rudraprayag District chosen as the primary pilot?
**Answer:**
- It is one of India's most hazard-prone mountain districts (#1 landslide density in ISRO Landslide Atlas).
- Site of the catastrophic June 2013 Kedarnath disaster with complex valley terrain (Mandakini and Alaknanda).
- Dense distribution of 653 rural habitations across steep terrain requiring urgent spatial planning.

---

## Problem Statement Questions

## Q: What specific problem statement requirements does this project address?
**Answer:**
- Fully addresses **PS-1 through PS-9** of Problem Statement 26191 (MoHA / NDRF).
- Delivers multi-hazard red zone delineation, hazard intensity grading, demographic vulnerability, disaster history, alternative site search, and carrying capacity.
- Maps habitations into Immediate, Short-Term, and Medium-Term relocation horizons with SDMA action workflows.

## Q: What is the biggest flaw with existing government disaster management approaches?
**Answer:**
- Current disaster response is almost entirely **reactive**, deploying relief and ad-hoc tin shelters only after destruction occurs.
- Relocation lists are often compiled based on subjective political representations rather than empirical multi-criteria screening.
- Data on terrain slope, floods, census demographics, roads, and land cover remain trapped in departmental silos.

## Q: How does your system address the gap between reactive relief and proactive planning?
**Answer:**
- Establishes a pre-monsoon baseline screening all 653 habitations across the district simultaneously.
- Ranks habitations across multi-year planning horizons (0–1 yr, 1–3 yr, 3–10 yr) before disasters strike.
- Pre-identifies 2,998 topographically feasible alternative relocation sites and models PMAY-G housing capacities.

---

## Solution Questions

## Q: What is your proposed solution in simple terms?
**Answer:**
- An enterprise-grade, glass-box **GIS Decision-Support System** (FastAPI backend + React 18 / Leaflet frontend).
- Synthesizes 30m DEM terrain physics, Census demographics, 22 historical disaster records, and road networks.
- Provides interactive maps, village dossiers, SDMA action queues, block summaries, and dynamic recomputation.

## Q: Does your software automatically authorize or order village relocations?
**Answer:**
- **No.** The platform strictly provides *decision-support indicators and recommendations*.
- It **never** issues mandatory relocation or eviction orders.
- Administrative approval, geotechnical borehole surveys, and community consent are legally mandatory before any relocation action.

## Q: How does the system help an SDMA planner on a day-to-day basis?
**Answer:**
- The **Authority Action Center** filters district risks down to the 12 Tier 1 habitations needing immediate field inspection.
- Provides Block-level aggregations (Ukhimath, Augustmuni, Jakholi) for resource allocation.
- Enables one-click export of prioritized, printable CSV reports with complete classification rationale.

---

## Architecture Questions

## Q: Describe the high-level architecture of your platform.
**Answer:**
- **Pipeline:** Python GIS scripts (`rasterio`, `geopandas`, `scipy`) processing 30m DEM and Census data.
- **Backend:** High-performance FastAPI ASGI microservice with in-memory GeoPandas caching and R-tree indexing.
- **Frontend:** React 18 + Vite + Tailwind CSS + Leaflet GIS SPA with TanStack Query.
- **Configuration:** Declarative YAML files decoupling physical thresholds from code.

## Q: How do the frontend and backend communicate?
**Answer:**
- RESTful HTTP JSON and GeoJSON APIs served over 12 modular route controllers.
- Sub-millisecond queries supported by in-memory spatial indexing (`.sindex`).
- Asynchronous polling (`/api/pipeline/status/{id}`) for tracking dynamic pipeline recomputations.

## Q: Why did you choose an in-memory data store instead of PostgreSQL/PostGIS?
**Answer:**
- For a district-scale dataset (653 villages, 289 red zones, 2,998 candidate areas), in-memory GeoPandas delivers sub-15ms latency.
- Eliminates database server maintenance, connection pooling overhead, and crash risks during live hackathon demos.
- Seamlessly migratable to PostGIS for future multi-state scaling.

---

## Technology Stack Questions

## Q: Why did you choose FastAPI over Django or Flask?
**Answer:**
- Native ASGI asynchronous performance and automatic OpenAPI/Swagger interactive documentation (`/docs`).
- Strict runtime request validation using Pydantic schemas.
- Lightweight, modular routing ideal for containerized microservice deployments.

## Q: Why did you use Leaflet instead of Mapbox GL JS or Google Maps?
**Answer:**
- 100% open-source with zero commercial API keys, billing limits, or vendor lock-in.
- Lightweight bundle size, superior mobile performance, and native GeoJSON vector styling.
- Perfectly aligned with open government software deployment principles.

## Q: What Python GIS libraries power your analytical pipeline?
**Answer:**
- `rasterio` & `numpy` for 30m raster matrix operations and gradient calculations.
- `geopandas` & `shapely` for vector overlays, spatial joins, and OGC GeoPackage persistence.
- `scipy.ndimage` for morphological 8-connectivity clustering of red zones.
- `networkx` for Dijkstra shortest-path road network graph impedance.

---

## Dataset Questions

## Q: What specific datasets are ingested into the platform?
**Answer:**
- **Copernicus GLO-30 DEM:** 30m physical elevation surface (ESA Open Access).
- **Census 2011 PCA:** 653 village socio-demographics (Registrar General of India).
- **SHRUG v2.2:** 653 village centroid spatial bridge (Development Data Lab).
- **ESA WorldCover 10m:** 2021 land cover classification (Tile N30E078).
- **OpenStreetMap:** 291 critical facilities and 6,397 km road network.
- **Disaster Registry:** 22 verified historical disaster records (1998–2024).

## Q: How did you join Census demographic tables to spatial coordinates?
**Answer:**
- Used an exact 1:1 code join linking the 6-digit Census 2011 Village ID to SHRUG v2.2 spatial centroid geometries.
- Achieved a verified **100% spatial join rate** ($653/653$ villages matched with zero orphan records).

## Q: How do you handle the fact that Census data is from 2011?
**Answer:**
- Acknowledged openly as a baseline vintage (~15 years old) across all UI cards and tooltips.
- Serves as contextual socioeconomic vulnerability indicators alongside physical hazard screening.
- Local Tehsil officers must conduct rapid household verifications prior to final resettlement.

---

## AI/ML Questions

## Q: What AI or Machine Learning models are used in your system?
**Answer:**
- Core spatial decision logic uses **deterministic, physics-based GIS algorithms and rule engines**, not black-box ML.
- Uncalibrated neural networks were intentionally excluded from safety-critical life-safety classifications to ensure 100% explainability.
- An optional RAG / LLM SOP assistant provides informational Q&A without write access to spatial scores.

## Q: Why did you not use a Deep Neural Network or Random Forest for landslide prediction?
**Answer:**
- Deep learning models function as opaque black boxes; administrators cannot legally justify relocating a community based on uninterpretable neural weights.
- Landslide prediction requires dense local geotechnical sensor telemetry that does not exist district-wide.
- Physics-based slope gradients and TWI hydrology provide transparent, auditable, and legally defensible screening.

## Q: Can an LLM or RAG assistant alter the priority rank of a village?
**Answer:**
- **No.** The RAG assistant is strictly isolated in the presentation layer.
- It has zero write access to spatial rasters, GeoPackages, or classification scoring scripts.

---

## Algorithm Questions

## Q: How do you mathematically calculate slope and aspect?
**Answer:**
- Derived from Copernicus DEM in metric projected space (`EPSG:32644`):
  $$\text{Slope}_{\text{deg}} = \arctan\left(\sqrt{(\partial z/\partial x)^2 + (\partial z/\partial y)^2}\right) \times \frac{180}{\pi}$$
  $$\text{Aspect}_{\text{geo}} = (90 - \text{atan2}(-\partial z/\partial y, \partial z/\partial x)) \pmod{360}$$

## Q: What is the Topographic Wetness Index (TWI) and how is it used?
**Answer:**
- Formulated by Beven & Kirkby (1979): $\text{TWI} = \ln(a / \tan\beta)$, where $a$ is specific catchment area and $\beta$ is slope.
- Quantifies topographic moisture accumulation and valley-floor drainage saturation.
- Normalized over $[3.5, 13.5]$ to generate continuous flood exposure proxies.

## Q: How are Candidate Red Zones extracted from raster data?
**Answer:**
- Selects pixels where Multi-Hazard Class equals 3 ($M \ge 0.65$).
- Applies morphological 8-connectivity connected-component labeling via `scipy.ndimage.label`.
- Filters out micro-clusters below $5,000\text{ m}^2$ (~0.5 ha) to yield 289 distinct polygon vectors.

## Q: What exact rule classifies a village into Tier 1 (Immediate)?
**Answer:**
- Direct spatial overlap of village centroid inside a Candidate Red Zone polygon ($\text{overlap} == \text{True}$).
- **OR:** Nearest hazard distance $\le 500\text{ m}$ **AND** Multi-Hazard Class at centroid $\ge 2$ (Moderate/Higher).

---

## Results Questions

## Q: What are the primary classification results for Rudraprayag District?
**Answer:**
- **Tier 1 (Immediate Field Assessment):** 12 villages (4,750 pop, 977 HH).
- **Tier 2 (Short-Term Planning):** 69 villages (23,012 pop, 4,674 HH).
- **Tier 3 (Medium-Term Monitoring):** 204 villages (64,463 pop, 13,978 HH).
- **Beyond Proximity (Routine):** 368 villages (140,135 pop, 31,253 HH).

## Q: How many candidate relocation sites were identified and what is their total area?
**Answer:**
- **2,998 discrete candidate polygons** meeting slope $\le 20^\circ$, hazard exclusion, and ESA WorldCover non-forest checks.
- Total topographically feasible land area: **8,095.52 hectares** (filtered to $1–10\text{ ha}$ MMU clusters).

## Q: How do you estimate dwelling-unit capacity on candidate relocation sites?
**Answer:**
- Applies MoRD PMAY-G housing standard: **$25.0\text{ m}^2$ built floor area per household**.
- Assumes **$40\%$ net buildable site efficiency** ($\eta = 0.40$) and average household size of **4.0 persons**.
- Imposes a $100\text{ ha}$ upper scale protection cap to prevent macro-scale overclaiming.

---

## Security Questions

## Q: How do you ensure data security and prevent unauthorized tampering?
**Answer:**
- Stateless FastAPI backend with Pydantic request validation and CORS origin whitelisting.
- Dynamic recompute endpoint enforces strict step whitelisting and 300-second execution timeouts.
- Every recompute job logs an immutable UUID, operator note, and execution timestamp.

## Q: Does the platform expose private citizen data or PII?
**Answer:**
- **No.** All demographic attributes are aggregated at the revenue village level from public Census 2011 PCA data.
- No individual names, Aadhaar numbers, phone numbers, or private financial records exist in the system.

---

## Scalability Questions

## Q: How does this system scale to other districts or states?
**Answer:**
- Fully config-driven and geographically generalized (`configs/project.yaml`).
- Spatial extents and CRS (`analysis_crs_metric`) are parameterized, not hardcoded.
- Adding a new district requires providing its DEM and Census PCA, then running the automated pipeline.

## Q: What is the latency and throughput of your API?
**Answer:**
- Village and decision summary queries resolve in **$< 15\text{ ms}$** via in-memory R-tree spatial cache.
- Full district pipeline recomputation executes in **~12–18 seconds** in background worker threads.

---

## Innovation Questions

## Q: What is the core novelty of your project?
**Answer:**
- First end-to-end open platform coupling **hazard exposure screening** with **topographically feasible relocation site extraction** and **PMAY-G capacity modeling**.
- Shift from opaque academic AI to **100% glass-box explainable rules** aligned with official multi-year administrative horizons.
- Live **dynamic recomputation engine** recalculating district priority profiles on demand.

---

## Existing Solution Comparison

## Q: How is this different from existing government hazard maps (e.g., Bhuvan)?
**Answer:**
- Bhuvan provides static hazard susceptibility zonation rasters without village demographic joins or action queues.
- SIH26191 provides an end-to-end decision workflow: hazard overlays $\rightarrow$ village ranking $\rightarrow$ candidate site extraction $\rightarrow$ PMAY-G capacity $\rightarrow$ SDMA block reports.

---

## Limitations Questions

## Q: What is the single biggest limitation of your current implementation?
**Answer:**
- **30-meter DEM resolution:** Cannot resolve micro-topographic roadside cuts or retaining wall fractures $<30\text{m}$.
- Mitigated by classifying outputs as *preliminary decision support* and requiring geotechnical on-site investigations.

## Q: Why do candidate relocation areas not guarantee safety?
**Answer:**
- Sites are screened based on surface slope ($\le 20^\circ$) and hazard exclusion.
- Subsurface geotechnical stability, soil bearing capacity, groundwater yield, and legal cadastre titles require on-ground verification.

---

## Future Scope Questions

## Q: If you had another 6 months, what would you improve?
**Answer:**
- Ingest high-resolution **1–5m drone / LiDAR topography** for all 12 Tier 1 habitations.
- Integrate official **Revenue Department cadastral ownership parcels** and Forest Department boundaries.
- Ingest **real-time IMD gridded rainfall feeds** for dynamic monsoon early warning alerts.
- Deploy a mobile ground-truthing app for Tehsil field surveyors.

---

## Deployment Questions

## Q: Is this system currently deployed and accessible?
**Answer:**
- **Yes.** Live production frontend is deployed on Vercel: `https://sih-26191.vercel.app/`.
- Containerized backend is orchestrated via Docker Compose (`docker-compose up --build`).
- Automated Pytest test suite passes with 100% assertion coverage across all 18 endpoint contracts.

---

## Challenging & Critical Questions

## Q: Why this model instead of an Advanced AI/ML model?
**Answer:**
- Life-safety relocation decisions require 100% legal auditability and transparency.
- AI models produce unexplainable probability floats and overfit on sparse mountain data.
- Deterministic physics and rule engines guarantee reproducible, justifiable administrative decisions.

## Q: How do you know your results are reliable?
**Answer:**
- 100% verified spatial join ($653/653$ Census villages matched to SHRUG centroids).
- All 12 Tier 1 villages strictly satisfy physical 500m proximity and Class 2 hazard criteria.
- Automated Pytest suite verifies mathematical conservation ($C_{\text{terrain}} + C_{\text{flood}} == M$).

## Q: What happens if the model gives an incorrect prediction?
**Answer:**
- The system does not predict events; it screens spatial proximity and terrain slope deterministically.
- All outputs carry mandatory disclaimers requiring official field inspections before administrative action.

## Q: What is the weakest part of your system?
**Answer:**
- Reliance on 2011 Census demographic vintage and point centroids rather than high-resolution building footprints.
- Openly disclosed in the `/status` Data Gap Register and methodology tooltips.

## Q: Why should a State Disaster Management Authority actually deploy this solution?
**Answer:**
- Saves lives and public funds by replacing reactive emergency relief with proactive pre-disaster planning.
- Narrows district-scale field survey requirements from 653 villages down to 12 high-priority targets.
- Zero commercial software licensing cost; fully containerized and open-source.
