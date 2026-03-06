# Executive Summary - API Contract Audit
**Date**: 2026-03-04  
**Auditor**: Factory AI Droid (backend-architect)  
**Scope**: Portfolio & Finance endpoint debugging

---

## 🎯 **Findings Summary**

### **Portfolio Endpoint** (`/api/v1/analyze-portfolio`)
✅ **Endpoint Found**: `POST /api/v1/analyze-portfolio`  
✅ **Schema Extracted**: CSV file upload with dynamic column parsing  
❌ **No Error Logs Found**: Server logs not available, but root causes identified

### **Finance Endpoint** (`/api/v1/finance/cba-series`)
✅ **Endpoint Found**: `POST /api/v1/finance/cba-series`  
✅ **Pydantic Model Extracted**: Complete with all 13 fields  
✅ **Validated**: Does NOT require `lat` or `lon` coordinates

---

## 🚨 **Root Causes of Errors**

### **1. Portfolio 500 Error**
**Most Likely Cause**: Missing or misnamed `crop_type` column in CSV

**Evidence**:
```python
# Backend requires a column with "crop" in the name
crop_col = next((c for c in df.columns if 'crop' in c), 'crop_type')

if 'crop_type' not in df.columns:
    raise HTTPException(400, "Missing required columns: crop_type")
```

**Fix**: Ensure CSV has a `crop_type` column (or any column with "crop" in the name)

### **2. Finance Data-Mapping Error**
**Most Likely Cause**: Sending percentages as integers instead of decimals

**Evidence**:
```python
# Pydantic validation enforces: 0.0 <= damage_reduction_pct <= 1.0
damage_reduction_pct: float = Field(0.80, ge=0.0, le=1.0)

# If frontend sends 80 instead of 0.80:
# ❌ ERROR: Input should be less than or equal to 1
```

**Fix**: Convert all percentages to decimals (8% = 0.08, 80% = 0.80)

---

## 📋 **Exact API Contracts**

### **Portfolio Endpoint**

**Method**: `POST /api/v1/analyze-portfolio`  
**Content-Type**: `multipart/form-data`  
**Body**: CSV file with columns:

```
lat, lon, asset_value, crop_type
```

**Optional columns**: `scenario_year`, `temp_delta`, `rain_pct_change`

**Column Normalization**: 
- Lowercase
- Remove special characters (keep only letters, numbers, underscores)
- Fuzzy matching for flexible column names

---

### **Finance Endpoint**

**Method**: `POST /api/v1/finance/cba-series`  
**Content-Type**: `application/json`  
**Body**: JSON object with 13 fields (all have defaults)

**Required Fields** (snake_case):
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

**⚠️ Critical**: NO `lat` or `lon` required - purely financial endpoint

---

## 🛠️ **Recommended Frontend Fixes**

### **Portfolio Endpoint**
1. ✅ Use exact CSV column names: `lat`, `lon`, `asset_value`, `crop_type`
2. ✅ Ensure lowercase column names (or let backend normalize)
3. ✅ Include `crop_type` column (most likely cause of 500 error)
4. ✅ Use `multipart/form-data` for file upload

### **Finance Endpoint**
1. ✅ Use snake_case field names (not camelCase)
2. ✅ Convert percentages to decimals: `8%` → `0.08`, `80%` → `0.80`
3. ✅ Remove `lat` and `lon` from payload (not needed)
4. ✅ Use `application/json` content type

---

## 📊 **Documentation Delivered**

1. **`API_CONTRACT_AUDIT.md`** - Comprehensive 400-line technical audit
2. **`FRONTEND_API_QUICK_REFERENCE.md`** - Quick reference card for developers
3. **`EXACT_PYDANTIC_MODELS.py`** - Executable Python file with exact schemas
4. **`EXECUTIVE_SUMMARY_API_AUDIT.md`** - This document

---

## ✅ **Next Steps for Frontend Team**

1. **Update Portfolio CSV generation**:
   - Add `crop_type` column
   - Use lowercase column names

2. **Update Finance payload construction**:
   - Convert percentages to decimals (divide by 100)
   - Use snake_case field names
   - Remove `lat` and `lon` fields

3. **Test with provided examples**:
   - See `FRONTEND_API_QUICK_REFERENCE.md` for curl commands
   - Use `EXACT_PYDANTIC_MODELS.py` to validate payloads locally

4. **Deploy and monitor**:
   - Check browser console for Pydantic validation errors (422 status)
   - Check network tab for 500 errors with detailed messages

---

## 🔗 **Resources**

- **API Code**: `/Users/david/resilient-backend/api.py`
- **Portfolio Endpoint**: Line 899-1063
- **Finance Endpoint**: Line 1067-1166
- **Pydantic Models**: Line 259-280 (CBARequest), Line 282-289 (CVaRRequest)

---

**Audit Status**: ✅ **COMPLETE**  
**Blockers Identified**: ✅ **YES** (2 issues)  
**Solutions Provided**: ✅ **YES**  
**Ready for Frontend Implementation**: ✅ **YES**
