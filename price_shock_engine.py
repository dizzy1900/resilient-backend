# =============================================================================
# Commodity Price Shock Engine
# =============================================================================
"""
Commodity Price Shock Engine for Climate-Induced Supply Disruptions

When climate stress reduces local crop yields, this engine calculates the
resulting spike in local commodity prices based on price elasticity of supply.

Theory:
- Price Elasticity of Supply: ε = (% change in quantity supplied) / (% change in price)
- When supply drops, prices rise according to: % price change = (% supply change) / ε
- For agricultural commodities, supply is typically inelastic in the short term
  (farmers can't quickly increase production), so price shocks can be severe.

References:
- Roberts, M. J., & Schlenker, W. (2013). "Identifying Supply and Demand Elasticities
  of Agricultural Commodities." American Economic Review.
- FAO (2023). "Price Volatility in Food and Agricultural Markets."
"""

from typing import Dict, Tuple


# =============================================================================
# BASELINE COMMODITY PRICES (USD per metric ton)
# =============================================================================
# Source: World Bank Commodity Price Data, USDA Agricultural Projections 2024-2033
# Note: These are global benchmark prices. Local prices may vary ±20-30%.

BASELINE_PRICES: Dict[str, float] = {
    # Grains
    "maize": 180.0,      # US No. 2 Yellow, FOB Gulf ports
    "corn": 180.0,       # Alias for maize
    "wheat": 220.0,      # US HRW, FOB Gulf ports
    "rice": 450.0,       # Thai 5% broken, FOB Bangkok
    
    # Oilseeds
    "soybeans": 450.0,   # US No. 1 Yellow, FOB Gulf ports
    "soy": 450.0,        # Alias for soybeans
    "canola": 500.0,     # Canadian No. 1, FOB Vancouver
    "rapeseed": 500.0,   # Alias for canola
    "sunflower": 420.0,  # FOB Black Sea ports
    
    # Cash Crops
    "cocoa": 2500.0,     # ICCO daily price, FOB West Africa
    "coffee": 3500.0,    # Arabica, ICO composite price
    "cotton": 1800.0,    # A Index, Middling 1-3/32"
    "sugar": 400.0,      # ISA daily price, FOB Caribbean
    
    # Pulses
    "chickpeas": 800.0,  # Kabuli, FOB Mediterranean
    "lentils": 600.0,    # Red, FOB Canada
    "beans": 700.0,      # Pinto, FOB US ports
    
    # Other
    "barley": 200.0,     # Feed grade, FOB Australia
    "sorghum": 170.0,    # US No. 2, FOB Gulf ports
    "millet": 300.0,     # Pearl, FOB India
    "cassava": 250.0,    # Chips, FOB Thailand
    "potato": 350.0,     # Fresh, wholesale Europe
    "tomato": 600.0,     # Processing grade, FOB California
}


# =============================================================================
# PRICE ELASTICITY OF SUPPLY (dimensionless)
# =============================================================================
# Elasticity = (% change in quantity) / (% change in price)
# Inverse gives price impact: % price change = (% supply change) / elasticity
#
# For agricultural commodities, short-run elasticity is typically 0.1 - 0.5
# (inelastic), meaning a 10% drop in supply causes a 20-100% price increase.
#
# Long-run elasticity is higher (0.5 - 1.5) as farmers adjust planting decisions.
#
# References:
# - Roberts & Schlenker (2013): Estimated elasticities for major grains
# - USDA ERS: Agricultural Supply Response database

SUPPLY_ELASTICITY: Dict[str, float] = {
    # Grains (highly inelastic in short run)
    "maize": 0.25,       # 1% supply drop → 4% price increase
    "corn": 0.25,
    "wheat": 0.30,       # 1% supply drop → 3.3% price increase
    "rice": 0.20,        # 1% supply drop → 5% price increase (most inelastic)
    
    # Oilseeds (moderately inelastic)
    "soybeans": 0.35,    # 1% supply drop → 2.9% price increase
    "soy": 0.35,
    "canola": 0.40,
    "rapeseed": 0.40,
    "sunflower": 0.38,
    
    # Cash Crops (inelastic due to limited substitutes)
    "cocoa": 0.15,       # 1% supply drop → 6.7% price increase (highly inelastic)
    "coffee": 0.18,      # 1% supply drop → 5.6% price increase
    "cotton": 0.45,
    "sugar": 0.35,
    
    # Pulses (moderately elastic)
    "chickpeas": 0.50,
    "lentils": 0.55,
    "beans": 0.48,
    
    # Other (variable)
    "barley": 0.28,
    "sorghum": 0.30,
    "millet": 0.35,
    "cassava": 0.40,
    "potato": 0.60,      # More elastic due to local markets
    "tomato": 0.65,      # More elastic due to perishability
}


# =============================================================================
# CORE CALCULATION FUNCTIONS
# =============================================================================

def calculate_price_shock(
    crop_type: str,
    baseline_yield_tons: float,
    stressed_yield_tons: float
) -> Dict[str, any]:
    """
    Calculate commodity price shock from climate-induced yield loss.
    
    Args:
        crop_type: Crop identifier (e.g., "maize", "soybeans", "wheat")
        baseline_yield_tons: Expected yield under normal conditions (metric tons)
        stressed_yield_tons: Actual/projected yield under climate stress (metric tons)
    
    Returns:
        Dictionary containing:
        - baseline_price: Original commodity price (USD/ton)
        - shocked_price: New price after supply shock (USD/ton)
        - price_increase_pct: Percentage increase in price
        - price_increase_usd: Absolute increase in price (USD/ton)
        - yield_loss_pct: Percentage drop in yield
        - yield_loss_tons: Absolute drop in yield (tons)
        - elasticity: Supply elasticity used
        - forward_contract_recommendation: Risk management advice
        - revenue_impact: Net revenue change despite higher prices
    
    Raises:
        ValueError: If crop_type is not recognized or yields are invalid
    """
    # Normalize crop type (lowercase, strip whitespace)
    crop_type_normalized = crop_type.lower().strip()
    
    # Validate crop type
    if crop_type_normalized not in BASELINE_PRICES:
        available_crops = ", ".join(sorted(BASELINE_PRICES.keys()))
        raise ValueError(
            f"Crop type '{crop_type}' not recognized. "
            f"Available crops: {available_crops}"
        )
    
    # Validate yields
    if baseline_yield_tons <= 0:
        raise ValueError(f"Baseline yield must be positive, got {baseline_yield_tons}")
    
    if stressed_yield_tons < 0:
        raise ValueError(f"Stressed yield cannot be negative, got {stressed_yield_tons}")
    
    # Get baseline price and elasticity
    baseline_price = BASELINE_PRICES[crop_type_normalized]
    elasticity = SUPPLY_ELASTICITY[crop_type_normalized]
    
    # Calculate yield loss
    yield_loss_tons = baseline_yield_tons - stressed_yield_tons
    yield_loss_pct = (yield_loss_tons / baseline_yield_tons) * 100.0
    
    # Calculate price shock using inverse elasticity
    # Formula: % price change = (% supply change) / elasticity
    # Since supply drops, price rises (positive price change)
    price_increase_pct = (yield_loss_pct / elasticity)
    
    # Calculate shocked price
    shocked_price = baseline_price * (1 + price_increase_pct / 100.0)
    price_increase_usd = shocked_price - baseline_price
    
    # Calculate revenue impact
    # Revenue = Yield × Price
    baseline_revenue = baseline_yield_tons * baseline_price
    stressed_revenue = stressed_yield_tons * shocked_price
    revenue_impact_usd = stressed_revenue - baseline_revenue
    revenue_impact_pct = (revenue_impact_usd / baseline_revenue) * 100.0
    
    # Generate forward contract recommendation
    forward_contract_recommendation = _generate_recommendation(
        yield_loss_pct=yield_loss_pct,
        price_increase_pct=price_increase_pct,
        revenue_impact_pct=revenue_impact_pct
    )
    
    return {
        "baseline_price": round(baseline_price, 2),
        "shocked_price": round(shocked_price, 2),
        "price_increase_pct": round(price_increase_pct, 2),
        "price_increase_usd": round(price_increase_usd, 2),
        "yield_loss_pct": round(yield_loss_pct, 2),
        "yield_loss_tons": round(yield_loss_tons, 2),
        "elasticity": elasticity,
        "forward_contract_recommendation": forward_contract_recommendation,
        "revenue_impact": {
            "baseline_revenue_usd": round(baseline_revenue, 2),
            "stressed_revenue_usd": round(stressed_revenue, 2),
            "net_revenue_change_usd": round(revenue_impact_usd, 2),
            "net_revenue_change_pct": round(revenue_impact_pct, 2),
        },
    }


def _generate_recommendation(
    yield_loss_pct: float,
    price_increase_pct: float,
    revenue_impact_pct: float
) -> str:
    """
    Generate forward contract recommendation based on risk metrics.
    
    Args:
        yield_loss_pct: Percentage drop in yield
        price_increase_pct: Percentage increase in price
        revenue_impact_pct: Net revenue change percentage
    
    Returns:
        Human-readable recommendation string
    """
    # Severe yield loss (>30%) → Lock in NOW
    if yield_loss_pct > 30:
        return (
            "🚨 URGENT: Lock in forward contracts immediately. "
            f"Projected {yield_loss_pct:.1f}% yield loss will cause severe price volatility. "
            "Consider hedging 70-80% of expected production at current prices."
        )
    
    # High yield loss (15-30%) → Lock in soon
    elif yield_loss_pct > 15:
        return (
            "⚠️ HIGH RISK: Consider forward contracts now. "
            f"Projected {yield_loss_pct:.1f}% yield loss will drive prices {price_increase_pct:.1f}% higher. "
            "Hedge 50-60% of expected production to protect against further volatility."
        )
    
    # Moderate yield loss (5-15%) → Monitor closely
    elif yield_loss_pct > 5:
        return (
            "⚡ MODERATE RISK: Monitor markets closely. "
            f"Projected {yield_loss_pct:.1f}% yield loss may push prices {price_increase_pct:.1f}% higher. "
            "Consider hedging 30-40% of production if prices continue rising."
        )
    
    # Low yield loss (<5%) → No action needed
    else:
        return (
            "✅ LOW RISK: No immediate hedging needed. "
            f"Projected {yield_loss_pct:.1f}% yield loss will have minimal price impact. "
            "Continue monitoring weather forecasts and market conditions."
        )


def get_crop_info(crop_type: str) -> Dict[str, any]:
    """
    Get baseline price and elasticity information for a crop.
    
    Utility function for displaying crop parameters to users.
    
    Args:
        crop_type: Crop identifier (e.g., "maize", "soybeans", "wheat")
    
    Returns:
        Dictionary with baseline_price and elasticity
    
    Raises:
        ValueError: If crop_type is not recognized
    """
    crop_type_normalized = crop_type.lower().strip()
    
    if crop_type_normalized not in BASELINE_PRICES:
        available_crops = ", ".join(sorted(BASELINE_PRICES.keys()))
        raise ValueError(
            f"Crop type '{crop_type}' not recognized. "
            f"Available crops: {available_crops}"
        )
    
    return {
        "crop_type": crop_type_normalized,
        "baseline_price_usd_per_ton": BASELINE_PRICES[crop_type_normalized],
        "supply_elasticity": SUPPLY_ELASTICITY[crop_type_normalized],
        "elasticity_interpretation": (
            f"A 1% supply drop causes a {1.0/SUPPLY_ELASTICITY[crop_type_normalized]:.1f}% price increase"
        ),
    }


def get_all_crops() -> Dict[str, Dict[str, any]]:
    """
    Get information for all supported crops.
    
    Returns:
        Dictionary mapping crop names to their price/elasticity info
    """
    return {
        crop: get_crop_info(crop)
        for crop in sorted(BASELINE_PRICES.keys())
    }
