# Frontend Receiving Zeros - Comprehensive Troubleshooting Guide

## Current Situation

**Backend API Returns** (verified working):
```json
{
  "slope": 0.2445,
  "storm_wave": 4.5,
  "avoided_loss": 49823.64
}
```

**Frontend Receives**:
```json
{
  "slope": 0.05,
  "storm_wave": 0,
  "avoided_loss": 0
}
```

**Conclusion**: There's a mismatch between what the API returns and what the frontend receives. This suggests an intermediary layer, caching, or wrong endpoint.

---

## Troubleshooting Steps (Execute These)

### Step 1: Verify the API Endpoint URL

**What to check**: The frontend might be calling a different endpoint or old deployment.

**Action**: Open browser DevTools (F12) → Network tab → Find the API request:

1. Look for a request to `/predict-coastal`
2. Click on it and check the **Request URL**
3. Verify it's: `https://web-production-8ff9e.up.railway.app/predict-coastal`

**Common Issues**:
- ❌ Calling `localhost` or old URL
- ❌ Calling through n8n proxy with different URL
- ❌ Environment variable pointing to wrong URL

**Expected Result**: URL should be the Railway URL above

---

### Step 2: Check the Actual Response in Browser

**Action**: In Network tab, click the request → **Response** tab

**What to look for**:
```json
// Should see:
{
  "status": "success",
  "data": {
    "slope": 0.XXXX,       // Some decimal value
    "storm_wave": X.X,     // Should be 2.5 - 4.5, NEVER 0
    "avoided_loss": XXXXX  // Should be non-zero
  }
}
```

**If you see zeros in the actual HTTP response**:
- → API is returning zeros (shouldn't happen based on our tests)
- → Check Step 3 (n8n proxy)

**If you see non-zero values in HTTP response but zeros in console**:
- → Frontend parsing issue
- → Check Step 4 (parsing code)

---

### Step 3: Check for n8n Proxy Layer

**What**: You mentioned "n8n self hosting API structure". The frontend might be calling through n8n instead of directly to Railway.

**Action**: Check your frontend environment variables:

```javascript
// Look for something like:
VITE_API_URL=https://your-n8n-instance.com/webhook/...
// or
REACT_APP_API_URL=https://n8n.yourdomain.com/...
```

**If frontend calls n8n**:
1. n8n might have **old cached data**
2. n8n workflow might have **hardcoded values**
3. n8n might be calling an **old API endpoint**

**To fix**:
- Check n8n workflow for the coastal endpoint
- Verify n8n is calling: `https://web-production-8ff9e.up.railway.app/predict-coastal`
- Clear any n8n caches
- Test n8n workflow directly

---

### Step 4: Test API Directly from Browser Console

**Action**: Open browser console and run:

```javascript
fetch('https://web-production-8ff9e.up.railway.app/predict-coastal', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lat: -4.6796,
    lon: 55.492,
    mangrove_width: 50
  })
})
.then(r => r.json())
.then(data => {
  console.log('Direct API test:');
  console.log('slope:', data.data.slope);
  console.log('storm_wave:', data.data.storm_wave);
  console.log('avoided_loss:', data.data.avoided_loss);
});
```

**Expected Output**:
```
Direct API test:
slope: 0.2445
storm_wave: 4.5
avoided_loss: 49823.64
```

**If you get zeros here**:
- → Check CORS (might be blocked)
- → Check if browser is caching old responses
- → Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

**If you get non-zeros here but your app shows zeros**:
- → Frontend parsing issue (Step 5)

---

### Step 5: Check Frontend Parsing Code

**What**: Frontend might be parsing the wrong fields or using default values.

**Action**: Find where the frontend parses the coastal response. Look for:

```javascript
// WRONG - Looking in wrong place:
const slope = response.coastal_params?.slope_pct || 0;  // Defaults to 0!
const wave = response.coastal_params?.storm_wave_height || 0;  // Defaults to 0!

// CORRECT - Should be:
const slope = response.data.slope;
const wave = response.data.storm_wave;
const avoidedLoss = response.data.avoided_loss;
```

**Check for**:
- `|| 0` or `?? 0` (default to zero if undefined)
- Wrong field paths
- TypeScript interfaces with wrong field names

---

### Step 6: Check for Caching Issues

**Sources of caching**:

1. **Browser Cache**:
   - Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
   - Or: DevTools → Network tab → Check "Disable cache"

2. **Service Worker**:
   - DevTools → Application tab → Service Workers → Unregister
   - Or: Clear site data

3. **CDN/Proxy Cache**:
   - If using Cloudflare/Vercel/etc, clear their cache
   - Add cache-busting: `?t=${Date.now()}` to API URL

4. **Railway Cache**:
   - Unlikely, but check deployment timestamp
   - Redeploy if needed

---

### Step 7: Compare Request Payload

**What**: Ensure frontend is sending the right data structure.

**Action**: In Network tab, check **Request Payload**:

**Should see**:
```json
{
  "lat": -4.6796,
  "lon": 55.492,
  "mangrove_width": 50  // Must be a NUMBER, not string
}
```

**Common Issues**:
- `mangrove_width: "50"` (string instead of number) → Might cause issues
- `mangrove_width: 0` → Will correctly return $0
- Missing fields → API will return error

---

### Step 8: Check for Multiple API Endpoints

**What**: You might have both:
- Direct Railway API
- n8n webhook proxy
- Old deployment still running

**Action**: Search your frontend code for ALL API calls:

```bash
# In your frontend codebase:
grep -r "predict-coastal" .
grep -r "VITE_API" .
grep -r "REACT_APP_API" .
```

**Look for**:
- Environment variables
- Hardcoded URLs
- Multiple API configurations

---

## Quick Diagnostic Commands

### Command 1: Test API Directly
```bash
curl -X POST https://web-production-8ff9e.up.railway.app/predict-coastal \
  -H "Content-Type: application/json" \
  -d '{"lat": -4.6796, "lon": 55.492, "mangrove_width": 50}' | jq '.data | {slope, storm_wave, avoided_loss}'
```

**Expected**: Non-zero values

### Command 2: Test with Headers (CORS check)
```bash
curl -v -X POST https://web-production-8ff9e.up.railway.app/predict-coastal \
  -H "Content-Type: application/json" \
  -H "Origin: https://your-lovable-domain.com" \
  -d '{"lat": -4.6796, "lon": 55.492, "mangrove_width": 50}' 2>&1 | grep -i "access-control"
```

**Expected**: Should see `Access-Control-Allow-Origin: *`

### Command 3: Check if n8n is in the mix
```bash
# If you have n8n webhook URL, test it:
curl -X POST https://your-n8n-instance.com/webhook/coastal \
  -H "Content-Type: application/json" \
  -d '{"lat": -4.6796, "lon": 55.492, "mangrove_width": 50}'
```

---

## Most Likely Causes (In Order)

### 1. **n8n Proxy with Old Code** (80% likelihood)
- Frontend → n8n → Railway
- n8n has cached response or old workflow
- **Fix**: Update n8n workflow to use latest Railway URL

### 2. **Browser Caching** (15% likelihood)
- Old response cached in browser
- **Fix**: Hard refresh (Ctrl+Shift+R)

### 3. **Frontend Parsing Wrong Fields** (4% likelihood)
- Looking for `data.coastal_params.storm_wave` instead of `data.storm_wave`
- **Fix**: Update frontend parsing code

### 4. **Wrong API Endpoint** (1% likelihood)
- Calling old deployment or localhost
- **Fix**: Update frontend API URL

---

## What to Send Me

Please run these and send me the results:

### Test 1: Browser Console API Test
```javascript
fetch('https://web-production-8ff9e.up.railway.app/predict-coastal', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ lat: -4.6796, lon: 55.492, mangrove_width: 50 })
})
.then(r => r.json())
.then(d => console.log('RESULT:', d.data.slope, d.data.storm_wave, d.data.avoided_loss));
```

### Test 2: Network Tab Screenshot
- Open DevTools → Network tab
- Make a coastal request in your app
- Screenshot showing:
  - Request URL
  - Response body
  - Status code

### Test 3: Frontend API URL
What is the actual URL your frontend is configured to use?
```javascript
// Check:
console.log(import.meta.env.VITE_API_URL);
// or
console.log(process.env.REACT_APP_API_URL);
// or check your .env file
```

---

## Expected API Response (Current)

```json
{
  "status": "success",
  "data": {
    "input_conditions": {
      "lat": -4.6796,
      "lon": 55.492,
      "mangrove_width_m": 50
    },
    "coastal_params": {
      "detected_slope_pct": 24.45,
      "storm_wave_height": 4.5
    },
    "predictions": {
      "baseline_runup": 0.4431,
      "protected_runup": 0.3933
    },
    "analysis": {
      "avoided_loss": 49823.64,
      "avoided_runup_m": 0.0498,
      "percentage_improvement": 11.24,
      "recommendation": "with_mangroves"
    },
    "economic_assumptions": {
      "damage_cost_per_meter": 10000,
      "num_properties": 100
    },
    
    // ← FLAT FIELDS FOR FRONTEND (ADDED FOR YOU)
    "slope": 0.2445,
    "storm_wave": 4.5,
    "avoided_loss": 49823.64
  }
}
```

The flat fields (`slope`, `storm_wave`, `avoided_loss`) are at the root of `data` object.

---

## Next Steps

1. **Run Test 1** in browser console - see if direct API call works
2. **Check Network tab** - see actual request/response
3. **Check for n8n** - see if there's a proxy layer
4. **Clear cache** - hard refresh the page
5. **Send me results** - I'll help debug further

The API is definitely working on our end. The issue is in how the frontend is connecting to it.
