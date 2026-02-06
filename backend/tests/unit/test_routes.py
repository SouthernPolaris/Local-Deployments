from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_cyber_range(valid_topology_data):
    response = client.post("/api/v1/range", json=valid_topology_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "range_id" in data
    assert "message" in data

def test_create_cyber_range_invalid_topology(cyclic_topology_data):
    response = client.post("/api/v1/range", json=cyclic_topology_data)
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Invalid topology"