import time

from app.core.state_manager import StateManager
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_create_cyber_range_success(valid_topology_data):
    # POST valid topology to create a range
    response = client.post("/api/v1/range", json=valid_topology_data)
    assert response.status_code == 200

    # Wait briefly to simulate background task completion
    time.sleep(0.1)

    # Check if StateManager now has range saved as "running"
    range_id = valid_topology_data["range_metadata"]["id"]
    saved_state = StateManager.get_range(range_id)

    assert saved_state is not None
    assert saved_state["status"] == "running"
    assert saved_state["nodes"][0]["vmid"] is not None


def test_invalid_topology_rejection(cyclic_topology_data):
    response = client.post("/api/v1/range", json=cyclic_topology_data)
    assert response.status_code == 400
    assert "Invalid topology" in response.json()["detail"]
