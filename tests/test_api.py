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

def test_metadata_endpoint(client):
    response = client.get("/api/metadata")
    assert response.status_code == 200

def test_decision_summary(client):
    response = client.get("/api/decision/summary")
    assert response.status_code == 200

def test_villages_endpoint(client):
    response = client.get("/api/villages?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0

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
