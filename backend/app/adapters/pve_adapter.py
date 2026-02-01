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

    def get_cluster_status(self) -> list[Any]:
        result = self.api.nodes.get()
        if not result:
            return []
        return list(result)

    def clone_node(self, template_id: int, newid: int, name: str):
        # This will be triggered by Graph Logic
        print(f"Cloning {template_id} to {newid}...")
