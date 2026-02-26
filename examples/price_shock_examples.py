#!/usr/bin/env python3
"""
Example usage of the Commodity Price Shock Engine.

This script demonstrates various use cases for the price shock calculator.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from price_shock_engine import calculate_price_shock, get_crop_info, get_all_crops


def example_1_basic_drought():
    """Example 1: Basic drought scenario for maize farmer."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Maize Farmer Facing Drought")
    print("=" * 70)
    print("\nScenario: A maize farmer expects drought to reduce yield by 25%")
    print("Expected baseline yield: 500 tons")
    print("Expected stressed yield: 375 tons\n")
    
    result = calculate_price_shock(
        crop_type="maize",
        baseline_yield_tons=500.0,
        stressed_yield_tons=375.0
    )
    
    print(f"📊 PRICE ANALYSIS:")
    print(f"  Baseline Price: ${result['baseline_price']:.2f}/ton")
    print(f"  Shocked Price: ${result['shocked_price']:.2f}/ton")
    print(f"  Price Increase: {result['price_increase_pct']:.1f}%")
    print(f"  (+${result['price_increase_usd']:.2f}/ton)\n")
    
    print(f"📉 YIELD IMPACT:")
    print(f"  Yield Loss: {result['yield_loss_pct']:.1f}%")
    print(f"  Lost Production: {result['yield_loss_tons']:.0f} tons\n")
    
    print(f"💰 REVENUE ANALYSIS:")
    rev = result['revenue_impact']
    print(f"  Baseline Revenue: ${rev['baseline_revenue_usd']:,.2f}")
    print(f"  Stressed Revenue: ${rev['stressed_revenue_usd']:,.2f}")
    print(f"  Net Change: ${rev['net_revenue_change_usd']:,.2f} ({rev['net_revenue_change_pct']:.1f}%)\n")
    
    if rev['net_revenue_change_usd'] > 0:
        print("  ✅ Good news: Price spike compensates for yield loss!")
        print("     You'll actually earn MORE despite lower production.\n")
    else:
        print("  ⚠️  Warning: Revenue will decline despite price increase.\n")
    
    print(f"🎯 RECOMMENDATION:")
    print(f"  {result['forward_contract_recommendation']}\n")


def example_2_food_processor():
    """Example 2: Food processor assessing procurement costs."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Wheat Mill Procurement Planning")
    print("=" * 70)
    print("\nScenario: Regional wheat harvest expected down 15%")
    print("Annual wheat need: 10,000 tons")
    print("Need to assess price risk for procurement budget\n")
    
    result = calculate_price_shock(
        crop_type="wheat",
        baseline_yield_tons=100000.0,  # Regional production
        stressed_yield_tons=85000.0    # 15% loss
    )
    
    procurement_qty = 10000.0
    baseline_cost = procurement_qty * result['baseline_price']
    stressed_cost = procurement_qty * result['shocked_price']
    additional_cost = stressed_cost - baseline_cost
    
    print(f"📊 MARKET ANALYSIS:")
    print(f"  Regional Yield Loss: {result['yield_loss_pct']:.1f}%")
    print(f"  Expected Price Increase: {result['price_increase_pct']:.1f}%")
    print(f"  Baseline Price: ${result['baseline_price']:.2f}/ton")
    print(f"  Expected Price: ${result['shocked_price']:.2f}/ton\n")
    
    print(f"💸 BUDGET IMPACT:")
    print(f"  Baseline Procurement Cost: ${baseline_cost:,.2f}")
    print(f"  Stressed Procurement Cost: ${stressed_cost:,.2f}")
    print(f"  Additional Budget Needed: ${additional_cost:,.2f}\n")
    
    print(f"🎯 RECOMMENDATION:")
    print(f"  {result['forward_contract_recommendation']}\n")
    print(f"  💡 Strategy: Lock in prices now via forward contracts for")
    print(f"     50-60% of annual needs ({procurement_qty * 0.5:.0f}-{procurement_qty * 0.6:.0f} tons)\n")


def example_3_compare_crops():
    """Example 3: Compare price sensitivity across crops."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Comparing Price Sensitivity Across Crops")
    print("=" * 70)
    print("\nScenario: 10% yield loss across different crop types")
    print("Which crops are most vulnerable to price shocks?\n")
    
    crops = ["maize", "wheat", "soybeans", "rice", "cocoa", "coffee", "potato"]
    baseline = 1000.0
    stressed = 900.0  # 10% loss
    
    results = []
    for crop in crops:
        result = calculate_price_shock(crop, baseline, stressed)
        results.append({
            'crop': crop,
            'elasticity': result['elasticity'],
            'price_increase': result['price_increase_pct'],
            'baseline_price': result['baseline_price']
        })
    
    # Sort by price increase (most sensitive first)
    results.sort(key=lambda x: x['price_increase'], reverse=True)
    
    print("Ranking (most price-sensitive first):\n")
    print(f"{'Crop':<12} {'Elasticity':>12} {'Price Impact':>15} {'Baseline Price':>15}")
    print("-" * 70)
    
    for r in results:
        elasticity_label = "Highly Inelastic" if r['elasticity'] < 0.3 else \
                          "Inelastic" if r['elasticity'] < 0.5 else "Moderately Elastic"
        print(f"{r['crop'].capitalize():<12} "
              f"{r['elasticity']:>12.2f} "
              f"{r['price_increase']:>13.1f}% "
              f"${r['baseline_price']:>13.2f}/ton")
    
    print("\n💡 INSIGHT:")
    print(f"  • Most sensitive: {results[0]['crop'].upper()} "
          f"({results[0]['price_increase']:.1f}% price increase)")
    print(f"  • Least sensitive: {results[-1]['crop'].upper()} "
          f"({results[-1]['price_increase']:.1f}% price increase)")
    print(f"  • Highly inelastic crops (rice, cocoa, coffee) see 5-6x price impact")
    print(f"    compared to elastic crops (potato)\n")


def example_4_severe_drought():
    """Example 4: Severe drought scenario."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Severe Drought - Cocoa Farmer")
    print("=" * 70)
    print("\nScenario: Severe drought reduces cocoa yield by 40%")
    print("Cocoa is highly inelastic (elasticity = 0.15)")
    print("Expected: Extreme price shock\n")
    
    result = calculate_price_shock(
        crop_type="cocoa",
        baseline_yield_tons=100.0,
        stressed_yield_tons=60.0
    )
    
    print(f"📊 MARKET SHOCK:")
    print(f"  Yield Loss: {result['yield_loss_pct']:.0f}%")
    print(f"  Elasticity: {result['elasticity']:.2f} (extremely inelastic)")
    print(f"  Price Increase: {result['price_increase_pct']:.0f}%")
    print(f"  Baseline: ${result['baseline_price']:,.0f}/ton")
    print(f"  Shocked Price: ${result['shocked_price']:,.0f}/ton\n")
    
    print(f"💰 FARMER REVENUE:")
    rev = result['revenue_impact']
    print(f"  Baseline: ${rev['baseline_revenue_usd']:,.2f}")
    print(f"  Stressed: ${rev['stressed_revenue_usd']:,.2f}")
    print(f"  Net Change: ${rev['net_revenue_change_usd']:,.2f} "
          f"({rev['net_revenue_change_pct']:.1f}%)\n")
    
    print(f"🚨 CRITICAL ALERT:")
    print(f"  {result['forward_contract_recommendation']}\n")
    
    print("  ⚠️  WARNING: This level of price shock indicates:")
    print("     • Potential food security crisis")
    print("     • Consumer hardship (cocoa/chocolate prices will spike)")
    print("     • Opportunity for farmers to lock in high prices")
    print("     • Risk of supply chain disruptions\n")


def example_5_scenario_analysis():
    """Example 5: Scenario analysis across drought severities."""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Drought Severity Scenario Analysis - Maize")
    print("=" * 70)
    print("\nScenario: Model price response across drought intensities")
    print("Baseline yield: 1,000 tons\n")
    
    baseline = 1000.0
    drought_scenarios = [
        (5, "Mild drought"),
        (10, "Moderate drought"),
        (15, "Significant drought"),
        (20, "Severe drought"),
        (30, "Extreme drought"),
        (40, "Catastrophic drought")
    ]
    
    print(f"{'Scenario':<25} {'Yield':<10} {'Price':<15} {'Revenue':>15}")
    print("-" * 70)
    
    for loss_pct, label in drought_scenarios:
        stressed = baseline * (1 - loss_pct / 100)
        result = calculate_price_shock("maize", baseline, stressed)
        
        price_change = result['price_increase_pct']
        revenue_change = result['revenue_impact']['net_revenue_change_pct']
        
        print(f"{label:<25} "
              f"{-loss_pct:>6}% "
              f"+{price_change:>6.0f}% "
              f"{revenue_change:>+6.0f}%")
    
    print("\n💡 KEY INSIGHTS:")
    print("  • Mild droughts (5-10% loss) → Manageable price increases (20-40%)")
    print("  • Severe droughts (20-30% loss) → Dramatic price spikes (80-120%)")
    print("  • Price shock often compensates farmers for lost production")
    print("  • But consumers bear the cost of higher food prices\n")


def example_6_portfolio_risk():
    """Example 6: Multi-crop portfolio risk analysis."""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Diversified Farm Portfolio Risk")
    print("=" * 70)
    print("\nScenario: Diversified farmer growing multiple crops")
    print("Drought affects all crops, but to varying degrees\n")
    
    portfolio = [
        {"crop": "maize", "baseline": 300, "stressed": 240, "label": "30% loss"},
        {"crop": "wheat", "baseline": 200, "stressed": 170, "label": "15% loss"},
        {"crop": "soybeans", "baseline": 150, "stressed": 135, "label": "10% loss"},
    ]
    
    print(f"{'Crop':<12} {'Yield Loss':>12} {'Price Impact':>15} {'Revenue Change':>18}")
    print("-" * 70)
    
    total_baseline_rev = 0
    total_stressed_rev = 0
    
    for asset in portfolio:
        result = calculate_price_shock(
            crop_type=asset["crop"],
            baseline_yield_tons=asset["baseline"],
            stressed_yield_tons=asset["stressed"]
        )
        
        baseline_rev = result['revenue_impact']['baseline_revenue_usd']
        stressed_rev = result['revenue_impact']['stressed_revenue_usd']
        rev_change = result['revenue_impact']['net_revenue_change_pct']
        
        total_baseline_rev += baseline_rev
        total_stressed_rev += stressed_rev
        
        print(f"{asset['crop'].capitalize():<12} "
              f"{asset['label']:>12} "
              f"+{result['price_increase_pct']:>6.0f}% "
              f"{rev_change:>+6.0f}%")
    
    portfolio_rev_change = (
        (total_stressed_rev - total_baseline_rev) / total_baseline_rev * 100
    )
    
    print("-" * 70)
    print(f"{'PORTFOLIO TOTAL':<12} "
          f"{'':>12} {'':>15} "
          f"{portfolio_rev_change:>+6.0f}%\n")
    
    print(f"💰 FINANCIAL SUMMARY:")
    print(f"  Total Baseline Revenue: ${total_baseline_rev:,.2f}")
    print(f"  Total Stressed Revenue: ${total_stressed_rev:,.2f}")
    print(f"  Net Change: ${total_stressed_rev - total_baseline_rev:,.2f}\n")
    
    print("💡 DIVERSIFICATION BENEFIT:")
    print("  • Spreading across crops with different elasticities reduces risk")
    print("  • Some crops gain more revenue despite losses")
    print("  • Portfolio approach stabilizes overall farm income\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("COMMODITY PRICE SHOCK ENGINE - EXAMPLES")
    print("Climate-Induced Supply Disruption Modeling")
    print("=" * 70)
    
    example_1_basic_drought()
    example_2_food_processor()
    example_3_compare_crops()
    example_4_severe_drought()
    example_5_scenario_analysis()
    example_6_portfolio_risk()
    
    print("\n" + "=" * 70)
    print("For more information, see: docs/PRICE_SHOCK_ENGINE.md")
    print("API documentation: POST /api/v1/finance/price-shock")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
