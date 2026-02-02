import os

from app.adapters.mock_adapter import MockAdapter
from app.adapters.pve_adapter import ProxmoxAdapter
from app.core.graph_engine import GraphEngine
from app.models.schemas import CyberRangeRequest, DeploymentResponse
from app.core.state_manager import StateManager
from fastapi import APIRouter, BackgroundTasks, HTTPException
from uuid import UUID

router = APIRouter()


def get_adapter():
    if os.getenv("APP_MODE") == "PROD":
        return ProxmoxAdapter()
    return MockAdapter()


pve_adapter = get_adapter()


@router.post("/range", response_model=DeploymentResponse)
async def create_cyber_range(
    request: CyberRangeRequest, background_tasks: BackgroundTasks
):
    engine = GraphEngine(request)

    if not engine.validate_topology():
        raise HTTPException(status_code=400, detail="Invalid topology")

    # Save state
    StateManager.save_range(request, status="provisioning")
    # Move the heavy lifting to the background
    background_tasks.add_task(run_deployment, request, engine)

    return {
        "range_id": request.range_metadata.id,
        "status": "accepted",
        "message": "Deployment started in background.",
    }

async def run_deployment(request: CyberRangeRequest, engine: GraphEngine):
    print(f"--- Starting Background Deployment for {request.range_metadata.name} ---")
    
    for node in request.nodes:
        # Ask engine for needed bridges for node
        node_bridges = engine.get_node_interfaces(node.id)
        
        # Trigger the Mock Adapter
        # Note: In the future, this will be a real Proxmox clone
        pve_adapter.clone_node(
            template_id=node.template_id, 
            newid=1000, # Simplified for now
            name=node.label
        )
        
        print(f"PROVISIONED: {node.label} on {node_bridges}")
    
    print("--- Deployment Complete ---")

@router.get("/ranges")
async def list_cyber_ranges():
    """
    Returns list of all saved cyber range deployments in state
    """
    return StateManager.get_all()

@router.delete("/range/{range_id}")
async def delete_cyber_range(range_id: UUID):
    """
    Deletes a cyber range deployment from state
    (Mock only)
    TODO: Implement actual deletion logic in ProxmoxAdapter
    """
    success = StateManager.delete_range(range_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cyber Range not found")
    
    print(f"[DELETE] Cyber Range {range_id} removed from state")
    return {"range_id": range_id, "status": "deleted"}