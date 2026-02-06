import pytest
from app.models.schemas import CyberRangeRequest
from uuid import uuid4

@pytest.fixture
def valid_topology_data():
    """
    Returns a valid tree topology for testing (3 nodes, 2 links)
    """
    return {
        "range_metadata": {"id": str(uuid4()), "name": "Test Range"},
        "nodes": [
            {"id": "n1", "label": "Jumpbox", "role": "jumpbox_main", "template_id": 100},
            {"id": "n2", "label": "Service 1", "role": "service", "template_id": 101},
            {"id": "n3", "label": "Service 2", "role": "service", "template_id": 101},
        ],
        "links": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"}
        ]
    }

@pytest.fixture
def cyclic_topology_data(valid_topology_data):
    """Returns an invalid topology with a loop (n1-n2-n3-n1)"""
    data = valid_topology_data.copy()
    data["links"].append({"source": "n3", "target": "n1"})
    return data