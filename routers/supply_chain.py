"""Supply chain endpoints — upload and cascade simulation."""

from __future__ import annotations

import csv
import io
import uuid as uuid_lib
from typing import Optional, List, Literal, Dict, Any, Tuple

import networkx as nx
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from database import async_session
from models import SupplyChainNode, SupplyChainEdge

router = APIRouter(prefix="/api/v1/supply-chain", tags=["Supply Chain"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class NetworkUploadResponse(BaseModel):
    network_id: str
    nodes_created: int
    edges_created: int
    message: str


class CascadeRequest(BaseModel):
    network_id: str = Field(...)
    disrupted_node_id: Optional[str] = Field(None)
    hazard_severity: Optional[Literal["Moderate", "Severe", "Catastrophic"]] = Field(None)


class CascadeNodeData(BaseModel):
    label: str
    status: Literal["Secure", "Warning", "Critical"]
    type: str


class CascadeNode(BaseModel):
    id: str
    data: CascadeNodeData


class CascadeEdge(BaseModel):
    id: str
    source: str
    target: str
    is_disrupted: bool = False


class CascadeResponse(BaseModel):
    nodes: List[CascadeNode]
    edges: List[CascadeEdge]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_base_supply_chain_graph() -> Tuple[List[dict], List[dict]]:
    """Build the baseline supply chain network graph."""
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


def _simulate_cascade_failure(
    nodes: List[dict],
    edges: List[dict],
    disrupted_node_id: str,
    hazard_severity: str,
) -> Tuple[List[dict], List[dict]]:
    """Simulate cascading failure through the supply chain network."""
    updated_nodes = [node.copy() for node in nodes]
    updated_edges = [edge.copy() for edge in edges]

    disrupted_node = None
    for node in updated_nodes:
        if node["id"] == disrupted_node_id:
            node["status"] = "Critical"
            disrupted_node = node
            break

    if not disrupted_node:
        return updated_nodes, updated_edges

    disrupted_edge_ids = []
    for edge in updated_edges:
        if edge["source"] == disrupted_node_id:
            edge["is_disrupted"] = True
            disrupted_edge_ids.append(edge["id"])

    downstream_node_ids = set()
    for edge in updated_edges:
        if edge.get("is_disrupted", False):
            downstream_node_ids.add(edge["target"])

    for node in updated_nodes:
        if node["id"] in downstream_node_ids:
            if hazard_severity == "Catastrophic":
                node["status"] = "Critical"
            else:
                node["status"] = "Warning"

    return updated_nodes, updated_edges


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=NetworkUploadResponse)
async def upload_supply_chain_network(file: UploadFile = File(...)) -> dict:
    """Upload a CSV file to create a new supply chain network."""
    try:
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="File must be a CSV file (.csv extension required)")

        contents = await file.read()
        csv_text = contents.decode("utf-8")

        csv_reader = csv.DictReader(io.StringIO(csv_text))

        required_columns = ["source_id", "source_label", "source_type", "target_id", "target_label", "target_type"]
        if not all(col in csv_reader.fieldnames for col in required_columns):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {', '.join(required_columns)}")

        network_id = str(uuid_lib.uuid4())

        nodes_dict: Dict[str, dict] = {}
        edges_list: List[dict] = []

        for row in csv_reader:
            source_id = row["source_id"].strip()
            source_label = row["source_label"].strip()
            source_type = row["source_type"].strip()
            target_id = row["target_id"].strip()
            target_label = row["target_label"].strip()
            target_type = row["target_type"].strip()

            if source_id not in nodes_dict:
                nodes_dict[source_id] = {"label": source_label, "type": source_type}
            if target_id not in nodes_dict:
                nodes_dict[target_id] = {"label": target_label, "type": target_type}

            edges_list.append({"source": source_id, "target": target_id})

        if not nodes_dict:
            raise HTTPException(status_code=400, detail="CSV contains no valid nodes")
        if not edges_list:
            raise HTTPException(status_code=400, detail="CSV contains no valid edges")

        async with async_session() as session:
            for node_id, node_data in nodes_dict.items():
                node = SupplyChainNode(
                    network_id=network_id,
                    node_id=node_id,
                    label=node_data["label"],
                    node_type=node_data["type"],
                    baseline_status="Secure",
                )
                session.add(node)

            for edge_data in edges_list:
                edge = SupplyChainEdge(
                    network_id=network_id,
                    source_node_id=edge_data["source"],
                    target_node_id=edge_data["target"],
                )
                session.add(edge)

            await session.commit()

        return {
            "network_id": network_id,
            "nodes_created": len(nodes_dict),
            "edges_created": len(edges_list),
            "message": f"Successfully created network with {len(nodes_dict)} nodes and {len(edges_list)} edges",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload network: {str(e)}") from e


@router.post("/simulate-cascade", response_model=CascadeResponse)
async def simulate_supply_chain_cascade(req: CascadeRequest) -> dict:
    """Simulate cascading failures in a supply chain network graph."""
    try:
        async with async_session() as session:
            from sqlalchemy import select

            nodes_result = await session.execute(
                select(SupplyChainNode).where(SupplyChainNode.network_id == req.network_id)
            )
            db_nodes = nodes_result.scalars().all()

            if not db_nodes:
                raise HTTPException(status_code=404, detail=f"Network {req.network_id} not found")

            edges_result = await session.execute(
                select(SupplyChainEdge).where(SupplyChainEdge.network_id == req.network_id)
            )
            db_edges = edges_result.scalars().all()

            if not db_edges:
                raise HTTPException(status_code=404, detail=f"Network {req.network_id} has no edges")

        G = nx.DiGraph()

        node_data_map: Dict[str, dict] = {}
        for node in db_nodes:
            G.add_node(node.node_id)
            node_data_map[node.node_id] = {"label": node.label, "type": node.node_type, "status": node.baseline_status}

        for edge in db_edges:
            G.add_edge(edge.source_node_id, edge.target_node_id)

        if not req.disrupted_node_id:
            react_flow_nodes = [
                {"id": nid, "data": {"label": d["label"], "status": d["status"], "type": d["type"]}}
                for nid, d in node_data_map.items()
            ]
            react_flow_edges = [
                {"id": f"e{i}", "source": s, "target": t, "is_disrupted": False}
                for i, (s, t) in enumerate(G.edges(), 1)
            ]
            return {"nodes": react_flow_nodes, "edges": react_flow_edges}

        if req.disrupted_node_id not in G:
            raise HTTPException(status_code=404, detail=f"Node '{req.disrupted_node_id}' not found in network {req.network_id}")

        try:
            downstream_nodes = nx.descendants(G, req.disrupted_node_id)
        except nx.NetworkXError:
            downstream_nodes = set()

        node_data_map[req.disrupted_node_id]["status"] = "Critical"

        immediate_downstream = set(G.successors(req.disrupted_node_id))

        for nid in immediate_downstream:
            if req.hazard_severity == "Catastrophic":
                node_data_map[nid]["status"] = "Critical"
            else:
                node_data_map[nid]["status"] = "Warning"

        disrupted_edges = set()
        for target in G.successors(req.disrupted_node_id):
            disrupted_edges.add((req.disrupted_node_id, target))

        react_flow_nodes = [
            {"id": nid, "data": {"label": d["label"], "status": d["status"], "type": d["type"]}}
            for nid, d in node_data_map.items()
        ]
        react_flow_edges = [
            {"id": f"e{i}", "source": s, "target": t, "is_disrupted": (s, t) in disrupted_edges}
            for i, (s, t) in enumerate(G.edges(), 1)
        ]

        return {"nodes": react_flow_nodes, "edges": react_flow_edges}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supply chain cascade simulation failed: {str(e)}") from e
