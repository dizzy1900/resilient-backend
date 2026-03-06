# Frontend API Quick Reference
**For**: Frontend Development Team  
**Date**: 2026-03-04

---

## 🚀 **Portfolio Bulk Analysis**

### **Endpoint**
```
POST /api/v1/analyze-portfolio
```

### **Request Format**
- **Content-Type**: `multipart/form-data`
- **Body**: CSV file upload

### **CSV Column Names (EXACT)**
```csv
lat,lon,asset_value,crop_type,scenario_year,temp_delta,rain_pct_change
```

**Required**: `lat`, `lon`, `asset_value`, `crop_type`  
**Optional**: `scenario_year`, `temp_delta`, `rain_pct_change`

### **Example CSV**
```csv
lat,lon,asset_value,crop_type,scenario_year,temp_delta,rain_pct_change
34.0522,-118.2437,5000000,maize,2050,1.5,10.0
41.8781,-87.6298,3500000,wheat,2050,2.0,-5.0
40.7128,-74.0060,7200000,soy,2060,2.5,15.0
```

### **Frontend Code Example**
```typescript
const formData = new FormData();
formData.append('file', csvFile);

const response = await fetch('https://your-api.com/api/v1/analyze-portfolio', {
  method: 'POST',
  body: formData
});

const data = await response.json();
```

### **Response Structure**
```typescript
interface PortfolioResponse {
  portfolio_summary: {
    total_assets: number;
    successful_simulations: number;
    failed_simulations: number;
    total_portfolio_value_usd: number;
    total_value_at_risk_usd: number;
    average_resilience_score: number;
    total_npv_usd: number;
    total_expected_loss_usd: number;
    risk_exposure_pct: number;
    crop_distribution: Record<string, number>;
  };
  asset_results: Array<{
    row_index: number;
    status: 'success' | 'error';
    input: {
      lat: number;
      lon: number;
      asset_value: number;
      crop_type: string;
    };
    simulation?: any; // Full simulation data
    error?: string;
  }>;
}
```

---

## 💰 **Finance / Green Bond Simulation**

### **Endpoint**
```
POST /api/v1/finance/cba-series
```

### **Request Format**
- **Content-Type**: `application/json`
- **Body**: JSON object

### **JSON Field Names (EXACT - snake_case)**
```typescript
interface CBARequest {
  // CORE FINANCIAL PARAMETERS
  capex: number;                      // e.g., 500000.0
  annual_opex: number;                // e.g., 25000.0
  discount_rate: number;              // DECIMAL: 0.08 for 8%
  lifespan_years: number;             // e.g., 30
  annual_baseline_damage: number;     // e.g., 100000.0
  damage_reduction_pct: number;       // DECIMAL: 0.80 for 80%
  
  // PARAMETRIC INSURANCE
  base_insurance_premium: number;     // e.g., 50000.0
  insurance_reduction_pct: number;    // DECIMAL: 0.25 for 25%
  
  // GREEN BOND FINANCING
  standard_interest_rate: number;     // DECIMAL: 0.06 for 6%
  greenium_discount_bps: number;      // e.g., 50.0 (50 basis points)
  bond_tenor_years: number;           // e.g., 10
  
  // CARBON CREDIT REVENUE
  annual_carbon_credits: number;      // e.g., 0.0
  carbon_price_per_ton: number;       // e.g., 50.0
}
```

### **⚠️ IMPORTANT NOTES**
1. **NO `lat` or `lon` REQUIRED** - This is a financial-only endpoint
2. **Percentages must be DECIMALS**: 8% = 0.08, 80% = 0.80, 25% = 0.25
3. **All fields have defaults** - Only send what you need to change

### **Frontend Code Example**
```typescript
const payload: CBARequest = {
  capex: 500000.0,
  annual_opex: 25000.0,
  discount_rate: 0.08,  // 8% as decimal
  lifespan_years: 30,
  annual_baseline_damage: 100000.0,
  damage_reduction_pct: 0.80,  // 80% as decimal
  base_insurance_premium: 50000.0,
  insurance_reduction_pct: 0.25,  // 25% as decimal
  standard_interest_rate: 0.06,  // 6% as decimal
  greenium_discount_bps: 50.0,
  bond_tenor_years: 10,
  annual_carbon_credits: 0.0,
  carbon_price_per_ton: 50.0
};

const response = await fetch('https://your-api.com/api/v1/finance/cba-series', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});

const data = await response.json();
```

### **Response Structure**
```typescript
interface CBAResponse {
  status: 'success';
  summary_metrics: {
    npv: number;
    total_roi_pct: number;
    breakeven_year: number | null;
    annual_carbon_revenue: number;
  };
  bond_metrics: {
    principal: number;
    standard_rate: number;
    green_rate: number;
    standard_annual_payment: number;
    green_annual_payment: number;
    total_greenium_savings: number;
  };
  time_series: Array<{
    year: number;
    baseline_cost: number;
    intervention_cost: number;
    net_benefit: number;
  }>;
}
```

---

## 🐛 **Common Errors & Fixes**

### **Portfolio Endpoint**

#### ❌ **Error**: "Missing required columns: asset_value"
**Cause**: Column name doesn't match expected format  
**Fix**: Use exact column name `asset_value` (lowercase, no spaces)

#### ❌ **Error**: HTTP 500 Internal Server Error
**Cause**: Missing `crop_type` column or invalid data in CSV  
**Fix**: Ensure CSV has `crop_type` column with valid crop names (maize, wheat, soy, etc.)

#### ❌ **Error**: "Failed to parse CSV file"
**Cause**: Invalid CSV format  
**Fix**: Ensure proper CSV encoding (UTF-8) and no malformed rows

---

### **Finance Endpoint**

#### ❌ **Error**: "Input should be a valid number"
**Cause**: Sending percentage as integer instead of decimal  
**Fix**: Convert percentages to decimals
```typescript
// ❌ WRONG
{ "discount_rate": 8 }

// ✅ CORRECT
{ "discount_rate": 0.08 }
```

#### ❌ **Error**: Data mapping error / unexpected field
**Cause**: Using camelCase instead of snake_case  
**Fix**: Use exact field names from schema
```typescript
// ❌ WRONG
{ "discountRate": 0.08, "lifespanYears": 30 }

// ✅ CORRECT
{ "discount_rate": 0.08, "lifespan_years": 30 }
```

#### ❌ **Error**: Sending `lat` and `lon` causes confusion
**Cause**: Finance endpoint doesn't need coordinates  
**Fix**: Remove `lat` and `lon` from payload

---

## 📋 **Field Name Comparison**

| ❌ Common Mistake | ✅ Correct Field Name |
|------------------|----------------------|
| `discountRate` | `discount_rate` |
| `lifespanYears` | `lifespan_years` |
| `annualOpex` | `annual_opex` |
| `damageReductionPct` | `damage_reduction_pct` |
| `insuranceReductionPct` | `insurance_reduction_pct` |
| `standardInterestRate` | `standard_interest_rate` |
| `greeniumDiscountBps` | `greenium_discount_bps` |
| `bondTenorYears` | `bond_tenor_years` |
| `annualCarbonCredits` | `annual_carbon_credits` |
| `carbonPricePerTon` | `carbon_price_per_ton` |

---

## 🧪 **Quick Test Commands**

### **Test Portfolio (Bash)**
```bash
cat > test.csv << EOF
lat,lon,asset_value,crop_type
34.0522,-118.2437,5000000,maize
EOF

curl -X POST https://your-api.com/api/v1/analyze-portfolio \
  -F "file=@test.csv"
```

### **Test Finance (Bash)**
```bash
curl -X POST https://your-api.com/api/v1/finance/cba-series \
  -H "Content-Type: application/json" \
  -d '{
    "capex": 500000,
    "annual_opex": 25000,
    "discount_rate": 0.08,
    "lifespan_years": 30,
    "annual_baseline_damage": 100000,
    "damage_reduction_pct": 0.8
  }'
```

---

## 🆘 **Need Help?**

**Contact**: Backend Team  
**Documentation**: See `API_CONTRACT_AUDIT.md` for detailed analysis  
**Logs**: Check browser console for exact Pydantic validation errors
