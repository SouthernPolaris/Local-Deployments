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

    def configure_network(self, vmid: int, bridges: list[str]):
        """Implemented: Maps interfaces to bridges."""
        node = self._get_node()
        net_config = {f"net{i}": f"virtio,bridge={b}" for i, b in enumerate(bridges)}

        try:
            self.api.nodes(node).qemu(vmid).config.put(**net_config)
            print(f"Network configured for VM {vmid}: {bridges}")
        except Exception as e:
            print(f"NETWORK CONFIG ERROR: {e}")

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
