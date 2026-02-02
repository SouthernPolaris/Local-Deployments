import json
import os
from pathlib import Path
from uuid import UUID
from app.models.schemas import CyberRangeRequest

STATE_FILE = Path("active_ranges.json")

class StateManager:
    @staticmethod
    def _load_all() -> dict:
        if not STATE_FILE.exists():
            return {} 
        
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
        
    @staticmethod
    def save_range(request: CyberRangeRequest, status: str = "provisioning") -> None:
        """
        Saves or updates state of a cyber range deployment
        """
        data = StateManager._load_all()

        range_id = str(request.range_metadata.id)

        data[range_id] = {
            "metadata": request.range_metadata.model_dump(mode="json"),
            "nodes": [n.model_dump(mode="json") for n in request.nodes],
            "links": [l.model_dump(mode="json") for l in request.links],
            "status": status
        }

        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def delete_range(range_id: UUID) -> bool:
        """
        Deletes a cyber range deployment from state
        """
        data = StateManager._load_all()
        str_id = str(range_id)

        if str_id in data:
            del data[str_id]
            with open(STATE_FILE, "w") as f:
                json.dump(data, f, indent=4)
            return True
        return False
    
    @staticmethod
    def get_all() -> list:
        """
        Returns list of all saved cyber range deployments
        """
        data = StateManager._load_all()
        return list(data.values())