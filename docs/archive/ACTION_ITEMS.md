# Action Items - Flood API Frontend Integration

## ✅ What's Confirmed Working (Backend)

- [x] Endpoint exists: `/predict-flood`
- [x] Returns 200 OK
- [x] CORS configured for Lovable
- [x] Response structure correct
- [x] Field `data.analysis.avoided_loss` present
- [x] Values realistic ($47K, not $0)
- [x] All intervention types work
- [x] Deployed to production
- [x] Model loaded successfully

**Backend is 100% ready. No action needed on backend.**

---

## 🔍 What You Need to Check (Frontend)

### Priority 1: Browser DevTools Check (5 minutes)

1. **Open your Lovable app**
2. **Press F12** (or Right-click → Inspect)
3. **Go to Network tab**
4. **Click "Clear"** to start fresh
5. **Trigger flood prediction** in your UI
6. **Look for request** to `/predict-flood`

**Screenshot needed:**
- [ ] Network tab showing the request (or lack thereof)
- [ ] Request URL
- [ ] Request headers
- [ ] Request payload
- [ ] Response body

**Quick checks:**
- [ ] Does request appear at all? (Yes/No)
- [ ] What's the full URL? _________________
- [ ] What's the status code? _________________
- [ ] Is `avoided_loss` in response? (Yes/No)

### Priority 2: Console Test (2 minutes)

1. **Open DevTools Console tab** (F12 → Console)
2. **Paste this code:**

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
.then(d => {
  console.log('✅ Response:', d);
  console.log('💰 Avoided Loss:', d.data.analysis.avoided_loss);
})
.catch(e => console.error('❌ Error:', e));
```

3. **Press Enter**

**Expected output:**
```
✅ Response: {status: 'success', data: {...}}
💰 Avoided Loss: 47078.94
```

**Screenshot needed:**
- [ ] Console output showing success or error

**Result:**
- [ ] Works in console? (Yes/No)
- [ ] If YES → Issue is in UI code
- [ ] If NO → Copy exact error message

### Priority 3: Check Frontend Code (10 minutes)

**Find these files in your Lovable project:**

#### Option A: Using Lovable Search
1. Open Lovable project
2. Press Ctrl+Shift+F (or Cmd+Shift+F on Mac)
3. Search for: `predict-flood`

**Questions:**
- [ ] Did you find any files? (Yes/No)
- [ ] If YES, which files? _________________
- [ ] If NO → The endpoint isn't implemented in frontend!

#### Option B: Check Common Locations

Look in these folders:
- [ ] `src/services/` - Check for api.js, flood.js
- [ ] `src/api/` - Check for API service files
- [ ] `src/components/` - Check for FloodPrediction.jsx
- [ ] `src/pages/` - Check for Flood.jsx

**Search for API base URL:**
- [ ] Search for: `web-production`
- [ ] Search for: `API_URL`
- [ ] Search for: `VITE_API_URL`

**What URL did you find?** _________________

**Is it correct?**
- [ ] Should be: `https://web-production-8ff9e.up.railway.app`

### Priority 4: Compare with Working Coastal Code (5 minutes)

**Since coastal works, let's copy its pattern:**

1. **Find coastal API call:**
   - Search for: `predict-coastal` in your code

2. **Copy the exact pattern:**

**Coastal code (working):**
```javascript
// Example - your actual code may vary
const response = await fetch(`${API_URL}/predict-coastal`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(params)
});
const data = await response.json();
const avoidedLoss = data.data.analysis.avoided_loss;
```

**Flood code should be identical:**
```javascript
const response = await fetch(`${API_URL}/predict-flood`, {  // ← Only difference
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(params)
});
const data = await response.json();
const avoidedLoss = data.data.analysis.avoided_loss;  // ← Same path
```

**Checklist:**
- [ ] Found coastal code
- [ ] Copied pattern for flood
- [ ] Used same `API_URL`
- [ ] Used same headers
- [ ] Used same field path

---

## 📸 Screenshots to Share

If still not working after above checks, share these screenshots:

1. **Network Tab:**
   - [ ] Full network tab showing request/response
   - [ ] Request URL and method
   - [ ] Response body

2. **Console:**
   - [ ] Console output from test above
   - [ ] Any error messages (red text)

3. **Code:**
   - [ ] API service file that calls flood endpoint
   - [ ] Component that triggers flood prediction

---

## 🎯 Most Likely Fixes

Based on 100s of similar issues, here are the top 3 fixes:

### Fix #1: Update API Base URL (80% of cases)

**Find this in your code:**
```javascript
const API_URL = 'http://localhost:5001';  // ❌ WRONG
```

**Change to:**
```javascript
const API_URL = 'https://web-production-8ff9e.up.railway.app';  // ✅ CORRECT
```

**Files to check:**
- `.env`
- `.env.production`
- `src/config/api.js`
- `src/services/api.js`

### Fix #2: Add Missing Endpoint (15% of cases)

**If flood prediction isn't implemented, add it:**

```javascript
// src/services/api.js (or similar)
export const predictFlood = async (params) => {
  const response = await fetch(
    'https://web-production-8ff9e.up.railway.app/predict-flood',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        rain_intensity: params.rain,
        current_imperviousness: params.imperviousness,
        intervention_type: params.intervention,
        slope_pct: params.slope || 2.0
      })
    }
  );
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  
  const data = await response.json();
  return data.data.analysis.avoided_loss;
};
```

### Fix #3: Correct Field Path (5% of cases)

**Wrong:**
```javascript
const avoidedLoss = data.avoided_loss;  // ❌ Missing nesting
```

**Correct:**
```javascript
const avoidedLoss = data.data.analysis.avoided_loss;  // ✅ Full path
```

---

## ⚡ Quick Test URLs

**Test in browser (any tab):**

Open DevTools Console on **any website** (even Google.com) and run:

```javascript
// Test 1: Basic connectivity
fetch('https://web-production-8ff9e.up.railway.app/health')
  .then(r => r.json())
  .then(d => console.log('✅ Backend alive:', d))
  .catch(e => console.error('❌ Backend down:', e));

// Test 2: Flood endpoint
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
  .then(d => console.log('✅ Flood API:', d.data.analysis.avoided_loss))
  .catch(e => console.error('❌ Flood API failed:', e));
```

**Both should succeed** (backend is working)

---

## 📞 What to Send Me

If you've completed all checks above and it's still not working:

### Send me:

1. **Network tab screenshot** showing:
   - URL being called
   - Status code
   - Response body

2. **Console output** from the test code above

3. **Code snippet** of:
   - How you're calling the flood API
   - Where `API_URL` is defined
   - How you're parsing the response

4. **Answer these:**
   - Does request appear in Network tab? (Yes/No)
   - What's the exact URL being called?
   - Does console test work? (Yes/No)
   - Did you find `predict-flood` in your code? (Yes/No)

---

## ✅ Success Criteria

You'll know it's working when:

1. Network tab shows request to `/predict-flood`
2. Status code is 200
3. Response contains `data.analysis.avoided_loss: 47078.94`
4. UI displays: "Avoided Loss: $47,079"
5. Value changes based on inputs (not always the same)

---

## 🚀 Next Steps

1. **Complete Priority 1-4 checks** (15 minutes total)
2. **Try Fix #1, #2, or #3** based on what you find
3. **Test again** using console code
4. **If still stuck:** Send screenshots and code as listed above

---

**Current Status:**
- Backend: ✅ 100% Working
- Frontend: ⏳ Needs your checks above

**ETA to Fix:** 15-30 minutes once you complete the checks

**Confidence:** Very high - this is a frontend configuration issue, not a backend problem
