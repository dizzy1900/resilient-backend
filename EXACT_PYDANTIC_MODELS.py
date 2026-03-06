"""
EXACT PYDANTIC MODELS - Extracted from api.py
==============================================
These are the EXACT Pydantic models used by the backend.
Use these for TypeScript interface generation.

Generated: 2026-03-04
Source: /Users/david/resilient-backend/api.py
"""

from pydantic import BaseModel, Field
from typing import Optional


# ============================================================================
# FINANCE ENDPOINTS
# ============================================================================

class CBARequest(BaseModel):
    """
    Request for Cost-Benefit Analysis time series.
    
    Endpoint: POST /api/v1/finance/cba-series
    Content-Type: application/json
    
    ⚠️ NO lat/lon REQUIRED - This is a purely financial endpoint
    """
    
    # CORE FINANCIAL PARAMETERS
    capex: float = Field(
        500000.0,
        description="Upfront capital expenditure in USD"
    )
    annual_opex: float = Field(
        25000.0,
        description="Annual operating expenditure in USD"
    )
    discount_rate: float = Field(
        0.08,
        description="Discount rate as decimal (e.g. 0.08 for 8%)"
    )
    lifespan_years: int = Field(
        30,
        ge=1,
        le=100,
        description="Project lifespan in years"
    )
    annual_baseline_damage: float = Field(
        100000.0,
        description="Annual cost of doing nothing in USD"
    )
    damage_reduction_pct: float = Field(
        0.80,
        ge=0.0,
        le=1.0,
        description="Fraction of damage the intervention prevents"
    )
    
    # PARAMETRIC INSURANCE
    base_insurance_premium: float = Field(
        50000.0,
        description="Annual insurance premium without intervention in USD"
    )
    insurance_reduction_pct: float = Field(
        0.25,
        ge=0.0,
        le=1.0,
        description="Premium reduction from intervention (e.g. 0.25 for 25%)"
    )
    
    # GREEN BOND FINANCING
    standard_interest_rate: float = Field(
        0.06,
        description="Standard bond interest rate as decimal (e.g. 0.06 for 6%)"
    )
    greenium_discount_bps: float = Field(
        50.0,
        description="Green bond discount in basis points (e.g. 50 = 0.50%)"
    )
    bond_tenor_years: int = Field(
        10,
        ge=1,
        le=50,
        description="Bond repayment period in years"
    )
    
    # CARBON CREDIT REVENUE (Layered Value Stacking)
    annual_carbon_credits: float = Field(
        0.0,
        description="Tons of CO2 sequestered per year"
    )
    carbon_price_per_ton: float = Field(
        50.0,
        description="Price per ton of CO2 in USD"
    )


class CVaRRequest(BaseModel):
    """
    Request for Climate Value at Risk Monte Carlo simulation.
    
    Endpoint: POST /api/v1/finance/cvar-simulation
    Content-Type: application/json
    """
    asset_value: float = Field(
        5_000_000.0,
        description="Total asset value in USD"
    )
    mean_damage_pct: float = Field(
        0.02,
        description="Average annual damage as decimal (e.g. 0.02 for 2%)"
    )
    volatility_pct: float = Field(
        0.05,
        description="Damage volatility as decimal (e.g. 0.05 for 5%)"
    )
    num_simulations: int = Field(
        10_000,
        ge=100,
        le=1_000_000,
        description="Number of Monte Carlo trials"
    )


# ============================================================================
# PORTFOLIO ENDPOINT
# ============================================================================

# NOTE: The /api/v1/analyze-portfolio endpoint does NOT use a Pydantic model.
# It accepts a raw CSV file upload (multipart/form-data) and parses dynamically.
#
# Expected CSV columns (case-insensitive):
#   - lat (required)
#   - lon (required)
#   - asset_value (required) - accepts aliases: val, price, amount, cost, invest, usd
#   - crop_type (required)
#   - scenario_year (optional, default: 2050)
#   - temp_delta (optional, default: 0.0)
#   - rain_pct_change (optional, default: 0.0)
#
# The backend applies aggressive column normalization:
#   1. Lowercase
#   2. Remove special characters (keep only letters, numbers, underscores)
#
# Example CSV:
#   lat,lon,asset_value,crop_type,scenario_year,temp_delta,rain_pct_change
#   34.0522,-118.2437,5000000,maize,2050,1.5,10.0
#   41.8781,-87.6298,3500000,wheat,2050,2.0,-5.0


# ============================================================================
# TYPESCRIPT INTERFACE GENERATION
# ============================================================================

"""
TypeScript interfaces corresponding to these Pydantic models:

// CBA Request
interface CBARequest {
  capex: number;
  annual_opex: number;
  discount_rate: number;
  lifespan_years: number;
  annual_baseline_damage: number;
  damage_reduction_pct: number;
  base_insurance_premium: number;
  insurance_reduction_pct: number;
  standard_interest_rate: number;
  greenium_discount_bps: number;
  bond_tenor_years: number;
  annual_carbon_credits: number;
  carbon_price_per_ton: number;
}

// CVaR Request
interface CVaRRequest {
  asset_value: number;
  mean_damage_pct: number;
  volatility_pct: number;
  num_simulations: number;
}

// Portfolio CSV Row (not a Pydantic model, but for reference)
interface PortfolioAsset {
  lat: number;
  lon: number;
  asset_value: number;
  crop_type: string;
  scenario_year?: number;
  temp_delta?: number;
  rain_pct_change?: number;
}
"""


# ============================================================================
# VALIDATION RULES
# ============================================================================

"""
CRITICAL VALIDATION RULES:

1. PERCENTAGES MUST BE DECIMALS:
   - 8% = 0.08
   - 25% = 0.25
   - 80% = 0.80
   
2. FIELD NAMES MUST BE SNAKE_CASE:
   - discount_rate (not discountRate)
   - lifespan_years (not lifespanYears)
   - annual_opex (not annualOpex)

3. PORTFOLIO ENDPOINT:
   - Accepts CSV file, not JSON
   - Column names are normalized (lowercase, no special chars)
   - Fuzzy matching for column names (e.g., "Asset Value" → "assetvalue")

4. FINANCE ENDPOINTS:
   - Accept JSON, not form data
   - NO lat/lon coordinates required
   - All fields have defaults (only send what you need to override)
"""


# ============================================================================
# EXAMPLE PAYLOADS
# ============================================================================

# Example 1: Minimal CBA request (using all defaults)
MINIMAL_CBA_PAYLOAD = {
    "capex": 500000.0,
    "annual_opex": 25000.0,
    "discount_rate": 0.08,
    "lifespan_years": 30,
    "annual_baseline_damage": 100000.0,
    "damage_reduction_pct": 0.80
}

# Example 2: Full CBA request (overriding all defaults)
FULL_CBA_PAYLOAD = {
    "capex": 750000.0,
    "annual_opex": 35000.0,
    "discount_rate": 0.10,
    "lifespan_years": 25,
    "annual_baseline_damage": 150000.0,
    "damage_reduction_pct": 0.85,
    "base_insurance_premium": 60000.0,
    "insurance_reduction_pct": 0.30,
    "standard_interest_rate": 0.07,
    "greenium_discount_bps": 75.0,
    "bond_tenor_years": 12,
    "annual_carbon_credits": 1000.0,
    "carbon_price_per_ton": 60.0
}

# Example 3: CVaR request
CVAR_PAYLOAD = {
    "asset_value": 10_000_000.0,
    "mean_damage_pct": 0.03,
    "volatility_pct": 0.08,
    "num_simulations": 50_000
}

# Example 4: Portfolio CSV content
PORTFOLIO_CSV = """lat,lon,asset_value,crop_type,scenario_year,temp_delta,rain_pct_change
34.0522,-118.2437,5000000,maize,2050,1.5,10.0
41.8781,-87.6298,3500000,wheat,2050,2.0,-5.0
40.7128,-74.0060,7200000,soy,2060,2.5,15.0"""


if __name__ == "__main__":
    # Test Pydantic validation
    import json
    
    print("=" * 80)
    print("TESTING PYDANTIC MODELS")
    print("=" * 80)
    
    # Test CBA minimal payload
    print("\n1. Testing CBARequest (minimal):")
    try:
        cba_minimal = CBARequest(**MINIMAL_CBA_PAYLOAD)
        print("✅ VALID")
        print(json.dumps(cba_minimal.model_dump(), indent=2))
    except Exception as e:
        print(f"❌ INVALID: {e}")
    
    # Test CBA full payload
    print("\n2. Testing CBARequest (full):")
    try:
        cba_full = CBARequest(**FULL_CBA_PAYLOAD)
        print("✅ VALID")
        print(json.dumps(cba_full.model_dump(), indent=2))
    except Exception as e:
        print(f"❌ INVALID: {e}")
    
    # Test CVaR payload
    print("\n3. Testing CVaRRequest:")
    try:
        cvar = CVaRRequest(**CVAR_PAYLOAD)
        print("✅ VALID")
        print(json.dumps(cvar.model_dump(), indent=2))
    except Exception as e:
        print(f"❌ INVALID: {e}")
    
    # Test INVALID payload (percentage as integer)
    print("\n4. Testing INVALID payload (percentage as integer):")
    try:
        invalid = CBARequest(
            capex=500000.0,
            annual_opex=25000.0,
            discount_rate=8,  # WRONG: Should be 0.08
            lifespan_years=30,
            annual_baseline_damage=100000.0,
            damage_reduction_pct=80  # WRONG: Should be 0.80
        )
        print("✅ VALID (but semantically wrong)")
        print(json.dumps(invalid.model_dump(), indent=2))
        print("⚠️ WARNING: Percentages are technically valid as floats,")
        print("   but semantically incorrect (8 means 800%, not 8%)")
    except Exception as e:
        print(f"❌ INVALID: {e}")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
