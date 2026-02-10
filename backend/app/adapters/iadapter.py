"""
Abstract Base Class for cloud infrastructure providers.

Any new provider (e.g., AzureAdapter) must implement these methods to ensure
compatibility with the Engine.
"""

from abc import ABC, abstractmethod
from typing import Any


class ICloudAdapter(ABC):
    @abstractmethod
    def get_cluster_status(self) -> list[Any]:
        pass

    @abstractmethod
    def clone_node(self, template_id: int, newid: int, name: str):
        """
        NOTE: Implementations should ensure 'newid' is not already occupied
        by the provider's API.
        """
        pass

    @abstractmethod
    def delete_vm(self, vmid: int):
        pass

    @abstractmethod
    def configure_network(self, vmid: int, bridges: list[str]):
        pass
