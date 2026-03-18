"""Compliance endpoints — peer benchmarking and TCFD data."""

from __future__ import annotations

import os
from typing import Tuple, List

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/compliance", tags=["Compliance"])

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class BenchmarkResponse(BaseModel):
    sector: str
    hazard_type: str
    metric_name: str
    industry_average: float
    top_quartile_target: float
    unit: str
    data_source: str


# ---------------------------------------------------------------------------
# Benchmark data (loaded from CSV on startup)
# ---------------------------------------------------------------------------

_INDUSTRY_BENCHMARKS: List[dict] = []


def _parse_benchmark_value(value_str: str) -> Tuple[float, str]:
    """Parse benchmark value with unit (e.g., '13.8%' or '5.1 days')."""
    value_str = value_str.strip()
    numeric_str = ""
    unit = ""
    for char in value_str:
        if char.isdigit() or char == "." or char == "-":
            numeric_str += char
        else:
            unit = value_str[len(numeric_str):].strip()
            break
    try:
        numeric_value = float(numeric_str)
    except ValueError:
        raise ValueError(f"Could not parse numeric value from: {value_str}")
    return numeric_value, unit


def load_industry_benchmarks():
    """Load industry benchmark data from CSV file on application startup."""
    global _INDUSTRY_BENCHMARKS

    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "industry_benchmarks.csv")

    try:
        df = pd.read_csv(csv_path)
        benchmarks: list[dict] = []
        for _, row in df.iterrows():
            avg_value, avg_unit = _parse_benchmark_value(row["industry_average"])
            top_value, top_unit = _parse_benchmark_value(row["top_quartile"])

            if avg_unit != top_unit:
                print(f"[Warning] Unit mismatch for {row['sector']} - {row['hazard_type']}: {avg_unit} vs {top_unit}")

            benchmarks.append({
                "sector": row["sector"].strip(),
                "hazard_type": row["hazard_type"].strip(),
                "metric_name": row["metric_name"].strip(),
                "industry_average": avg_value,
                "top_quartile": top_value,
                "unit": avg_unit,
                "data_source": row["data_source"].strip(),
            })

        _INDUSTRY_BENCHMARKS = benchmarks
        print(f"[Benchmark] Loaded {len(benchmarks)} industry benchmarks from CSV")

    except FileNotFoundError:
        print(f"[Benchmark] ERROR: CSV file not found at {csv_path}")
        _INDUSTRY_BENCHMARKS = []
    except Exception as e:
        print(f"[Benchmark] ERROR loading CSV: {e}")
        _INDUSTRY_BENCHMARKS = []


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/benchmark", response_model=BenchmarkResponse)
def get_industry_benchmark(sector: str, hazard_type: str) -> dict:
    """Get peer benchmarking data for regulatory reporting and TCFD compliance."""
    try:
        sector_lower = sector.strip().lower()
        hazard_lower = hazard_type.strip().lower()

        matching_benchmark = None
        for benchmark in _INDUSTRY_BENCHMARKS:
            if benchmark["sector"].lower() == sector_lower and benchmark["hazard_type"].lower() == hazard_lower:
                matching_benchmark = benchmark
                break

        if matching_benchmark is None:
            raise HTTPException(status_code=404, detail="Benchmark data not available for this sector and hazard.")

        return {
            "sector": matching_benchmark["sector"],
            "hazard_type": matching_benchmark["hazard_type"],
            "metric_name": matching_benchmark["metric_name"],
            "industry_average": matching_benchmark["industry_average"],
            "top_quartile_target": matching_benchmark["top_quartile"],
            "unit": matching_benchmark["unit"],
            "data_source": matching_benchmark["data_source"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark lookup failed: {str(e)}") from e
