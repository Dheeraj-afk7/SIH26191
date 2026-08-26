# data/outputs/ — Final Decision-Support Outputs

This directory holds **final GIS outputs** ready to be served by the FastAPI backend and displayed in the React/Leaflet frontend.
These files are the direct outputs of the priority, site selection, and capacity modules.

## What belongs here

- Candidate Hazard Zone polygons (GeoJSON) — labelled "Candidate Hazard-Based Red Zone"
- Scored habitation layer (GeoJSON) — with vulnerability composite index per habitation
- Relocation Priority layer (GeoJSON) — Tier 1 / Tier 2 / Tier 3 per habitation
- Candidate Topographically Feasible Sites (GeoJSON) — with suitability scores
- Preliminary Spatial Capacity Estimate table (JSON / CSV)
- Summary statistics (JSON)

## Output labelling requirement

Every GeoJSON feature in this directory that relates to hazard zones or relocation must include
a `disclaimer` property in its feature properties, e.g.:

```json
"disclaimer": "Candidate zone — requires official geotechnical and administrative verification before any relocation action."
```

This is a mandatory project rule (see `docs/PROJECT_SPEC.md §7`).

## Rules

- Files here are **served directly by the FastAPI backend**. Filenames must be stable and match the API route configuration.
- Files are **reproducible** — regenerate by running the full processing pipeline.
- Do not manually edit GeoJSON features here. All changes must come through the pipeline.

## Expected file types

`.geojson` `.json` `.csv`

## Git tracking

**Final output files are NOT committed to Git.** This directory's contents are excluded via `.gitignore` (`data/outputs/**`).
Only this `README.md` is tracked to preserve directory intent.
Regenerate contents by running the full pipeline on locally acquired data.

## Pipeline role

```
data/processed/  →  processing/priority, sites, capacity  →  data/outputs/  →  FastAPI backend  →  React/Leaflet
```
