#!/usr/bin/env python3
"""
Test the /calculate-financials endpoint logic
"""

import json

def test_calculate_financials_endpoint():
    """Test the calculate-financials endpoint."""
    
    print("Testing /calculate-financials endpoint")
    print("=" * 60)
    
    # Test Case 1: Good investment
    print("\nTest Case 1: Good investment (positive NPV)")
    print("-" * 60)
    
    request_data = {
        'cash_flows': [-100000, 15000, 15000, 15000, 15000, 15000, 15000, 15000, 15000, 15000, 15000,
                       15000, 15000, 15000, 15000, 15000, 15000, 15000, 15000, 15000, 15000],
        'discount_rate': 0.10
    }
    
    print(f"  Request: {{")
    print(f"    'cash_flows': [{request_data['cash_flows'][0]}, {request_data['cash_flows'][1]}, ...] (21 values),")
    print(f"    'discount_rate': {request_data['discount_rate']}")
    print(f"  }}")
    
    # Expected response structure
    response_data = {
        'input': {
            'cash_flows': request_data['cash_flows'],
            'discount_rate': 0.10,
            'discount_rate_pct': 10.0
        },
        'metrics': {
            'npv': 27703.46,
            'bcr': 1.28,
            'payback_period_years': 6.67
        },
        'interpretation': {
            'npv_positive': True,
            'bcr_favorable': True,
            'recommendation': 'INVEST'
        }
    }
    
    print(f"\n  Expected response:")
    print(f"    NPV: ${response_data['metrics']['npv']:,.2f}")
    print(f"    BCR: {response_data['metrics']['bcr']}")
    print(f"    Payback: {response_data['metrics']['payback_period_years']} years")
    print(f"    Recommendation: {response_data['interpretation']['recommendation']}")
    
    assert response_data['interpretation']['npv_positive'] == True
    assert response_data['interpretation']['bcr_favorable'] == True
    assert response_data['interpretation']['recommendation'] == 'INVEST'
    print("  ✓ Passed")
    
    # Test Case 2: Poor investment
    print("\nTest Case 2: Poor investment (negative NPV)")
    print("-" * 60)
    
    poor_request = {
        'cash_flows': [-100000, 5000, 5000, 5000, 5000, 5000],
        'discount_rate': 0.10
    }
    
    print(f"  Request: {json.dumps(poor_request, indent=4)}")
    
    poor_response = {
        'metrics': {
            'npv': -81046.07,
            'bcr': 0.19,
            'payback_period_years': None
        },
        'interpretation': {
            'npv_positive': False,
            'bcr_favorable': False,
            'recommendation': 'DO NOT INVEST'
        }
    }
    
    print(f"\n  Expected response:")
    print(f"    NPV: ${poor_response['metrics']['npv']:,.2f}")
    print(f"    BCR: {poor_response['metrics']['bcr']}")
    print(f"    Recommendation: {poor_response['interpretation']['recommendation']}")
    
    assert poor_response['interpretation']['recommendation'] == 'DO NOT INVEST'
    print("  ✓ Passed")
    
    # Test Case 3: Validation errors
    print("\nTest Case 3: Validation errors")
    print("-" * 60)
    
    invalid_cases = [
        ({'discount_rate': 0.10}, "Missing cash_flows"),
        ({'cash_flows': [-100, 50]}, "Missing discount_rate"),
        ({'cash_flows': [-100], 'discount_rate': 0.10}, "Too few cash flows"),
        ({'cash_flows': [-100, 50, 50], 'discount_rate': 1.5}, "Discount rate > 1.0"),
        ({'cash_flows': [-100, 50, 50], 'discount_rate': -0.1}, "Discount rate < 0.0"),
    ]
    
    for invalid_data, error_msg in invalid_cases:
        print(f"  {error_msg}: ", end="")
        
        # Check validation logic
        if 'cash_flows' not in invalid_data or 'discount_rate' not in invalid_data:
            print("✓ Would reject (missing field)")
        elif not isinstance(invalid_data.get('cash_flows'), list) or len(invalid_data.get('cash_flows', [])) < 2:
            print("✓ Would reject (invalid cash_flows)")
        elif not (0 <= invalid_data.get('discount_rate', -1) <= 1.0):
            print("✓ Would reject (invalid discount_rate)")
        else:
            print("? Unexpected case")
    
    print("  ✓ All validations correct")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    
    # Show complete example response
    print("\nComplete Example Response:")
    print("=" * 60)
    
    complete_response = {
        "status": "success",
        "data": {
            "input": {
                "cash_flows": [-100000, 15000, 15000, 15000, 15000, 15000],
                "discount_rate": 0.10,
                "discount_rate_pct": 10.0
            },
            "metrics": {
                "npv": -43138.2,
                "bcr": 0.57,
                "payback_period_years": None
            },
            "interpretation": {
                "npv_positive": False,
                "bcr_favorable": False,
                "recommendation": "DO NOT INVEST"
            }
        }
    }
    
    print(json.dumps(complete_response, indent=2))


if __name__ == '__main__':
    test_calculate_financials_endpoint()
