import os
from uuid import uuid4

import pytest
from app.core.state_manager import STATE_FILE


@pytest.fixture
def master_id():
    """Fixed ID for the Jumpbox to test stability."""
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def valid_topology_data(master_id):
    """Returns a valid tree topology (n1 -> n2 -> n3)."""
    return {
        "range_metadata": {"id": str(uuid4()), "name": "Test Range"},
        "nodes": [
            {
                "id": master_id,
                "label": "Jumpbox",
                "role": "jumpbox_main",
                "template_id": 1001,
            },
            {"id": "n2", "label": "Service 1", "role": "service", "template_id": 1001},
            {"id": "n3", "label": "Service 2", "role": "service", "template_id": 1001},
        ],
        "links": [
            {"source": master_id, "target": "n2", "connection_type": "vlan_bridge"},
            {"source": "n2", "target": "n3", "connection_type": "vlan_bridge"},
        ],
    }


@pytest.fixture
def cyclic_topology_data(valid_topology_data, master_id):
    """Returns an invalid topology with a loop (n1-n2-n3-n1)."""
    data = valid_topology_data.copy()
    # Create a deep copy of links
    data["links"] = list(valid_topology_data["links"])
    data["links"].append(
        {"source": "n3", "target": master_id, "connection_type": "vlan_bridge"}
    )
    return data


@pytest.fixture
def orphan_topology_data(master_id):
    """Returns a topology where 'n3' is disconnected (Jumpbox -> n2 | n3)."""
    return {
        "range_metadata": {"id": str(uuid4()), "name": "Orphan Range"},
        "nodes": [
            {
                "id": master_id,
                "label": "Jumpbox",
                "role": "jumpbox_main",
                "template_id": 1001,
            },
            {"id": "n2", "label": "Connected", "role": "service", "template_id": 1001},
            {"id": "n3", "label": "Isolated", "role": "service", "template_id": 1001},
        ],
        "links": [
            {"source": master_id, "target": "n2", "connection_type": "vlan_bridge"}
            # No link to n3
        ],
    }


@pytest.fixture(autouse=True)
def clean_state_file():
    """
    Runs before and after EVERY test.
    Ensures we start with a clean slate and don't leave junk files.
    """
    if STATE_FILE.exists():
        os.remove(STATE_FILE)

    yield  # Run the test

    if STATE_FILE.exists():
        os.remove(STATE_FILE)
