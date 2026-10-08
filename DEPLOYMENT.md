# SIH26191 — Disaster Decision-Support Platform Deployment Guide

This guide describes how to run, test, and deploy the **SIH26191 GIS Decision-Support System for Rudraprayag District, Uttarakhand**.

---

## 1. Quick Start: Docker Compose (Recommended)

Run the entire application (FastAPI Backend + React Frontend + Nginx Reverse Proxy) with a single command:

```bash
docker-compose up --build -d
```

### Access URLs:
- **Frontend Command Center:** [http://localhost](http://localhost) (or [http://localhost:3000](http://localhost:3000))
- **FastAPI OpenAPI Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **API Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Stop Services:
```bash
docker-compose down
```

---

## 2. Local Development Setup

To run directly on your workstation without Docker:

### Step 1 — Python Virtual Environment & Backend:
```bash
# From workspace root
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
python -m backend.main
```
*Backend runs on `http://localhost:8000`.*

### Step 2 — React + Vite Frontend:
```bash
# In a second terminal
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:3000` (or `http://localhost:5173`).*

### Step 3 — Run Automated Verification Tests:
```bash
# In backend virtual environment
pytest
```
*Runs all 18 test cases validating endpoint contracts, spatial serializations, and error handling.*

---

## 3. Cloud Deployment (Vercel + Render / Railway)

### Step A: Deploy Backend (FastAPI on Render.com)
1. Log into [Render.com](https://render.com) and click **New Web Service**.
2. Connect this GitHub repository: `Dheeraj-afk7/SIH26191`.
3. Configure the Web Service:
   - **Environment:** `Python 3`
   - **Branch:** `main`
   - **Root Directory:** *(leave blank / project root)*
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables (if needed):
   - `PYTHONUNBUFFERED` = `1`
   - `CORS_ORIGINS` = `*` (or your frontend Vercel URL)
5. Click **Create Web Service**.
6. Copy your live backend URL (e.g., `https://sih26191-backend.onrender.com`).

### Step B: Deploy Frontend (React on Vercel)
1. Log into [Vercel](https://vercel.com) and click **Add New Project**.
2. Select this repository: `Dheeraj-afk7/SIH26191`.
3. Configure Project Settings:
   - **Framework Preset:** `Vite`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Configure Environment Variables:
   - `VITE_API_BASE_URL` = `https://sih26191-backend.onrender.com`
5. Click **Deploy**.

---

## 4. Environment Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API URL used by frontend Axios client |
| `CORS_ORIGINS` | `["http://localhost:3000", "http://localhost:5173", "*"]` | Permitted CORS origins for FastAPI middleware |
| `PORT` | `8000` | Port for backend Uvicorn server |

---

## 5. Troubleshooting & Diagnostics

- **Data layers not loading in Backend:** Ensure `data/outputs/` and `data/processed/` contain the GeoJSON/GPKG files, or run `POST /api/pipeline/recompute` to regenerate derived layers.
- **CORS errors in Browser:** Verify that `VITE_API_BASE_URL` matches the running backend URL.
- **Port Conflicts:** If port 8000 or 3000 is occupied, change the port in `docker-compose.yml` or pass `--port <new_port>` to Uvicorn/Vite.
