"""
SIH26191 — processing.terrain
==============================================================================
Terrain processing sub-package for the SIH26191 pilot pipeline.

Modules
-------
derive_slope   : Reprojects DEM to metric CRS and computes slope in degrees.
derive_aspect  : Reprojects DEM to metric CRS and computes aspect in degrees.

All processing:
  - Reads the raw DEM from the path defined in configs/project.yaml.
  - Uses the configured analysis CRS (EPSG:32644) for metric calculations.
  - Writes derived outputs to data/processed/terrain/.
  - Never modifies the raw DEM.
  - Is fully deterministic and reproducible.

Outputs are decision-support terrain layers, not engineering-certified data.
"""
