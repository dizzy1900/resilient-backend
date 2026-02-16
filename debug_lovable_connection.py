"""
Debug why Lovable frontend cannot reach flood simulation API
"""

import requests
import json
from datetime import datetime

API_BASE = "https://web-production-8ff9e.up.railway.app"

print("=" * 80)
print("LOVABLE FRONTEND CONNECTION DEBUG")
print(f"Testing: {API_BASE}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# Test 1: Check if server is responding at all
print("\n1. Server Availability Test")
print("-" * 80)
try:
    response = requests.get(f"{API_BASE}/health", timeout=10)
    print(f"✅ Server is UP - Status: {response.status_code}")
    print(f"   Response: {response.json()}")
except Exception as e:
    print(f"❌ Server is DOWN - Error: {e}")
    print("   → This means Railway deployment failed or server is offline")
    exit(1)

# Test 2: Test OPTIONS request (CORS preflight)
print("\n2. CORS Preflight (OPTIONS) Test")
print("-" * 80)
print("   Simulating browser preflight request...")

try:
    options_response = requests.options(
        f"{API_BASE}/predict-flood",
        headers={
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type',
            'Origin': 'https://lovable.dev'
        },
        timeout=10
    )
    
    print(f"   Status: {options_response.status_code}")
    
    cors_headers = {
        'Access-Control-Allow-Origin': options_response.headers.get('Access-Control-Allow-Origin'),
        'Access-Control-Allow-Methods': options_response.headers.get('Access-Control-Allow-Methods'),
        'Access-Control-Allow-Headers': options_response.headers.get('Access-Control-Allow-Headers')
    }
    
    print(f"   CORS Headers:")
    for header, value in cors_headers.items():
        status = "✅" if value else "❌"
        print(f"   {status} {header}: {value}")
        
    if not cors_headers['Access-Control-Allow-Origin']:
        print("\n   ❌ CRITICAL: CORS headers missing!")
        print("   → Browser will block all requests")
    else:
        print("\n   ✅ CORS preflight working")
        
except Exception as e:
    print(f"   ❌ Preflight failed: {e}")

# Test 3: Test actual POST request
print("\n3. POST Request Test")
print("-" * 80)

test_payload = {
    "rain_intensity": 100.0,
    "current_imperviousness": 0.7,
    "intervention_type": "green_roof",
    "slope_pct": 2.0
}

print(f"   Payload: {json.dumps(test_payload)}")

try:
    response = requests.post(
        f"{API_BASE}/predict-flood",
        json=test_payload,
        headers={
            'Content-Type': 'application/json',
            'Origin': 'https://lovable.dev',
            'User-Agent': 'Lovable-Frontend-Test'
        },
        timeout=30
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Request successful")
        
        # Check response
        data = response.json()
        
        # Verify structure
        if 'data' in data and 'analysis' in data['data']:
            avoided_loss = data['data']['analysis'].get('avoided_loss')
            print(f"   ✅ Response structure correct")
            print(f"   💰 avoided_loss: ${avoided_loss:,.2f}")
            
            if avoided_loss and avoided_loss > 0:
                print(f"   ✅ Real value returned (not $0)")
            else:
                print(f"   ❌ Value is $0 or missing")
        else:
            print(f"   ❌ Response structure incorrect")
            print(f"   Response: {json.dumps(data, indent=2)[:500]}")
            
    elif response.status_code == 404:
        print("   ❌ Endpoint not found")
        print("   → /predict-flood route might not be deployed")
        
    elif response.status_code == 500:
        print("   ❌ Server error")
        print(f"   Response: {response.text[:500]}")
        
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("   ❌ Request timed out")
    print("   → Server might be slow or unresponsive")
    
except Exception as e:
    print(f"   ❌ Request failed: {e}")

# Test 4: Test with minimal payload
print("\n4. Minimal Payload Test")
print("-" * 80)
print("   Testing without optional slope_pct...")

minimal_payload = {
    "rain_intensity": 100.0,
    "current_imperviousness": 0.7,
    "intervention_type": "green_roof"
}

try:
    response = requests.post(
        f"{API_BASE}/predict-flood",
        json=minimal_payload,
        headers={'Content-Type': 'application/json'},
        timeout=30
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Minimal payload works")
    else:
        print(f"   ❌ Failed with status {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Check what Lovable might be sending
print("\n5. Common Lovable Issues")
print("-" * 80)

issues_to_check = [
    {
        'name': 'Wrong URL',
        'test': lambda: requests.post("https://adaptmetric-backend.railway.app/predict-flood", 
                                     json=test_payload, timeout=5),
        'expected_fail': True
    },
    {
        'name': 'Missing Content-Type',
        'test': lambda: requests.post(f"{API_BASE}/predict-flood", 
                                     data=json.dumps(test_payload), timeout=5),
        'expected_fail': True
    },
    {
        'name': 'Wrong field name',
        'test': lambda: requests.post(f"{API_BASE}/predict-flood",
                                     json={'rainfall': 100, 'imperviousness': 0.7, 'intervention': 'green_roof'},
                                     headers={'Content-Type': 'application/json'},
                                     timeout=5),
        'expected_fail': True
    }
]

for issue in issues_to_check:
    try:
        response = issue['test']()
        if issue['expected_fail']:
            print(f"   ⚠️  {issue['name']}: Status {response.status_code}")
            if response.status_code != 200:
                print(f"      → This might be what Lovable is doing!")
        else:
            print(f"   ✅ {issue['name']}: OK")
    except Exception as e:
        if issue['expected_fail']:
            print(f"   ❌ {issue['name']}: Failed as expected")
        else:
            print(f"   ❌ {issue['name']}: {str(e)[:50]}")

# Test 6: Test from different origins
print("\n6. Origin Test")
print("-" * 80)

test_origins = [
    'https://lovable.dev',
    'https://lovable.app', 
    'http://localhost:5173',
    'https://your-app.lovable.app'
]

for origin in test_origins:
    try:
        response = requests.post(
            f"{API_BASE}/predict-flood",
            json=test_payload,
            headers={
                'Content-Type': 'application/json',
                'Origin': origin
            },
            timeout=10
        )
        
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        if cors_header:
            print(f"   ✅ {origin}: CORS allowed")
        else:
            print(f"   ❌ {origin}: CORS blocked")
            
    except Exception as e:
        print(f"   ❌ {origin}: {str(e)[:30]}")

# Summary
print("\n" + "=" * 80)
print("DIAGNOSTIC SUMMARY")
print("=" * 80)

print("""
If all tests passed above:
  → Backend API is working correctly
  → Issue is in Lovable frontend code

If tests failed:
  → Note which test failed
  → Share the error messages

Next steps for you:
  1. Run this Python script yourself to see results
  2. Share any test that shows ❌ FAILED
  3. Check Lovable frontend code for:
     - Correct API URL
     - Correct field names in payload
     - Proper headers (Content-Type: application/json)

Common Lovable issues:
  - API URL hardcoded to localhost
  - Environment variable not set
  - Field names don't match backend
  - Not handling async/promises correctly
  - Displaying cached/dummy data instead of API response
""")
