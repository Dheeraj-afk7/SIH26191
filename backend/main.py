import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.services.data_loader import data_store
from backend.api.routes import system, decision, villages, zones, candidate_areas, hazards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up SIH26191 Backend API...")
    data_store.load_all()
    yield
    # Shutdown
    logger.info("Shutting down API...")

app = FastAPI(
    title=settings.project_name,
    version=settings.api_version,
    lifespan=lifespan,
    description="Backend API for Hazard Red Zone & Relocation Decision Support"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(decision.router, prefix="/api/decision", tags=["Decision"])
app.include_router(villages.router, prefix="/api/villages", tags=["Villages"])
app.include_router(zones.router, prefix="/api", tags=["Zones"])
app.include_router(candidate_areas.router, prefix="/api", tags=["Candidate Areas"])
app.include_router(hazards.router, prefix="/api", tags=["Hazards"])

@app.get("/", tags=["System"])
def root():
    return {
        "status": "healthy",
        "name": settings.project_name,
        "version": settings.api_version,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "endpoints": {
            "health": "/api/health",
            "metadata": "/api/metadata",
            "decision_summary": "/api/decision/summary",
            "villages": "/api/villages",
            "red_zones": "/api/red-zones",
            "candidate_areas": "/api/candidate-areas",
            "hazards": "/api/hazards"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
