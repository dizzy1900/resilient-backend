# =============================================================================
# MAIZE YIELD LOSS MODEL - Physics Engine
# Process-based modeling of heat and drought stress
# =============================================================================

# Critical temperature threshold (°C)
CRITICAL_TEMP_C = 30.0

# Heat loss rates (% yield loss per degree above threshold)
HEAT_LOSS_RATE_OPTIMAL = 1.0    # Under optimal rainfed conditions
HEAT_LOSS_RATE_DROUGHT = 1.7   # Under drought conditions

# Rainfall thresholds (mm)
MIN_RAINFALL_MM = 300.0
OPTIMAL_RAINFALL_MIN_MM = 500.0
OPTIMAL_RAINFALL_MAX_MM = 800.0

# Resilience delta for climate-smart varieties (°C)
RESILIENCE_DELTA_C = 2.0


def simulate_maize_yield(temp: float, rain: float, seed_type: int) -> float:
    """
    Calculate maize yield based on temperature, rainfall, and seed type.
    
    Args:
        temp: Temperature in °C
        rain: Rainfall in mm
        seed_type: 0 = Standard, 1 = Resilient (climate-smart)
    
    Returns:
        Yield as percentage (0-100) of maximum potential yield
    """
    # Start with 100% potential yield
    yield_pct = 100.0
    
    # Adjust critical temperature for resilient varieties
    effective_critical_temp = CRITICAL_TEMP_C
    if seed_type == 1:
        effective_critical_temp += RESILIENCE_DELTA_C
    
    # Determine if drought conditions exist
    is_drought = rain < OPTIMAL_RAINFALL_MIN_MM
    
    # Apply heat stress loss if temperature exceeds threshold
    if temp > effective_critical_temp:
        excess_temp = temp - effective_critical_temp
        loss_rate = HEAT_LOSS_RATE_DROUGHT if is_drought else HEAT_LOSS_RATE_OPTIMAL
        heat_loss = excess_temp * loss_rate
        yield_pct -= heat_loss
    
    # Apply rainfall-based yield adjustment
    if rain < MIN_RAINFALL_MM:
        # Below minimum: severe yield reduction
        rain_factor = rain / MIN_RAINFALL_MM
        yield_pct *= rain_factor * 0.5  # Max 50% yield at minimum threshold
    elif rain < OPTIMAL_RAINFALL_MIN_MM:
        # Sub-optimal: linear reduction
        rain_factor = 0.5 + 0.5 * (rain - MIN_RAINFALL_MM) / (OPTIMAL_RAINFALL_MIN_MM - MIN_RAINFALL_MM)
        yield_pct *= rain_factor
    elif rain > OPTIMAL_RAINFALL_MAX_MM:
        # Excess rainfall: waterlogging reduces yield
        excess_rain = rain - OPTIMAL_RAINFALL_MAX_MM
        waterlog_loss = min(excess_rain / 1000.0 * 20.0, 30.0)  # Max 30% loss
        yield_pct -= waterlog_loss
    
    # Clamp yield between 0 and 100
    return max(0.0, min(100.0, yield_pct))
