"""
Test CORS fix is working for different origins
"""

import requests

API_URL = "https://web-production-8ff9e.up.railway.app/predict-flood"

def test_cors_with_origin(origin):
    """Test CORS with specific origin."""
    print(f"\nTesting with Origin: {origin}")
    print("-" * 60)
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': origin
    }
    
    payload = {
        'rain_intensity': 100,
        'current_imperviousness': 0.7,
        'intervention_type': 'green_roof'
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        
        print(f"Status: {response.status_code}")
        
        # Check CORS header
        cors_header = response.headers.get('Access-Control-Allow-Origin', 'NOT SET')
        print(f"Access-Control-Allow-Origin: {cors_header}")
        
        if cors_header == 'NOT SET':
            print("❌ CORS HEADER MISSING - Browser will block!")
            return False
        elif cors_header == '*':
            print("✅ CORS allows ALL origins")
            return True
        elif cors_header == origin:
            print(f"✅ CORS allows this origin")
            return True
        else:
            print(f"⚠️  CORS header doesn't match (expected {origin}, got {cors_header})")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


print("=" * 60)
print("CORS FIX VERIFICATION")
print("=" * 60)

# Test with different origins that Lovable might use
test_origins = [
    'https://lovable.dev',
    'https://preview-123.lovable.app',
    'http://localhost:3000',
    'https://www.example.com'
]

results = []
for origin in test_origins:
    result = test_cors_with_origin(origin)
    results.append((origin, result))

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

all_pass = all(r[1] for r in results)

for origin, passed in results:
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {origin}")

print("\n" + "=" * 60)
if all_pass:
    print("🎉 CORS FIX IS WORKING!")
    print("Frontend should now be able to read responses.")
else:
    print("⚠️  Some origins failed CORS check")
    print("Check Railway deployment status")
