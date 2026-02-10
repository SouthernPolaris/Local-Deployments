from app.adapters.pve_adapter import ProxmoxAdapter

# IMPORTANT: Update these IDs to match Proxmox VE setup before running the test
# My template ID (must exist in your Proxmox VE)
MY_TEMPLATE_ID = 100
# Test VM ID (will be created during the test; must not already exist in your Proxmox VE)
TEST_VM_ID = 999


def run_test():
    print("[INFO] Connecting to Proxmox...")
    try:
        adapter = ProxmoxAdapter()

        print(f"[INFO] Cloning Template {MY_TEMPLATE_ID} to VM {TEST_VM_ID}...")
        adapter.clone_node(MY_TEMPLATE_ID, TEST_VM_ID, "Integration-Test-VM")

        print("[INFO] Configuring Network (vmbr0)...")
        adapter.configure_network(TEST_VM_ID, ["vmbr0"])

        print("[SUCCESS] Check your Proxmox UI to see the new VM.")
        print("To clean up, you can now run: adapter.delete_vm(999)")

    except Exception as e:
        print(f"[FAILURE] TEST FAILED: {e}")


if __name__ == "__main__":
    run_test()
