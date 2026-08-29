# Step 11: Backend API Documentation

## 1. Backend Architecture
The backend is built with **FastAPI** to serve the previously generated, validated deterministic decision-support outputs. 
- **In-Memory Caching**: To avoid repeated disk reads, datasets (GeoJSON/GPKG) are loaded into memory at startup using `geopandas` inside the `DataLoader` singleton service.
- **CORS Configuration**: Controlled via `FastAPI CORSMiddleware`. Allowed origins are set in `backend.core.config`, defaulting to standard local dev ports (`localhost:3000`, `localhost:8000`) if not explicitly specified.
- **Spatial Queries**: Managed natively via `geopandas.cx` bounded box intersection logic.

## 2. Actual Datasets Served
1. `data/processed/decision/decision_summary.json`
2. `data/processed/decision/decision_metadata.json`
3. `data/processed/decision/village_priority_profiles.gpkg`
4. `data/outputs/candidate_hazard_based_red_zones.geojson`
5. `data/outputs/candidate_topographically_feasible_areas_attributed.geojson`
6. `data/processed/hazards/*` (metadata/availability checks only)

## 3. Endpoint List

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | System status and memory load status for datasets. |
| GET | `/api/metadata` | Overall project metadata, methodologies, and strict disclaimers. |
| GET | `/api/villages` | GeoJSON of villages. Supports filtering (`priority_tier`, `name`). |
| GET | `/api/villages/{id}` | Detailed properties for a single village feature. |
| GET | `/api/red-zones` | GeoJSON of Candidate Hazard-Based Red Zones. |
| GET | `/api/candidate-areas` | GeoJSON of Candidate Topographically Feasible Areas. Supports `bbox` spatial filtering and pagination (`limit`, `offset`). |
| GET | `/api/candidate-areas/{id}` | Detailed properties for a single candidate area feature. |
| GET | `/api/hazards` | Returns metadata distinguishing *Configured* hazard indicators from *Actually Available* raster layers. |
| GET | `/api/decision/summary` | Raw deterministic decision summary JSON payload. |
| GET | `/api/decision/metadata` | Raw decision metadata JSON payload. |

## 4. Request Parameters & Filtering

### `/api/villages`
- `priority_tier` (string, optional): One of `Tier1_AttentionPriority`, `Tier2_ElevatedAttention`, `Tier3_Monitoring`, `BeyondProximity`.
- `name` (string, optional): Partial match search on `village_name`.
- `limit` (integer, default=100)
- `offset` (integer, default=0)

### `/api/candidate-areas`
- `bbox` (string, optional): Format `min_lon,min_lat,max_lon,max_lat` (EPSG:4326). Uses `cx` indexing to return only candidate areas intersecting the bounding box, solving bandwidth/performance limits for large ~15MB data.
- `limit` (integer, default=50, max=500)
- `offset` (integer, default=0)

## 5. Known Limitations
- The API serves spatial vector data but intentionally **does not serve massive raster files directly**. Raster data must be exposed through a specialized map server component (like GeoServer or Mapbox tiles).
- This is a *read-only* data presentation API.

## 6. Decision-Support Disclaimer
All payloads are bound by the primary project limitation:
> **Decision Support — Requires Official Verification & Geotechnical Assessment**
> The endpoints strictly deliver preliminary terrain-derived screening outputs and do not declare official Red Zones, Safe Zones, or provide safety certifications. CA-0001 warnings explicitly remain intact.

## 7. How Step 12 Frontend Should Consume the API
1. On initial load, fetch `/api/metadata` and display the **Mandatory Scientific Disclaimer** immediately to the user.
2. Query `/api/decision/summary` to populate dashboard aggregate metrics (Total Habitations, Tier counts).
3. Use `/api/candidate-areas?bbox=...` matching the current map view bounds dynamically to avoid fetching the full 15MB file upfront.
4. Visualize `/api/red-zones` and `/api/villages` directly on the mapping component, honoring the `priority_tier` fields for styling.

## 8. How to Run Locally
```bash
# Start the server (uvicorn)
python -m backend.main
```
The API will be available at `http://localhost:8000`. Swagger documentation is automatically available at `http://localhost:8000/docs`.
