# data/raw/ — Raw Input Datasets

This directory holds **original, unmodified input datasets** as acquired from their source.

## What belongs here

- Digital Elevation Model (DEM) rasters (GeoTIFF)
- Land Use / Land Cover rasters (GeoTIFF)
- River network shapefiles (Shapefile / GeoJSON)
- Administrative boundary shapefiles (Census of India / Survey of India)
- Population data tables (CSV / Shapefile)
- Historical disaster event records (CSV)
- Rainfall grids (NetCDF / GeoTIFF)
- Geology / Lithology shapefiles (GSI)

## Rules

- **Never modify files in this directory.** All processing must read from here and write to `data/processed/`.
- **Never fabricate or substitute datasets.** Every file must be real, downloaded from a citable open source.
- **Document every dataset** in `data/raw/SOURCES.md` (to be created) with: source URL, download date, licence, and CRS.

## Expected file types

`.tif` `.tiff` `.shp` `.dbf` `.shx` `.prj` `.cpg` `.geojson` `.csv` `.nc` `.img`

## Git tracking

**Large geospatial files are NOT committed to Git.** This directory's contents are excluded via `.gitignore` (`data/raw/**`).
Only this `README.md` is tracked to preserve directory intent.
Datasets must be acquired locally by each team member following `data/raw/SOURCES.md`.

## Pipeline role

```
data/raw/  →  processing/*  →  data/processed/
```
