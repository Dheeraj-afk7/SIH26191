# Processed Hydrology Datasets (Step 5)

This directory stores intermediate deterministic hydrological terrain derivatives generated from the verified Copernicus GLO-30 DEM.

## Contents:
- `flow_direction.tif`: D8 flow direction raster (EPSG:32644, uint8, NoData 255)
- `flow_accumulation.tif`: Flow accumulation raster in cell units (EPSG:32644, float32, NoData NaN)
- `topographic_wetness_index.tif`: Topographic Wetness Index (TWI) raster (EPSG:32644, float32, NoData NaN)

All files are strictly deterministic, reproducible, and configuration-driven (`configs/project.yaml`).
