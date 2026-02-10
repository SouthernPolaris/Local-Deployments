"""
Interprets the CyberRangeRequest to build a graph representation of the topology.
"""

import networkx as nx
from app.models.schemas import CyberRangeRequest


class GraphEngine:
    """
    Computes network topologies and validates graph integrity.
    Converts a CyberRangeRequest into a NetworkX graph to determine
    bridge assignments and reachability.
    """

    def __init__(self, request: CyberRangeRequest):
        self.request = request
        self.graph = nx.Graph()
        self._build_graph()

        # Pre-compute bridge mapping
        self.bridge_map = {
            tuple(sorted((u, v))): f"vmbr{i + 100}"
            for i, (u, v) in enumerate(self.graph.edges())
        }

    def _build_graph(self) -> None:
        """Constructs the graph from the request's nodes and links."""
        for node in self.request.nodes:
            self.graph.add_node(str(node.id), label=node.label, role=node.role)
        for edge in self.request.links:
            self.graph.add_edge(str(edge.source), str(edge.target))

    def validate_topology(self) -> bool:
        """
        Ensures the graph has a Master Jumpbox and is fully connected,
        and is a valid tree (no cycles).
        """

        # Check for at least one Master Jumpbox
        has_master = any(n.role == "jumpbox_main" for n in self.request.nodes)
        if not has_master:
            return False
        return nx.is_connected(self.graph) and nx.is_tree(self.graph)

    def get_node_interfaces(self, node_id: str) -> list[str]:
        """
        Determines which vmbr interfaces a node should be connected to based on its edges.
        Main jumpbox always gets vmbr0, and other nodes get vmbrX based on their connections.
        """
        interfaces = []
        if node_id not in self.graph:
            return []

        for neighbor in self.graph.neighbors(node_id):
            edge = tuple(sorted((node_id, neighbor)))
            if edge in self.bridge_map:
                interfaces.append(self.bridge_map[edge])

        if self.graph.nodes[node_id].get("role") == "jumpbox_main":
            interfaces.append("vmbr0")

        return interfaces

    def get_reachable_nodes(self):
        """
        Returns a list of nodes that are reachable from Master Jumpbox.
        """
        master = next((n for n in self.request.nodes if n.role == "jumpbox_main"), None)
        if not master:
            return []

        # Convert master ID to string for lookup
        master_id_str = str(master.id)
        if master_id_str not in self.graph:
            return []

        reachable_ids = nx.node_connected_component(self.graph, master_id_str)
        return [n for n in self.request.nodes if str(n.id) in reachable_ids]

    def generate_vmid(self, base: int, exclude: set[int]) -> int:
        while base in exclude:
            base += 1
        return base
