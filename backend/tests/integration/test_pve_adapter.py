from app.adapters.pve_adapter import ProxmoxAdapter

def run_automated_demo():
    adapter = ProxmoxAdapter()
    
    # Configuration
    TEMPLATE_ID = 100 
    NEW_BRIDGE = "vmbr1"
    JB_ID, TG_ID = 401, 402

    print("--- STARTING FULL DEPLOYMENT ---")

    # 1. Create the Internal Bridge (The Virtual Switch)
    adapter.create_bridge(NEW_BRIDGE, "Internal Lab Segment")

    # 2. Deploy Jumpbox (The Router/Pivot)
    print(f"Cloning Jumpbox {JB_ID}...")
    adapter.clone_node(TEMPLATE_ID, JB_ID, "demo-jumpbox")
    
    # Matching the dictionary format your adapter expects:
    print(f"Configuring Jumpbox Network & IPs...")
    adapter.configure_network(JB_ID, [
        {"bridge": "vmbr0", "ip": "dhcp"},        # Management/Internet
        {"bridge": NEW_BRIDGE, "ip": "10.0.0.1/24"} # Internal Lab
    ])

    # 3. Deploy Isolated Target
    print(f"Cloning Target {TG_ID}...")
    adapter.clone_node(TEMPLATE_ID, TG_ID, "demo-target")
    
    print(f"Configuring Target Network & IPs...")
    adapter.configure_network(TG_ID, [
        {"bridge": NEW_BRIDGE, "ip": "10.0.0.2/24"} # Internal Lab ONLY
    ])

    # 4. Power Everything On
    print("⚡ Booting Range...")
    adapter.start_vm(JB_ID)
    adapter.start_vm(TG_ID)

    print("\nFULLY AUTOMATED DEPLOYMENT COMPLETE")
    print("-" * 30)
    print(f"Jumpbox: VM {JB_ID} -> 10.0.0.1")
    print(f"Target:  VM {TG_ID} -> 10.0.0.2")
    print("-" * 30)

if __name__ == "__main__":
    run_automated_demo()