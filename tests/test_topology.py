"""
Tests for AEGIS Dependency Graph & DSA Algorithms
"""

import pytest
from engine.topology.graph import DependencyGraph

def test_dependency_graph_topology():
    graph = DependencyGraph()
    # Check default nodes
    assert "api_gateway" in graph.nodes
    assert "order_service" in graph.nodes
    assert "inventory_service" in graph.nodes
    assert "postgres" in graph.nodes

    # Check direct dependencies
    deps = graph.get_dependencies("order_service")
    assert "inventory_service" in deps
    assert "payment_service" in deps

def test_blast_radius_computation():
    graph = DependencyGraph()
    # If inventory_service fails, order_service and api_gateway should be impacted
    blast = graph.compute_blast_radius("inventory_service")
    assert "order_service" in blast["impacted_services"]
    assert "api_gateway" in blast["impacted_services"]
    assert blast["blast_radius_count"] >= 3
    assert blast["blast_radius_score"] > 0.3

def test_shortest_propagation_path():
    graph = DependencyGraph()
    path = graph.find_shortest_propagation_path("postgres", "api_gateway")
    assert path is not None
    # Path propagates up: postgres -> inventory_service -> order_service -> api_gateway
    assert path[0] == "postgres"
    assert path[-1] == "api_gateway"

def test_topological_relevance_scoring():
    graph = DependencyGraph()
    # When api_gateway and order_service observe symptoms, inventory_service should have high relevance
    score = graph.calculate_topological_relevance("inventory_service", ["order_service", "api_gateway"])
    assert score > 0.5

    # Completely unrelated component should have very low score
    score_unrelated = graph.calculate_topological_relevance("non_existent_service", ["order_service"])
    assert score_unrelated == 0.0
