# SIH26191

## Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations

> **Smart India Hackathon 2026 — Problem Statement SIH26191**
> Pilot area: **Rudraprayag District, Uttarakhand, India**

---

## Overview

This application is a **GIS-enabled decision-support tool** designed to help district administrators and disaster management authorities:

1. Identify multi-hazard candidate zones (landslide susceptibility + flood exposure).
2. Identify vulnerable and exposed habitations.
3. Assess population and infrastructure vulnerability.
4. Integrate historical disaster evidence.
5. Prioritize habitations for **Immediate / Short-Term / Medium-Term** relocation.
6. Identify candidate lower-hazard relocation sites.
7. Produce a preliminary spatial carrying-capacity estimate.
8. Provide actionable, **explainable** decision support.
9. Support dynamic recalculation when new relevant data is supplied.

---

## Architecture

```
processing/   ← Python GIS pipeline (rasterio, geopandas, shapely)
backend/      ← FastAPI REST API (serves processed results)
frontend/     ← React + Leaflet interactive GIS map
data/         ← raw → processed → outputs data flow
configs/      ← environment & parameter configuration
```

---

## Project Structure

```
SIH26191/
├── backend/              # FastAPI application
├── frontend/             # React + Leaflet frontend
├── processing/
│   ├── terrain/          # DEM derivatives (slope, aspect, curvature)
│   ├── hazards/          # Landslide susceptibility, flood exposure
│   ├── exposure/         # Habitation overlay, vulnerability scoring
│   ├── priority/         # Relocation priority classification
│   ├── sites/            # Candidate relocation site selection
│   └── capacity/         # Preliminary spatial capacity estimation
├── data/
│   ├── raw/              # Original input datasets (DO NOT modify)
│   ├── processed/        # Intermediate GIS outputs
│   └── outputs/          # Final decision-support layers
├── configs/              # YAML parameter files
├── docs/                 # Project documentation
├── scripts/              # Utility / automation scripts
└── tests/                # Unit and integration tests
```

---

## How to Run Locally

### 1. Python Environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. GIS Processing Pipeline

```bash
# Run from project root — individual module scripts will be added per module
python processing/hazards/landslide_susceptibility.py
python processing/hazards/flood_exposure.py
python processing/priority/relocation_priority.py
```

### 3. Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
# App at http://localhost:5173
```

---

## Scientific Rules & Limitations

See [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) for the full specification and mandatory scientific rules.

---

## Status

- [x] Project foundation created
- [ ] Module 1: Landslide Susceptibility
- [ ] Module 2: Flood Exposure
- [ ] Module 3: Multi-Hazard Candidate Zones
- [ ] Module 4: Habitation Exposure and Vulnerability
- [ ] Module 5: Relocation Priority
- [ ] Module 6: Candidate Relocation Site Selection
- [ ] Module 7: Preliminary Spatial Capacity
- [ ] FastAPI Backend
- [ ] React Frontend
# SIH26191
