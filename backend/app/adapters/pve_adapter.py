import os
from typing import Any

from app.adapters.iadapter import ICloudAdapter
from dotenv import load_dotenv
from proxmoxer import ProxmoxAPI

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

    def _get_first_node(self) -> str:
        """Helper to get a valid node name safely"""
        nodes = self.api.nodes.get()
        if not nodes:
            raise Exception(
                "Could not connect to Proxmox or no nodes found. Check your .env credentials."
            )
        return nodes[0]["node"]

    def get_cluster_status(self) -> list[Any]:
        nodes = self.api.nodes.get()
        return list(nodes) if nodes else []

    def clone_node(self, template_id: int, newid: int, name: str):
        target_node = self._get_first_node()
        print(f"Cloning {template_id} to {newid} on {target_node}...")

        # We wrap this in a try-except because the API call might fail if ID exists
        try:
            self.api.nodes(target_node).qemu(template_id).clone.post(
                newid=newid, name=name, full=1
            )
        except Exception as e:
            print(f"FAILED TO CLONE: {e}")

    def delete_vm(self, vmid: int):
        target_node = self._get_first_node()
        try:
            # We must stop the VM before we can delete it in Proxmox
            self.api.nodes(target_node).qemu(vmid).status.stop.post()
            print(f"Stopping and deleting VM {vmid}...")
            self.api.nodes(target_node).qemu(vmid).delete()
        except Exception:
            # Silently fail if VM doesn't exist (normal for cleanup)
            pass

    def configure_network(self, vmid: int, bridges: list[str]):
        target_node = self._get_first_node()
        net_config = {}
        for i, bridge in enumerate(bridges):
            net_config[f"net{i}"] = f"virtio,bridge={bridge}"

        self.api.nodes(target_node).qemu(vmid).config.put(**net_config)
