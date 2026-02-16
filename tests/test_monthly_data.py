#!/usr/bin/env python3
"""
Test script for get_monthly_data function
"""

from gee_connector import get_monthly_data

# Test with a sample location (e.g., Iowa, USA - good agricultural area)
lat = 42.0
lon = -93.5

print(f"Testing get_monthly_data for lat={lat}, lon={lon}")
print("-" * 60)

try:
    result = get_monthly_data(lat, lon)
    
    print("\nRainfall Monthly (mm):")
    print(f"  Length: {len(result['rainfall_monthly_mm'])}")
    print(f"  Values: {result['rainfall_monthly_mm']}")
    
    print("\nSoil Moisture Monthly:")
    print(f"  Length: {len(result['soil_moisture_monthly'])}")
    print(f"  Values: {result['soil_moisture_monthly']}")
    
    # Validate structure
    assert len(result['rainfall_monthly_mm']) == 12, "Rainfall should have 12 months"
    assert len(result['soil_moisture_monthly']) == 12, "Soil moisture should have 12 months"
    
    print("\n✓ Test passed! Function returns correct structure.")
    
except Exception as e:
    print(f"\n✗ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
