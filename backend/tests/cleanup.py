from app.adapters.pve_adapter import ProxmoxAdapter

def cleanup():
    adapter = ProxmoxAdapter()
    
    # IDs we've been using in our tests
    vms_to_wipe = [1000, 1001, 1002]
    # Bridges we've been using (vmbr100, vmbr101, etc.)
    bridges_to_wipe = ["vmbr100", "vmbr101", "vmbr102"]
    
    print("Starting Deep Clean of Lab Environment...")

    # Wipe VMs
    for vmid in vms_to_wipe:
        print(f"Checking VM {vmid}...")
        adapter.delete_vm(vmid)
        
    # Wipe Bridges
    for bridge in bridges_to_wipe:
        print(f"Checking Bridge {bridge}...")
        adapter.delete_bridge(bridge)
        
    print("Lab environment is now pristine.")

if __name__ == "__main__":
    cleanup()