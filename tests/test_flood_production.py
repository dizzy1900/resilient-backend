"""
Test the flood prediction endpoint on production to diagnose frontend integration issues
"""

import requests
import json

# Production URL
API_BASE = "https://web-production-8ff9e.up.railway.app"

def test_flood_endpoint():
    """Test flood endpoint and show exact response structure."""
    
    print("=" * 70)
    print("FLOOD ENDPOINT PRODUCTION TEST")
    print("=" * 70)
    print(f"\nTesting: {API_BASE}/predict-flood\n")
    
    # Test Case: Green Roof intervention
    payload = {
        "rain_intensity": 100.0,
        "current_imperviousness": 0.7,
        "intervention_type": "green_roof",
        "slope_pct": 2.0
    }
    
    print("Request Payload:")
    print(json.dumps(payload, indent=2))
    print("\n" + "-" * 70 + "\n")
    
    try:
        response = requests.post(
            f"{API_BASE}/predict-flood",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}\n")
        
        if response.status_code == 200:
            data = response.json()
            
            print("FULL RESPONSE:")
            print(json.dumps(data, indent=2))
            print("\n" + "=" * 70)
            
            # Check field structure
            print("\nFIELD STRUCTURE ANALYSIS:")
            print("-" * 70)
            
            # Check if it matches agricultural/coastal pattern
            if 'data' in data:
                print("✅ Has 'data' field")
                
                if 'analysis' in data['data']:
                    print("✅ Has 'data.analysis' field")
                    
                    if 'avoided_loss' in data['data']['analysis']:
                        avoided_loss = data['data']['analysis']['avoided_loss']
                        print(f"✅ Has 'data.analysis.avoided_loss': ${avoided_loss:,.2f}")
                    else:
                        print("❌ MISSING 'data.analysis.avoided_loss'")
                        print(f"   Available fields in analysis: {list(data['data']['analysis'].keys())}")
                else:
                    print("❌ MISSING 'data.analysis' field")
                    print(f"   Available fields in data: {list(data['data'].keys())}")
                    
                # Check for flat fields (frontend compatibility)
                if 'avoided_loss' in data['data']:
                    print(f"✅ Has flat 'data.avoided_loss': ${data['data']['avoided_loss']:,.2f}")
                else:
                    print("❌ MISSING flat 'data.avoided_loss'")
                    
            else:
                print("❌ MISSING 'data' field")
                
            print("\n" + "=" * 70)
            print("\nFRONTEND SHOULD DISPLAY:")
            print("-" * 70)
            
            if 'data' in data and 'analysis' in data['data'] and 'avoided_loss' in data['data']['analysis']:
                print(f"Avoided Loss: ${data['data']['analysis']['avoided_loss']:,.2f}")
            elif 'data' in data and 'avoided_loss' in data['data']:
                print(f"Avoided Loss: ${data['data']['avoided_loss']:,.2f}")
            else:
                print("⚠️  Cannot find avoided_loss - Frontend will show $0 or error")
                
        elif response.status_code == 404:
            print("❌ ENDPOINT NOT FOUND")
            print("   The /predict-flood endpoint may not be deployed yet")
            print(f"   Check: {API_BASE}/health")
            
        elif response.status_code == 500:
            print("❌ SERVER ERROR")
            print(response.text)
            print("\n   Possible causes:")
            print("   - flood_surrogate.pkl not uploaded to production")
            print("   - Model loading failed")
            print("   - Dependencies missing")
            
        else:
            print(f"❌ UNEXPECTED STATUS: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR")
        print(f"   Cannot reach {API_BASE}")
        print("   Check if the production server is running")
        
    except requests.exceptions.Timeout:
        print("❌ REQUEST TIMEOUT")
        print("   Server took too long to respond")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        

def test_other_endpoints():
    """Test if other endpoints are working."""
    print("\n\n" + "=" * 70)
    print("TESTING OTHER ENDPOINTS (for comparison)")
    print("=" * 70)
    
    # Test health endpoint
    print("\n1. Testing /health:")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test agricultural endpoint
    print("\n2. Testing /predict (agricultural):")
    try:
        response = requests.post(
            f"{API_BASE}/predict",
            json={"temp": 30.0, "rain": 450.0},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'analysis' in data['data']:
                print(f"   avoided_loss: {data['data']['analysis']['avoided_loss']}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test coastal endpoint
    print("\n3. Testing /predict-coastal:")
    try:
        response = requests.post(
            f"{API_BASE}/predict-coastal",
            json={"lat": 25.76, "lon": -80.19, "mangrove_width": 50},
            timeout=10
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'analysis' in data['data']:
                print(f"   avoided_loss: ${data['data']['analysis']['avoided_loss']:,.2f}")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    test_flood_endpoint()
    test_other_endpoints()
    
    print("\n\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    print("""
If /predict-flood returns 404:
  → The endpoint is not deployed. Push code and redeploy.

If /predict-flood returns 500 with MODEL_NOT_FOUND:
  → Upload flood_surrogate.pkl to production server
  → Or run train_flood_surrogate.py on production

If /predict-flood returns 200 but frontend shows $0:
  → Check that response has 'data.analysis.avoided_loss' field
  → Verify field structure matches agricultural and coastal APIs
  → Frontend expects consistent field paths across all APIs
    """)
