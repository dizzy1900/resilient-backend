"""
Test script for the /predict-flood endpoint
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_flood_prediction():
    """Test the flood prediction endpoint with different interventions."""
    
    print("=" * 60)
    print("Testing /predict-flood Endpoint")
    print("=" * 60)
    
    # Test Case 1: Green Roof intervention
    print("\n1. Testing Green Roof Intervention:")
    print("-" * 40)
    
    payload1 = {
        "rain_intensity": 100.0,
        "current_imperviousness": 0.7,
        "intervention_type": "green_roof",
        "slope_pct": 2.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict-flood", json=payload1)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nResponse:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Case 2: Permeable Pavement intervention
    print("\n\n2. Testing Permeable Pavement Intervention:")
    print("-" * 40)
    
    payload2 = {
        "rain_intensity": 80.0,
        "current_imperviousness": 0.8,
        "intervention_type": "permeable_pavement",
        "slope_pct": 3.0
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict-flood", json=payload2)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nBaseline Depth: {data['data']['depth_baseline']} cm")
            print(f"Intervention Depth: {data['data']['depth_intervention']} cm")
            print(f"Avoided Depth: {data['data']['analysis']['avoided_depth_cm']} cm")
            print(f"Avoided Loss: ${data['data']['avoided_loss']:,.2f}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Case 3: No intervention
    print("\n\n3. Testing No Intervention:")
    print("-" * 40)
    
    payload3 = {
        "rain_intensity": 50.0,
        "current_imperviousness": 0.5,
        "intervention_type": "none"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict-flood", json=payload3)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nBaseline Depth: {data['data']['depth_baseline']} cm")
            print(f"Intervention Depth: {data['data']['depth_intervention']} cm")
            print(f"Avoided Depth: {data['data']['analysis']['avoided_depth_cm']} cm")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Case 4: Error handling - invalid intervention
    print("\n\n4. Testing Error Handling (Invalid Intervention):")
    print("-" * 40)
    
    payload4 = {
        "rain_intensity": 100.0,
        "current_imperviousness": 0.7,
        "intervention_type": "invalid_type"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict-flood", json=payload4)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Testing Complete")
    print("=" * 60)


if __name__ == "__main__":
    test_flood_prediction()
