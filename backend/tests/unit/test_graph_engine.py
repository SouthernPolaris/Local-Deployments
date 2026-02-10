from app.core.graph_engine import GraphEngine
from app.models.schemas import CyberRangeRequest


def test_valid_tree_topology(valid_topology_data):
    request = CyberRangeRequest(**valid_topology_data)
    engine = GraphEngine(request)
    assert engine.validate_topology()


def test_reject_cyclic_topology(cyclic_topology_data):
    request = CyberRangeRequest(**cyclic_topology_data)
    engine = GraphEngine(request)
    assert not engine.validate_topology()


def test_bridge_mapping(valid_topology_data):
    request = CyberRangeRequest(**valid_topology_data)
    engine = GraphEngine(request)

    # Check that bridge_map was built correctly (3 nodes, 2 links = 2 entries)
    assert len(engine.bridge_map) == 2

    # Check node interfaces for a specific node
    # In valid_topology, n2 connected to both n1 and n3
    n2_interfaces = engine.get_node_interfaces("n2")
    assert len(n2_interfaces) == 2
    assert all("vmbr" in i for i in n2_interfaces)


def test_reachable_nodes_logic(orphan_topology_data):
    request = CyberRangeRequest(**orphan_topology_data)
    engine = GraphEngine(request)

    reachable = engine.get_reachable_nodes()
    reachable_ids = [str(n.id) for n in reachable]

    assert "n3" not in reachable_ids  # Orphan node
    assert "n2" in reachable_ids  # Connected node
