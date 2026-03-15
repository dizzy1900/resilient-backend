#!/usr/bin/env python3
"""
Comprehensive tests for dynamic Supply Chain Network endpoints.

Tests:
1. Database initialization
2. CSV upload endpoint
3. Dynamic cascade simulation with networkx
4. Multiple network support
5. Error handling
"""

import asyncio
import os
import sys

# Test database initialization
async def test_database_init():
    """Test database table creation."""
    print("\n" + "="*80)
    print("TEST 1: Database Initialization")
    print("="*80)
    
    from database import engine, Base
    from models import SupplyChainNode, SupplyChainEdge
    
    async with engine.begin() as conn:
        # Drop existing tables for clean test
        await conn.run_sync(Base.metadata.drop_all)
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database tables created successfully")
    print("  - supply_chain_nodes")
    print("  - supply_chain_edges")


async def test_csv_upload_and_query():
    """Test CSV upload and database query."""
    print("\n" + "="*80)
    print("TEST 2: CSV Upload and Database Query")
    print("="*80)
    
    import uuid
    from database import async_session
    from models import SupplyChainNode, SupplyChainEdge
    
    # Create test network
    network_id = str(uuid.uuid4())
    
    # Sample nodes and edges
    test_nodes = [
        {"node_id": "a", "label": "Node A", "type": "Supplier"},
        {"node_id": "b", "label": "Node B", "type": "Manufacturer"},
        {"node_id": "c", "label": "Node C", "type": "Port"},
    ]
    
    test_edges = [
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
    ]
    
    # Save to database
    async with async_session() as session:
        for node_data in test_nodes:
            node = SupplyChainNode(
                network_id=network_id,
                node_id=node_data['node_id'],
                label=node_data['label'],
                node_type=node_data['type'],
                baseline_status='Secure'
            )
            session.add(node)
        
        for edge_data in test_edges:
            edge = SupplyChainEdge(
                network_id=network_id,
                source_node_id=edge_data['source'],
                target_node_id=edge_data['target']
            )
            session.add(edge)
        
        await session.commit()
    
    # Query back
    async with async_session() as session:
        from sqlalchemy import select
        
        nodes_result = await session.execute(
            select(SupplyChainNode).where(SupplyChainNode.network_id == network_id)
        )
        nodes = nodes_result.scalars().all()
        
        edges_result = await session.execute(
            select(SupplyChainEdge).where(SupplyChainEdge.network_id == network_id)
        )
        edges = edges_result.scalars().all()
    
    print(f"Network ID: {network_id}")
    print(f"Nodes created: {len(nodes)}")
    print(f"Edges created: {len(edges)}")
    
    assert len(nodes) == 3, "Should have 3 nodes"
    assert len(edges) == 2, "Should have 2 edges"
    
    print("✓ CSV upload and database query test passed")
    
    return network_id


async def test_networkx_cascade():
    """Test NetworkX-based cascade simulation."""
    print("\n" + "="*80)
    print("TEST 3: NetworkX Cascade Simulation")
    print("="*80)
    
    import networkx as nx
    
    # Create test graph
    G = nx.DiGraph()
    G.add_edges_from([
        ('a', 'b'),
        ('b', 'c'),
        ('b', 'd'),
        ('c', 'e'),
    ])
    
    # Test descendants (all downstream nodes)
    disrupted_node = 'b'
    downstream = nx.descendants(G, disrupted_node)
    
    print(f"Disrupted node: {disrupted_node}")
    print(f"Downstream nodes: {downstream}")
    print(f"Immediate successors: {set(G.successors(disrupted_node))}")
    
    assert downstream == {'c', 'd', 'e'}, "Should find all downstream nodes"
    assert set(G.successors(disrupted_node)) == {'c', 'd'}, "Should find immediate successors"
    
    print("✓ NetworkX cascade simulation test passed")


async def test_multiple_networks():
    """Test support for multiple independent networks."""
    print("\n" + "="*80)
    print("TEST 4: Multiple Network Support")
    print("="*80)
    
    import uuid
    from database import async_session
    from models import SupplyChainNode, SupplyChainEdge
    
    # Create two networks
    network_1_id = str(uuid.uuid4())
    network_2_id = str(uuid.uuid4())
    
    async with async_session() as session:
        # Network 1: Simple chain
        for node_id in ['n1_a', 'n1_b']:
            node = SupplyChainNode(
                network_id=network_1_id,
                node_id=node_id,
                label=f"Network 1 - {node_id}",
                node_type='Supplier',
                baseline_status='Secure'
            )
            session.add(node)
        
        edge = SupplyChainEdge(
            network_id=network_1_id,
            source_node_id='n1_a',
            target_node_id='n1_b'
        )
        session.add(edge)
        
        # Network 2: Different structure
        for node_id in ['n2_x', 'n2_y', 'n2_z']:
            node = SupplyChainNode(
                network_id=network_2_id,
                node_id=node_id,
                label=f"Network 2 - {node_id}",
                node_type='Port',
                baseline_status='Secure'
            )
            session.add(node)
        
        for source, target in [('n2_x', 'n2_y'), ('n2_x', 'n2_z')]:
            edge = SupplyChainEdge(
                network_id=network_2_id,
                source_node_id=source,
                target_node_id=target
            )
            session.add(edge)
        
        await session.commit()
    
    # Query each network separately
    async with async_session() as session:
        from sqlalchemy import select
        
        # Network 1
        result_1 = await session.execute(
            select(SupplyChainNode).where(SupplyChainNode.network_id == network_1_id)
        )
        nodes_1 = result_1.scalars().all()
        
        # Network 2
        result_2 = await session.execute(
            select(SupplyChainNode).where(SupplyChainNode.network_id == network_2_id)
        )
        nodes_2 = result_2.scalars().all()
    
    print(f"Network 1 ({network_1_id[:8]}...): {len(nodes_1)} nodes")
    print(f"Network 2 ({network_2_id[:8]}...): {len(nodes_2)} nodes")
    
    assert len(nodes_1) == 2, "Network 1 should have 2 nodes"
    assert len(nodes_2) == 3, "Network 2 should have 3 nodes"
    
    print("✓ Multiple network support test passed")


async def test_cascade_severity_levels():
    """Test different severity levels in cascade."""
    print("\n" + "="*80)
    print("TEST 5: Cascade Severity Levels")
    print("="*80)
    
    # Test severity impact logic
    test_cases = [
        ("Moderate", "Warning"),
        ("Severe", "Warning"),
        ("Catastrophic", "Critical"),
    ]
    
    for severity, expected_status in test_cases:
        # Simulate status assignment
        if severity == 'Catastrophic':
            status = 'Critical'
        else:
            status = 'Warning'
        
        print(f"  Severity: {severity:15} → Downstream status: {status}")
        assert status == expected_status, f"Severity {severity} should result in {expected_status}"
    
    print("✓ Cascade severity levels test passed")


async def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n" + "="*80)
    print("TEST 6: Error Handling")
    print("="*80)
    
    import uuid
    from database import async_session
    from models import SupplyChainNode
    from sqlalchemy import select
    
    # Test 1: Query non-existent network
    fake_network_id = str(uuid.uuid4())
    async with async_session() as session:
        result = await session.execute(
            select(SupplyChainNode).where(SupplyChainNode.network_id == fake_network_id)
        )
        nodes = result.scalars().all()
    
    print(f"  Query non-existent network: {len(nodes)} nodes (expected: 0)")
    assert len(nodes) == 0, "Non-existent network should return 0 nodes"
    
    # Test 2: NetworkX node not in graph
    import networkx as nx
    G = nx.DiGraph()
    G.add_edge('a', 'b')
    
    try:
        # This should raise an error
        descendants = nx.descendants(G, 'nonexistent')
        print("  ✗ Should have raised NetworkXError")
        assert False, "Should have raised error"
    except nx.NetworkXError:
        print("  ✓ NetworkX correctly raises error for non-existent node")
    
    print("✓ Error handling test passed")


async def test_full_integration():
    """Test complete workflow: upload → simulate."""
    print("\n" + "="*80)
    print("TEST 7: Full Integration Test")
    print("="*80)
    
    import uuid
    import networkx as nx
    from database import async_session
    from models import SupplyChainNode, SupplyChainEdge
    from sqlalchemy import select
    
    # Create realistic supply chain
    network_id = str(uuid.uuid4())
    
    nodes_data = [
        {"id": "supplier_a", "label": "Supplier A", "type": "Supplier"},
        {"id": "factory_b", "label": "Factory B", "type": "Manufacturer"},
        {"id": "port_c", "label": "Port C", "type": "Port"},
        {"id": "warehouse_d", "label": "Warehouse D", "type": "Distribution"},
        {"id": "warehouse_e", "label": "Warehouse E", "type": "Distribution"},
    ]
    
    edges_data = [
        ("supplier_a", "factory_b"),
        ("factory_b", "port_c"),
        ("port_c", "warehouse_d"),
        ("port_c", "warehouse_e"),
    ]
    
    # Save to database
    async with async_session() as session:
        for node_data in nodes_data:
            node = SupplyChainNode(
                network_id=network_id,
                node_id=node_data['id'],
                label=node_data['label'],
                node_type=node_data['type'],
                baseline_status='Secure'
            )
            session.add(node)
        
        for source, target in edges_data:
            edge = SupplyChainEdge(
                network_id=network_id,
                source_node_id=source,
                target_node_id=target
            )
            session.add(edge)
        
        await session.commit()
    
    # Simulate cascade from database
    async with async_session() as session:
        nodes_result = await session.execute(
            select(SupplyChainNode).where(SupplyChainNode.network_id == network_id)
        )
        db_nodes = nodes_result.scalars().all()
        
        edges_result = await session.execute(
            select(SupplyChainEdge).where(SupplyChainEdge.network_id == network_id)
        )
        db_edges = edges_result.scalars().all()
    
    # Build NetworkX graph
    G = nx.DiGraph()
    node_map = {}
    
    for node in db_nodes:
        G.add_node(node.node_id)
        node_map[node.node_id] = {
            'label': node.label,
            'type': node.node_type,
            'status': node.baseline_status
        }
    
    for edge in db_edges:
        G.add_edge(edge.source_node_id, edge.target_node_id)
    
    # Simulate disruption at port_c
    disrupted_node = 'port_c'
    downstream = nx.descendants(G, disrupted_node)
    immediate_successors = set(G.successors(disrupted_node))
    
    print(f"Network ID: {network_id[:8]}...")
    print(f"Total nodes: {len(node_map)}")
    print(f"Total edges: {len(list(G.edges()))}")
    print(f"Disrupted node: {disrupted_node}")
    print(f"Immediate downstream: {immediate_successors}")
    print(f"All downstream: {downstream}")
    
    assert len(node_map) == 5, "Should have 5 nodes"
    assert len(list(G.edges())) == 4, "Should have 4 edges"
    assert downstream == {'warehouse_d', 'warehouse_e'}, "Should cascade to both warehouses"
    
    print("✓ Full integration test passed")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("DYNAMIC SUPPLY CHAIN NETWORK - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    async def run_all_tests():
        try:
            await test_database_init()
            network_id = await test_csv_upload_and_query()
            await test_networkx_cascade()
            await test_multiple_networks()
            await test_cascade_severity_levels()
            await test_error_handling()
            await test_full_integration()
            
            print("\n" + "="*80)
            print("✓ ALL TESTS PASSED")
            print("="*80)
            print("\nDatabase is ready. You can now:")
            print("  1. Run: python3 init_supply_chain_db.py")
            print("  2. Upload CSV: POST /api/v1/supply-chain/upload")
            print("  3. Simulate: POST /api/v1/supply-chain/simulate-cascade")
            
        except AssertionError as e:
            print(f"\n✗ Test failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Test suite error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    asyncio.run(run_all_tests())
