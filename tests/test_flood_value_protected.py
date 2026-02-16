"""
Test script to verify Value Protected changes with interventions
"""
import requests
import json

BASE_URL = "http://localhost:5001"

def test_flood_scenarios():
    """Test flood predictions with different interventions."""
    
    # Test scenario: High rain, high imperviousness
    test_params = {
        "rain_intensity": 100.0,  # High rain (100 mm/hr)
        "current_imperviousness": 0.75,  # 75% impervious
        "slope_pct": 2.0,
        "building_value": 750000,
        "num_buildings": 1
    }
    
    print("=" * 70)
    print("FLOOD VALUE PROTECTED TEST")
    print("=" * 70)
    print(f"\nTest Parameters:")
    print(f"  Rain Intensity: {test_params['rain_intensity']} mm/hr")
    print(f"  Current Imperviousness: {test_params['current_imperviousness'] * 100}%")
    print(f"  Slope: {test_params['slope_pct']}%")
    print(f"  Building Value: ${test_params['building_value']:,}")
    print(f"  Number of Buildings: {test_params['num_buildings']}")
    print("\n" + "=" * 70)
    
    interventions = ['none', 'green_roof', 'permeable_pavement']
    results = {}
    
    for intervention in interventions:
        payload = {**test_params, "intervention_type": intervention}
        
        try:
            response = requests.post(
                f"{BASE_URL}/predict-flood",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()['data']
                results[intervention] = data
                
                print(f"\n{intervention.upper().replace('_', ' ')}")
                print("-" * 70)
                print(f"  Imperviousness Change:")
                print(f"    Baseline: {data['imperviousness_change']['baseline']}")
                print(f"    After Intervention: {data['imperviousness_change']['intervention']}")
                print(f"    Reduction: {data['imperviousness_change']['absolute_reduction']}")
                print(f"\n  Flood Depth Predictions:")
                print(f"    Baseline: {data['predictions']['baseline_depth_cm']:.2f} cm")
                print(f"    With Intervention: {data['predictions']['intervention_depth_cm']:.2f} cm")
                print(f"    Avoided Depth: {data['analysis']['avoided_depth_cm']:.2f} cm")
                print(f"\n  Damage Assessment:")
                print(f"    Baseline Damage: {data['analysis']['baseline_damage_pct']:.2f}%")
                print(f"    Intervention Damage: {data['analysis']['intervention_damage_pct']:.2f}%")
                print(f"    Avoided Damage: {data['analysis']['avoided_damage_pct']:.2f}%")
                print(f"\n  💰 VALUE PROTECTED: ${data['analysis']['avoided_loss']:,.2f}")
                print(f"  📊 Improvement: {data['analysis']['percentage_improvement']:.2f}%")
            else:
                print(f"\n{intervention}: ERROR - {response.status_code}")
                print(response.text)
        
        except Exception as e:
            print(f"\n{intervention}: ERROR - {str(e)}")
    
    # Summary comparison
    print("\n" + "=" * 70)
    print("SUMMARY COMPARISON")
    print("=" * 70)
    print(f"{'Intervention':<25} {'Depth (cm)':<15} {'Damage %':<15} {'Value Protected':<20}")
    print("-" * 70)
    
    for intervention in interventions:
        if intervention in results:
            data = results[intervention]
            depth = data['predictions']['baseline_depth_cm']
            damage = data['analysis']['baseline_damage_pct']
            value = data['analysis']['avoided_loss']
            print(f"{intervention.replace('_', ' ').title():<25} {depth:>8.2f} cm     {damage:>6.2f}%         ${value:>12,.2f}")
    
    print("=" * 70)
    
    # Check if values are changing
    if len(results) == 3:
        none_value = results['none']['analysis']['avoided_loss']
        green_value = results['green_roof']['analysis']['avoided_loss']
        perm_value = results['permeable_pavement']['analysis']['avoided_loss']
        
        print("\n✅ SUCCESS CRITERIA:")
        print(f"  ✓ None intervention should have $0 protected: ${none_value:,.2f}")
        print(f"  ✓ Green Roof should protect more than $0: ${green_value:,.2f}")
        print(f"  ✓ Permeable Pavement should protect more than Green Roof: ${perm_value:,.2f}")
        
        if none_value == 0 and green_value > 0 and perm_value > green_value:
            print("\n🎉 ALL TESTS PASSED! Value Protected is changing correctly.")
        else:
            print("\n⚠️  WARNING: Value Protected may not be changing as expected.")

if __name__ == "__main__":
    test_flood_scenarios()
