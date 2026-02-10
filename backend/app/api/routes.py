"""
API routes for managing cyber range deployments.
Defines endpoints for creating, listing, and deleting ranges
and includes the background task logic for syncing desired state with actual state.
"""

import os
from uuid import UUID

from app.adapters.mock_adapter import MockAdapter
from app.adapters.pve_adapter import ProxmoxAdapter
from app.core.graph_engine import GraphEngine
from app.core.state_manager import StateManager
from app.models.schemas import CyberRangeRequest, DeploymentResponse
from fastapi import APIRouter, BackgroundTasks, HTTPException

router = APIRouter()


# --- Dependencies ---
def get_adapter():
    """Returns the appropriate adapter based on the environment."""
    return ProxmoxAdapter() if os.getenv("APP_MODE") == "PROD" else MockAdapter()


pve_adapter = get_adapter()


# --- Background Task Logic ---
async def run_deployment(request: CyberRangeRequest, engine: GraphEngine):
    """
    Main syncing loop. Syncs desired state (request)
    with actual state (stored JSON).
    """
    range_id = str(request.range_metadata.id).strip()
    print(f"--- Syncing: {request.range_metadata.name} ({range_id}) ---")

    # Reachability Safety Check (Prune Orphans)
    request.nodes = engine.get_reachable_nodes()

    # Load and Map Existing State
    old_state = StateManager.get_range(range_id)
    old_nodes_map = StateManager.map_nodes_by_id(old_state)

    _handle_deletions(request, old_nodes_map)
    _handle_provisioning(request, engine, old_nodes_map)

    StateManager.save_range(request, status="running")
    print("--- Reconciliation Complete ---")


def _handle_deletions(request: CyberRangeRequest, old_nodes_map: dict):
    """Destroys VMs that exist in state but not in the new request."""
    new_node_ids = {str(node.id).strip() for node in request.nodes}

    for old_id, old_node in old_nodes_map.items():
        if old_id not in new_node_ids:
            vmid = old_node.get("vmid")
            if vmid:
                print(f"REMOVING: {old_node.get('label')} (VMID: {vmid})")
                pve_adapter.delete_vm(vmid)


def _handle_provisioning(
    request: CyberRangeRequest, engine: GraphEngine, old_nodes_map: dict
):
    """Iterates through nodes to sync network or clone fresh templates."""
    # Ensure used_vmids only contains actual integers
    used_vmids = {
        n["vmid"] for n in old_nodes_map.values() if isinstance(n.get("vmid"), int)
    }

    for i, node in enumerate(request.nodes):
        node_id = str(node.id).strip()
        interfaces = engine.get_node_interfaces(node_id)
        existing = old_nodes_map.get(node_id)

        # Try Syncing Existing VM
        if existing:
            vmid = existing.get("vmid")
            if isinstance(vmid, int):
                node.vmid = vmid
                print(f"SYNCING: {node.label} (VMID: {node.vmid})")
                pve_adapter.configure_network(vmid, interfaces)
                continue

        # ELSE: Clone New VM (Runs if node is new or vmid missing)
        new_vmid = engine.generate_vmid(base=1000 + i, exclude=used_vmids)
        used_vmids.add(new_vmid)

        print(f"CLONING: {node.label} (VMID: {new_vmid})")
        pve_adapter.clone_node(node.template_id, new_vmid, node.label)
        pve_adapter.configure_network(new_vmid, interfaces)
        node.vmid = new_vmid


# --- API Endpoints ---
@router.post("/range", response_model=DeploymentResponse)
async def create_cyber_range(
    request: CyberRangeRequest, background_tasks: BackgroundTasks
):
    engine = GraphEngine(request)

    if not engine.validate_topology():
        raise HTTPException(
            status_code=400,
            detail="Invalid topology: No Master Jumpbox found or graph is disconnected.",
        )

    background_tasks.add_task(run_deployment, request, engine)

    return {
        "range_id": request.range_metadata.id,
        "status": "accepted",
        "message": "Reconciliation task started.",
    }


@router.get("/ranges")
async def list_cyber_ranges():
    return StateManager.get_all()


@router.delete("/range/{range_id}")
async def delete_cyber_range(range_id: UUID):
    if not StateManager.delete_range(range_id):
        raise HTTPException(status_code=404, detail="Range not found")
    return {"range_id": range_id, "status": "deleted"}
