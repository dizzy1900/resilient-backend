# =============================================================================
# MULTI-CROP YIELD MODEL - Physics Engine
# Process-based modeling of heat and drought stress
# Supports: Maize, Cocoa, Rice, Soy, Wheat
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

# ============= RICE PARAMETERS =============
# Rice is water-tolerant (very high rainfall optimum) but suffers under drought.
RICE_CRITICAL_TEMP_C = 32.0
RICE_HEAT_LOSS_RATE_OPTIMAL = 2.0
RICE_HEAT_LOSS_RATE_DROUGHT = 3.0
RICE_MIN_RAINFALL_MM = 800.0
RICE_OPTIMAL_RAINFALL_MIN_MM = 1200.0
RICE_OPTIMAL_RAINFALL_MAX_MM = 2500.0
RICE_RESILIENCE_DELTA_C = 2.0
RICE_RESILIENCE_DROUGHT_FACTOR = 0.75
RICE_WATERLOG_LOSS_PER_100MM = 1.0  # rice is relatively tolerant

# ============= SOY PARAMETERS =============
SOY_CRITICAL_TEMP_C = 30.0
SOY_HEAT_LOSS_RATE_OPTIMAL = 2.5
SOY_HEAT_LOSS_RATE_DROUGHT = 3.5
SOY_MIN_RAINFALL_MM = 400.0
SOY_OPTIMAL_RAINFALL_MIN_MM = 600.0
SOY_OPTIMAL_RAINFALL_MAX_MM = 1600.0
SOY_RESILIENCE_DELTA_C = 2.0
SOY_RESILIENCE_DROUGHT_FACTOR = 0.75
SOY_WATERLOG_LOSS_PER_100MM = 4.0

# ============= WHEAT PARAMETERS =============
# Wheat tends to be cooler-season; more sensitive to heat.
WHEAT_CRITICAL_TEMP_C = 26.0
WHEAT_HEAT_LOSS_RATE_OPTIMAL = 3.0
WHEAT_HEAT_LOSS_RATE_DROUGHT = 4.5
WHEAT_MIN_RAINFALL_MM = 250.0
WHEAT_OPTIMAL_RAINFALL_MIN_MM = 450.0
WHEAT_OPTIMAL_RAINFALL_MAX_MM = 1100.0
WHEAT_RESILIENCE_DELTA_C = 1.5
WHEAT_RESILIENCE_DROUGHT_FACTOR = 0.8
WHEAT_WATERLOG_LOSS_PER_100MM = 5.0

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


def _calculate_staple_crop_yield(
    *,
    temp: float,
    rain: float,
    seed_type: int,
    temp_delta: float,
    rain_pct_change: float,
    critical_temp_c: float,
    heat_loss_rate_optimal: float,
    heat_loss_rate_drought: float,
    min_rainfall_mm: float,
    optimal_rainfall_min_mm: float,
    optimal_rainfall_max_mm: float,
    resilience_delta_c: float,
    resilience_drought_factor: float,
    waterlog_loss_per_100mm: float,
    waterlog_resilience_multiplier: float = 0.6,
) -> float:
    """Generic yield model used for maize-like staple crops."""
    yield_pct = 100.0

    simulated_temp = temp + temp_delta
    simulated_rain = max(0.0, rain * (1 + (rain_pct_change / 100)))

    effective_critical_temp = critical_temp_c
    if seed_type == 1:
        effective_critical_temp += resilience_delta_c

    is_drought = simulated_rain < optimal_rainfall_min_mm

    if simulated_temp > effective_critical_temp:
        excess_temp = simulated_temp - effective_critical_temp
        loss_rate = heat_loss_rate_drought if is_drought else heat_loss_rate_optimal
        yield_pct -= excess_temp * loss_rate

    # Rainfall-based yield adjustments (piecewise)
    if simulated_rain < min_rainfall_mm:
        rain_factor = simulated_rain / min_rainfall_mm if min_rainfall_mm > 0 else 0.0
        base_yield = rain_factor * 0.5

        if seed_type == 1:
            base_yield = min(base_yield * 1.3, 0.7)

        yield_pct *= base_yield

    elif simulated_rain < optimal_rainfall_min_mm:
        denom = (optimal_rainfall_min_mm - min_rainfall_mm)
        rain_factor = 0.5 + 0.5 * (simulated_rain - min_rainfall_mm) / denom if denom != 0 else 0.5

        if seed_type == 1:
            drought_penalty = 1.0 - rain_factor
            rain_factor = 1.0 - (drought_penalty * resilience_drought_factor)

        yield_pct *= rain_factor

    elif simulated_rain > optimal_rainfall_max_mm:
        excess_rain = simulated_rain - optimal_rainfall_max_mm
        waterlog_loss = (excess_rain / 100.0) * waterlog_loss_per_100mm

        if seed_type == 1:
            waterlog_loss *= waterlog_resilience_multiplier

        yield_pct -= waterlog_loss

    return max(0.0, min(100.0, yield_pct))


def calculate_maize_yield(temp: float, rain: float, seed_type: int, temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """Calculate maize yield based on temperature, rainfall, and seed type."""
    return _calculate_staple_crop_yield(
        temp=temp,
        rain=rain,
        seed_type=seed_type,
        temp_delta=temp_delta,
        rain_pct_change=rain_pct_change,
        critical_temp_c=MAIZE_CRITICAL_TEMP_C,
        heat_loss_rate_optimal=MAIZE_HEAT_LOSS_RATE_OPTIMAL,
        heat_loss_rate_drought=MAIZE_HEAT_LOSS_RATE_DROUGHT,
        min_rainfall_mm=MAIZE_MIN_RAINFALL_MM,
        optimal_rainfall_min_mm=MAIZE_OPTIMAL_RAINFALL_MIN_MM,
        optimal_rainfall_max_mm=MAIZE_OPTIMAL_RAINFALL_MAX_MM,
        resilience_delta_c=MAIZE_RESILIENCE_DELTA_C,
        resilience_drought_factor=MAIZE_RESILIENCE_DROUGHT_FACTOR,
        waterlog_loss_per_100mm=5.0,
        waterlog_resilience_multiplier=0.6,
    )


def calculate_rice_yield(temp: float, rain: float, seed_type: int, temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """Calculate rice yield (simplified water-tolerant crop model)."""
    return _calculate_staple_crop_yield(
        temp=temp,
        rain=rain,
        seed_type=seed_type,
        temp_delta=temp_delta,
        rain_pct_change=rain_pct_change,
        critical_temp_c=RICE_CRITICAL_TEMP_C,
        heat_loss_rate_optimal=RICE_HEAT_LOSS_RATE_OPTIMAL,
        heat_loss_rate_drought=RICE_HEAT_LOSS_RATE_DROUGHT,
        min_rainfall_mm=RICE_MIN_RAINFALL_MM,
        optimal_rainfall_min_mm=RICE_OPTIMAL_RAINFALL_MIN_MM,
        optimal_rainfall_max_mm=RICE_OPTIMAL_RAINFALL_MAX_MM,
        resilience_delta_c=RICE_RESILIENCE_DELTA_C,
        resilience_drought_factor=RICE_RESILIENCE_DROUGHT_FACTOR,
        waterlog_loss_per_100mm=RICE_WATERLOG_LOSS_PER_100MM,
        waterlog_resilience_multiplier=0.8,
    )


def calculate_soy_yield(temp: float, rain: float, seed_type: int, temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """Calculate soy yield (simplified staple crop model)."""
    return _calculate_staple_crop_yield(
        temp=temp,
        rain=rain,
        seed_type=seed_type,
        temp_delta=temp_delta,
        rain_pct_change=rain_pct_change,
        critical_temp_c=SOY_CRITICAL_TEMP_C,
        heat_loss_rate_optimal=SOY_HEAT_LOSS_RATE_OPTIMAL,
        heat_loss_rate_drought=SOY_HEAT_LOSS_RATE_DROUGHT,
        min_rainfall_mm=SOY_MIN_RAINFALL_MM,
        optimal_rainfall_min_mm=SOY_OPTIMAL_RAINFALL_MIN_MM,
        optimal_rainfall_max_mm=SOY_OPTIMAL_RAINFALL_MAX_MM,
        resilience_delta_c=SOY_RESILIENCE_DELTA_C,
        resilience_drought_factor=SOY_RESILIENCE_DROUGHT_FACTOR,
        waterlog_loss_per_100mm=SOY_WATERLOG_LOSS_PER_100MM,
        waterlog_resilience_multiplier=0.6,
    )


def calculate_wheat_yield(temp: float, rain: float, seed_type: int, temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """Calculate wheat yield (simplified cool-season staple crop model)."""
    return _calculate_staple_crop_yield(
        temp=temp,
        rain=rain,
        seed_type=seed_type,
        temp_delta=temp_delta,
        rain_pct_change=rain_pct_change,
        critical_temp_c=WHEAT_CRITICAL_TEMP_C,
        heat_loss_rate_optimal=WHEAT_HEAT_LOSS_RATE_OPTIMAL,
        heat_loss_rate_drought=WHEAT_HEAT_LOSS_RATE_DROUGHT,
        min_rainfall_mm=WHEAT_MIN_RAINFALL_MM,
        optimal_rainfall_min_mm=WHEAT_OPTIMAL_RAINFALL_MIN_MM,
        optimal_rainfall_max_mm=WHEAT_OPTIMAL_RAINFALL_MAX_MM,
        resilience_delta_c=WHEAT_RESILIENCE_DELTA_C,
        resilience_drought_factor=WHEAT_RESILIENCE_DROUGHT_FACTOR,
        waterlog_loss_per_100mm=WHEAT_WATERLOG_LOSS_PER_100MM,
        waterlog_resilience_multiplier=0.6,
    )


def calculate_yield(temp: float, rain: float, seed_type: int, crop_type: str = 'maize', temp_delta: float = 0.0, rain_pct_change: float = 0.0) -> float:
    """Calculate crop yield based on temperature, rainfall, seed type, and crop type.

    This is the main entry point for yield calculations.

    Supported crop types:
    - maize
    - cocoa
    - rice
    - soy
    - wheat
    """
    crop_type_lower = crop_type.lower()

    if crop_type_lower == 'maize':
        return calculate_maize_yield(temp, rain, seed_type, temp_delta, rain_pct_change)
    if crop_type_lower == 'cocoa':
        return calculate_cocoa_yield(temp, rain, seed_type, temp_delta, rain_pct_change)
    if crop_type_lower == 'rice':
        return calculate_rice_yield(temp, rain, seed_type, temp_delta, rain_pct_change)
    if crop_type_lower == 'soy':
        return calculate_soy_yield(temp, rain, seed_type, temp_delta, rain_pct_change)
    if crop_type_lower == 'wheat':
        return calculate_wheat_yield(temp, rain, seed_type, temp_delta, rain_pct_change)

    raise ValueError(
        f"Unsupported crop_type: {crop_type}. Supported crops: 'maize', 'cocoa', 'rice', 'soy', 'wheat'"
    )


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
