"""
Handles persistence of active cyber range states in a JSON file.
NOTE: Only for demonstration. Needs to be unmodifiable except from this class to prevent corruption.
Otherwise, Zombie VMs may occur if the file is manually edited while the Engine is running.
"""

import json
from pathlib import Path
from uuid import UUID

from app.models.schemas import CyberRangeRequest

STATE_FILE = Path("active_ranges.json")


class StateManager:
    """
    Manages the saving, loading, and deletion of cyber range states.
    """

    @staticmethod
    def _load_all() -> dict:
        if not STATE_FILE.exists():
            return {}
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    @staticmethod
    def _write_all(data: dict) -> None:
        temp_file = STATE_FILE.with_suffix(".tmp")
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)
        temp_file.replace(STATE_FILE)

    @staticmethod
    def get_range(range_id: UUID | str) -> dict | None:
        return StateManager._load_all().get(str(range_id))

    @staticmethod
    def save_range(request: CyberRangeRequest, status: str = "provisioning") -> None:
        data = StateManager._load_all()
        range_id = str(request.range_metadata.id)

        data[range_id] = {
            "metadata": request.range_metadata.model_dump(mode="json"),
            "nodes": [iter_node.model_dump(mode="json") for iter_node in request.nodes],
            "links": [iter_link.model_dump(mode="json") for iter_link in request.links],
            "status": status,
        }
        StateManager._write_all(data)

    @staticmethod
    def get_all() -> list:
        return list(StateManager._load_all().values())

    @staticmethod
    def delete_range(range_id: UUID | str) -> bool:
        data = StateManager._load_all()
        str_id = str(range_id)
        if str_id in data:
            del data[str_id]
            StateManager._write_all(data)
            return True
        return False

    @staticmethod
    def map_nodes_by_id(state: dict | None) -> dict:
        """Maps nodes for O(1) lookup during syncing."""
        if not state:
            return {}
        return {str(n["id"]).strip(): n for n in state.get("nodes", [])}
