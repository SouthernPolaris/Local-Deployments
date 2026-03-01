"""
API routes for managing cyber range deployments.
Defines endpoints for creating, listing, and deleting ranges
and includes the background task logic for syncing desired state with actual state.
"""

import os
import time
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
    range_id = str(request.range_metadata.id).strip()
    StateManager.save_range(request, status="provisioning") # Notify frontend we've started
    
    print(f"--- Syncing: {request.range_metadata.name} ({range_id}) ---")

    # 1. Topology Prep
    request.nodes = engine.get_reachable_nodes()
    old_state = StateManager.get_range(range_id)
    old_nodes_map = StateManager.map_nodes_by_id(old_state)

    # 2. Cleanup
    _handle_deletions(request, old_nodes_map)

    # 3. Infrastructure Prep (Auto-create bridges defined in the graph)
    # This assumes engine.get_required_bridges() returns a list of bridge names
    for bridge_name in engine.get_required_bridges():
        pve_adapter.create_bridge(bridge_name, f"Auto-gen for {range_id}")

    # 4. Provision & Power On
    _handle_provisioning(request, engine, old_nodes_map)

    StateManager.save_range(request, status="running")
    print("--- Reconciliation Complete: All Systems Go ---")


def _handle_deletions(request: CyberRangeRequest, old_nodes_map: dict):
    """Destroys VMs and Bridges that exist in state but not in the new request."""
    new_node_ids = {str(node.id).strip() for node in request.nodes}
    
    for old_id, old_node in old_nodes_map.items():
        if old_id not in new_node_ids:
            vmid = old_node.get("vmid")
            if vmid:
                print(f"REMOVING VM: {old_node.get('label')} (VMID: {vmid})")
                pve_adapter.delete_vm(vmid)

    engine = GraphEngine(request)
    new_bridges = set(engine.get_required_bridges())
    
    all_pve_networks = pve_adapter.api.nodes(pve_adapter._get_node()).network.get()
    
    for net in all_pve_networks:
        iface = net['iface']
        # Only touch bridges we created (vmbr100 and above)
        if iface.startswith("vmbr") and iface != "vmbr0":
            try:
                bridge_num = int(iface.replace("vmbr", ""))
                if bridge_num >= 100 and iface not in new_bridges:
                    print(f"REMOVING BRIDGE: {iface}")
                    pve_adapter.delete_bridge(iface)
            except ValueError:
                continue # Skip non-numeric bridges


def _handle_provisioning(request: CyberRangeRequest, engine: GraphEngine, old_nodes_map: dict):
    used_vmids = {n["vmid"] for n in old_nodes_map.values() if isinstance(n.get("vmid"), int)}

    for i, node in enumerate(request.nodes):
        node_id = str(node.id).strip()
        interfaces = engine.get_node_interfaces(node_id)
        existing = old_nodes_map.get(node_id)

        # 1. Sanitize the label for Proxmox DNS requirements
        # replaces spaces/underscores with hyphens and strips non-alphanumeric
        clean_label = "".join(c if c.isalnum() else "-" for c in node.label).lower()
        clean_label = clean_label.replace("--", "-").strip("-")

        if existing and isinstance(existing.get("vmid"), int):
            vmid = existing["vmid"]
            node.vmid = vmid
            print(f"UPDATING: {clean_label} (VMID: {vmid})")
            pve_adapter.configure_network(vmid, interfaces)
            pve_adapter.start_vm(vmid)
            continue

        new_vmid = engine.generate_vmid(base=1000 + i, exclude=used_vmids)
        used_vmids.add(new_vmid)
        node.vmid = new_vmid

        # Use the clean_label for both the log and the API call
        print(f"PROVISIONING: {clean_label} (VMID: {new_vmid})")
        pve_adapter.clone_node(node.template_id, new_vmid, clean_label)
        
        time.sleep(2) 
        
        pve_adapter.configure_network(new_vmid, interfaces)
        pve_adapter.start_vm(new_vmid)


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
    # Get the state so we know which VMs to kill
    range_state = StateManager.get_range(str(range_id))
    if not range_state:
        raise HTTPException(status_code=404, detail="Range not found")

    # Kill all VMs
    for node in range_state.nodes:
        if node.vmid:
            pve_adapter.delete_vm(node.vmid)

    # Kill all Bridges associated with this range
    engine = GraphEngine(range_state)
    for bridge in engine.get_required_bridges():
        pve_adapter.delete_bridge(bridge)

    # Remove from disk
    StateManager.delete_range(range_id)
    return {"range_id": range_id, "status": "deleted"}
