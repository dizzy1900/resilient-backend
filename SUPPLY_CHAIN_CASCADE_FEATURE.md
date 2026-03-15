# Supply Chain Network Graph - Cascading Failure Simulation

## Overview

Production-ready endpoint for simulating cascading failures in multi-tier supply chain networks. Models how disruptions propagate from ports, suppliers, and manufacturers through distribution networks using graph traversal algorithms.

## Endpoint

```
POST /api/v1/supply-chain/simulate-cascade
```

## Request Schema

### `CascadeRequest`

```json
{
  "disrupted_node_id": "port_la",           // Optional: Node ID to disrupt
  "hazard_severity": "Severe"               // Optional: "Moderate" | "Severe" | "Catastrophic"
}
```

**Fields:**
- `disrupted_node_id` (string, optional): ID of the node to disrupt (e.g., "port_la"). If omitted, returns baseline healthy graph.
- `hazard_severity` (string, optional): Severity level affecting downstream propagation. Options:
  - `"Moderate"`: Downstream nodes → Warning status
  - `"Severe"`: Downstream nodes → Warning status
  - `"Catastrophic"`: Downstream nodes → Critical status

### Empty Request (Baseline Graph)

```json
{}
```

Returns the baseline supply chain graph with all nodes in "Secure" status.

## Response Schema

### `CascadeResponse`

```json
{
  "nodes": [
    {
      "id": "port_la",
      "data": {
        "label": "Port of Los Angeles",
        "status": "Critical",
        "type": "Port"
      }
    },
    {
      "id": "chicago_dc",
      "data": {
        "label": "Chicago Distribution Center",
        "status": "Warning",
        "type": "Distribution"
      }
    }
  ],
  "edges": [
    {
      "id": "e4",
      "source": "port_la",
      "target": "chicago_dc",
      "is_disrupted": true
    }
  ]
}
```

**Fields:**
- `nodes`: Array of nodes in React Flow format
  - `id`: Unique node identifier
  - `data.label`: Display name
  - `data.status`: Operational status (`"Secure"` | `"Warning"` | `"Critical"`)
  - `data.type`: Node type (`"Supplier"` | `"Manufacturer"` | `"Port"` | `"Distribution"`)
- `edges`: Array of edges showing supply flow
  - `id`: Unique edge identifier
  - `source`: Source node ID
  - `target`: Target node ID
  - `is_disrupted`: Boolean indicating if this edge is disrupted by cascade

## Base Network Structure

The endpoint uses a realistic 8-node supply chain spanning Asia-Pacific to North America:

### Nodes (8)

1. **taiwan_fab** - Taiwan Semiconductor Fab (Supplier)
2. **shenzhen_assembly** - Shenzhen Assembly Plant (Manufacturer)
3. **port_shanghai** - Port of Shanghai (Port)
4. **port_la** - Port of Los Angeles (Port)
5. **chicago_dc** - Chicago Distribution Center (Distribution)
6. **dallas_warehouse** - Dallas Regional Warehouse (Distribution)
7. **miami_warehouse** - Miami Regional Warehouse (Distribution)
8. **ny_retail** - New York Retail Hub (Distribution)

### Edges (8)

Supply flow path:
```
Taiwan Fab → Shenzhen Assembly → Port Shanghai → Port LA → Chicago DC
                                                              ├→ Dallas Warehouse → NY Retail
                                                              ├→ Miami Warehouse
                                                              └→ NY Retail
```

## Cascading Failure Algorithm

### Logic Flow

1. **Mark Disrupted Node**: Set `status = "Critical"` for the specified node
2. **Find Outgoing Edges**: Identify all edges where `source = disrupted_node_id`
3. **Mark Disrupted Edges**: Set `is_disrupted = true` for these edges
4. **Find Downstream Nodes**: Collect all `target` nodes from disrupted edges
5. **Apply Severity Impact**:
   - **Moderate/Severe**: Downstream nodes → `"Warning"`
   - **Catastrophic**: Downstream nodes → `"Critical"`

### Example: Port LA Disruption (Severe)

**Input:**
```json
{
  "disrupted_node_id": "port_la",
  "hazard_severity": "Severe"
}
```

**Cascade:**
1. `port_la` → Status: `"Critical"`
2. Edge `e4` (`port_la` → `chicago_dc`) → `is_disrupted: true`
3. `chicago_dc` → Status: `"Warning"` (downstream of disrupted edge)
4. Edges `e5`, `e6`, `e7` (`chicago_dc` → warehouses) → **NOT** disrupted (cascade stops at first hop)

**Result:**
- Critical: `port_la`
- Warning: `chicago_dc`
- Secure: All other nodes
- Disrupted edges: `e4` only

## Use Cases

### 1. Port Disruption Scenario Analysis
**Context:** Typhoon, labor strike, or geopolitical event shuts down Port of LA

```json
{
  "disrupted_node_id": "port_la",
  "hazard_severity": "Catastrophic"
}
```

**Business Impact:**
- Identifies critical single point of failure in import logistics
- Quantifies downstream distribution network exposure
- Supports multi-port diversification strategies

### 2. Semiconductor Supply Chain Resilience
**Context:** Taiwan fab disruption due to earthquake or water shortage

```json
{
  "disrupted_node_id": "taiwan_fab",
  "hazard_severity": "Severe"
}
```

**Business Impact:**
- Maps upstream supplier risk to manufacturing operations
- Informs dual-sourcing and inventory buffer decisions
- Supports supply chain insurance underwriting

### 3. Distribution Hub Failure Analysis
**Context:** Chicago DC closure due to flooding or infrastructure failure

```json
{
  "disrupted_node_id": "chicago_dc",
  "hazard_severity": "Severe"
}
```

**Business Impact:**
- Reveals multi-warehouse dependency on single hub
- Guides regional distribution network redesign
- Calculates business continuity plan ROI

### 4. Insurance Underwriting
**Context:** Supply chain disruption policy pricing

- Model parametric triggers (e.g., port closure > 7 days)
- Calculate expected loss from cascading failures
- Structure multi-tier coverage based on network topology

## React Flow Integration

### Frontend Implementation

The response format is optimized for React Flow visualization library:

```typescript
import ReactFlow from 'reactflow';

const SupplyChainGraph = () => {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  const simulateCascade = async (disruptedNode: string, severity: string) => {
    const response = await fetch('/api/v1/supply-chain/simulate-cascade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        disrupted_node_id: disruptedNode,
        hazard_severity: severity
      })
    });
    
    const data = await response.json();
    setGraphData(data);
  };

  return (
    <ReactFlow
      nodes={graphData.nodes}
      edges={graphData.edges}
      // Auto-layout handled by frontend (dagre, elkjs, etc.)
    />
  );
};
```

### Node Styling by Status

```typescript
const getNodeStyle = (status: string) => {
  switch (status) {
    case 'Critical':
      return { background: '#ef4444', color: 'white' };
    case 'Warning':
      return { background: '#f59e0b', color: 'white' };
    case 'Secure':
      return { background: '#10b981', color: 'white' };
  }
};
```

### Edge Styling by Disruption

```typescript
const getEdgeStyle = (isDisrupted: boolean) => ({
  stroke: isDisrupted ? '#ef4444' : '#6b7280',
  strokeWidth: isDisrupted ? 3 : 1,
  strokeDasharray: isDisrupted ? '5,5' : '0'
});
```

## Technical Implementation

### Key Functions

#### `_build_base_supply_chain_graph()`
- Returns baseline 8-node network graph
- All nodes initialized with `status = "Secure"`
- Edges define directed supply flow

#### `_simulate_cascade_failure(nodes, edges, disrupted_node_id, hazard_severity)`
- Graph traversal algorithm
- Single-hop downstream propagation
- Returns updated nodes and edges with disruption states

### Performance

- **Response Time**: < 50ms (in-memory graph operations)
- **Scalability**: O(n) where n = number of edges
- **Memory**: ~2KB per simulation (8 nodes + 8 edges)

## Testing

### Unit Tests

Run comprehensive unit tests:

```bash
cd /Users/david/resilient-backend
python3 test_cascade_unit.py
```

**Test Coverage:**
1. Baseline graph construction
2. Moderate severity cascade
3. Catastrophic severity cascade
4. Upstream supplier disruption
5. Multi-downstream node propagation
6. Invalid node ID handling
7. React Flow format validation

### Integration Test (requires server)

```bash
# Start server
uvicorn api:app --reload --port 8000

# Run integration tests
python3 test_supply_chain_cascade.py
```

## API Contract

### Success Response (200 OK)

```json
{
  "nodes": [...],
  "edges": [...]
}
```

### Error Response (500 Internal Server Error)

```json
{
  "detail": "Supply chain cascade simulation failed: {error_message}"
}
```

## Future Enhancements

### Phase 2: Advanced Features

1. **Multi-Hop Cascade**
   - Propagate disruptions beyond immediate downstream nodes
   - Implement decay factor (e.g., 50% impact reduction per hop)

2. **Custom Network Upload**
   - Accept user-defined graph topology (JSON/GeoJSON)
   - Support 100+ node enterprise supply chains

3. **Economic Quantification**
   - Calculate value-at-risk (VaR) per node
   - Estimate total cascade cost (delay + spoilage + lost sales)

4. **Temporal Simulation**
   - Multi-day cascade with recovery timelines
   - Inventory depletion modeling

5. **Intervention Analysis**
   - Compare cascade impact with/without redundancy (e.g., backup port)
   - Calculate ROI of dual-sourcing strategies

## Related Endpoints

- **Route Risk**: `/api/v1/network/route-risk` - Truck route flood exposure
- **Grid Resilience**: `/api/v1/network/grid-resilience` - Energy grid brownout risk
- **Portfolio Analysis**: `/api/v1/portfolio/analyze` - Multi-asset climate risk

## References

- React Flow Documentation: https://reactflow.dev/
- Graph Traversal Algorithms: DFS/BFS for cascading failures
- Supply Chain Risk Management: ISO 28000 standards

## Changelog

### 2026-03-15 - Initial Release
- ✅ Base 8-node supply chain graph
- ✅ Single-hop cascading failure simulation
- ✅ Three severity levels (Moderate, Severe, Catastrophic)
- ✅ React Flow compatible response format
- ✅ Comprehensive unit test coverage
