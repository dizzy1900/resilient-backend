#!/usr/bin/env python3
"""
Narrative Engine: Chief Risk Officer Layer
Generates executive summaries for each location using rule-based AI logic.
"""

import json
from datetime import datetime
from typing import Any


def generate_agriculture_summary(location: dict) -> str:
    """Generate executive summary for agriculture projects."""
    name = location.get("target", {}).get("name", "Unknown Location")
    crop = location.get("crop_analysis", {}).get("crop_type", "unknown")
    npv = location.get("financial_analysis", {}).get("npv_usd", 0)
    avoided_loss = location.get("crop_analysis", {}).get("avoided_loss_pct", 0)
    standard_yield = location.get("crop_analysis", {}).get("standard_yield_pct", 100)
    resilient_yield = location.get("crop_analysis", {}).get("resilient_yield_pct", 100)
    recommendation = location.get("crop_analysis", {}).get("recommendation", "standard")
    temp = location.get("climate_conditions", {}).get("temperature_c", 25)
    rainfall = location.get("climate_conditions", {}).get("rainfall_mm", 1000)
    
    # Calculate derived metrics
    yield_loss = 100 - standard_yield
    improvement_pct = location.get("crop_analysis", {}).get("percentage_improvement", 0)
    
    # Sentence 1: Financial verdict
    if npv > 800000:
        verdict = f"STRONG BUY: {name} demonstrates exceptional investment potential with NPV of ${npv:,.0f}."
    elif npv > 500000:
        verdict = f"INVESTABLE: {name} shows solid fundamentals with NPV of ${npv:,.0f}."
    elif npv > 200000:
        verdict = f"MODERATE OPPORTUNITY: {name} presents acceptable returns with NPV of ${npv:,.0f}."
    elif npv > 0:
        verdict = f"CAUTION ADVISED: {name} shows marginal viability with NPV of ${npv:,.0f}."
    else:
        verdict = f"CRITICAL WARNING: {name} shows signs of stranded value with negative NPV."
    
    # Sentence 2: Primary risk driver
    risk_factors = []
    
    if crop == "cocoa" and temp > 28:
        risk_factors.append(f"High sensitivity to drought-induced yield shocks detected for {crop} at {temp:.1f}°C.")
    elif crop == "rice" and rainfall < 1500:
        risk_factors.append(f"Water stress vulnerability identified for {crop} production with {rainfall:.0f}mm annual rainfall.")
    elif crop == "wheat" and temp > 30:
        risk_factors.append(f"Heat stress during grain filling poses significant threat to {crop} yields.")
    elif crop == "maize" and temp > 35:
        risk_factors.append(f"Critical temperature threshold breach risk for {crop} pollination.")
    elif crop == "soy" and yield_loss > 15:
        risk_factors.append(f"Climate-driven yield volatility of {yield_loss:.1f}% threatens {crop} production stability.")
    
    if yield_loss > 20:
        risk_factors.append(f"Severe climate stress indicated by {yield_loss:.1f}% baseline yield reduction.")
    elif yield_loss > 10:
        risk_factors.append(f"Moderate climate pressure with {yield_loss:.1f}% expected yield reduction.")
    elif yield_loss > 0:
        risk_factors.append(f"Minor yield sensitivity of {yield_loss:.1f}% under projected climate conditions.")
    else:
        risk_factors.append(f"Robust climate resilience with stable yields for {crop} cultivation.")
    
    risk_driver = risk_factors[0] if risk_factors else f"Primary risk stems from commodity price volatility in {crop} markets."
    
    # Sentence 3: Strategic recommendation
    if recommendation == "resilient" and improvement_pct > 5:
        strategy = f"Deploy climate-resilient {crop} varieties immediately to capture {improvement_pct:.1f}% yield advantage."
    elif recommendation == "resilient":
        strategy = f"Transition to resilient {crop} cultivars for long-term production security."
    elif npv > 600000:
        strategy = f"Maintain current {crop} operations while monitoring climate indicators for future adaptation triggers."
    elif yield_loss > 15:
        strategy = f"Implement diversification strategy to hedge against {crop} climate exposure."
    else:
        strategy = f"Standard {crop} practices remain viable; establish monitoring protocols for early warning detection."
    
    return f"{verdict} {risk_driver} {strategy}"


def generate_coastal_summary(location: dict) -> str:
    """Generate executive summary for coastal projects."""
    name = location.get("target", {}).get("name", "Unknown Location")
    elevation = location.get("flood_risk", {}).get("elevation_m", 0)
    risk_category = location.get("flood_risk", {}).get("risk_category", "Unknown")
    flood_depth = location.get("flood_risk", {}).get("flood_depth_m", 0)
    slr = location.get("input_conditions", {}).get("slr_projection_m", 1.0)
    total_water = location.get("input_conditions", {}).get("total_water_level_m", 3.5)
    is_underwater = location.get("flood_risk", {}).get("is_underwater", False)
    
    # Sentence 1: Financial verdict
    if is_underwater:
        verdict = f"CRITICAL WARNING: {name} faces existential threat from sea level rise—asset stranding imminent."
    elif risk_category == "Extreme" or flood_depth > 2:
        verdict = f"TOXIC ASSET: {name} demonstrates unacceptable flood exposure with {flood_depth:.1f}m inundation risk."
    elif risk_category == "High" or flood_depth > 1:
        verdict = f"HIGH RISK: {name} requires significant adaptation investment to remain viable."
    elif risk_category == "Moderate" or flood_depth > 0.5:
        verdict = f"MODERATE CONCERN: {name} shows manageable but material coastal risk profile."
    elif risk_category == "Low":
        verdict = f"INVESTABLE: {name} demonstrates strong coastal resilience at {elevation}m elevation."
    else:
        verdict = f"UNDER REVIEW: {name} coastal risk assessment requires additional analysis."
    
    # Sentence 2: Primary risk driver
    if elevation < 5:
        risk_driver = f"Critical elevation vulnerability at {elevation}m above sea level exposes infrastructure to {slr}m SLR scenario plus storm surge."
    elif elevation < 10:
        risk_driver = f"Marginal elevation buffer of {elevation}m requires monitoring under combined SLR and surge scenarios totaling {total_water:.1f}m."
    elif elevation < 20:
        risk_driver = f"Moderate elevation of {elevation}m provides adequate but not unlimited protection against extreme events."
    else:
        risk_driver = f"Strong natural elevation defense at {elevation}m significantly reduces long-term coastal risk exposure."
    
    # Sentence 3: Strategic recommendation
    if is_underwater or flood_depth > 2:
        strategy = "Initiate managed retreat planning and asset divestment strategy within 5-year horizon."
    elif risk_category == "High" or flood_depth > 1:
        strategy = "Deploy hard infrastructure defenses (seawalls, barriers) and elevate critical systems."
    elif elevation < 10:
        strategy = "Implement nature-based solutions (mangrove restoration, living shorelines) to enhance natural protection."
    elif risk_category == "Moderate":
        strategy = "Establish flood early warning systems and periodic vulnerability reassessment protocols."
    else:
        strategy = "Maintain current operations with standard insurance coverage and climate monitoring."
    
    return f"{verdict} {risk_driver} {strategy}"


def generate_flood_summary(location: dict) -> str:
    """Generate executive summary for flood projects."""
    name = location.get("target", {}).get("name", "Unknown Location")
    risk_increase = location.get("flash_flood_analysis", {}).get("risk_increase_pct", 0)
    future_flood_area = location.get("flash_flood_analysis", {}).get("future_flood_area_km2", 0)
    rain_intensity_increase = location.get("input_conditions", {}).get("rain_intensity_increase_pct", 0)
    
    # Get rainfall frequency data
    rain_data = location.get("rainfall_frequency", {}).get("rain_chart_data", [])
    hundredyr_future = 0
    for period in rain_data:
        if period.get("period") == "100yr":
            hundredyr_future = period.get("future_mm", 0)
    
    # Sentence 1: Financial verdict
    if risk_increase > 50:
        verdict = f"CRITICAL WARNING: {name} faces catastrophic flood risk escalation of {risk_increase:.0f}%—immediate action required."
    elif risk_increase > 25:
        verdict = f"HIGH ALERT: {name} demonstrates significant flood vulnerability with {risk_increase:.0f}% risk increase projected."
    elif risk_increase > 10:
        verdict = f"ELEVATED RISK: {name} shows material flood exposure requiring adaptation investment."
    elif future_flood_area > 5:
        verdict = f"MODERATE CONCERN: {name} faces expanding flood zone of {future_flood_area:.1f} km² under future scenarios."
    else:
        verdict = f"MANAGEABLE RISK: {name} shows contained flood exposure under current projections."
    
    # Sentence 2: Primary risk driver
    if rain_intensity_increase > 30:
        risk_driver = f"Extreme precipitation intensification of {rain_intensity_increase:.0f}% drives severe flash flood probability increase."
    elif rain_intensity_increase > 20:
        risk_driver = f"Significant rainfall intensity growth of {rain_intensity_increase:.0f}% overwhelms existing drainage infrastructure capacity."
    elif hundredyr_future > 200:
        risk_driver = f"100-year storm event now delivers {hundredyr_future:.0f}mm, exceeding historical design standards."
    else:
        risk_driver = f"Gradual precipitation pattern shifts require monitoring of urban drainage system adequacy."
    
    # Sentence 3: Strategic recommendation
    if risk_increase > 30 or future_flood_area > 10:
        strategy = "Implement comprehensive green-grey infrastructure hybrid solution with retention basins and permeable surfaces."
    elif risk_increase > 15:
        strategy = "Upgrade stormwater systems to handle 100-year design storm under future climate scenarios."
    elif rain_intensity_increase > 25:
        strategy = "Deploy real-time flood early warning systems and establish community evacuation protocols."
    else:
        strategy = "Enhance urban drainage maintenance and establish periodic capacity reassessment schedule."
    
    return f"{verdict} {risk_driver} {strategy}"


def generate_health_summary(location: dict) -> str:
    """Generate executive summary for health projects."""
    name = location.get("target", {}).get("name", "Unknown Location")
    productivity_loss = location.get("productivity_analysis", {}).get("productivity_loss_pct", 0)
    heat_stress_cat = location.get("productivity_analysis", {}).get("heat_stress_category", "Low")
    wbgt = location.get("productivity_analysis", {}).get("wbgt_estimate", 20)
    malaria_risk = location.get("malaria_risk", {}).get("risk_category", "Low")
    malaria_score = location.get("malaria_risk", {}).get("risk_score", 0)
    annual_loss = location.get("economic_impact", {}).get("total_economic_impact", {}).get("annual_loss", 0)
    per_worker_loss = location.get("economic_impact", {}).get("total_economic_impact", {}).get("per_worker_annual_loss", 0)
    temp = location.get("climate_conditions", {}).get("temperature_c", 25)
    
    # Sentence 1: Financial verdict
    if annual_loss > 50000:
        verdict = f"CRITICAL WARNING: {name} faces severe workforce health crisis with ${annual_loss:,.0f} annual economic impact."
    elif annual_loss > 30000:
        verdict = f"HIGH CONCERN: {name} demonstrates material health-related productivity drag of ${annual_loss:,.0f}/year."
    elif annual_loss > 15000:
        verdict = f"MODERATE RISK: {name} shows quantifiable health impacts totaling ${annual_loss:,.0f} annually."
    elif annual_loss > 5000:
        verdict = f"MANAGEABLE: {name} presents contained health risks with ${annual_loss:,.0f} annual exposure."
    else:
        verdict = f"LOW RISK: {name} demonstrates favorable workforce health conditions."
    
    # Sentence 2: Primary risk driver
    risk_factors = []
    
    if heat_stress_cat in ["High", "Extreme"] or wbgt > 28:
        risk_factors.append(f"Extreme heat stress (WBGT {wbgt:.1f}°C) causes {productivity_loss:.1f}% workforce productivity collapse.")
    elif heat_stress_cat == "Moderate" or wbgt > 25:
        risk_factors.append(f"Elevated heat exposure (WBGT {wbgt:.1f}°C) drives {productivity_loss:.1f}% productivity degradation.")
    
    if malaria_risk == "High" and malaria_score >= 80:
        risk_factors.append(f"High malaria transmission risk (score: {malaria_score}) compounds health burden significantly.")
    elif malaria_risk == "Moderate":
        risk_factors.append(f"Moderate vector-borne disease pressure adds incremental health costs.")
    
    if not risk_factors:
        if temp > 30:
            risk_factors.append(f"Ambient temperature of {temp:.1f}°C approaches thermal comfort thresholds.")
        else:
            risk_factors.append(f"Climate conditions remain within acceptable occupational health parameters.")
    
    risk_driver = risk_factors[0]
    
    # Sentence 3: Strategic recommendation
    if heat_stress_cat in ["High", "Extreme"]:
        strategy = "Deploy cooling infrastructure, shift work schedules to cooler hours, and implement mandatory hydration protocols."
    elif malaria_risk == "High":
        strategy = "Invest in comprehensive vector control program including treated nets, prophylaxis, and standing water elimination."
    elif productivity_loss > 5:
        strategy = "Implement heat acclimatization programs and establish air-conditioned rest areas for workforce recovery."
    elif annual_loss > 10000:
        strategy = "Deploy integrated occupational health monitoring system with preventive care protocols."
    else:
        strategy = "Maintain standard workplace health protocols with periodic climate risk reassessment."
    
    return f"{verdict} {risk_driver} {strategy}"


def generate_executive_summary(location: dict) -> str:
    """Generate executive summary based on project type."""
    project_type = location.get("project_type", "unknown")
    
    generators = {
        "agriculture": generate_agriculture_summary,
        "coastal": generate_coastal_summary,
        "flood": generate_flood_summary,
        "health": generate_health_summary
    }
    
    generator = generators.get(project_type)
    if generator:
        return generator(location)
    else:
        name = location.get("target", {}).get("name", "Unknown Location")
        return f"UNDER REVIEW: {name} requires project-type specific analysis. Manual assessment recommended."


def process_atlas(input_path: str, output_path: str) -> dict:
    """Process the entire atlas and add executive summaries."""
    print(f"Loading risk atlas from: {input_path}")
    
    with open(input_path, 'r') as f:
        atlas = json.load(f)
    
    print(f"Processing {len(atlas)} locations...")
    
    # Statistics tracking
    stats = {
        "total": len(atlas),
        "by_project_type": {},
        "verdicts": {"CRITICAL": 0, "HIGH": 0, "MODERATE": 0, "INVESTABLE": 0, "OTHER": 0}
    }
    
    for i, location in enumerate(atlas):
        project_type = location.get("project_type", "unknown")
        name = location.get("target", {}).get("name", f"Location {i+1}")
        
        # Generate executive summary
        summary = generate_executive_summary(location)
        location["executive_summary"] = summary
        
        # Track statistics
        stats["by_project_type"][project_type] = stats["by_project_type"].get(project_type, 0) + 1
        
        # Categorize verdict
        if "CRITICAL" in summary:
            stats["verdicts"]["CRITICAL"] += 1
        elif "HIGH" in summary or "TOXIC" in summary:
            stats["verdicts"]["HIGH"] += 1
        elif "MODERATE" in summary:
            stats["verdicts"]["MODERATE"] += 1
        elif "INVESTABLE" in summary or "STRONG BUY" in summary or "MANAGEABLE" in summary or "LOW RISK" in summary:
            stats["verdicts"]["INVESTABLE"] += 1
        else:
            stats["verdicts"]["OTHER"] += 1
        
        print(f"  [{i+1}/{len(atlas)}] {name} ({project_type}): Generated summary")
    
    # Save output
    print(f"\nSaving enhanced atlas to: {output_path}")
    with open(output_path, 'w') as f:
        json.dump(atlas, f, indent=2)
    
    return stats


def main():
    """Main entry point."""
    input_path = "/workspace/adaptmetric-backend/final_global_atlas.json"
    output_path = "/workspace/adaptmetric-backend/global_atlas_with_insights.json"
    
    print("=" * 60)
    print("NARRATIVE ENGINE: Chief Risk Officer Layer")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    stats = process_atlas(input_path, output_path)
    
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"\nSummary Statistics:")
    print(f"  Total locations processed: {stats['total']}")
    print(f"\n  By Project Type:")
    for ptype, count in stats["by_project_type"].items():
        print(f"    - {ptype}: {count}")
    print(f"\n  Risk Verdict Distribution:")
    for verdict, count in stats["verdicts"].items():
        print(f"    - {verdict}: {count}")
    print(f"\nOutput saved to: {output_path}")


if __name__ == "__main__":
    main()
