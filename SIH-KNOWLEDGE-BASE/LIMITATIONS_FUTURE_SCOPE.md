# Limitations & Future Scope: SIH26191

## Current Limitations (What the Current Implementation Cannot Do)

### 1. Spatial Resolution of Digital Elevation Model (30-Meter Precision)
- **Current Behavior:** Terrain slope, aspect, and hydrological flow paths are derived from the 30m Copernicus GLO-30 DEM.
- **Limitation:** Micro-topographic features—such as localized slope cuts $<30\text{m}$, retaining wall fractures, drainage ditch blockages, and individual building foundation cuts—cannot be resolved at satellite scale.
- **Operational Impact:** Site-level slope stability cannot be certified without on-ground geotechnical investigations.

### 2. Demographic Baseline Vintage (Census 2011 Data)
- **Current Behavior:** Population, household counts, and demographic vulnerability indicators are derived from the 2011 Primary Census Abstract.
- **Limitation:** The data represents a ~15-year-old baseline and does not reflect post-2013 Kedarnath disaster population out-migration, demographic shifts, or new hamlet construction.
- **Operational Impact:** Serves as a baseline context only; current population counts must be re-verified by local Tehsil revenue officers prior to rehabilitation planning.

### 3. Administrative Centroids vs. Actual Settlement Footprints
- **Current Behavior:** Habitations are represented as single reference point centroids (from SHRUG v2.2) linked to Census village codes.
- **Limitation:** Mountain villages often sprawl across several hundred meters of valley terraces. Outlying hamlets may sit closer to steep hazard slopes than the reference centroid indicates.
- **Operational Impact:** Proximity distances represent centroid-to-zone distances; physical settlement boundaries require boundary mapping during field surveys.

### 4. Equal-Weight Multi-Hazard Combination Baseline (50% Terrain / 50% Flood)
- **Current Behavior:** Multi-hazard score combines terrain susceptibility proxy (50%) and TWI flood exposure proxy (50%) linearly.
- **Limitation:** Represents an uncalibrated deterministic baseline in the absence of an empirical district damage calibration matrix.
- **Operational Impact:** While transparent and configurable via `configs/project.yaml`, weights have not been tuned against multi-decade economic damage curves.

### 5. Preliminary Spatial Capacity Scenarios vs. Engineering Carrying Capacity
- **Current Behavior:** Computes dwelling-unit capacities using the GoI PMAY-G $25\text{ m}^2/\text{HH}$ standard with a $40\%$ net buildable efficiency factor and a $100\text{ ha}$ scale cap.
- **Limitation:** Does not evaluate subsurface soil mechanics, borehole drill logs, rock shear strength, groundwater aquifer yield, or electrical grid connectivity.
- **Operational Impact:** Outputs are strictly labeled *Preliminary Spatial Capacity Estimates*; engineering carrying capacity certification is legally mandatory before construction.

### 6. Absence of Cadastral Land Ownership & Reserve Forest Boundaries
- **Current Behavior:** Candidate relocation areas are screened for gentle slope ($\le 20^\circ$), hazard exclusion, and ESA WorldCover 10m land cover (excluding tree cover, snow, and water).
- **Limitation:** The platform does not ingest official district cadastral maps or statutory Reserve Forest / Wildlife Sanctuary cadastre boundaries (e.g., Kedarnath Wildlife Sanctuary statutory boundary).
- **Operational Impact:** A topographically feasible polygon may fall within private agricultural land or protected government forest, requiring Forest Conservation Act clearances.

### 7. Non-Authorizing Stance (Human-in-the-Loop Mandate)
- **Current Behavior:** The system deterministically classifies habitations and identifies candidate relocation areas.
- **Limitation:** The software does **not** automatically assign specific villages to specific relocation sites and does **not** issue statutory relocation or evacuation orders.
- **Operational Impact:** Preserves human-in-the-loop governance; all administrative decisions require multi-departmental review and community consent.

### 8. Static Baseline vs. Live Meteorological Telemetry
- **Current Behavior:** Ingests static satellite DEM and multi-year historical records.
- **Limitation:** Does not ingest live real-time IoT ground-sensor telemetry or real-time IMD radar rainfall forecasts.
- **Operational Impact:** Designed for pre-disaster planning rather than 15-minute emergency evacuation warnings.

---

## Future Scope (Explicitly Planned & Structured Roadmap)

### 1. Ingestion of High-Resolution Drone / LiDAR Topography (1–5 Meter Resolution)
- **Objective:** Ingest Survey of India / USDMA drone photogrammetry and LiDAR DEMs for high-priority Tier 1 habitations and top candidate relocation sites.
- **Expected Outcome:** High-precision micro-slope modeling capable of resolving roadside cuts and individual terrace stability.

### 2. Integration of Official Cadastral & Forest Department Land Records
- **Objective:** Integrate Uttarakhand Revenue Department *Bhulekh* cadastral survey maps and Forest Department GIS boundary shapefiles.
- **Expected Outcome:** Automatic masking of private agricultural parcels and Reserve Forests, isolating government *Civil Soyam* / *Nazul* land ready for immediate legal transfer.

### 3. Real-Time IMD Gridded Rainfall Alerts & Dynamic Thresholding
- **Objective:** Ingest India Meteorological Department (IMD) gridded rainfall feeds and automatic weather station (AWS) APIs.
- **Expected Outcome:** Dynamically adjust hazard screening intensity bands and trigger early warning alerts when rainfall exceeds empirical empirical landslide initiation thresholds.

### 4. Mobile Ground-Truthing App for Field Officers
- **Objective:** Deploy a lightweight React Native / Flutter mobile app for Tehsil field assessment teams and BDOs.
- **Expected Outcome:** Offline field data collection allowing surveyors to photograph slope cracks, record household census updates, verify village boundaries, and sync directly with the backend API.

### 5. Multi-District Scaling Across Uttarakhand & Himalayan States
- **Objective:** Generalize the platform across all 13 districts of Uttarakhand (e.g., Chamoli, Uttarkashi, Pithoragarh) and neighboring states (Himachal Pradesh, Sikkim).
- **Expected Outcome:** State-wide SDMA Command Dashboard for comparative district risk monitoring.

### 6. Participatory Community Mapping & Relocation Consent Portal
- **Objective:** Provide a public participatory GIS portal where local Gram Panchayats can review proposed relocation candidate sites, submit traditional knowledge on past landslide events, and log community relocation consent.
- **Expected Outcome:** Socially cohesive, community-accepted resettlement planning.

### 7. Enterprise Role-Based Access Control (RBAC) & Single Sign-On
- **Objective:** Implement OAuth2 / OpenID Connect authentication integrated with Government of India *MeriPehchan* / NIC Single Sign-On.
- **Expected Outcome:** Tiered administrative permissions separating public viewers, district planners, and state disaster authorities.
