from app.core.graph_engine import GraphEngine
from app.models.schemas import CyberRangeRequest

def test_valid_tree_topology(valid_topology_data):
    request = CyberRangeRequest(**valid_topology_data)
    engine = GraphEngine(request)
    assert engine.validate_topology() == True

def test_reject_cyclic_topology(cyclic_topology_data):
    request = CyberRangeRequest(**cyclic_topology_data)
    engine = GraphEngine(request)
    assert engine.validate_topology() == False

def test_bridge_mapping(valid_topology_data):
    request = CyberRangeRequest(**valid_topology_data)
    engine = GraphEngine(request)
    plan = engine.compute_network_plan()
    
    # 2 links -> 2 bridges
    assert len(plan) == 2
    assert plan[0]["bridge"] != plan[1]["bridge"]