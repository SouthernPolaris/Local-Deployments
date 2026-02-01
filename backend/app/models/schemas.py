from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# --- Metadata for whole range ---
class RangeMetadata(BaseModel):
    id: UUID
    name: str
    created_by: str | None = None


# --- Hardware Resources ---
class VMResource(BaseModel):
    cores: int = 2
    memory: int = 2048  # in MB


class VMNode(BaseModel):
    id: str
    label: str
    template_id: int
    role: Literal["jumpbox_main", "jumpbox_local", "service"]
    resources: VMResource = Field(default_factory=VMResource)


# --- Connection between VMs ---
class VMLink(BaseModel):
    id: str | None = None
    source: str
    target: str
    connection_type: Literal["vlan_bridge", "direct_link"] = "vlan_bridge"


# --- Root Object (Request Body) ---
class CyberRangeRequest(BaseModel):
    range_metadata: RangeMetadata
    nodes: list[VMNode]
    links: list[VMLink]


class DeploymentResponse(BaseModel):
    range_id: UUID
    status: str
    message: str
