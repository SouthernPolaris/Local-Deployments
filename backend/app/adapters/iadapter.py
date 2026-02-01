from abc import ABC, abstractmethod
from typing import Any


class ICloudAdapter(ABC):
    @abstractmethod
    def get_cluster_status(self) -> list[Any]:
        pass

    @abstractmethod
    def clone_node(self, template_id: int, newid: int, name: str):
        pass
