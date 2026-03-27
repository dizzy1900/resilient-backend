"""Portfolio analysis endpoints — CSV upload and structured portfolio."""

from __future__ import annotations

import asyncio
import io
import json
import os
import re
import sys
from typing import Dict, Any, List, Literal, Optional
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from resilient_score import calculate_resilient_score

router = APIRouter(prefix="/api/v1/portfolio", tags=["Portfolio"])


def _resolve_headless_runner_path() -> Path:
    """Resolve `headless_runner.py` without relying on current working directory."""
    this_dir = Path(__file__).resolve().parent
    for candidate_dir in (this_dir, *this_dir.parents):
        candidate = candidate_dir / "headless_runner.py"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Unable to locate 'headless_runner.py' in the repo.")

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class PortfolioAsset(BaseModel):
    id: str
    property_name: str
    location: str
    asset_value: float = Field(..., gt=0)
    primary_hazard: Literal["Flood", "Heat", "Coastal", "Supply Chain"]


class PortfolioRequest(BaseModel):
    assets: List[PortfolioAsset] = Field(..., min_length=1)


class CalculatedAsset(BaseModel):
    id: str
    property_name: str
    location: str
    asset_value: float
    primary_hazard: str
    value_at_risk: float
    resilience_score: float
    status: Literal["Critical", "Warning", "Secure"]


class PortfolioSummary(BaseModel):
    total_portfolio_value: float
    total_value_at_risk: float
    average_resilience_score: float
    average_resilient_score: Optional[float] = None


class PortfolioVisualizations(BaseModel):
    var_by_hazard: Dict[str, float]
    top_at_risk_assets: List[CalculatedAsset]


class PortfolioResponse(BaseModel):
    summary: PortfolioSummary
    visualizations: PortfolioVisualizations
    ledger: List[CalculatedAsset]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def process_single_asset(row_data: dict, row_index: int) -> dict:
    """Process a single portfolio asset asynchronously."""
    try:
        runner_path = _resolve_headless_runner_path()
        lat = float(row_data["lat"])
        lon = float(row_data["lon"])
        crop_type = str(row_data["crop_type"])
        asset_value = float(row_data["asset_value"])

        scenario_year = int(row_data.get("scenario_year", 2050))
        temp_delta = float(row_data.get("temp_delta", 0.0))
        rain_pct_change = float(row_data.get("rain_pct_change", 0.0))

        cmd = [
            sys.executable,
            str(runner_path),
            "--lat", str(lat), "--lon", str(lon),
            "--scenario_year", str(scenario_year),
            "--project_type", "agriculture",
            "--crop_type", crop_type,
            "--temp_delta", str(temp_delta),
            "--rain_pct_change", str(rain_pct_change),
        ]

        env = os.environ.copy()
        env["FINANCIAL_CAPEX"] = str(asset_value)
        env["FINANCIAL_OPEX"] = str(asset_value * 0.1)
        env["FINANCIAL_DISCOUNT_RATE"] = "0.10"
        env["FINANCIAL_YEARS"] = "10"

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(runner_path.parent),
            env=env,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return {"row_index": row_index, "status": "error", "error": f"Simulation failed: {stderr.decode()}", "input": row_data}

        result = json.loads(stdout.decode())
        result["row_index"] = row_index
        result["status"] = "success"
        result["input"] = row_data
        try:
            result["resilient_score_data"] = calculate_resilient_score(result)
        except Exception:
            result["resilient_score_data"] = None
        return result

    except json.JSONDecodeError as e:
        return {"row_index": row_index, "status": "error", "error": f"Failed to parse simulation output: {str(e)}", "input": row_data}
    except (ValueError, KeyError) as e:
        return {"row_index": row_index, "status": "error", "error": f"Invalid row data: {str(e)}", "input": row_data}
    except Exception as e:
        return {"row_index": row_index, "status": "error", "error": f"Unexpected error: {str(e)}", "input": row_data}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/analyze-csv")
async def analyze_portfolio_csv(file: UploadFile = File(...)) -> dict:
    """Analyze a CSV portfolio upload with concurrent processing."""
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        df.columns = df.columns.astype(str).str.lower().str.replace(r"[^a-z0-9_]", "", regex=True)

        lat_col = next((c for c in df.columns if "lat" in c), "lat")
        lon_col = next((c for c in df.columns if "lon" in c or "lng" in c), "lon")
        val_col = next((c for c in df.columns if any(x in c for x in ["val", "price", "amount", "cost", "invest", "usd"])), None)
        if not val_col and len(df.columns) > 2:
            val_col = df.columns[2]
        if not val_col:
            val_col = "asset_value"
        crop_col = next((c for c in df.columns if "crop" in c), "crop_type")

        df.dropna(how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)

        required_columns = [lat_col, lon_col, val_col, crop_col]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Detected columns: {list(df.columns)}",
            )

        records: list[dict] = []
        for _, row in df.iterrows():
            raw_val = str(row.get(val_col, "0")).lower()
            multiplier = 1
            if "m" in raw_val:
                multiplier = 1000000
            elif "k" in raw_val:
                multiplier = 1000
            elif "b" in raw_val:
                multiplier = 1000000000
            clean_val = re.sub(r"[^0-9.]", "", raw_val)
            try:
                val = float(clean_val) * multiplier if clean_val else 0.0
            except ValueError:
                val = 0.0
            lat = float(row.get(lat_col, 0.0))
            lon = float(row.get(lon_col, 0.0))
            crop = str(row.get(crop_col, "unknown"))
            record: dict = {"lat": lat, "lon": lon, "asset_value": val, "crop_type": crop}
            for col in df.columns:
                if col not in (lat_col, lon_col, val_col, crop_col):
                    record[col] = row.get(col)
            records.append(record)

        tasks = [process_single_asset(row, idx) for idx, row in enumerate(records)]
        results = await asyncio.gather(*tasks)

        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") == "error"]

        total_portfolio_value = sum(r["input"]["asset_value"] for r in results)

        total_value_at_risk = 0.0
        resilience_scores: list[float] = []
        total_npv = 0.0
        total_expected_loss = 0.0

        for result in successful:
            monte_carlo = result.get("monte_carlo", {})
            var_95 = monte_carlo.get("var_95", 0.0)
            if var_95:
                total_value_at_risk += abs(float(var_95))

            resilience_score = result.get("resilience_score")
            if resilience_score is not None:
                try:
                    resilience_scores.append(float(resilience_score))
                except (ValueError, TypeError):
                    pass

            financial = result.get("financial", {})
            npv = financial.get("npv_usd", 0.0)
            if npv:
                total_npv += float(npv)

            risk = result.get("risk", {})
            expected_loss = risk.get("expected_loss_usd", 0.0)
            if expected_loss:
                total_expected_loss += float(expected_loss)

        average_resilience_score = sum(resilience_scores) / len(resilience_scores) if resilience_scores else 0.0

        scores = [a.get("resilient_score_data", {}).get("resilient_score") for a in results if a.get("resilient_score_data")]
        scores = [s for s in scores if s is not None]
        average_resilient_score = round(sum(scores) / len(scores), 1) if scores else None

        portfolio_summary = {
            "total_assets": len(records),
            "successful_simulations": len(successful),
            "failed_simulations": len(failed),
            "total_portfolio_value_usd": round(float(total_portfolio_value), 2),
            "total_value_at_risk_usd": round(float(total_value_at_risk), 2),
            "average_resilience_score": round(float(average_resilience_score), 2),
            "total_npv_usd": round(float(total_npv), 2),
            "total_expected_loss_usd": round(float(total_expected_loss), 2),
            "risk_exposure_pct": round((total_value_at_risk / total_portfolio_value * 100) if total_portfolio_value > 0 else 0.0, 2),
            "crop_distribution": df[crop_col].value_counts().to_dict(),
            "average_resilient_score": average_resilient_score,
        }
        return {"portfolio_summary": portfolio_summary, "asset_results": results}

    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Uploaded CSV file is empty")
    except pd.errors.ParserError as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV file: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio analysis failed: {str(e)}") from e


@router.post("/analyze", response_model=PortfolioResponse)
def analyze_portfolio(req: PortfolioRequest) -> dict:
    """Analyze macro-portfolio risk across multiple assets with different climate hazards."""
    try:
        HAZARD_VAR = {"Flood": 0.15, "Heat": 0.05, "Coastal": 0.20, "Supply Chain": 0.10}

        calculated_assets = []
        for asset in req.assets:
            var_percentage = HAZARD_VAR[asset.primary_hazard]
            value_at_risk = asset.asset_value * var_percentage
            resilience_score = 100.0 - (var_percentage * 100.0 * 5.0)

            if resilience_score < 40:
                status = "Critical"
            elif resilience_score <= 70:
                status = "Warning"
            else:
                status = "Secure"

            calculated_assets.append({
                "id": asset.id,
                "property_name": asset.property_name,
                "location": asset.location,
                "asset_value": asset.asset_value,
                "primary_hazard": asset.primary_hazard,
                "value_at_risk": round(value_at_risk, 2),
                "resilience_score": round(resilience_score, 2),
                "status": status,
            })

        total_portfolio_value = sum(a.asset_value for a in req.assets)
        total_value_at_risk = sum(a["value_at_risk"] for a in calculated_assets)
        average_resilience_score = sum(a["resilience_score"] for a in calculated_assets) / len(calculated_assets)

        var_by_hazard: Dict[str, float] = {}
        for asset in calculated_assets:
            hazard = asset["primary_hazard"]
            var_by_hazard[hazard] = var_by_hazard.get(hazard, 0.0) + asset["value_at_risk"]

        sorted_assets = sorted(calculated_assets, key=lambda x: x["value_at_risk"], reverse=True)
        top_at_risk_assets = sorted_assets[:5]

        return {
            "summary": {
                "total_portfolio_value": round(total_portfolio_value, 2),
                "total_value_at_risk": round(total_value_at_risk, 2),
                "average_resilience_score": round(average_resilience_score, 2),
            },
            "visualizations": {
                "var_by_hazard": {k: round(v, 2) for k, v in var_by_hazard.items()},
                "top_at_risk_assets": top_at_risk_assets,
            },
            "ledger": calculated_assets,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio analysis failed: {str(e)}") from e
