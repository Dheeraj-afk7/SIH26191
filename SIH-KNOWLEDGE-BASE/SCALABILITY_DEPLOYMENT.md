# Scalability & Deployment: SIH26191

## Current Deployment Status (Implemented)

### 1. Live Production Deployment
- **Frontend Live Application:** Deployed on Vercel CDN Edge Network (`https://sih-26191.vercel.app/`).
  - Automated continuous deployment triggered via Git commits.
  - Global edge caching of static assets, HTML5 SPA routing, and TLS 1.3 SSL termination.
- **Backend API Service:** Stateless FastAPI ASGI microservice containerized via Docker and deployed on cloud container platforms (Render / Railway) with live OpenAPI Swagger documentation at `/docs`.
  - Production process command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.

### 2. Containerized Local Orchestration
- **Docker Compose (`docker-compose.yml`):**
  - Full-stack multi-container orchestration.
  - `Dockerfile.backend`: Multi-stage Python 3.11-slim container with pre-installed GDAL, GEOS, and PROJ C-libraries.
  - Frontend Container: Nginx reverse proxy serving compiled static Vite assets and routing `/api` proxy traffic.

---

## Infrastructure & Hardware Requirements

| Deployment Tier | Environment | Compute Requirements | Memory Requirements | Disk Storage | Target Capacity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Edge Production (API Only)** | Cloud Container (Render/Railway) | 1 vCPU (x86_64 or ARM64) | **512 MB – 1 GB RAM** | 500 MB (derived decision layers) | > 500 requests/sec |
| **Pipeline Processing & Recompute** | Dedicated Processing Node / Workstation | 2–4 CPU Cores (2.4 GHz+) | **4 GB – 8 GB RAM** | 2 GB (includes 30m DEM rasters) | Recomputes district in ~15s |
| **Frontend Client Access** | Web Browser (Chrome/Firefox/Edge) | Standard Mobile / Desktop CPU | 256 MB Browser Heap | Zero (cached static assets) | Interactive 60 FPS mapping |

---

## Scalability Strategy & Multi-District Generalization

### 1. Geographic Generalization Architecture
- The system is architected to be **completely district-agnostic and geographically generalizable**.
- Spatial extents, coordinate systems, and bounding boxes are **never hardcoded** in Python scripts.
- **District Scaling Workflow:**
  1. Add target district bounding box and DEM to `data/raw/` (e.g., Chamoli, Uttarkashi, Pauri Garhwal).
  2. Configure district metadata in `configs/project.yaml` (`pilot_district`, `analysis_crs_metric`).
  3. Execute automated pipeline: `python processing/run_pipeline.py`.
  4. Backend automatically binds and serves the new district spatial layers.

### 2. Spatial Indexing & In-Memory Performance
- **R-Tree Spatial Indexing (`sindex`):** All GeoPandas spatial layers (villages, candidate areas, red zones) build in-memory R-tree spatial indexes on startup.
- **Bounding Box Query Optimization:** Spatial queries (`GET /api/candidate-areas?bbox=...`) execute in $\mathcal{O}(\log N)$ time, enabling instantaneous viewport clipping for thousands of vector polygons.

---

## Expected Bottlenecks & Technical Mitigations

| Identified Bottleneck | Cause | Current Implemented Mitigation | Future Scale Plan |
| :--- | :--- | :--- | :--- |
| **Large-Scale Raster Hydrology** | Multi-district DEM flow accumulation across $>50\text{M}$ grid cells consumes high CPU/RAM. | Processing is pre-computed offline; backend serves pre-vectorized GeoJSON/GeoPackage outputs. | Implement distributed chunk-based raster tiling using `rasterio.windows` and Dask. |
| **Memory Footprint with Multiple Districts** | Loading dozens of districts into a single in-memory Python process increases RAM usage. | Current single-district memory footprint is only ~180 MB. | Migrate storage from in-memory GeoPandas to a shared PostgreSQL / PostGIS database cluster. |
| **Dynamic Recomputation Concurrency** | Multiple simultaneous operators triggering `POST /api/pipeline/recompute` could overload CPU. | Subprocess background execution is serialized with unique job UUIDs and timeout limits. | Implement Celery / Redis task queues with dedicated worker pools. |

---

## Database & Cloud Migration Strategy (Future Plan)

1. **Enterprise PostGIS Migration (When scaling to State/National Level):**
   - In-memory GeoPandas architecture will seamlessly transition to **PostgreSQL 16 + PostGIS 3.4**.
   - Spatial tables partitioned by `state_code` and `district_code` with spatial GiST indexing.
   - Enables multi-user concurrent editing and transactional rollback.
2. **Tile Server Integration for Large Raster Surfaces:**
   - Deploy dynamic Cloud-Optimized GeoTIFF (COG) tile servers (e.g., `titiler` or GeoServer) for streaming multi-gigabyte continuous hazard rasters directly to Leaflet via Web Map Tile Services (WMTS).
3. **Cloud Native Object Storage:**
   - Store raw satellite rasters and historical disaster catalogs in AWS S3 / Cloudflare R2 object storage with pre-signed upload URLs.

---

## Monitoring, Maintenance & Health Checks

- **Automated Health Probes (`GET /api/health`):** Continuously monitors the load state of all 8 core spatial datasets (`decision_metadata`, `villages`, `red_zones`, `candidate_areas`, `infrastructure`, `disasters`, `roads`).
- **System Provenance Probe (`GET /api/metadata`):** Audits active coordinate reference systems and dataset snapshot timestamps.
- **Frontend Health Indicator:** UI Header features a real-time pulsing backend connection badge (green = healthy, red = offline).
- **Automated Pytest CI Suite:** 18 comprehensive endpoint contract tests (`pytest tests/test_api.py`) executed on every build.

---

## Cost Considerations

- **Operational Cost Analysis:**
  - **Frontend:** $0.00 / month (Hosted on Vercel Global Free Tier).
  - **Backend API:** $0.00 to $7.00 / month (Hosted on Render / Railway Starter Containers).
  - **Data Ingestion:** $0.00 (All ingested datasets—Copernicus DEM, Census 2011, OpenStreetMap, ESA WorldCover, SHRUG—are 100% open-access with zero commercial API licensing fees).
  - **Total Solution Hosting Cost:** **Under $10 / month**, delivering maximum return on investment for public disaster management agencies.
