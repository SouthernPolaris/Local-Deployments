
import networkx as nx
from app.models.schemas import CyberRangeRequest


class GraphEngine:
    def __init__(self, request: CyberRangeRequest):
        self.request = request
        self.graph = nx.Graph()
        self._build_graph()

        self.bridge_map = {
            tuple(sorted((u, v))): f"vmbr{i + 100}"
            for i, (u, v) in enumerate(self.graph.edges())
        }

    def _build_graph(self) -> None:
        """
        Loads nodes and edges into a NetworkX graph object
        """
        for node in self.request.nodes:
            self.graph.add_node(node.id, label=node.label, role=node.role)

        for edge in self.request.links:
            self.graph.add_edge(
                edge.source,
                edge.target,
            )

    def validate_topology(self) -> bool:
        """
        Ensure range is a valid undirected tree
        (all nodes connected, no cycles)
        """

        is_connected = nx.is_connected(self.graph)
        is_tree = nx.is_tree(self.graph)
        return is_connected and is_tree

    def compute_network_plan(self) -> list[dict[str, str]]:
        """
        Translates Graph Edges into Proxmox Bridges
        Each edge in undirected tree becomes an isolated bridge
        """

        plan = []

        # Iterate over edges to assign bridge names
        for i, (u, v) in enumerate(self.graph.edges()):
            bridge_name = f"vmbr{i + 100}"  # Starting from vmbr100
            plan.append({"source": u, "target": v, "bridge": bridge_name})

        return plan

    def get_node_interfaces(self, node_id: str) -> list[str]:
        """
        Returns list of bridges a specific VM needs to connect to
        """
        interfaces = []

        # Get internal bridges from graph logic
        for edge in self.graph.edges(node_id):
            sorted_edge = tuple(sorted(edge))
            interfaces.append(self.bridge_map[sorted_edge])

        # Add external connection for the main jumpbox
        node_data = self.graph.nodes[node_id]
        if node_data.get("role") == "jumpbox_main":
            interfaces.append("vmbr0")

        return interfaces
