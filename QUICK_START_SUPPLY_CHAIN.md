# Supply Chain Network Graph - Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies

```bash
cd /Users/david/resilient-backend

# Install NetworkX and greenlet
pip install networkx==3.2.1 greenlet==3.0.3

# Or install all requirements
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python3 init_supply_chain_db.py
```

Expected output:
```
✓ Database tables created successfully:
  - supply_chain_nodes
  - supply_chain_edges
```

### 3. Start API Server

```bash
uvicorn api:app --reload --port 8000
```

---

## Usage Example (End-to-End)

### Step 1: Upload Supply Chain Network (CSV)

Create a CSV file `my_supply_chain.csv`:

```csv
source_id,source_label,source_type,target_id,target_label,target_type
supplier_a,Supplier A,Supplier,factory_b,Factory B,Manufacturer
factory_b,Factory B,Manufacturer,port_c,Port C,Port
port_c,Port C,Port,warehouse_d,Warehouse D,Distribution
port_c,Port C,Port,warehouse_e,Warehouse E,Distribution
```

Upload via API:

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/upload \
  -F "file=@my_supply_chain.csv"
```

Response:
```json
{
  "network_id": "a3f4e8b2-1234-5678-9abc-def012345678",
  "nodes_created": 5,
  "edges_created": 4,
  "message": "Successfully created network with 5 nodes and 4 edges"
}
```

**Save the `network_id` - you'll need it for simulation!**

---

### Step 2: Simulate Baseline (No Disruption)

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/simulate-cascade \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": "a3f4e8b2-1234-5678-9abc-def012345678"
  }'
```

Response shows all nodes in "Secure" status:
```json
{
  "nodes": [
    {
      "id": "supplier_a",
      "data": {
        "label": "Supplier A",
        "status": "Secure",
        "type": "Supplier"
      }
    },
    ...
  ],
  "edges": [
    {
      "id": "e1",
      "source": "supplier_a",
      "target": "factory_b",
      "is_disrupted": false
    },
    ...
  ]
}
```

---

### Step 3: Simulate Disruption (Port C Closure)

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/simulate-cascade \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": "a3f4e8b2-1234-5678-9abc-def012345678",
    "disrupted_node_id": "port_c",
    "hazard_severity": "Severe"
  }'
```

Response shows cascade impacts:
```json
{
  "nodes": [
    {
      "id": "port_c",
      "data": {
        "label": "Port C",
        "status": "Critical",
        "type": "Port"
      }
    },
    {
      "id": "warehouse_d",
      "data": {
        "label": "Warehouse D",
        "status": "Warning",
        "type": "Distribution"
      }
    },
    {
      "id": "warehouse_e",
      "data": {
        "label": "Warehouse E",
        "status": "Warning",
        "type": "Distribution"
      }
    }
  ],
  "edges": [
    {
      "id": "e3",
      "source": "port_c",
      "target": "warehouse_d",
      "is_disrupted": true
    },
    {
      "id": "e4",
      "source": "port_c",
      "target": "warehouse_e",
      "is_disrupted": true
    }
  ]
}
```

**Analysis:**
- ❌ **Port C**: Critical (disrupted)
- ⚠️ **Warehouse D**: Warning (downstream impact)
- ⚠️ **Warehouse E**: Warning (downstream impact)
- ✅ **Supplier A, Factory B**: Secure (upstream, unaffected)

---

## Severity Levels

| Severity | Impact on Downstream Nodes |
|----------|----------------------------|
| **Moderate** | Downstream → Warning |
| **Severe** | Downstream → Warning |
| **Catastrophic** | Downstream → Critical |

### Example: Catastrophic Severity

```bash
curl -X POST http://localhost:8000/api/v1/supply-chain/simulate-cascade \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": "YOUR_NETWORK_ID",
    "disrupted_node_id": "port_c",
    "hazard_severity": "Catastrophic"
  }'
```

Result:
- Port C: **Critical**
- Warehouse D: **Critical** (escalated from Warning)
- Warehouse E: **Critical** (escalated from Warning)

---

## Sample CSV Templates

### Template 1: Simple Linear Chain

```csv
source_id,source_label,source_type,target_id,target_label,target_type
node_a,Node A,Supplier,node_b,Node B,Manufacturer
node_b,Node B,Manufacturer,node_c,Node C,Port
node_c,Node C,Port,node_d,Node D,Distribution
```

### Template 2: Hub-and-Spoke

```csv
source_id,source_label,source_type,target_id,target_label,target_type
supplier,Central Supplier,Supplier,hub,Distribution Hub,Distribution
hub,Distribution Hub,Distribution,region_1,Region 1 Warehouse,Distribution
hub,Distribution Hub,Distribution,region_2,Region 2 Warehouse,Distribution
hub,Distribution Hub,Distribution,region_3,Region 3 Warehouse,Distribution
```

### Template 3: Multi-Tier (Realistic)

```csv
source_id,source_label,source_type,target_id,target_label,target_type
raw_supplier,Raw Material Supplier,Supplier,component_mfg,Component Manufacturer,Manufacturer
component_mfg,Component Manufacturer,Manufacturer,assembly_plant,Assembly Plant,Manufacturer
assembly_plant,Assembly Plant,Manufacturer,port_origin,Port of Origin,Port
port_origin,Port of Origin,Port,port_destination,Port of Destination,Port
port_destination,Port of Destination,Port,regional_dc,Regional DC,Distribution
regional_dc,Regional DC,Distribution,local_warehouse_1,Local Warehouse 1,Distribution
regional_dc,Regional DC,Distribution,local_warehouse_2,Local Warehouse 2,Distribution
```

---

## Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Upload network
with open('my_supply_chain.csv', 'rb') as f:
    response = requests.post(
        f"{BASE_URL}/api/v1/supply-chain/upload",
        files={'file': f}
    )
    upload_result = response.json()
    network_id = upload_result['network_id']
    print(f"Network ID: {network_id}")

# Step 2: Simulate cascade
cascade_request = {
    "network_id": network_id,
    "disrupted_node_id": "port_c",
    "hazard_severity": "Severe"
}

response = requests.post(
    f"{BASE_URL}/api/v1/supply-chain/simulate-cascade",
    json=cascade_request
)

cascade_result = response.json()

# Analyze results
critical_nodes = [n for n in cascade_result['nodes'] if n['data']['status'] == 'Critical']
warning_nodes = [n for n in cascade_result['nodes'] if n['data']['status'] == 'Warning']
disrupted_edges = [e for e in cascade_result['edges'] if e['is_disrupted']]

print(f"Critical Nodes: {[n['id'] for n in critical_nodes]}")
print(f"Warning Nodes: {[n['id'] for n in warning_nodes]}")
print(f"Disrupted Edges: {len(disrupted_edges)}")
```

---

## React Integration

```typescript
import React, { useState } from 'react';
import ReactFlow from 'reactflow';

const SupplyChainVisualization = () => {
  const [networkId, setNetworkId] = useState('');
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });

  // Upload CSV
  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('/api/v1/supply-chain/upload', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();
    setNetworkId(result.network_id);
    
    // Load baseline graph
    simulateCascade(result.network_id, null, null);
  };

  // Simulate cascade
  const simulateCascade = async (
    netId: string,
    disruptedNode: string | null,
    severity: string | null
  ) => {
    const response = await fetch('/api/v1/supply-chain/simulate-cascade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        network_id: netId,
        disrupted_node_id: disruptedNode,
        hazard_severity: severity
      })
    });

    const data = await response.json();
    setGraphData(data);
  };

  return (
    <div>
      <input
        type="file"
        accept=".csv"
        onChange={(e) => e.target.files && handleFileUpload(e.target.files[0])}
      />
      
      <button onClick={() => simulateCascade(networkId, 'port_c', 'Severe')}>
        Simulate Port C Disruption
      </button>

      <div style={{ height: '600px' }}>
        <ReactFlow
          nodes={graphData.nodes}
          edges={graphData.edges}
          fitView
        />
      </div>
    </div>
  );
};
```

---

## Testing

### Run Unit Tests

```bash
python3 test_supply_chain_dynamic.py
```

Expected output:
```
✓ ALL TESTS PASSED

Database is ready. You can now:
  1. Run: python3 init_supply_chain_db.py
  2. Upload CSV: POST /api/v1/supply-chain/upload
  3. Simulate: POST /api/v1/supply-chain/simulate-cascade
```

---

## Troubleshooting

### Issue: "File must be a CSV file"

**Error:**
```json
{
  "detail": "File must be a CSV file (.csv extension required)"
}
```

**Solution:** Ensure file has `.csv` extension.

---

### Issue: "CSV must contain columns"

**Error:**
```json
{
  "detail": "CSV must contain columns: source_id, source_label, source_type, target_id, target_label, target_type"
}
```

**Solution:** Add header row to CSV:
```csv
source_id,source_label,source_type,target_id,target_label,target_type
node_a,Node A,Supplier,node_b,Node B,Manufacturer
```

---

### Issue: "Network not found"

**Error:**
```json
{
  "detail": "Network a3f4e8b2-... not found"
}
```

**Solution:** 
1. Verify `network_id` matches upload response
2. Check database: `sqlite3 resilient.db "SELECT * FROM supply_chain_nodes;"`

---

## Next Steps

1. **Explore Advanced Features**: See `SUPPLY_CHAIN_DYNAMIC_UPGRADE.md`
2. **Run Full Test Suite**: `python3 test_supply_chain_dynamic.py`
3. **Deploy to Production**: Migrate to PostgreSQL (see upgrade guide)
4. **Integrate with Frontend**: Use React Flow for visualization

---

## Support

- **Documentation**: `SUPPLY_CHAIN_DYNAMIC_UPGRADE.md`
- **API Examples**: `examples/supply_chain_cascade_examples.md`
- **Sample CSV**: `examples/sample_supply_chain.csv`
- **Tests**: `test_supply_chain_dynamic.py`
