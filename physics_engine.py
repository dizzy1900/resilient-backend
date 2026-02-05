# =============================================================================
# MAIZE YIELD LOSS MODEL - Physics Engine
# Process-based modeling of heat and drought stress
# =============================================================================

# Critical temperature threshold (°C)
CRITICAL_TEMP_C = 28.0  # Lowered to make heat stress more common

# Heat loss rates (% yield loss per degree above threshold)
HEAT_LOSS_RATE_OPTIMAL = 2.5    # Increased from 1.0
HEAT_LOSS_RATE_DROUGHT = 4.0    # Increased from 1.7

# Rainfall thresholds (mm)
MIN_RAINFALL_MM = 300.0
OPTIMAL_RAINFALL_MIN_MM = 500.0
OPTIMAL_RAINFALL_MAX_MM = 900.0  # Increased from 800.0

# Resilience delta for climate-smart varieties
RESILIENCE_DELTA_C = 3.0  # Increased from 2.0 - better heat tolerance
RESILIENCE_DROUGHT_FACTOR = 0.7  # Resilient seeds lose only 70% as much under drought


def simulate_maize_yield(temp: float, rain: float, seed_type: int, temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """
    Calculate maize yield based on temperature, rainfall, and seed type.
    
    Args:
        temp: Temperature in °C
        rain: Rainfall in mm
        seed_type: 0 = Standard, 1 = Resilient (climate-smart)
        temp_delta: Temperature increase for climate scenario (°C), default 0.0
        rain_pct_change: Percentage change in rainfall (e.g., 8 for +8%, -10 for -10%), default 0.0
    
    Returns:
        Yield as percentage (0-100) of maximum potential yield
    """
    # Start with 100% potential yield
    yield_pct = 100.0
    
    # Apply climate perturbation using Delta Method
    # Temperature: additive (T_new = T_obs + delta)
    simulated_temp = temp + temp_delta
    
    # Rainfall: scaling factor (R_new = R_obs * (1 + pct_change/100))
    simulated_rain = rain * (1 + (rain_pct_change / 100))
    
    # Ensure rainfall never drops below 0
    simulated_rain = max(0.0, simulated_rain)
    
    # Adjust critical temperature for resilient varieties
    effective_critical_temp = CRITICAL_TEMP_C
    if seed_type == 1:
        effective_critical_temp += RESILIENCE_DELTA_C
    
    # Determine if drought conditions exist
    is_drought = simulated_rain < OPTIMAL_RAINFALL_MIN_MM
    
    # Apply heat stress loss if temperature exceeds threshold
    if simulated_temp > effective_critical_temp:
        excess_temp = simulated_temp - effective_critical_temp
        loss_rate = HEAT_LOSS_RATE_DROUGHT if is_drought else HEAT_LOSS_RATE_OPTIMAL
        heat_loss = excess_temp * loss_rate
        yield_pct -= heat_loss
    
    # Apply rainfall-based yield adjustment
    if simulated_rain < MIN_RAINFALL_MM:
        # Below minimum: severe yield reduction
        rain_factor = simulated_rain / MIN_RAINFALL_MM
        base_yield = rain_factor * 0.5  # Max 50% yield at minimum threshold
        
        # Resilient seeds perform better under severe drought
        if seed_type == 1:
            base_yield = min(base_yield * 1.3, 0.7)  # 30% better, capped at 70%
        
        yield_pct *= base_yield
    elif simulated_rain < OPTIMAL_RAINFALL_MIN_MM:
        # Sub-optimal: linear reduction
        rain_factor = 0.5 + 0.5 * (simulated_rain - MIN_RAINFALL_MM) / (OPTIMAL_RAINFALL_MIN_MM - MIN_RAINFALL_MM)
        
        # Resilient seeds handle drought stress better
        if seed_type == 1:
            drought_penalty = 1.0 - rain_factor
            rain_factor = 1.0 - (drought_penalty * RESILIENCE_DROUGHT_FACTOR)
        
        yield_pct *= rain_factor
    elif simulated_rain > OPTIMAL_RAINFALL_MAX_MM:
        # Excess rainfall: waterlogging reduces yield
        # Gentler penalty: 5% loss per 100mm excess
        excess_rain = simulated_rain - OPTIMAL_RAINFALL_MAX_MM
        waterlog_loss = (excess_rain / 100.0) * 5.0  # 5% per 100mm
        
        # Resilient seeds tolerate waterlogging better
        if seed_type == 1:
            waterlog_loss *= 0.6  # 40% less waterlogging damage
        
        yield_pct -= waterlog_loss
    
    # Clamp yield between 0 and 100
    return max(0.0, min(100.0, yield_pct))
