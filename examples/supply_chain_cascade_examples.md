# Supply Chain Cascade API - Example Requests & Responses

## Example 1: Baseline Graph (No Disruption)

### Request

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/simulate-cascade \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Response (200 OK)

```json
{
  "nodes": [
    {
      "id": "taiwan_fab",
      "data": {
        "label": "Taiwan Semiconductor Fab",
        "status": "Secure",
        "type": "Supplier"
      }
    },
    {
      "id": "shenzhen_assembly",
      "data": {
        "label": "Shenzhen Assembly Plant",
        "status": "Secure",
        "type": "Manufacturer"
      }
    },
    {
      "id": "port_shanghai",
      "data": {
        "label": "Port of Shanghai",
        "status": "Secure",
        "type": "Port"
      }
    },
    {
      "id": "port_la",
      "data": {
        "label": "Port of Los Angeles",
        "status": "Secure",
        "type": "Port"
      }
    },
    {
      "id": "chicago_dc",
      "data": {
        "label": "Chicago Distribution Center",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "dallas_warehouse",
      "data": {
        "label": "Dallas Regional Warehouse",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "miami_warehouse",
      "data": {
        "label": "Miami Regional Warehouse",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "ny_retail",
      "data": {
        "label": "New York Retail Hub",
        "status": "Secure",
        "type": "Distribution"
      }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "taiwan_fab",
      "target": "shenzhen_assembly",
      "is_disrupted": false
    },
    {
      "id": "e2",
      "source": "shenzhen_assembly",
      "target": "port_shanghai",
      "is_disrupted": false
    },
    {
      "id": "e3",
      "source": "port_shanghai",
      "target": "port_la",
      "is_disrupted": false
    },
    {
      "id": "e4",
      "source": "port_la",
      "target": "chicago_dc",
      "is_disrupted": false
    },
    {
      "id": "e5",
      "source": "chicago_dc",
      "target": "dallas_warehouse",
      "is_disrupted": false
    },
    {
      "id": "e6",
      "source": "chicago_dc",
      "target": "miami_warehouse",
      "is_disrupted": false
    },
    {
      "id": "e7",
      "source": "chicago_dc",
      "target": "ny_retail",
      "is_disrupted": false
    },
    {
      "id": "e8",
      "source": "dallas_warehouse",
      "target": "ny_retail",
      "is_disrupted": false
    }
  ]
}
```

---

## Example 2: Port LA Disruption (Moderate Severity)

### Request

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/simulate-cascade \
  -H "Content-Type: application/json" \
  -d '{
    "disrupted_node_id": "port_la",
    "hazard_severity": "Moderate"
  }'
```

### Response (200 OK)

```json
{
  "nodes": [
    {
      "id": "taiwan_fab",
      "data": {
        "label": "Taiwan Semiconductor Fab",
        "status": "Secure",
        "type": "Supplier"
      }
    },
    {
      "id": "shenzhen_assembly",
      "data": {
        "label": "Shenzhen Assembly Plant",
        "status": "Secure",
        "type": "Manufacturer"
      }
    },
    {
      "id": "port_shanghai",
      "data": {
        "label": "Port of Shanghai",
        "status": "Secure",
        "type": "Port"
      }
    },
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
    },
    {
      "id": "dallas_warehouse",
      "data": {
        "label": "Dallas Regional Warehouse",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "miami_warehouse",
      "data": {
        "label": "Miami Regional Warehouse",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "ny_retail",
      "data": {
        "label": "New York Retail Hub",
        "status": "Secure",
        "type": "Distribution"
      }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "taiwan_fab",
      "target": "shenzhen_assembly",
      "is_disrupted": false
    },
    {
      "id": "e2",
      "source": "shenzhen_assembly",
      "target": "port_shanghai",
      "is_disrupted": false
    },
    {
      "id": "e3",
      "source": "port_shanghai",
      "target": "port_la",
      "is_disrupted": false
    },
    {
      "id": "e4",
      "source": "port_la",
      "target": "chicago_dc",
      "is_disrupted": true
    },
    {
      "id": "e5",
      "source": "chicago_dc",
      "target": "dallas_warehouse",
      "is_disrupted": false
    },
    {
      "id": "e6",
      "source": "chicago_dc",
      "target": "miami_warehouse",
      "is_disrupted": false
    },
    {
      "id": "e7",
      "source": "chicago_dc",
      "target": "ny_retail",
      "is_disrupted": false
    },
    {
      "id": "e8",
      "source": "dallas_warehouse",
      "target": "ny_retail",
      "is_disrupted": false
    }
  ]
}
```

**Key Changes:**
- `port_la` → Status: `Critical`
- `chicago_dc` → Status: `Warning`
- Edge `e4` → `is_disrupted: true`

---

## Example 3: Port LA Disruption (Catastrophic Severity)

### Request

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/simulate-cascade \
  -H "Content-Type: application/json" \
  -d '{
    "disrupted_node_id": "port_la",
    "hazard_severity": "Catastrophic"
  }'
```

### Response (200 OK)

```json
{
  "nodes": [
    {
      "id": "taiwan_fab",
      "data": {
        "label": "Taiwan Semiconductor Fab",
        "status": "Secure",
        "type": "Supplier"
      }
    },
    {
      "id": "shenzhen_assembly",
      "data": {
        "label": "Shenzhen Assembly Plant",
        "status": "Secure",
        "type": "Manufacturer"
      }
    },
    {
      "id": "port_shanghai",
      "data": {
        "label": "Port of Shanghai",
        "status": "Secure",
        "type": "Port"
      }
    },
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
        "status": "Critical",
        "type": "Distribution"
      }
    },
    {
      "id": "dallas_warehouse",
      "data": {
        "label": "Dallas Regional Warehouse",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "miami_warehouse",
      "data": {
        "label": "Miami Regional Warehouse",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "ny_retail",
      "data": {
        "label": "New York Retail Hub",
        "status": "Secure",
        "type": "Distribution"
      }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "taiwan_fab",
      "target": "shenzhen_assembly",
      "is_disrupted": false
    },
    {
      "id": "e2",
      "source": "shenzhen_assembly",
      "target": "port_shanghai",
      "is_disrupted": false
    },
    {
      "id": "e3",
      "source": "port_shanghai",
      "target": "port_la",
      "is_disrupted": false
    },
    {
      "id": "e4",
      "source": "port_la",
      "target": "chicago_dc",
      "is_disrupted": true
    },
    {
      "id": "e5",
      "source": "chicago_dc",
      "target": "dallas_warehouse",
      "is_disrupted": false
    },
    {
      "id": "e6",
      "source": "chicago_dc",
      "target": "miami_warehouse",
      "is_disrupted": false
    },
    {
      "id": "e7",
      "source": "chicago_dc",
      "target": "ny_retail",
      "is_disrupted": false
    },
    {
      "id": "e8",
      "source": "dallas_warehouse",
      "target": "ny_retail",
      "is_disrupted": false
    }
  ]
}
```

**Key Changes:**
- `port_la` → Status: `Critical`
- `chicago_dc` → Status: `Critical` (escalated from Warning due to Catastrophic severity)
- Edge `e4` → `is_disrupted: true`

---

## Example 4: Taiwan Fab Disruption (Upstream Supplier)

### Request

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/simulate-cascade \
  -H "Content-Type: application/json" \
  -d '{
    "disrupted_node_id": "taiwan_fab",
    "hazard_severity": "Severe"
  }'
```

### Response (200 OK)

```json
{
  "nodes": [
    {
      "id": "taiwan_fab",
      "data": {
        "label": "Taiwan Semiconductor Fab",
        "status": "Critical",
        "type": "Supplier"
      }
    },
    {
      "id": "shenzhen_assembly",
      "data": {
        "label": "Shenzhen Assembly Plant",
        "status": "Warning",
        "type": "Manufacturer"
      }
    },
    {
      "id": "port_shanghai",
      "data": {
        "label": "Port of Shanghai",
        "status": "Secure",
        "type": "Port"
      }
    },
    {
      "id": "port_la",
      "data": {
        "label": "Port of Los Angeles",
        "status": "Secure",
        "type": "Port"
      }
    },
    {
      "id": "chicago_dc",
      "data": {
        "label": "Chicago Distribution Center",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "dallas_warehouse",
      "data": {
        "label": "Dallas Regional Warehouse",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "miami_warehouse",
      "data": {
        "label": "Miami Regional Warehouse",
        "status": "Secure",
        "type": "Distribution"
      }
    },
    {
      "id": "ny_retail",
      "data": {
        "label": "New York Retail Hub",
        "status": "Secure",
        "type": "Distribution"
      }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "taiwan_fab",
      "target": "shenzhen_assembly",
      "is_disrupted": true
    },
    {
      "id": "e2",
      "source": "shenzhen_assembly",
      "target": "port_shanghai",
      "is_disrupted": false
    },
    {
      "id": "e3",
      "source": "port_shanghai",
      "target": "port_la",
      "is_disrupted": false
    },
    {
      "id": "e4",
      "source": "port_la",
      "target": "chicago_dc",
      "is_disrupted": false
    },
    {
      "id": "e5",
      "source": "chicago_dc",
      "target": "dallas_warehouse",
      "is_disrupted": false
    },
    {
      "id": "e6",
      "source": "chicago_dc",
      "target": "miami_warehouse",
      "is_disrupted": false
    },
    {
      "id": "e7",
      "source": "chicago_dc",
      "target": "ny_retail",
      "is_disrupted": false
    },
    {
      "id": "e8",
      "source": "dallas_warehouse",
      "target": "ny_retail",
      "is_disrupted": false
    }
  ]
}
```

**Key Changes:**
- `taiwan_fab` → Status: `Critical`
- `shenzhen_assembly` → Status: `Warning`
- Edge `e1` → `is_disrupted: true`
- Cascade stops at first hop (port_shanghai remains Secure)

---

## Example 5: Chicago DC Disruption (Multiple Downstream)

### Request

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/simulate-cascade \
  -H "Content-Type: application/json" \
  -d '{
    "disrupted_node_id": "chicago_dc",
    "hazard_severity": "Severe"
  }'
```

### Response (200 OK)

```json
{
  "nodes": [
    {
      "id": "taiwan_fab",
      "data": {
        "label": "Taiwan Semiconductor Fab",
        "status": "Secure",
        "type": "Supplier"
      }
    },
    {
      "id": "shenzhen_assembly",
      "data": {
        "label": "Shenzhen Assembly Plant",
        "status": "Secure",
        "type": "Manufacturer"
      }
    },
    {
      "id": "port_shanghai",
      "data": {
        "label": "Port of Shanghai",
        "status": "Secure",
        "type": "Port"
      }
    },
    {
      "id": "port_la",
      "data": {
        "label": "Port of Los Angeles",
        "status": "Secure",
        "type": "Port"
      }
    },
    {
      "id": "chicago_dc",
      "data": {
        "label": "Chicago Distribution Center",
        "status": "Critical",
        "type": "Distribution"
      }
    },
    {
      "id": "dallas_warehouse",
      "data": {
        "label": "Dallas Regional Warehouse",
        "status": "Warning",
        "type": "Distribution"
      }
    },
    {
      "id": "miami_warehouse",
      "data": {
        "label": "Miami Regional Warehouse",
        "status": "Warning",
        "type": "Distribution"
      }
    },
    {
      "id": "ny_retail",
      "data": {
        "label": "New York Retail Hub",
        "status": "Warning",
        "type": "Distribution"
      }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "taiwan_fab",
      "target": "shenzhen_assembly",
      "is_disrupted": false
    },
    {
      "id": "e2",
      "source": "shenzhen_assembly",
      "target": "port_shanghai",
      "is_disrupted": false
    },
    {
      "id": "e3",
      "source": "port_shanghai",
      "target": "port_la",
      "is_disrupted": false
    },
    {
      "id": "e4",
      "source": "port_la",
      "target": "chicago_dc",
      "is_disrupted": false
    },
    {
      "id": "e5",
      "source": "chicago_dc",
      "target": "dallas_warehouse",
      "is_disrupted": true
    },
    {
      "id": "e6",
      "source": "chicago_dc",
      "target": "miami_warehouse",
      "is_disrupted": true
    },
    {
      "id": "e7",
      "source": "chicago_dc",
      "target": "ny_retail",
      "is_disrupted": true
    },
    {
      "id": "e8",
      "source": "dallas_warehouse",
      "target": "ny_retail",
      "is_disrupted": false
    }
  ]
}
```

**Key Changes:**
- `chicago_dc` → Status: `Critical`
- `dallas_warehouse`, `miami_warehouse`, `ny_retail` → Status: `Warning`
- Edges `e5`, `e6`, `e7` → `is_disrupted: true`
- Demonstrates multi-downstream propagation from single hub

---

## Frontend JavaScript Examples

### Fetch Baseline Graph

```javascript
async function loadBaselineGraph() {
  const response = await fetch('/api/v1/supply-chain/simulate-cascade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({})
  });
  
  const data = await response.json();
  console.log('Baseline nodes:', data.nodes.length);
  console.log('Baseline edges:', data.edges.length);
  return data;
}
```

### Simulate Port Disruption

```javascript
async function simulatePortDisruption(portId, severity) {
  const response = await fetch('/api/v1/supply-chain/simulate-cascade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      disrupted_node_id: portId,
      hazard_severity: severity
    })
  });
  
  const data = await response.json();
  
  // Count impacts
  const criticalNodes = data.nodes.filter(n => n.data.status === 'Critical');
  const warningNodes = data.nodes.filter(n => n.data.status === 'Warning');
  const disruptedEdges = data.edges.filter(e => e.is_disrupted);
  
  console.log(`Critical nodes: ${criticalNodes.length}`);
  console.log(`Warning nodes: ${warningNodes.length}`);
  console.log(`Disrupted edges: ${disruptedEdges.length}`);
  
  return data;
}

// Usage
simulatePortDisruption('port_la', 'Catastrophic');
```

### React Component Example

```typescript
import React, { useState, useEffect } from 'react';
import ReactFlow, { Node, Edge } from 'reactflow';

interface CascadeData {
  nodes: Node[];
  edges: Edge[];
}

const SupplyChainSimulator: React.FC = () => {
  const [graphData, setGraphData] = useState<CascadeData>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<string>('');
  const [severity, setSeverity] = useState<string>('Severe');

  const loadBaseline = async () => {
    const response = await fetch('/api/v1/supply-chain/simulate-cascade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await response.json();
    setGraphData(data);
  };

  const simulateCascade = async () => {
    if (!selectedNode) return;
    
    const response = await fetch('/api/v1/supply-chain/simulate-cascade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        disrupted_node_id: selectedNode,
        hazard_severity: severity
      })
    });
    const data = await response.json();
    setGraphData(data);
  };

  useEffect(() => {
    loadBaseline();
  }, []);

  return (
    <div>
      <div style={{ marginBottom: '20px' }}>
        <select value={selectedNode} onChange={(e) => setSelectedNode(e.target.value)}>
          <option value="">Select node to disrupt</option>
          <option value="port_la">Port of Los Angeles</option>
          <option value="chicago_dc">Chicago Distribution Center</option>
          <option value="taiwan_fab">Taiwan Semiconductor Fab</option>
        </select>
        
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
          <option value="Moderate">Moderate</option>
          <option value="Severe">Severe</option>
          <option value="Catastrophic">Catastrophic</option>
        </select>
        
        <button onClick={simulateCascade}>Simulate Cascade</button>
        <button onClick={loadBaseline}>Reset</button>
      </div>
      
      <div style={{ height: '600px', border: '1px solid #ccc' }}>
        <ReactFlow
          nodes={graphData.nodes}
          edges={graphData.edges}
          fitView
        />
      </div>
    </div>
  );
};

export default SupplyChainSimulator;
```

---

## Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def simulate_cascade(disrupted_node=None, severity=None):
    """Simulate supply chain cascade failure."""
    payload = {}
    if disrupted_node:
        payload['disrupted_node_id'] = disrupted_node
    if severity:
        payload['hazard_severity'] = severity
    
    response = requests.post(
        f"{BASE_URL}/api/v1/supply-chain/simulate-cascade",
        json=payload
    )
    
    return response.json()

# Example: Baseline graph
baseline = simulate_cascade()
print(f"Baseline: {len(baseline['nodes'])} nodes, {len(baseline['edges'])} edges")

# Example: Port LA disruption
disruption = simulate_cascade('port_la', 'Severe')
critical = [n for n in disruption['nodes'] if n['data']['status'] == 'Critical']
print(f"Critical nodes: {[n['id'] for n in critical]}")
```
