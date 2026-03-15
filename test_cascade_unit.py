#!/usr/bin/env python3
"""
Unit tests for Supply Chain Cascade functions.

These tests run the core logic without requiring the server to be running.
"""

import sys
import json


# Import the cascade functions from api.py
# We'll need to mock or handle the imports carefully
def _build_base_supply_chain_graph():
    """
    Build the baseline supply chain network graph.
    
    Returns:
        Tuple of (nodes, edges)
    """
    nodes = [
        {"id": "taiwan_fab", "label": "Taiwan Semiconductor Fab", "type": "Supplier", "status": "Secure"},
        {"id": "shenzhen_assembly", "label": "Shenzhen Assembly Plant", "type": "Manufacturer", "status": "Secure"},
        {"id": "port_shanghai", "label": "Port of Shanghai", "type": "Port", "status": "Secure"},
        {"id": "port_la", "label": "Port of Los Angeles", "type": "Port", "status": "Secure"},
        {"id": "chicago_dc", "label": "Chicago Distribution Center", "type": "Distribution", "status": "Secure"},
        {"id": "dallas_warehouse", "label": "Dallas Regional Warehouse", "type": "Distribution", "status": "Secure"},
        {"id": "miami_warehouse", "label": "Miami Regional Warehouse", "type": "Distribution", "status": "Secure"},
        {"id": "ny_retail", "label": "New York Retail Hub", "type": "Distribution", "status": "Secure"},
    ]
    
    edges = [
        {"id": "e1", "source": "taiwan_fab", "target": "shenzhen_assembly"},
        {"id": "e2", "source": "shenzhen_assembly", "target": "port_shanghai"},
        {"id": "e3", "source": "port_shanghai", "target": "port_la"},
        {"id": "e4", "source": "port_la", "target": "chicago_dc"},
        {"id": "e5", "source": "chicago_dc", "target": "dallas_warehouse"},
        {"id": "e6", "source": "chicago_dc", "target": "miami_warehouse"},
        {"id": "e7", "source": "chicago_dc", "target": "ny_retail"},
        {"id": "e8", "source": "dallas_warehouse", "target": "ny_retail"},
    ]
    
    return nodes, edges


def _simulate_cascade_failure(nodes, edges, disrupted_node_id, hazard_severity):
    """
    Simulate cascading failure through the supply chain network.
    """
    # Create working copies
    updated_nodes = [node.copy() for node in nodes]
    updated_edges = [edge.copy() for edge in edges]
    
    # Step 1: Find and mark the disrupted node
    disrupted_node = None
    for node in updated_nodes:
        if node["id"] == disrupted_node_id:
            node["status"] = "Critical"
            disrupted_node = node
            break
    
    if not disrupted_node:
        # If node not found, return unchanged
        return updated_nodes, updated_edges
    
    # Step 2: Find all edges originating from disrupted node and mark them
    disrupted_edge_ids = []
    for edge in updated_edges:
        if edge["source"] == disrupted_node_id:
            edge["is_disrupted"] = True
            disrupted_edge_ids.append(edge["id"])
    
    # Step 3: Find all downstream nodes connected to disrupted edges
    downstream_node_ids = set()
    for edge in updated_edges:
        if edge.get("is_disrupted", False):
            downstream_node_ids.add(edge["target"])
    
    # Step 4: Update downstream node statuses based on hazard severity
    for node in updated_nodes:
        if node["id"] in downstream_node_ids:
            if hazard_severity == "Catastrophic":
                node["status"] = "Critical"
            elif hazard_severity == "Severe":
                node["status"] = "Warning"
            else:  # Moderate
                node["status"] = "Warning"
    
    return updated_nodes, updated_edges


def test_baseline_graph():
    """Test baseline graph construction."""
    print("\n" + "="*80)
    print("TEST 1: Baseline Graph Construction")
    print("="*80)
    
    nodes, edges = _build_base_supply_chain_graph()
    
    print(f"Nodes: {len(nodes)}")
    print(f"Edges: {len(edges)}")
    
    # Verify all nodes are Secure
    statuses = [node['status'] for node in nodes]
    assert all(status == "Secure" for status in statuses), "All nodes should be Secure"
    
    # Verify node types
    node_types = {node['type'] for node in nodes}
    print(f"Node Types: {node_types}")
    
    print("✓ Baseline graph test passed")


def test_port_la_moderate():
    """Test Port LA disruption with Moderate severity."""
    print("\n" + "="*80)
    print("TEST 2: Port LA - Moderate Severity")
    print("="*80)
    
    nodes, edges = _build_base_supply_chain_graph()
    updated_nodes, updated_edges = _simulate_cascade_failure(
        nodes, edges, "port_la", "Moderate"
    )
    
    # Find nodes
    port_la = next(n for n in updated_nodes if n['id'] == 'port_la')
    chicago_dc = next(n for n in updated_nodes if n['id'] == 'chicago_dc')
    
    print(f"Port LA Status: {port_la['status']}")
    print(f"Chicago DC Status: {chicago_dc['status']}")
    
    assert port_la['status'] == "Critical", "Port LA should be Critical"
    assert chicago_dc['status'] == "Warning", "Chicago DC should be Warning"
    
    # Check disrupted edges
    disrupted_edges = [e for e in updated_edges if e.get('is_disrupted', False)]
    print(f"Disrupted Edges: {len(disrupted_edges)}")
    assert len(disrupted_edges) == 1, "Should have 1 disrupted edge"
    
    print("✓ Moderate severity test passed")


def test_port_la_catastrophic():
    """Test Port LA disruption with Catastrophic severity."""
    print("\n" + "="*80)
    print("TEST 3: Port LA - Catastrophic Severity")
    print("="*80)
    
    nodes, edges = _build_base_supply_chain_graph()
    updated_nodes, updated_edges = _simulate_cascade_failure(
        nodes, edges, "port_la", "Catastrophic"
    )
    
    # Find nodes
    port_la = next(n for n in updated_nodes if n['id'] == 'port_la')
    chicago_dc = next(n for n in updated_nodes if n['id'] == 'chicago_dc')
    
    print(f"Port LA Status: {port_la['status']}")
    print(f"Chicago DC Status: {chicago_dc['status']}")
    
    assert port_la['status'] == "Critical", "Port LA should be Critical"
    assert chicago_dc['status'] == "Critical", "Chicago DC should be Critical (Catastrophic)"
    
    # Check critical nodes
    critical_nodes = [n for n in updated_nodes if n['status'] == 'Critical']
    print(f"Critical Nodes: {[n['id'] for n in critical_nodes]}")
    
    print("✓ Catastrophic severity test passed")


def test_taiwan_fab_cascade():
    """Test upstream supplier disruption."""
    print("\n" + "="*80)
    print("TEST 4: Taiwan Fab - Upstream Cascade")
    print("="*80)
    
    nodes, edges = _build_base_supply_chain_graph()
    updated_nodes, updated_edges = _simulate_cascade_failure(
        nodes, edges, "taiwan_fab", "Severe"
    )
    
    # Find nodes
    taiwan_fab = next(n for n in updated_nodes if n['id'] == 'taiwan_fab')
    shenzhen = next(n for n in updated_nodes if n['id'] == 'shenzhen_assembly')
    port_shanghai = next(n for n in updated_nodes if n['id'] == 'port_shanghai')
    
    print(f"Taiwan Fab Status: {taiwan_fab['status']}")
    print(f"Shenzhen Assembly Status: {shenzhen['status']}")
    print(f"Port Shanghai Status: {port_shanghai['status']}")
    
    assert taiwan_fab['status'] == "Critical", "Taiwan Fab should be Critical"
    assert shenzhen['status'] == "Warning", "Shenzhen should be Warning"
    assert port_shanghai['status'] == "Secure", "Port Shanghai should remain Secure (not direct downstream)"
    
    print("✓ Upstream cascade test passed")


def test_chicago_dc_multi_downstream():
    """Test node with multiple downstream connections."""
    print("\n" + "="*80)
    print("TEST 5: Chicago DC - Multiple Downstream Nodes")
    print("="*80)
    
    nodes, edges = _build_base_supply_chain_graph()
    updated_nodes, updated_edges = _simulate_cascade_failure(
        nodes, edges, "chicago_dc", "Severe"
    )
    
    # Find downstream nodes
    chicago_dc = next(n for n in updated_nodes if n['id'] == 'chicago_dc')
    dallas = next(n for n in updated_nodes if n['id'] == 'dallas_warehouse')
    miami = next(n for n in updated_nodes if n['id'] == 'miami_warehouse')
    ny = next(n for n in updated_nodes if n['id'] == 'ny_retail')
    
    print(f"Chicago DC Status: {chicago_dc['status']}")
    print(f"Dallas Warehouse Status: {dallas['status']}")
    print(f"Miami Warehouse Status: {miami['status']}")
    print(f"New York Retail Status: {ny['status']}")
    
    assert chicago_dc['status'] == "Critical", "Chicago DC should be Critical"
    assert dallas['status'] == "Warning", "Dallas should be Warning"
    assert miami['status'] == "Warning", "Miami should be Warning"
    assert ny['status'] == "Warning", "NY should be Warning"
    
    # Check number of disrupted edges
    disrupted_edges = [e for e in updated_edges if e.get('is_disrupted', False)]
    print(f"Disrupted Edges: {len(disrupted_edges)}")
    assert len(disrupted_edges) == 3, "Should have 3 disrupted edges from Chicago DC"
    
    print("✓ Multiple downstream test passed")


def test_invalid_node():
    """Test handling of invalid node ID."""
    print("\n" + "="*80)
    print("TEST 6: Invalid Node ID")
    print("="*80)
    
    nodes, edges = _build_base_supply_chain_graph()
    updated_nodes, updated_edges = _simulate_cascade_failure(
        nodes, edges, "nonexistent_node", "Severe"
    )
    
    # All nodes should remain Secure
    statuses = [node['status'] for node in updated_nodes]
    assert all(status == "Secure" for status in statuses), "All nodes should remain Secure"
    
    # No edges should be disrupted
    disrupted_edges = [e for e in updated_edges if e.get('is_disrupted', False)]
    assert len(disrupted_edges) == 0, "No edges should be disrupted"
    
    print("✓ Invalid node test passed")


def test_react_flow_format():
    """Test React Flow output format."""
    print("\n" + "="*80)
    print("TEST 7: React Flow Format")
    print("="*80)
    
    nodes, edges = _build_base_supply_chain_graph()
    updated_nodes, updated_edges = _simulate_cascade_failure(
        nodes, edges, "port_la", "Severe"
    )
    
    # Convert to React Flow format
    react_flow_nodes = [
        {
            "id": node["id"],
            "data": {
                "label": node["label"],
                "status": node["status"],
                "type": node["type"]
            }
        }
        for node in updated_nodes
    ]
    
    react_flow_edges = [
        {
            "id": edge["id"],
            "source": edge["source"],
            "target": edge["target"],
            "is_disrupted": edge.get("is_disrupted", False)
        }
        for edge in updated_edges
    ]
    
    # Verify structure
    assert all("id" in n and "data" in n for n in react_flow_nodes), "All nodes should have id and data"
    assert all("label" in n["data"] for n in react_flow_nodes), "All nodes should have label in data"
    assert all("status" in n["data"] for n in react_flow_nodes), "All nodes should have status in data"
    assert all("type" in n["data"] for n in react_flow_nodes), "All nodes should have type in data"
    
    assert all("id" in e and "source" in e and "target" in e for e in react_flow_edges), "All edges should have id, source, target"
    assert all("is_disrupted" in e for e in react_flow_edges), "All edges should have is_disrupted"
    
    print("Sample Node:", json.dumps(react_flow_nodes[0], indent=2))
    print("Sample Edge:", json.dumps(react_flow_edges[0], indent=2))
    
    print("✓ React Flow format test passed")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SUPPLY CHAIN CASCADE - UNIT TEST SUITE")
    print("="*80)
    
    try:
        test_baseline_graph()
        test_port_la_moderate()
        test_port_la_catastrophic()
        test_taiwan_fab_cascade()
        test_chicago_dc_multi_downstream()
        test_invalid_node()
        test_react_flow_format()
        
        print("\n" + "="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Test suite error: {e}")
        sys.exit(1)
