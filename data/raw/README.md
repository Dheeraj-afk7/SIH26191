# data/raw/ — Raw Input Datasets

This directory holds **original, unmodified input datasets** as acquired from authoritative open data sources for project **SIH26191** (Primary Pilot Area: Rudraprayag District, Uttarakhand, India).

---

## 1. Directory Purpose

The `data/raw/` folder serves as the single source of truth for all un-processed geospatial, tabular, and environmental data. All processing modules treat this directory as read-only.

---

## 2. Documented Raw Datasets

### Copernicus GLO-30 DEM (Rudraprayag Pilot)

- **File Path:** `data/raw/copernicus_glo30_rudraprayag.tif`
- **Source Dataset:** Copernicus GLO-30 Digital Elevation Model (30m spatial resolution)
- **File Format:** GeoTIFF (`.tif`)
- **GDAL Driver:** `GTiff` / GeoTIFF
- **Data Type:** `Float32` (32-bit Floating Point)
- **Coordinate Reference System (CRS):** `EPSG:4326` — WGS 84 (Geographic)
- **Raster Dimensions:** 1979 × 2294 pixels
- **Elevation Range:** ~832.0 m to ~5935.8 m above mean sea level
- **Geographic Extent:**
  - Longitude: ~78.126° E to ~79.362° E
  - Latitude: ~30.176° N to ~30.814° N
- **File Size:** ~18.17 MB
- **Verification Status:** Manually inspected and visually verified in QGIS. Raster integrity, spatial alignment, and elevation data ranges confirmed.

---

## 3. Dataset Role in Pipeline

The Copernicus GLO-30 DEM provides the foundational elevation grid for:

1. **Terrain Analysis:** Basic morphometric processing.
2. **Slope Derivation:** Slope angle calculation in degrees/percent.
3. **Aspect & Curvature Derivation:** Terrain orientation and profile/plan curvature.
4. **Terrain-Derived Hazard Indicators:** Input into Landslide Susceptibility Index (LSI) and Topographic Wetness Index (TWI) for Flood Exposure modeling.
5. **Candidate Topographically Feasible Site Analysis:** Identifying low-hazard, slope-suitable terrain for potential relocation consideration.
6. **Preliminary Spatial Capacity Estimate Analysis:** Providing topographically constrained area estimates for capacity planning scenarios.

---

## 4. Raw Data Handling Policy

1. **Strict Immutability:** Never edit, crop, or overwrite raw files directly in `data/raw/`.
2. **Read-Only Access:** Processing scripts in `processing/` must treat `data/raw/` purely as read input.
3. **Structured Pipeline Output:**
   - Intermediate/derived raster and vector layers must be written to `data/processed/`.
   - Final GeoJSON decision-support layers must be written to `data/outputs/`.
4. **Mandatory Documentation:** Every new dataset added to `data/raw/` must be documented with verified metadata (source, format, CRS, resolution, extent, and file size).

---

## 5. Data Pipeline Diagram

```
+-------------------------------------------------------+
|                      data/raw/                        |
|       (e.g., copernicus_glo30_rudraprayag.tif)        |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|                    processing/                        |
|   (terrain, hazards, exposure, priority, sites, cap)  |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|                    data/processed/                    |
|      (intermediate slope, LSI, flood exposure)        |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|                    data/outputs/                      |
| (Candidate Red Zones, Candidate Topographically       |
| Feasible Sites, Preliminary Spatial Capacity Estimate)|
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|                    FastAPI Backend                    |
+-------------------------------------------------------+
                           |
                           v
+-------------------------------------------------------+
|                 React + Leaflet GIS UI                |
+-------------------------------------------------------+
```

---

## 6. Git Tracking Policy

Large geospatial datasets (`.tif`, `.shp`, `.gpkg`, `.nc`) are excluded from version control via `.gitignore` (`data/raw/**`). Only metadata documentation files (such as this `README.md`) are tracked in Git.
