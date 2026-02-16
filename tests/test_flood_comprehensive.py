"""
Comprehensive production test for all flood intervention types
"""

import requests
import json

API_BASE = "https://web-production-8ff9e.up.railway.app"

def test_intervention(intervention_type, rain, imperviousness, slope=2.0):
    """Test a specific intervention type."""
    
    payload = {
        "rain_intensity": rain,
        "current_imperviousness": imperviousness,
        "intervention_type": intervention_type,
        "slope_pct": slope
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/predict-flood",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            avoided_loss = data['data']['analysis']['avoided_loss']
            avoided_depth = data['data']['analysis']['avoided_depth_cm']
            improvement = data['data']['analysis']['percentage_improvement']
            
            return {
                'success': True,
                'avoided_loss': avoided_loss,
                'avoided_depth': avoided_depth,
                'improvement': improvement
            }
        else:
            return {
                'success': False,
                'error': f"Status {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


print("=" * 80)
print("COMPREHENSIVE FLOOD ENDPOINT TEST")
print("=" * 80)
print(f"\nTesting: {API_BASE}/predict-flood\n")

test_cases = [
    {
        'name': 'Green Roof (30% reduction)',
        'intervention': 'green_roof',
        'rain': 100.0,
        'imperviousness': 0.7,
        'expected_range': (35000, 50000)
    },
    {
        'name': 'Permeable Pavement (40% reduction)',
        'intervention': 'permeable_pavement',
        'rain': 80.0,
        'imperviousness': 0.8,
        'expected_range': (40000, 60000)
    },
    {
        'name': 'Bioswales (25% reduction)',
        'intervention': 'bioswales',
        'rain': 90.0,
        'imperviousness': 0.65,
        'expected_range': (30000, 45000)
    },
    {
        'name': 'Rain Gardens (20% reduction)',
        'intervention': 'rain_gardens',
        'rain': 120.0,
        'imperviousness': 0.6,
        'expected_range': (25000, 45000)
    },
    {
        'name': 'No Intervention (0% reduction)',
        'intervention': 'none',
        'rain': 50.0,
        'imperviousness': 0.5,
        'expected_range': (0, 100)
    }
]

results = []
all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. Testing: {test['name']}")
    print("-" * 80)
    print(f"   Rain: {test['rain']} mm/hr")
    print(f"   Imperviousness: {test['imperviousness'] * 100:.0f}%")
    print(f"   Intervention: {test['intervention']}")
    
    result = test_intervention(
        test['intervention'],
        test['rain'],
        test['imperviousness']
    )
    
    if result['success']:
        avoided_loss = result['avoided_loss']
        avoided_depth = result['avoided_depth']
        improvement = result['improvement']
        
        print(f"\n   ✅ SUCCESS")
        print(f"   Avoided Loss: ${avoided_loss:,.2f}")
        print(f"   Avoided Depth: {avoided_depth:.2f} cm")
        print(f"   Improvement: {improvement:.1f}%")
        
        # Check if in expected range
        min_expected, max_expected = test['expected_range']
        if min_expected <= avoided_loss <= max_expected:
            print(f"   ✅ Within expected range: ${min_expected:,} - ${max_expected:,}")
        else:
            print(f"   ⚠️  Outside expected range: ${min_expected:,} - ${max_expected:,}")
            all_passed = False
        
        results.append({
            'test': test['name'],
            'status': 'PASS',
            'value': f"${avoided_loss:,.2f}"
        })
    else:
        print(f"\n   ❌ FAILED: {result['error']}")
        all_passed = False
        results.append({
            'test': test['name'],
            'status': 'FAIL',
            'value': result['error']
        })

print("\n\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

for result in results:
    status_icon = "✅" if result['status'] == 'PASS' else "❌"
    print(f"{status_icon} {result['test']:45s} {result['value']}")

print("\n" + "=" * 80)
if all_passed:
    print("🎉 ALL TESTS PASSED - Frontend integration ready!")
else:
    print("⚠️  Some tests failed - Check errors above")
print("=" * 80)
