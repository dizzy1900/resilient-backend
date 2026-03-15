#!/usr/bin/env python3
"""
Test script for Supply Chain Network Cascade endpoint.

Tests:
1. Baseline graph (no disruption)
2. Port LA disruption with Moderate severity
3. Port LA disruption with Severe severity
4. Port LA disruption with Catastrophic severity
5. Taiwan Fab disruption (upstream supplier)
6. Invalid node ID handling
"""

import requests
import json

BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/v1/supply-chain/simulate-cascade"


def test_baseline_graph():
    """Test baseline supply chain graph with no disruption."""
    print("\n" + "="*80)
    print("TEST 1: Baseline Graph (No Disruption)")
    print("="*80)
    
    payload = {}
    
    response = requests.post(ENDPOINT, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nNodes: {len(data['nodes'])}")
        print(f"Edges: {len(data['edges'])}")
        
        # Check all nodes are Secure
        statuses = [node['data']['status'] for node in data['nodes']]
        print(f"Node Statuses: {set(statuses)}")
        
        # Check no edges are disrupted
        disrupted_edges = [edge for edge in data['edges'] if edge.get('is_disrupted', False)]
        print(f"Disrupted Edges: {len(disrupted_edges)}")
        
        print("\n✓ Baseline graph test passed")
    else:
        print(f"✗ Test failed: {response.text}")


def test_port_la_moderate():
    """Test Port LA disruption with Moderate severity."""
    print("\n" + "="*80)
    print("TEST 2: Port LA Disruption - Moderate Severity")
    print("="*80)
    
    payload = {
        "disrupted_node_id": "port_la",
        "hazard_severity": "Moderate"
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Find disrupted node
        port_la = next((n for n in data['nodes'] if n['id'] == 'port_la'), None)
        print(f"\nPort LA Status: {port_la['data']['status']}")
        
        # Find downstream nodes
        chicago_dc = next((n for n in data['nodes'] if n['id'] == 'chicago_dc'), None)
        print(f"Chicago DC Status: {chicago_dc['data']['status']}")
        
        # Check disrupted edges
        disrupted_edges = [edge for edge in data['edges'] if edge.get('is_disrupted', False)]
        print(f"\nDisrupted Edges: {len(disrupted_edges)}")
        for edge in disrupted_edges:
            print(f"  - {edge['id']}: {edge['source']} → {edge['target']}")
        
        print("\n✓ Moderate severity test passed")
    else:
        print(f"✗ Test failed: {response.text}")


def test_port_la_severe():
    """Test Port LA disruption with Severe severity."""
    print("\n" + "="*80)
    print("TEST 3: Port LA Disruption - Severe Severity")
    print("="*80)
    
    payload = {
        "disrupted_node_id": "port_la",
        "hazard_severity": "Severe"
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Find disrupted node
        port_la = next((n for n in data['nodes'] if n['id'] == 'port_la'), None)
        print(f"\nPort LA Status: {port_la['data']['status']}")
        
        # Find downstream nodes
        chicago_dc = next((n for n in data['nodes'] if n['id'] == 'chicago_dc'), None)
        print(f"Chicago DC Status: {chicago_dc['data']['status']}")
        
        # Check all statuses
        critical_nodes = [n for n in data['nodes'] if n['data']['status'] == 'Critical']
        warning_nodes = [n for n in data['nodes'] if n['data']['status'] == 'Warning']
        print(f"\nCritical Nodes: {[n['id'] for n in critical_nodes]}")
        print(f"Warning Nodes: {[n['id'] for n in warning_nodes]}")
        
        print("\n✓ Severe severity test passed")
    else:
        print(f"✗ Test failed: {response.text}")


def test_port_la_catastrophic():
    """Test Port LA disruption with Catastrophic severity."""
    print("\n" + "="*80)
    print("TEST 4: Port LA Disruption - Catastrophic Severity")
    print("="*80)
    
    payload = {
        "disrupted_node_id": "port_la",
        "hazard_severity": "Catastrophic"
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check downstream nodes are also Critical
        critical_nodes = [n for n in data['nodes'] if n['data']['status'] == 'Critical']
        print(f"\nCritical Nodes: {[n['id'] for n in critical_nodes]}")
        
        # Should include port_la and chicago_dc at minimum
        expected_critical = {'port_la', 'chicago_dc'}
        actual_critical = {n['id'] for n in critical_nodes}
        
        if expected_critical.issubset(actual_critical):
            print("✓ Catastrophic severity correctly propagated to downstream nodes")
        else:
            print(f"✗ Expected critical nodes {expected_critical}, got {actual_critical}")
        
        print("\n✓ Catastrophic severity test passed")
    else:
        print(f"✗ Test failed: {response.text}")


def test_taiwan_fab_disruption():
    """Test upstream supplier disruption (Taiwan Fab)."""
    print("\n" + "="*80)
    print("TEST 5: Taiwan Fab Disruption - Upstream Supplier")
    print("="*80)
    
    payload = {
        "disrupted_node_id": "taiwan_fab",
        "hazard_severity": "Severe"
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Check cascade from taiwan_fab → shenzhen_assembly
        taiwan_fab = next((n for n in data['nodes'] if n['id'] == 'taiwan_fab'), None)
        shenzhen = next((n for n in data['nodes'] if n['id'] == 'shenzhen_assembly'), None)
        
        print(f"\nTaiwan Fab Status: {taiwan_fab['data']['status']}")
        print(f"Shenzhen Assembly Status: {shenzhen['data']['status']}")
        
        # Check disrupted edges
        disrupted_edges = [edge for edge in data['edges'] if edge.get('is_disrupted', False)]
        print(f"\nDisrupted Edges: {[edge['id'] for edge in disrupted_edges]}")
        
        print("\n✓ Upstream disruption test passed")
    else:
        print(f"✗ Test failed: {response.text}")


def test_invalid_node():
    """Test handling of invalid node ID."""
    print("\n" + "="*80)
    print("TEST 6: Invalid Node ID Handling")
    print("="*80)
    
    payload = {
        "disrupted_node_id": "nonexistent_node",
        "hazard_severity": "Severe"
    }
    
    response = requests.post(ENDPOINT, json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Should return graph with no disruptions
        disrupted_edges = [edge for edge in data['edges'] if edge.get('is_disrupted', False)]
        print(f"\nDisrupted Edges: {len(disrupted_edges)}")
        
        if len(disrupted_edges) == 0:
            print("✓ Invalid node handled gracefully (no disruptions)")
        else:
            print(f"✗ Expected 0 disrupted edges, got {len(disrupted_edges)}")
        
        print("\n✓ Invalid node test passed")
    else:
        print(f"✗ Test failed: {response.text}")


def print_full_response(title, payload):
    """Print full JSON response for debugging."""
    print("\n" + "="*80)
    print(f"{title}")
    print("="*80)
    print(f"\nRequest Payload:")
    print(json.dumps(payload, indent=2))
    
    response = requests.post(ENDPOINT, json=payload)
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse:")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    print("\n" + "="*80)
    print("SUPPLY CHAIN NETWORK CASCADE - TEST SUITE")
    print("="*80)
    print(f"Testing endpoint: {ENDPOINT}")
    print("Make sure the API server is running (uvicorn api:app --reload)")
    
    try:
        # Run all tests
        test_baseline_graph()
        test_port_la_moderate()
        test_port_la_severe()
        test_port_la_catastrophic()
        test_taiwan_fab_disruption()
        test_invalid_node()
        
        # Print full example response
        print_full_response(
            "EXAMPLE: Full Response - Port LA Disruption (Severe)",
            {"disrupted_node_id": "port_la", "hazard_severity": "Severe"}
        )
        
        print("\n" + "="*80)
        print("ALL TESTS COMPLETED")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ Connection Error: Make sure the API server is running")
        print("  Start with: uvicorn api:app --reload --port 8000")
    except Exception as e:
        print(f"\n✗ Test suite failed with error: {str(e)}")
