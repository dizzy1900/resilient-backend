"""
Comprehensive troubleshooting for flood endpoint frontend integration
Tests CORS, response format, headers, and compares with working endpoints
"""

import requests
import json
from datetime import datetime

API_BASE = "https://web-production-8ff9e.up.railway.app"

def print_header(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_cors_and_headers(endpoint_path, method="POST", payload=None):
    """Test CORS headers and response details."""
    
    print(f"\n📍 Testing: {endpoint_path}")
    print(f"   Method: {method}")
    
    url = f"{API_BASE}{endpoint_path}"
    
    # Simulate browser preflight OPTIONS request
    print("\n1️⃣  Testing CORS Preflight (OPTIONS):")
    try:
        preflight_headers = {
            'Access-Control-Request-Method': method,
            'Access-Control-Request-Headers': 'content-type',
            'Origin': 'https://lovable.dev'  # Typical Lovable origin
        }
        
        options_response = requests.options(url, headers=preflight_headers, timeout=10)
        print(f"   Status Code: {options_response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin', 'NOT SET'),
            'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods', 'NOT SET'),
            'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers', 'NOT SET'),
            'Access-Control-Allow-Credentials': options_response.headers.get('Access-Control-Allow-Credentials', 'NOT SET')
        }
        
        for header, value in cors_headers.items():
            status = "✅" if value != 'NOT SET' else "❌"
            print(f"   {status} {header}: {value}")
            
    except Exception as e:
        print(f"   ❌ Preflight failed: {e}")
    
    # Test actual request
    if method == "POST" and payload:
        print(f"\n2️⃣  Testing Actual {method} Request:")
        try:
            request_headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://lovable.dev'
            }
            
            response = requests.post(url, json=payload, headers=request_headers, timeout=30)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Time: {response.elapsed.total_seconds():.2f}s")
            
            # Check CORS headers in response
            cors_origin = response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
            print(f"   CORS Allow-Origin: {cors_origin}")
            
            if cors_origin == 'NOT SET':
                print("   ❌ CRITICAL: No CORS headers in response!")
                print("   → Frontend will be blocked by browser CORS policy")
            elif cors_origin == '*':
                print("   ✅ CORS allows all origins")
            else:
                print(f"   ⚠️  CORS restricted to: {cors_origin}")
            
            # Check response content
            print(f"\n3️⃣  Response Content:")
            content_type = response.headers.get('Content-Type', 'NOT SET')
            print(f"   Content-Type: {content_type}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   JSON Valid: ✅")
                    print(f"   Response Keys: {list(data.keys())}")
                    
                    if 'data' in data and 'analysis' in data.get('data', {}):
                        avoided_loss = data['data']['analysis'].get('avoided_loss', 'NOT FOUND')
                        print(f"   data.analysis.avoided_loss: {avoided_loss}")
                        
                        if avoided_loss != 'NOT FOUND':
                            print(f"   ✅ Field structure correct!")
                        else:
                            print(f"   ❌ Missing avoided_loss field!")
                    else:
                        print(f"   ❌ Incorrect response structure!")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Invalid JSON response")
                    print(f"   Raw: {response.text[:200]}")
            else:
                print(f"   ❌ Error Response:")
                print(f"   {response.text[:500]}")
                
            return response
            
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            return None


def compare_endpoints():
    """Compare flood endpoint with working coastal endpoint."""
    
    print_header("ENDPOINT COMPARISON TEST")
    
    # Test coastal endpoint (known working)
    print("\n🌊 COASTAL ENDPOINT (Working Baseline):")
    coastal_payload = {
        "lat": 25.7617,
        "lon": -80.1918,
        "mangrove_width": 50
    }
    coastal_response = test_cors_and_headers('/predict-coastal', 'POST', coastal_payload)
    
    # Test flood endpoint (troubleshooting)
    print("\n\n🌊 FLOOD ENDPOINT (Troubleshooting):")
    flood_payload = {
        "rain_intensity": 100.0,
        "current_imperviousness": 0.7,
        "intervention_type": "green_roof",
        "slope_pct": 2.0
    }
    flood_response = test_cors_and_headers('/predict-flood', 'POST', flood_payload)
    
    # Compare
    print_header("COMPARISON SUMMARY")
    
    if coastal_response and flood_response:
        print("\n✅ Both endpoints responded")
        
        # Compare CORS headers
        coastal_cors = coastal_response.headers.get('Access-Control-Allow-Origin', 'NONE')
        flood_cors = flood_response.headers.get('Access-Control-Allow-Origin', 'NONE')
        
        print(f"\nCORS Headers:")
        print(f"  Coastal: {coastal_cors}")
        print(f"  Flood:   {flood_cors}")
        
        if coastal_cors != flood_cors:
            print("  ⚠️  CORS headers differ!")
        else:
            print("  ✅ CORS headers match")
        
        # Compare status codes
        print(f"\nStatus Codes:")
        print(f"  Coastal: {coastal_response.status_code}")
        print(f"  Flood:   {flood_response.status_code}")
        
        if coastal_response.status_code == flood_response.status_code == 200:
            print("  ✅ Both return 200 OK")
        else:
            print("  ❌ Status codes differ!")
            
    else:
        print("\n❌ One or both endpoints failed to respond")


def test_from_browser_perspective():
    """Simulate exactly how a browser would call the API."""
    
    print_header("BROWSER SIMULATION TEST")
    
    print("\nSimulating browser fetch() call from Lovable frontend:")
    print("Origin: https://lovable.dev")
    
    # Exact headers a browser would send
    browser_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': 'https://lovable.dev',
        'Referer': 'https://lovable.dev/',
        'User-Agent': 'Mozilla/5.0 (Lovable Frontend)'
    }
    
    flood_payload = {
        "rain_intensity": 100.0,
        "current_imperviousness": 0.7,
        "intervention_type": "green_roof"
    }
    
    print(f"\nRequest Headers:")
    for key, value in browser_headers.items():
        print(f"  {key}: {value}")
    
    print(f"\nRequest Body:")
    print(f"  {json.dumps(flood_payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_BASE}/predict-flood",
            json=flood_payload,
            headers=browser_headers,
            timeout=30
        )
        
        print(f"\n✅ Response Received:")
        print(f"  Status: {response.status_code}")
        print(f"  Time: {response.elapsed.total_seconds():.2f}s")
        
        # Check critical CORS header
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        print(f"\n🔍 Critical Check - CORS Header:")
        if cors_header:
            print(f"  ✅ Access-Control-Allow-Origin: {cors_header}")
            print(f"  → Browser will ALLOW this response")
        else:
            print(f"  ❌ Access-Control-Allow-Origin: NOT SET")
            print(f"  → Browser will BLOCK this response")
            print(f"  → This is the problem!")
        
        # Show all response headers
        print(f"\n📋 All Response Headers:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
        
        # Show response body
        if response.status_code == 200:
            print(f"\n📦 Response Body (first 500 chars):")
            print(f"  {response.text[:500]}")
        else:
            print(f"\n❌ Error Response:")
            print(f"  {response.text}")
            
    except Exception as e:
        print(f"\n❌ Request Failed: {e}")


def check_endpoint_availability():
    """Check if all endpoints are accessible."""
    
    print_header("ENDPOINT AVAILABILITY CHECK")
    
    endpoints = [
        ('Health', 'GET', '/health', None),
        ('Agricultural', 'POST', '/predict', {'temp': 30, 'rain': 450}),
        ('Coastal', 'POST', '/predict-coastal', {'lat': 25.76, 'lon': -80.19, 'mangrove_width': 50}),
        ('Flood', 'POST', '/predict-flood', {'rain_intensity': 100, 'current_imperviousness': 0.7, 'intervention_type': 'green_roof'})
    ]
    
    results = []
    
    for name, method, path, payload in endpoints:
        print(f"\n{name:15s} {method:6s} {path:20s} ... ", end='')
        
        try:
            if method == 'GET':
                response = requests.get(f"{API_BASE}{path}", timeout=10)
            else:
                response = requests.post(f"{API_BASE}{path}", json=payload, timeout=30)
            
            status = "✅ OK" if response.status_code == 200 else f"❌ {response.status_code}"
            print(status)
            
            results.append({
                'name': name,
                'status': response.status_code,
                'success': response.status_code == 200
            })
            
        except Exception as e:
            print(f"❌ FAILED: {str(e)[:50]}")
            results.append({
                'name': name,
                'status': 'ERROR',
                'success': False
            })
    
    # Summary
    print(f"\n📊 Summary:")
    working = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"  Working: {working}/{total}")
    
    if working < total:
        print(f"\n⚠️  Not all endpoints are working!")
        for r in results:
            if not r['success']:
                print(f"    ❌ {r['name']}: {r['status']}")


def test_error_cases():
    """Test error handling."""
    
    print_header("ERROR HANDLING TEST")
    
    test_cases = [
        {
            'name': 'Missing required field',
            'payload': {'rain_intensity': 100}
        },
        {
            'name': 'Invalid intervention type',
            'payload': {
                'rain_intensity': 100,
                'current_imperviousness': 0.7,
                'intervention_type': 'invalid_type'
            }
        },
        {
            'name': 'Out of range rain',
            'payload': {
                'rain_intensity': 200,
                'current_imperviousness': 0.7,
                'intervention_type': 'green_roof'
            }
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 Test: {test['name']}")
        print(f"   Payload: {json.dumps(test['payload'])}")
        
        try:
            response = requests.post(
                f"{API_BASE}/predict-flood",
                json=test['payload'],
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 400:
                print(f"   ✅ Correctly returns 400 for invalid input")
                data = response.json()
                if 'message' in data:
                    print(f"   Message: {data['message']}")
            else:
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")


def main():
    """Run all troubleshooting tests."""
    
    print("=" * 80)
    print(" FLOOD ENDPOINT FRONTEND INTEGRATION TROUBLESHOOTING")
    print(f" Testing: {API_BASE}")
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run tests
    check_endpoint_availability()
    compare_endpoints()
    test_from_browser_perspective()
    test_error_cases()
    
    # Final recommendations
    print_header("TROUBLESHOOTING RECOMMENDATIONS")
    
    print("""
If CORS headers are missing:
  1. Check that Flask-CORS is in requirements.txt
  2. Verify CORS(app) is called in main.py
  3. Redeploy to Railway

If endpoint returns 404:
  1. Verify /predict-flood route is in main.py
  2. Check Railway deployment logs
  3. Confirm latest code is deployed

If endpoint returns 500:
  1. Check Railway logs for errors
  2. Verify flood_surrogate.pkl exists
  3. Check model training logs

If response structure is wrong:
  1. Compare with /predict-coastal response
  2. Verify data.analysis.avoided_loss exists
  3. Check main.py endpoint code

For frontend testing:
  1. Open browser DevTools → Network tab
  2. Trigger flood prediction in UI
  3. Look for OPTIONS and POST requests
  4. Check if CORS error appears in console
  5. Inspect actual request/response
    """)


if __name__ == "__main__":
    main()
