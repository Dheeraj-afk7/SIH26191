import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "docs_url" in data
    assert "endpoints" in data

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["datasets_loaded"]["decision_metadata"] is True
    assert data["datasets_loaded"]["decision_summary"] is True
    assert data["datasets_loaded"]["villages"] is True
    assert data["datasets_loaded"]["red_zones"] is True
    assert data["datasets_loaded"]["candidate_areas"] is True
    assert data["datasets_loaded"]["infrastructure"] is True
    assert data["datasets_loaded"]["disasters"] is True
    assert data["datasets_loaded"]["roads"] is True

def test_metadata_endpoint(client):
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "provenance_layers" in data

def test_decision_summary(client):
    response = client.get("/api/decision/summary")
    assert response.status_code == 200

def test_villages_endpoint(client):
    response = client.get("/api/villages?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    props = data["features"][0]["properties"]
    assert "dist_to_nearest_health_facility_m" in props
    assert "dist_to_nearest_disaster_m" in props
    assert "dist_to_nearest_road_m" in props

def test_red_zones_endpoint(client):
    response = client.get("/api/red-zones")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

def test_candidate_areas_endpoint(client):
    response = client.get("/api/candidate-areas?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

def test_hazards_endpoint(client):
    response = client.get("/api/hazards")
    assert response.status_code == 200
    data = response.json()
    assert "layers" in data

def test_infrastructure_endpoint(client):
    response = client.get("/api/infrastructure?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 10
    props = data["features"][0]["properties"]
    assert "facility_id" in props
    assert "facility_category" in props
    assert "explicitly_evidenced_emergency_capability" in props
    assert "potential_emergency_receiving_facility" in props

def test_infrastructure_summary(client):
    response = client.get("/api/infrastructure/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_critical_facilities"] == 291
    assert data["emergency_capability_breakdown"]["explicitly_evidenced_emergency_facilities"] == 4
    assert data["emergency_capability_breakdown"]["potential_emergency_receiving_clinical_facilities"] == 42

def test_disasters_endpoint(client):
    response = client.get("/api/disasters")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 22
    props = data["features"][0]["properties"]
    assert "canonical_incident_id" in props
    assert "hazard_type" in props
    assert "fatalities" in props
    assert "source_provider" in props

def test_disaster_summary(client):
    response = client.get("/api/disasters/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_canonical_events"] == 22
    assert data["total_fatalities_recorded"] == 6913

def test_roads_endpoint(client):
    response = client.get("/api/roads?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

def test_roads_summary(client):
    response = client.get("/api/roads/summary")
    assert response.status_code == 200

def test_lulc_summary(client):
    response = client.get("/api/lulc/summary")
    assert response.status_code == 200
    data = response.json()
    assert "ESA WorldCover 10m 2021 v200" in data["source_dataset"]

def test_pipeline_steps_endpoint(client):
    response = client.get("/api/pipeline/steps")
    assert response.status_code == 200
    data = response.json()
    assert "available_steps" in data
