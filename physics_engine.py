# =============================================================================
# MULTI-CROP YIELD MODEL - Physics Engine
# Process-based modeling of heat and drought stress
# Supports: Maize, Cocoa
# =============================================================================

# ============= MAIZE PARAMETERS =============
# Critical temperature threshold (°C)
MAIZE_CRITICAL_TEMP_C = 28.0  # Lowered to make heat stress more common

# Heat loss rates (% yield loss per degree above threshold)
MAIZE_HEAT_LOSS_RATE_OPTIMAL = 2.5    # Increased from 1.0
MAIZE_HEAT_LOSS_RATE_DROUGHT = 4.0    # Increased from 1.7

# Rainfall thresholds (mm)
MAIZE_MIN_RAINFALL_MM = 300.0
MAIZE_OPTIMAL_RAINFALL_MIN_MM = 500.0
MAIZE_OPTIMAL_RAINFALL_MAX_MM = 1300.0  # Widened optimal range for high-rainfall regions

# Resilience delta for climate-smart varieties
MAIZE_RESILIENCE_DELTA_C = 3.0  # Increased from 2.0 - better heat tolerance
MAIZE_RESILIENCE_DROUGHT_FACTOR = 0.7  # Resilient seeds lose only 70% as much under drought

# ============= COCOA PARAMETERS =============
# Cocoa is more sensitive to drought than maize but handles humidity better
COCOA_OPTIMAL_RAIN_MM = 1750.0
COCOA_MIN_RAIN_MM = 1200.0
COCOA_OPTIMAL_TEMP_C = 25.0
COCOA_HEAT_LIMIT_C = 33.0

# Cocoa loss rates
COCOA_RAIN_PENALTY_PER_100MM = 10.0  # Steep penalty: 10% per 100mm below minimum
COCOA_HEAT_PENALTY_PER_DEGREE = 5.0  # 5% per degree above heat limit

# Cocoa resilience factors
COCOA_RESILIENCE_DROUGHT_FACTOR = 0.6  # Resilient varieties lose only 60% as much under drought
COCOA_RESILIENCE_HEAT_FACTOR = 0.7  # Resilient varieties lose only 70% as much under heat stress


def calculate_cocoa_yield(temp: float, rain: float, seed_type: int, temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """
    Calculate cocoa yield based on temperature, rainfall, and seed type.
    
    Cocoa is more sensitive to drought than maize but handles humidity better.
    
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
    simulated_temp = temp + temp_delta
    simulated_rain = max(0.0, rain * (1 + (rain_pct_change / 100)))
    
    # Rain Penalty: Cocoa is very sensitive to drought
    if simulated_rain < COCOA_MIN_RAIN_MM:
        # Steep penalty for rainfall below minimum
        rain_deficit_mm = COCOA_MIN_RAIN_MM - simulated_rain
        rain_penalty = (rain_deficit_mm / 100.0) * COCOA_RAIN_PENALTY_PER_100MM
        
        # Resilient varieties handle drought better
        if seed_type == 1:
            rain_penalty *= COCOA_RESILIENCE_DROUGHT_FACTOR
        
        yield_pct -= rain_penalty
    elif simulated_rain < COCOA_OPTIMAL_RAIN_MM:
        # Sub-optimal rainfall: gentle linear reduction
        rain_factor = simulated_rain / COCOA_OPTIMAL_RAIN_MM
        rain_penalty = (1.0 - rain_factor) * 20.0  # Max 20% penalty at minimum rain
        
        # Resilient varieties handle sub-optimal rain better
        if seed_type == 1:
            rain_penalty *= COCOA_RESILIENCE_DROUGHT_FACTOR
        
        yield_pct -= rain_penalty
    # Cocoa handles excess rainfall well (no waterlogging penalty like maize)
    
    # Heat Penalty: Temperature above heat limit
    if simulated_temp > COCOA_HEAT_LIMIT_C:
        excess_temp = simulated_temp - COCOA_HEAT_LIMIT_C
        heat_penalty = excess_temp * COCOA_HEAT_PENALTY_PER_DEGREE
        
        # Resilient varieties tolerate heat better
        if seed_type == 1:
            heat_penalty *= COCOA_RESILIENCE_HEAT_FACTOR
        
        yield_pct -= heat_penalty
    
    # Clamp yield between 0 and 100
    return max(0.0, min(100.0, yield_pct))


def calculate_maize_yield(temp: float, rain: float, seed_type: int, temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
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
    simulated_temp = temp + temp_delta
    simulated_rain = max(0.0, rain * (1 + (rain_pct_change / 100)))
    
    # Adjust critical temperature for resilient varieties
    effective_critical_temp = MAIZE_CRITICAL_TEMP_C
    if seed_type == 1:
        effective_critical_temp += MAIZE_RESILIENCE_DELTA_C
    
    # Determine if drought conditions exist
    is_drought = simulated_rain < MAIZE_OPTIMAL_RAINFALL_MIN_MM
    
    # Apply heat stress loss if temperature exceeds threshold
    if simulated_temp > effective_critical_temp:
        excess_temp = simulated_temp - effective_critical_temp
        loss_rate = MAIZE_HEAT_LOSS_RATE_DROUGHT if is_drought else MAIZE_HEAT_LOSS_RATE_OPTIMAL
        heat_loss = excess_temp * loss_rate
        yield_pct -= heat_loss
    
    # Apply rainfall-based yield adjustment
    if simulated_rain < MAIZE_MIN_RAINFALL_MM:
        # Below minimum: severe yield reduction
        rain_factor = simulated_rain / MAIZE_MIN_RAINFALL_MM
        base_yield = rain_factor * 0.5  # Max 50% yield at minimum threshold
        
        # Resilient seeds perform better under severe drought
        if seed_type == 1:
            base_yield = min(base_yield * 1.3, 0.7)  # 30% better, capped at 70%
        
        yield_pct *= base_yield
    elif simulated_rain < MAIZE_OPTIMAL_RAINFALL_MIN_MM:
        # Sub-optimal: linear reduction
        rain_factor = 0.5 + 0.5 * (simulated_rain - MAIZE_MIN_RAINFALL_MM) / (MAIZE_OPTIMAL_RAINFALL_MIN_MM - MAIZE_MIN_RAINFALL_MM)
        
        # Resilient seeds handle drought stress better
        if seed_type == 1:
            drought_penalty = 1.0 - rain_factor
            rain_factor = 1.0 - (drought_penalty * MAIZE_RESILIENCE_DROUGHT_FACTOR)
        
        yield_pct *= rain_factor
    elif simulated_rain > MAIZE_OPTIMAL_RAINFALL_MAX_MM:
        # Excess rainfall: waterlogging reduces yield
        # Gentler penalty: 5% loss per 100mm excess
        excess_rain = simulated_rain - MAIZE_OPTIMAL_RAINFALL_MAX_MM
        waterlog_loss = (excess_rain / 100.0) * 5.0  # 5% per 100mm
        
        # Resilient seeds tolerate waterlogging better
        if seed_type == 1:
            waterlog_loss *= 0.6  # 40% less waterlogging damage
        
        yield_pct -= waterlog_loss
    
    # Clamp yield between 0 and 100
    return max(0.0, min(100.0, yield_pct))


def calculate_yield(temp: float, rain: float, seed_type: int, crop_type: str = 'maize', temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """
    Calculate crop yield based on temperature, rainfall, seed type, and crop type.
    
    This is the main entry point for yield calculations. Routes to specific crop functions.
    
    Args:
        temp: Temperature in °C
        rain: Rainfall in mm
        seed_type: 0 = Standard, 1 = Resilient (climate-smart)
        crop_type: 'maize' or 'cocoa' (default: 'maize')
        temp_delta: Temperature increase for climate scenario (°C), default 0.0
        rain_pct_change: Percentage change in rainfall (e.g., 8 for +8%, -10 for -10%), default 0.0
    
    Returns:
        Yield as percentage (0-100) of maximum potential yield
    """
    crop_type_lower = crop_type.lower()
    
    if crop_type_lower == 'maize':
        return calculate_maize_yield(temp, rain, seed_type, temp_delta, rain_pct_change)
    elif crop_type_lower == 'cocoa':
        return calculate_cocoa_yield(temp, rain, seed_type, temp_delta, rain_pct_change)
    else:
        raise ValueError(f"Unsupported crop_type: {crop_type}. Supported crops: 'maize', 'cocoa'")


# Legacy function for backwards compatibility
def simulate_maize_yield(temp: float, rain: float, seed_type: int, temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """
    Legacy function for backwards compatibility.
    Redirects to calculate_yield with crop_type='maize'.
    """
    return calculate_yield(temp, rain, seed_type, 'maize', temp_delta, rain_pct_change)


def calculate_volatility(yield_history_list: list) -> float:
    """
    Calculate yield volatility using Coefficient of Variation (CV).
    
    CV measures the relative variability of yields over time.
    Higher CV = more volatile/risky production.
    
    Args:
        yield_history_list: List of annual yields (e.g., [85, 40, 90, 20, ...])
    
    Returns:
        Coefficient of Variation as percentage (float)
        
    Example:
        >>> yields = [85, 40, 90, 20, 75]
        >>> cv = calculate_volatility(yields)
        >>> print(f"CV: {cv:.1f}%")
        CV: 38.7%
    """
    import statistics
    
    if not yield_history_list or len(yield_history_list) < 2:
        return 0.0
    
    # Calculate mean
    mean_yield = statistics.mean(yield_history_list)
    
    # Avoid division by zero
    if mean_yield == 0:
        return 0.0
    
    # Calculate standard deviation
    std_dev = statistics.stdev(yield_history_list)
    
    # Calculate Coefficient of Variation as percentage
    cv = (std_dev / mean_yield) * 100
    
    return round(cv, 2)
