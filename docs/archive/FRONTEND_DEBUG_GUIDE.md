# Frontend Integration Debug Guide

## 🎯 Summary: Backend is 100% Working!

**Test Results:**
- ✅ Endpoint responds: 200 OK
- ✅ CORS headers: Properly configured for Lovable
- ✅ Response structure: Matches coastal/agricultural APIs
- ✅ Field path: `data.analysis.avoided_loss` exists
- ✅ Values: Real predictions ($47,079)
- ✅ Error handling: Validates inputs correctly

**Conclusion:** The issue is in the **frontend code**, not the backend.

---

## 🔍 Most Likely Issues

### Issue #1: Wrong API URL (Most Common)

The frontend might be calling:
- ❌ `localhost:5001` (development)
- ❌ `adaptmetric-backend.railway.app` (wrong Railway URL)
- ❌ Missing `/predict-flood` in the path

**Should be:**
- ✅ `https://web-production-8ff9e.up.railway.app/predict-flood`

### Issue #2: Endpoint Not Wired to UI

The flood prediction might not be:
- Connected to a button/form in UI
- Included in API service file
- Added to routing/navigation

### Issue #3: Environment Variable Not Set

Lovable might use environment variables for API URLs:
- `VITE_API_URL` or similar might not include flood endpoint
- Different env var for each API type

### Issue #4: Hardcoded Test Data

The UI might be showing hardcoded dummy data instead of calling the API

---

## 🛠️ Manual Testing Steps

### Step 1: Check Browser Network Tab

1. **Open Lovable app in browser**
2. **Open DevTools** (F12 or Right-click → Inspect)
3. **Go to Network tab**
4. **Filter by "predict"** (or "flood")
5. **Trigger flood prediction in UI**

**Look for:**
- ✅ Request to `/predict-flood`
- ✅ Status: 200
- ✅ Response with `avoided_loss` value

**If you see:**
- ❌ No request appears → UI not calling API
- ❌ Request to wrong URL → URL issue
- ❌ 404 error → Endpoint path wrong
- ❌ CORS error → Origin issue (unlikely, our tests passed)

### Step 2: Check Browser Console

1. **Open DevTools Console tab**
2. **Trigger flood prediction**

**Look for:**
- ❌ "CORS" error → Unlikely (our tests passed)
- ❌ "Failed to fetch" → Network/URL issue
- ❌ "undefined is not a function" → Code error
- ❌ Any red errors → Share these with me

### Step 3: Check API URL in Code

**In Lovable project, search for:**

```bash
# Search for API URL patterns
grep -r "web-production" .
grep -r "predict-flood" .
grep -r "VITE_API_URL" .
grep -r "API_BASE" .
```

**Expected to find:**
```javascript
const API_URL = 'https://web-production-8ff9e.up.railway.app';
// or
const API_URL = import.meta.env.VITE_API_URL;
```

**Check if flood endpoint is included:**
```javascript
// Should have something like:
const endpoints = {
  flood: '/predict-flood',
  coastal: '/predict-coastal',
  agricultural: '/predict'
};
```

### Step 4: Test Directly in Browser Console

**Open Lovable app** → **Open DevTools Console** → **Paste this code:**

```javascript
// Test flood prediction directly
fetch('https://web-production-8ff9e.up.railway.app/predict-flood', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    rain_intensity: 100,
    current_imperviousness: 0.7,
    intervention_type: 'green_roof'
  })
})
.then(res => res.json())
.then(data => {
  console.log('✅ Flood API Response:', data);
  console.log('💰 Avoided Loss:', data.data.analysis.avoided_loss);
})
.catch(err => {
  console.error('❌ Error:', err);
});
```

**Expected output:**
```
✅ Flood API Response: {status: 'success', data: {...}}
💰 Avoided Loss: 47078.94
```

**If this works but UI doesn't:**
→ The problem is in the UI code, not the API

---

## 📝 Common Frontend Code Issues

### Issue: API URL Not Configured

**❌ Wrong:**
```javascript
// Using localhost (development only)
const API_URL = 'http://localhost:5001';
```

**✅ Correct:**
```javascript
// Use production URL
const API_URL = 'https://web-production-8ff9e.up.railway.app';
```

### Issue: Endpoint Path Missing

**❌ Wrong:**
```javascript
// Missing endpoint
fetch(API_URL, { ... })
```

**✅ Correct:**
```javascript
// Include full path
fetch(`${API_URL}/predict-flood`, { ... })
```

### Issue: Field Path Incorrect

**❌ Wrong:**
```javascript
// Looking in wrong place
const avoidedLoss = data.avoided_loss;  // undefined!
```

**✅ Correct:**
```javascript
// Correct nested path
const avoidedLoss = data.data.analysis.avoided_loss;
```

### Issue: Not Handling Response

**❌ Wrong:**
```javascript
// Not extracting data
fetch(url).then(res => {
  console.log(res);  // This is the Response object, not data!
});
```

**✅ Correct:**
```javascript
// Parse JSON first
fetch(url)
  .then(res => res.json())  // Parse JSON
  .then(data => {
    console.log(data.data.analysis.avoided_loss);
  });
```

---

## 🔎 Detailed Debugging Checklist

### Frontend Code Files to Check

In your Lovable project, look for these files:

1. **API Service Files**
   - `src/services/api.js` (or `.ts`)
   - `src/api/flood.js`
   - `src/utils/api.js`
   - `src/lib/api.ts`

2. **Component Files**
   - `src/components/FloodPrediction.jsx`
   - `src/pages/Flood.jsx`
   - Any component with "flood" in the name

3. **Environment Files**
   - `.env`
   - `.env.production`
   - `.env.local`

### What to Look For

**In API service files:**
```javascript
// Check base URL
const API_BASE_URL = '...';  // Should be web-production URL

// Check endpoints object
const endpoints = {
  flood: '/predict-flood',  // Should exist
  // ...
};

// Check fetch calls
fetch(`${API_BASE_URL}/predict-flood`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(params)
});
```

**In component files:**
```javascript
// Check if API is being called
const handleFloodPrediction = async () => {
  const response = await fetch(...);  // Should call API
  const data = await response.json();
  
  // Check field path
  const avoidedLoss = data.data.analysis.avoided_loss;  // Correct path
};
```

**In environment files:**
```bash
# Should have production URL
VITE_API_URL=https://web-production-8ff9e.up.railway.app
# or
REACT_APP_API_URL=https://web-production-8ff9e.up.railway.app
```

---

## 🧪 Test Cases to Run

### Test 1: Direct Browser Fetch (from any website)

1. Open **any website** (e.g., google.com)
2. Open DevTools Console
3. Run this:

```javascript
fetch('https://web-production-8ff9e.up.railway.app/predict-flood', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    rain_intensity: 100,
    current_imperviousness: 0.7,
    intervention_type: 'green_roof'
  })
})
.then(r => r.json())
.then(d => console.log('Avoided Loss:', d.data.analysis.avoided_loss));
```

**Expected:** `Avoided Loss: 47078.94`

### Test 2: Compare with Working Coastal Endpoint

If coastal predictions work in your UI, compare the code:

**Coastal (working):**
```javascript
// What URL does it use?
// What headers?
// How does it parse response?
```

**Flood (not working):**
```javascript
// Should use SAME pattern as coastal!
```

### Test 3: Check if Data is Hardcoded

Look for:
```javascript
// Dummy data that never changes
const floodData = {
  avoidedLoss: 50000,  // Always the same?
  // ...
};
```

If values never change regardless of inputs → using dummy data!

---

## 📊 Comparison Table

Since coastal API works and flood doesn't, they should be **identical**:

| Aspect | Coastal (Working) | Flood (Should Match) |
|--------|------------------|----------------------|
| **Base URL** | `https://web-production-8ff9e.up.railway.app` | ✅ Same |
| **Endpoint** | `/predict-coastal` | `/predict-flood` |
| **Method** | `POST` | `POST` |
| **Headers** | `Content-Type: application/json` | ✅ Same |
| **Response Path** | `data.analysis.avoided_loss` | ✅ Same |
| **CORS** | ✅ Configured | ✅ Configured |

---

## 🚨 What to Send Me

If you're still stuck, send me:

### 1. Network Tab Screenshot
- Show the request to `/predict-flood`
- Show headers, payload, response

### 2. Console Errors
- Any red errors in browser console
- Full error messages

### 3. Code Snippets
```javascript
// The API service code that calls flood endpoint
// The component code that handles flood predictions
// The environment variables (hide sensitive data)
```

### 4. Test Results

Run this in browser console on your Lovable app:
```javascript
// Test 1: Check if API is defined
console.log('API URL:', window.YOUR_API_CONFIG);

// Test 2: Direct test
fetch('https://web-production-8ff9e.up.railway.app/predict-flood', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    rain_intensity: 100,
    current_imperviousness: 0.7,
    intervention_type: 'green_roof'
  })
})
.then(r => r.json())
.then(d => {
  console.log('✅ API works!', d);
  console.log('Avoided Loss:', d.data.analysis.avoided_loss);
})
.catch(e => console.error('❌ API failed:', e));
```

Share the console output!

---

## ✅ Quick Fix Checklist

1. ☐ Verify production URL in frontend code
2. ☐ Check `/predict-flood` is in endpoint path
3. ☐ Confirm field path is `data.analysis.avoided_loss`
4. ☐ Compare with working coastal endpoint code
5. ☐ Test direct fetch in browser console
6. ☐ Check browser Network tab during UI interaction
7. ☐ Look for CORS errors in console
8. ☐ Verify environment variables

---

## 💡 Most Likely Fix

Based on similar issues with coastal endpoint, the fix is probably:

**Find this in your frontend code:**
```javascript
// ❌ Wrong URL or missing endpoint
const response = await fetch('wrong-url');
```

**Change to:**
```javascript
// ✅ Correct URL
const API_URL = 'https://web-production-8ff9e.up.railway.app';
const response = await fetch(`${API_URL}/predict-flood`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    rain_intensity: params.rain,
    current_imperviousness: params.imperviousness,
    intervention_type: params.intervention
  })
});

const data = await response.json();
const avoidedLoss = data.data.analysis.avoided_loss;
```

---

**Backend Status:** ✅ 100% Working  
**Next Step:** Debug frontend code using steps above  
**Need Help:** Share Network tab screenshots and console errors
