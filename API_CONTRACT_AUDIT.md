# API Contract Audit - Portfolio & Finance Endpoints
**Date**: 2026-03-04  
**Purpose**: Debug frontend-to-backend data pipeline issues  
**Status**: 🔍 **AUDIT COMPLETE**

---

## 🚨 **Issue Summary**

1. **Portfolio Endpoint** (`/api/v1/analyze-portfolio`): HTTP 500 error
2. **Finance Endpoint** (`/api/v1/finance/cba-series`): Data-mapping error

---

## 📋 **1. PORTFOLIO ENDPOINT - `/api/v1/analyze-portfolio`**

### **HTTP Method**
```
POST /api/v1/analyze-portfolio
```

### **Content-Type**
```
multipart/form-data
```

### **Request Format**
**CSV file upload** with the following columns:

#### **REQUIRED COLUMNS** (case-insensitive)
```csv
lat, lon, asset_value, crop_type
```

#### **OPTIONAL COLUMNS**
```csv
scenario_year, temp_delta, rain_pct_change
```

### **Exact Pydantic Schema**
❌ **NO PYDANTIC MODEL** - This endpoint accepts a raw `UploadFile` and parses CSV dynamically.

### **Column Name Normalization Rules**
The backend applies aggressive normalization:
```python
# 1. Convert to lowercase
# 2. Remove ALL special characters except letters, numbers, underscores
df.columns = df.columns.astype(str).str.lower().str.replace(r'[^a-z0-9_]', '', regex=True)
```

**Examples**:
- `"Asset Value ($)"` → `"assetvalue"`
- `"Lat."` → `"lat"`
- `"Crop-Type"` → `"croptype"`

### **Column Matching Logic**
The backend uses **fuzzy matching** for flexibility:

| Column | Fuzzy Match Logic |
|--------|-------------------|
| **lat** | Any column containing `"lat"` |
| **lon** | Any column containing `"lon"` or `"lng"` |
| **asset_value** | Any column containing: `"val"`, `"price"`, `"amount"`, `"cost"`, `"invest"`, `"usd"` |
| **crop_type** | Any column containing `"crop"` |

**Fallback**: If no `asset_value` match found, uses 3rd column (index 2).

### **Value Parsing**
The backend handles currency strings intelligently:
```python
# Supports suffixes: K, M, B
"$1.5M" → 1,500,000
"500K" → 500,000
"$2.3B" → 2,300,000,000

# Strips: $, commas, spaces
"$1,234,567.89" → 1234567.89
```

### **Expected CSV Example**
```csv
lat,lon,asset_value,crop_type,scenario_year,temp_delta,rain_pct_change
34.0522,-118.2437,5000000,maize,2050,1.5,10.0
41.8781,-87.6298,3500000,wheat,2050,2.0,-5.0
40.7128,-74.0060,7200000,soy,2060,2.5,15.0
```

### **Response Schema**
```json
{
  "portfolio_summary": {
    "total_assets": 3,
    "successful_simulations": 3,
    "failed_simulations": 0,
    "total_portfolio_value_usd": 15700000.00,
    "total_value_at_risk_usd": 314000.00,
    "average_resilience_score": 0.85,
    "total_npv_usd": 2450000.00,
    "total_expected_loss_usd": 314000.00,
    "risk_exposure_pct": 2.00,
    "crop_distribution": {
      "maize": 1,
      "wheat": 1,
      "soy": 1
    }
  },
  "asset_results": [
    {
      "row_index": 0,
      "status": "success",
      "input": {
        "lat": 34.0522,
        "lon": -118.2437,
        "asset_value": 5000000.0,
        "crop_type": "maize"
      },
      "simulation": { /* ... detailed simulation data ... */ }
    }
  ]
}
```

### **Error Responses**

#### **400 - Missing Required Columns**
```json
{
  "detail": "Missing required columns: lat, asset_value. Detected columns: ['location', 'value']"
}
```

#### **400 - Empty CSV**
```json
{
  "detail": "Uploaded CSV file is empty"
}
```

#### **500 - Processing Error**
```json
{
  "detail": "Portfolio analysis failed: <error_message>"
}
```

---

## 🔍 **PORTFOLIO 500 ERROR - ROOT CAUSE ANALYSIS**

### **Most Likely Causes**

#### **1. Column Name Mismatch**
**Frontend sends**:
```csv
Latitude,Longitude,AssetValue,CropType
```

**Backend expects** (after normalization):
```
lat, lon, assetvalue (must contain "val"|"price"|"amount"|"cost"|"invest"|"usd"), croptype
```

**Fix**: Frontend should send lowercase, simple column names:
```csv
lat,lon,asset_value,crop_type
```

#### **2. Missing `crop_type` Column**
The backend REQUIRES a crop type for agriculture simulations. If missing:
```python
# Line 948 in api.py
crop_col = next((c for c in df.columns if 'crop' in c), 'crop_type')

if 'crop_type' not in df.columns:
    raise HTTPException(400, "Missing required columns: crop_type")
```

**Fix**: Ensure CSV includes a column with `"crop"` in the name.

#### **3. Invalid Asset Value Format**
If the `asset_value` column contains non-numeric data:
```csv
lat,lon,asset_value,crop_type
34.05,-118.24,INVALID,maize  ← Will cause parsing error
```

**Fix**: Ensure all asset values are numeric or properly formatted currency strings.

#### **4. Row Data Parsing Failure**
If individual rows fail during async processing:
```python
# Line 883 in api.py
except (ValueError, KeyError) as e:
    return {
        "status": "error",
        "error": f"Invalid row data: {str(e)}"
    }
```

Check `asset_results` for failed rows in the response.

---

## 💰 **2. FINANCE ENDPOINT - `/api/v1/finance/cba-series`**

### **HTTP Method**
```
POST /api/v1/finance/cba-series
```

### **Content-Type**
```
application/json
```

### **Exact Pydantic Model**
```python
class CBARequest(BaseModel):
    """Cost-Benefit Analysis time series for climate adaptation project."""
    
    # CORE FINANCIAL PARAMETERS
    capex: float = Field(500000.0, description="Upfront capital expenditure in USD")
    annual_opex: float = Field(25000.0, description="Annual operating expenditure in USD")
    discount_rate: float = Field(0.08, description="Discount rate as decimal (e.g. 0.08 for 8%)")
    lifespan_years: int = Field(30, ge=1, le=100, description="Project lifespan in years")
    annual_baseline_damage: float = Field(100000.0, description="Annual cost of doing nothing in USD")
    damage_reduction_pct: float = Field(0.80, ge=0.0, le=1.0, description="Fraction of damage the intervention prevents")
    
    # PARAMETRIC INSURANCE
    base_insurance_premium: float = Field(50000.0, description="Annual insurance premium without intervention in USD")
    insurance_reduction_pct: float = Field(0.25, ge=0.0, le=1.0, description="Premium reduction from intervention (e.g. 0.25 for 25%)")
    
    # GREEN BOND FINANCING
    standard_interest_rate: float = Field(0.06, description="Standard bond interest rate as decimal (e.g. 0.06 for 6%)")
    greenium_discount_bps: float = Field(50.0, description="Green bond discount in basis points (e.g. 50 = 0.50%)")
    bond_tenor_years: int = Field(10, ge=1, le=50, description="Bond repayment period in years")
    
    # CARBON CREDIT REVENUE (Layered Value Stacking)
    annual_carbon_credits: float = Field(0.0, description="Tons of CO2 sequestered per year")
    carbon_price_per_ton: float = Field(50.0, description="Price per ton of CO2 in USD")
```

### **❌ NO `lat` OR `lon` REQUIRED**
This is a **purely financial endpoint**. It does NOT require geographic coordinates.

### **Request Example (Minimal)**
```json
{
  "capex": 500000.0,
  "annual_opex": 25000.0,
  "discount_rate": 0.08,
  "lifespan_years": 30,
  "annual_baseline_damage": 100000.0,
  "damage_reduction_pct": 0.80
}
```

### **Request Example (Full with Defaults)**
```json
{
  "capex": 500000.0,
  "annual_opex": 25000.0,
  "discount_rate": 0.08,
  "lifespan_years": 30,
  "annual_baseline_damage": 100000.0,
  "damage_reduction_pct": 0.80,
  "base_insurance_premium": 50000.0,
  "insurance_reduction_pct": 0.25,
  "standard_interest_rate": 0.06,
  "greenium_discount_bps": 50.0,
  "bond_tenor_years": 10,
  "annual_carbon_credits": 0.0,
  "carbon_price_per_ton": 50.0
}
```

### **Response Schema**
```json
{
  "status": "success",
  "summary_metrics": {
    "npv": 1245678.90,
    "total_roi_pct": 248.5,
    "breakeven_year": 3,
    "annual_carbon_revenue": 0.0
  },
  "bond_metrics": {
    "principal": 500000.0,
    "standard_rate": 0.06,
    "green_rate": 0.055,
    "standard_annual_payment": 67934.62,
    "green_annual_payment": 64883.12,
    "total_greenium_savings": 30515.00
  },
  "time_series": [
    {
      "year": 2026,
      "baseline_cost": 138888.89,
      "intervention_cost": 523148.15,
      "net_benefit": -384259.26
    },
    {
      "year": 2027,
      "baseline_cost": 266666.67,
      "intervention_cost": 536296.30,
      "net_benefit": -269629.63
    }
    // ... continues for 30 years
  ]
}
```

### **Error Responses**

#### **422 - Validation Error (Pydantic)**
```json
{
  "detail": [
    {
      "type": "float_parsing",
      "loc": ["body", "capex"],
      "msg": "Input should be a valid number",
      "input": "INVALID"
    }
  ]
}
```

#### **500 - Processing Error**
```json
{
  "detail": "<error_message>"
}
```

---

## 🔍 **FINANCE DATA-MAPPING ERROR - ROOT CAUSE ANALYSIS**

### **Most Likely Causes**

#### **1. Sending `lat` and `lon` (Unnecessary)**
**Frontend sends**:
```json
{
  "lat": 34.0522,
  "lon": -118.2437,
  "capex": 500000.0,
  ...
}
```

**Backend expects**: NO geographic coordinates for CBA endpoint.

**Fix**: Remove `lat` and `lon` from the payload.

#### **2. Incorrect Field Names (Snake Case Required)**
**Frontend sends (camelCase)**:
```json
{
  "capEx": 500000.0,
  "annualOpex": 25000.0,
  "discountRate": 0.08
}
```

**Backend expects (snake_case)**:
```json
{
  "capex": 500000.0,
  "annual_opex": 25000.0,
  "discount_rate": 0.08
}
```

**Fix**: Use exact snake_case field names from the Pydantic model.

#### **3. Percentage Format Mismatch**
**Frontend sends (percentage as integer)**:
```json
{
  "discount_rate": 8,  ← WRONG (should be 0.08)
  "damage_reduction_pct": 80  ← WRONG (should be 0.80)
}
```

**Backend expects (decimal format)**:
```json
{
  "discount_rate": 0.08,  // 8%
  "damage_reduction_pct": 0.80  // 80%
}
```

**Fix**: Convert percentages to decimals (divide by 100).

#### **4. Missing Required Fields**
All fields have defaults, but if frontend explicitly sends `null`:
```json
{
  "capex": null  ← Will trigger validation error
}
```

**Fix**: Either omit the field (use default) or provide a valid number.

---

## 🛠️ **RECOMMENDED FIXES FOR FRONTEND**

### **Portfolio Endpoint**
```typescript
// ✅ CORRECT
const formData = new FormData();
formData.append('file', csvFile);

// CSV should have EXACT columns (lowercase, no special chars):
// lat,lon,asset_value,crop_type

const response = await fetch('/api/v1/analyze-portfolio', {
  method: 'POST',
  body: formData
});
```

### **Finance Endpoint**
```typescript
// ✅ CORRECT
const payload = {
  capex: 500000.0,
  annual_opex: 25000.0,
  discount_rate: 0.08,  // 8% as decimal
  lifespan_years: 30,
  annual_baseline_damage: 100000.0,
  damage_reduction_pct: 0.80,  // 80% as decimal
  base_insurance_premium: 50000.0,
  insurance_reduction_pct: 0.25,  // 25% as decimal
  standard_interest_rate: 0.06,  // 6% as decimal
  greenium_discount_bps: 50.0,  // 50 basis points
  bond_tenor_years: 10,
  annual_carbon_credits: 0.0,
  carbon_price_per_ton: 50.0
};

const response = await fetch('/api/v1/finance/cba-series', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload)
});
```

---

## 📊 **TESTING ENDPOINTS**

### **Test Portfolio Endpoint**
```bash
# Create test CSV
cat > test_portfolio.csv << EOF
lat,lon,asset_value,crop_type
34.0522,-118.2437,5000000,maize
41.8781,-87.6298,3500000,wheat
EOF

# Test upload
curl -X POST http://localhost:8000/api/v1/analyze-portfolio \
  -F "file=@test_portfolio.csv"
```

### **Test Finance Endpoint**
```bash
curl -X POST http://localhost:8000/api/v1/finance/cba-series \
  -H "Content-Type: application/json" \
  -d '{
    "capex": 500000.0,
    "annual_opex": 25000.0,
    "discount_rate": 0.08,
    "lifespan_years": 30,
    "annual_baseline_damage": 100000.0,
    "damage_reduction_pct": 0.80
  }'
```

---

## 📝 **SUMMARY FOR FRONTEND TEAM**

### **Portfolio Endpoint (`/api/v1/analyze-portfolio`)**
- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Input**: CSV file with columns: `lat`, `lon`, `asset_value`, `crop_type`
- **Column names**: Lowercase, no special characters
- **Common error**: Missing `crop_type` column or invalid column names

### **Finance Endpoint (`/api/v1/finance/cba-series`)**
- **Method**: POST
- **Content-Type**: `application/json`
- **Input**: JSON object with financial parameters (see exact schema above)
- **⚠️ NO `lat` or `lon` REQUIRED** - This is a pure financial calculation
- **Common error**: Sending percentages as integers (should be decimals: 8% = 0.08)

---

**Audit Completed By**: Factory AI Droid (backend-architect)  
**Date**: 2026-03-04  
**Status**: ✅ **READY FOR FRONTEND ALIGNMENT**
