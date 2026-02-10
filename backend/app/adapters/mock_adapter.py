"""
Mock adapter for testing and development without a real Proxmox cluster
"""

import random
import time
from typing import Any

from app.adapters.iadapter import ICloudAdapter


class MockAdapter(ICloudAdapter):
    def __init__(self):
        print("Initialised MockAdapter")
        self.deployed_vms: list[int] = []

    def get_cluster_status(self) -> list[Any]:
        """Simulates a healthy 3-node cluster"""
        return [
            {"node": "pve-mock-01", "status": "online", "cpu": 0.12, "mem": 4096},
            {"node": "pve-mock-02", "status": "online", "cpu": 0.05, "mem": 8192},
            {"node": "pve-mock-03", "status": "online", "cpu": 0.45, "mem": 2048},
        ]

    def clone_node(self, template_id: int, newid: int, name: str) -> None:
        """
        Simulates the latency of cloning a VM
        NOTE: Implementations should ensure 'newid' is not already occupied
        by the provider's API.
        """
        print(
            f"DEBUG: [Mock] Starting clone of template {template_id} to ID {newid}..."
        )

        # Simulate network/disk latency (0.5 to 2 seconds)
        time.sleep(random.uniform(0.5, 2.0))

        self.deployed_vms.append(newid)
        print(f"DEBUG: [Mock] VM '{name}' (ID: {newid}) is now READY.")

    def delete_vm(self, vmid: int):
        """Simulates destroying a VM"""
        if vmid in self.deployed_vms:
            self.deployed_vms.remove(vmid)
        print(f"DEBUG: [Mock] VM {vmid} DESTROYED.")

    def configure_network(self, vmid: int, bridges: list[str]):
        """Simulates attaching virtual cables to bridges"""
        for i, bridge in enumerate(bridges):
            print(f"DEBUG: [Mock] VM {vmid} -> net{i} connected to {bridge}")
