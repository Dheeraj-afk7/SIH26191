# SIH26191 — Disaster Decision-Support Platform Deployment Guide

This guide describes how to run and deploy the **SIH26191 GIS Decision-Support System for Rudraprayag District**.

---

## 1. Quick Start: Docker Compose (Recommended)

Run the entire application (Backend + Frontend + Nginx) with a single command:

```bash
docker-compose up --build -d
```

- **Frontend Application:** [http://localhost](http://localhost)
- **FastAPI API & OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

To stop the containers:
```bash
docker-compose down
```

---

## 2. Cloud Deployment (Vercel + Render / Railway)

### Step A: Deploy Backend (FastAPI on Render.com)
1. In Render, click **New Web Service** and connect this GitHub repository (`Dheeraj-afk7/SIH26191`).
2. Set configuration:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Copy your deployed backend URL (e.g. `https://sih26191-backend.onrender.com`).

### Step B: Deploy Frontend (React on Vercel)
1. In Vercel, click **Add New Project** and select this repository.
2. Set:
   - **Root Directory:** `frontend`
   - **Framework Preset:** `Vite`
3. Add an Environment Variable:
   - `VITE_API_BASE_URL` = `https://sih26191-backend.onrender.com`
4. Click **Deploy**.

---

## 3. Local Development / Hackathon Pitch Mode

To run directly on a host machine without Docker:

### Terminal 1 — Backend:
```bash
python -m backend.main
# Runs on http://localhost:8000
```

### Terminal 2 — Frontend:
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```
