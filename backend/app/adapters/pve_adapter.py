import os
import time
from typing import Any, cast

import urllib3
from app.adapters.iadapter import ICloudAdapter
from dotenv import load_dotenv
from proxmoxer import ProxmoxAPI

# Silence the InsecureRequestWarning for a cleaner console
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


class ProxmoxAdapter(ICloudAdapter):
    def __init__(self):
        host = os.getenv("PVE_HOST")
        user = os.getenv("PVE_USER")
        t_name = os.getenv("PVE_TOKEN_NAME")
        t_value = os.getenv("PVE_TOKEN_VALUE")

        if not all([host, user, t_name, t_value]):
            raise ValueError("Missing Proxmox configuration in environment variables.")

        self.api = ProxmoxAPI(
            str(host),
            user=str(user),
            token_name=str(t_name),
            token_value=str(t_value),
            verify_ssl=False,
        )
        self._cached_node: str | None = None

    def _get_node(self) -> str:
        if not self._cached_node:
            nodes = self.api.nodes.get()
            if not nodes or not isinstance(nodes, list):
                raise Exception("No Proxmox nodes reachable.")
            self._cached_node = str(nodes[0]["node"])
        return self._cached_node

    # --- IMPLEMENTING ABSTRACT METHODS ---

    def get_cluster_status(self) -> list[Any]:
        """Implemented: Satisfies ICloudAdapter requirement."""
        try:
            nodes = self.api.nodes.get()
            return list(nodes) if isinstance(nodes, list) else []
        except Exception as e:
            print(f"Error fetching cluster status: {e}")
            return []

    def clone_node(self, template_id: int, newid: int, name: str):
        """Implemented: Handles async cloning and task waiting."""
        node = self._get_node()
        try:
            upid = (
                self.api.nodes(node)
                .qemu(template_id)
                .clone.post(newid=newid, name=name, full=1)
            )

            if isinstance(upid, str):
                print(f"Clone started (UPID: {upid}). Waiting...")
                self._wait_for_task(upid)
            else:
                raise Exception(f"Unexpected response from Proxmox clone: {upid}")
        except Exception as e:
            print(f"FAILED TO CLONE: {e}")

    def delete_vm(self, vmid: int):
        """Implemented: Stops VM safely before deletion."""
        node = self._get_node()
        try:
            # Stop task
            stop_upid = self.api.nodes(node).qemu(vmid).status.stop.post()
            if isinstance(stop_upid, str):
                print(f"Stopping VM {vmid}...")
                self._wait_for_task(stop_upid)

            # Delete command
            print(f"Deleting VM {vmid}...")
            self.api.nodes(node).qemu(vmid).delete()
        except Exception:
            # Silently fail if VM is already gone or stop fails
            pass

    def configure_network(self, vmid: int, interfaces: list):
        node = self._get_node()
        config_payload = {}
        
        for i, item in enumerate(interfaces):
            # IF item is a string ("vmbr100"), convert it to dictionary on the fly
            if isinstance(item, str):
                bridge_name = item
                ip_config = "dhcp" # Default for strings
            else:
                # IT is a dictionary ({"bridge": "...", "ip": "..."})
                bridge_name = item.get('bridge')
                ip_config = item.get('ip', 'dhcp')

            config_payload[f"net{i}"] = f"virtio,bridge={bridge_name}"
            config_payload[f"ipconfig{i}"] = f"ip={ip_config}"

        try:
            self.api.nodes(node).qemu(vmid).config.put(**config_payload)
            print(f"Network configured for VM {vmid}")
        except Exception as e:
            print(f"PVE API Error: {e}")

    def delete_bridge(self, bridge_name: str):
        node = self._get_node()
        try:
            # Fetch all networks to see if bridge_name exists
            active_nets = [n['iface'] for n in self.api.nodes(node).network.get()]
            
            if bridge_name in active_nets:
                self.api.nodes(node).network(bridge_name).delete()
                # Apply changes
                self.api.nodes(node).network.put() 
                print(f"Bridge {bridge_name} removed.")
            else:
                print(f"Bridge {bridge_name} does not exist, skipping.")
                
        except Exception as e:
            print(f"Error during bridge cleanup: {e}")

    def create_bridge(self, bridge_name: str, comment: str = "Auto-generated"):
        """Dynamically creates a Linux Bridge (Virtual Switch) on the Proxmox host."""
        node = self._get_node()
        try:
            # Check if bridge already exists
            existing = self.api.nodes(node).network.get()
            if any(iface['iface'] == bridge_name for iface in existing):
                return

            print(f"Creating bridge {bridge_name}...")
            self.api.nodes(node).network.post(
                iface=bridge_name,
                type="bridge",
                autostart=1,
                comments=comment
            )
            # Triggers the 'Apply Configuration' in Proxmox
            self.api.nodes(node).network.put() 
        except Exception as e:
            print(f"Failed to create bridge: {e}")

    def start_vm(self, vmid: int):
        """Powers on the VM."""
        node = self._get_node()
        try:
            self.api.nodes(node).qemu(vmid).status.start.post()
            print(f"VM {vmid} power on command sent.")
        except Exception as e:
            print(f"Error starting VM {vmid}: {e}")

    def destroy_range(self, vmids: list[int]):
        """Cleanup: Deletes all VMs in the provided list."""
        for vmid in vmids:
            self.delete_vm(vmid)

    # --- HELPER METHODS ---

    def _wait_for_task(self, upid: str, timeout: int = 300):
        """Polls Proxmox task status until completion."""
        node = self._get_node()
        start = time.time()
        while time.time() - start < timeout:
            status = cast(dict[str, Any], self.api.nodes(node).tasks(upid).status.get())

            if status and status.get("status") == "stopped":
                exitstatus = status.get("exitstatus")
                if exitstatus == "OK":
                    return True
                raise Exception(f"Task failed: {exitstatus}")
            time.sleep(1)
        raise TimeoutError(f"Task {upid} timed out.")
