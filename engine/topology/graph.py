"""
AEGIS Service Dependency Graph Engine
Implements graph data structures and DSA algorithms: BFS, DFS, shortest path,
blast radius, and topological candidate relevance ranking.
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import deque
from engine.models.schemas import DependencyEdge

class DependencyGraph:
    def __init__(self):
        # Directed adjacency lists
        # forward_adj: caller -> list of callees (dependencies)
        self.forward_adj: Dict[str, List[str]] = {}
        # backward_adj: callee -> list of callers (dependents)
        self.backward_adj: Dict[str, List[str]] = {}
        self.edges: List[DependencyEdge] = []
        self.nodes: Set[str] = set()

        self._build_default_topology()

    def _build_default_topology(self):
        default_edges = [
            DependencyEdge(source_service_id="api_gateway", target_service_id="user_service", dependency_type="SYNC_HTTP"),
            DependencyEdge(source_service_id="api_gateway", target_service_id="order_service", dependency_type="SYNC_HTTP"),
            DependencyEdge(source_service_id="order_service", target_service_id="user_service", dependency_type="SYNC_HTTP"),
            DependencyEdge(source_service_id="order_service", target_service_id="inventory_service", dependency_type="SYNC_HTTP"),
            DependencyEdge(source_service_id="order_service", target_service_id="payment_service", dependency_type="SYNC_HTTP"),
            DependencyEdge(source_service_id="payment_service", target_service_id="redis", dependency_type="CACHE_LOOKUP"),
            DependencyEdge(source_service_id="inventory_service", target_service_id="postgres", dependency_type="DB_CALL"),
        ]
        for edge in default_edges:
            self.add_edge(edge)

    def add_edge(self, edge: DependencyEdge):
        self.edges.append(edge)
        u, v = edge.source_service_id, edge.target_service_id
        self.nodes.add(u)
        self.nodes.add(v)

        if u not in self.forward_adj:
            self.forward_adj[u] = []
        if v not in self.forward_adj[u]:
            self.forward_adj[u].append(v)

        if v not in self.backward_adj:
            self.backward_adj[v] = []
        if u not in self.backward_adj[v]:
            self.backward_adj[v].append(u)

    def get_dependencies(self, service_id: str) -> List[str]:
        """Direct callees of service_id."""
        return self.forward_adj.get(service_id, [])

    def get_dependents(self, service_id: str) -> List[str]:
        """Direct callers of service_id."""
        return self.backward_adj.get(service_id, [])

    def get_all_downstream_dependencies(self, service_id: str) -> List[str]:
        """BFS: All transitive dependencies that service_id relies on."""
        visited = set()
        queue = deque([service_id])
        result = []

        while queue:
            curr = queue.popleft()
            for neighbor in self.forward_adj.get(curr, []):
                if neighbor not in visited and neighbor != service_id:
                    visited.add(neighbor)
                    result.append(neighbor)
                    queue.append(neighbor)
        return result

    def get_all_upstream_impacted(self, service_id: str) -> List[str]:
        """BFS: All upstream services impacted if service_id fails (blast radius)."""
        visited = set()
        queue = deque([service_id])
        result = []

        while queue:
            curr = queue.popleft()
            for caller in self.backward_adj.get(curr, []):
                if caller not in visited and caller != service_id:
                    visited.add(caller)
                    result.append(caller)
                    queue.append(caller)
        return result

    def compute_blast_radius(self, root_service: str) -> Dict[str, Any]:
        impacted = self.get_all_upstream_impacted(root_service)
        total_services = len(self.nodes)
        score = (len(impacted) + 1) / max(1, total_services)
        return {
            "root_service": root_service,
            "impacted_services": impacted,
            "blast_radius_count": len(impacted) + 1,
            "blast_radius_score": round(min(1.0, score), 2)
        }

    def find_shortest_propagation_path(self, from_service: str, to_service: str) -> Optional[List[str]]:
        """BFS shortest path from potential root cause to symptom."""
        if from_service == to_service:
            return [from_service]

        queue = deque([(from_service, [from_service])])
        visited = {from_service}

        while queue:
            curr, path = queue.popleft()
            # In propagation, failure propagates along backward_adj (caller of callee)
            for caller in self.backward_adj.get(curr, []):
                if caller == to_service:
                    return path + [caller]
                if caller not in visited:
                    visited.add(caller)
                    queue.append((caller, path + [caller]))

        return None

    def calculate_topological_relevance(self, candidate: str, anomalous_services: List[str]) -> float:
        """
        Calculates topological likelihood that 'candidate' is the root cause.
        Higher if candidate can reach (explain) all anomalous services via propagation.
        """
        if not anomalous_services:
            return 0.1

        if candidate not in self.nodes:
            return 0.0

        reachable_count = 0
        for symptom in anomalous_services:
            if candidate == symptom:
                reachable_count += 1
            else:
                path = self.find_shortest_propagation_path(candidate, symptom)
                if path:
                    reachable_count += 1

        coverage_ratio = reachable_count / len(anomalous_services)
        
        # Downstream services explaining upstream symptoms get priority
        downstream_depth = len(self.get_dependencies(candidate))
        has_upstream_symptoms = reachable_count > 1
        depth_boost = 1.15 if (has_upstream_symptoms and downstream_depth >= 1) else 1.0

        score = coverage_ratio * depth_boost
        return round(float(min(1.0, max(0.05, score))), 3)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": list(self.nodes),
            "edges": [
                {
                    "source": e.source_service_id,
                    "target": e.target_service_id,
                    "type": e.dependency_type
                }
                for e in self.edges
            ]
        }
