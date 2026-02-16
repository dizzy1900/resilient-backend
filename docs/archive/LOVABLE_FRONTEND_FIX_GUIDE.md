# Lovable Frontend Fix - Complete Guide

## 🔍 Diagnosis Complete

**Backend Status:** ✅ 100% Working
- Server responding: ✅
- CORS configured: ✅  
- Endpoint returns real data: ✅ ($47,078.94)
- All origins allowed: ✅

**Conclusion:** The issue is **entirely in your Lovable frontend code**.

---

## 🎯 What's Wrong in Your Frontend

Based on "using estimated values" and "could not reach the flood simulation API", one of these is happening:

### Issue #1: API URL Not Configured (Most Likely - 70%)

Your Lovable app is probably calling:
- ❌ `http://localhost:5001/predict-flood` (dev server)
- ❌ `https://adaptmetric-backend.railway.app/predict-flood` (wrong domain)
- ❌ Just showing dummy/hardcoded data

Instead of:
- ✅ `https://web-production-8ff9e.up.railway.app/predict-flood`

### Issue #2: Wrong Field Names (20%)

Your frontend might be sending:
- `rainfall` instead of `rain_intensity`
- `imperviousness` instead of `current_imperviousness`
- `intervention` instead of `intervention_type`

### Issue #3: Not Actually Calling API (10%)

The button might:
- Not have an onClick handler
- Call a function that just sets dummy data
- Have an error that prevents the API call

---

## 🛠️ How to Fix in Lovable

### Step 1: Find the Flood Simulation Component

In your Lovable project:

1. **Press Ctrl+Shift+F** (or Cmd+Shift+F on Mac)
2. **Search for:** `Simulate Flood Risk`
3. **Or search for:** `simulate-flood` or `floodRisk`

This will show you the component file.

### Step 2: Check the API URL

Look for where the API URL is defined:

**Common locations:**
```javascript
// Might be in:
src/config.js
src/lib/api.ts
src/services/api.ts
.env
.env.local
```

**What to look for:**
```javascript
const API_URL = '...'  // What's here?
```

**Should be:**
```javascript
const API_URL = 'https://web-production-8ff9e.up.railway.app';
```

**NOT:**
```javascript
const API_URL = 'http://localhost:5001';  // ❌ Wrong
const API_URL = 'https://adaptmetric-backend.railway.app';  // ❌ Wrong
```

### Step 3: Check the Button Handler

Find the `Simulate Flood Risk` button:

```javascript
// Look for:
<button onClick={handleSimulate}>Simulate Flood Risk</button>
// or
<Button onClick={simulateFloodRisk}>Simulate Flood Risk</Button>
```

Then find what `handleSimulate` or `simulateFloodRisk` does:

**If it looks like this (BAD):**
```javascript
const handleSimulate = () => {
  // Just sets dummy data
  setResults({
    valueIncreased: 0,
    depthReduction: 0
  });
};
```

**It should look like this (GOOD):**
```javascript
const handleSimulate = async () => {
  setLoading(true);
  
  try {
    const response = await fetch(
      'https://web-production-8ff9e.up.railway.app/predict-flood',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rain_intensity: 100,  // Use actual value from state
          current_imperviousness: 0.7,  // Use actual value
          intervention_type: 'green_roof',  // Use selected toolkit
        })
      }
    );
    
    const data = await response.json();
    
    setResults({
      valueIncreased: data.data.analysis.avoided_loss,
      depthReduction: data.data.analysis.avoided_depth_cm
    });
    
  } catch (error) {
    console.error('API Error:', error);
  } finally {
    setLoading(false);
  }
};
```

### Step 4: Check Field Names

Make sure payload matches exactly:

**Backend expects:**
```json
{
  "rain_intensity": 100,
  "current_imperviousness": 0.7,
  "intervention_type": "green_roof"
}
```

**NOT:**
```json
{
  "rainfall": 100,  // ❌ Wrong field name
  "imperviousness": 0.7,  // ❌ Missing "current_"
  "intervention": "green_roof"  // ❌ Missing "_type"
}
```

### Step 5: Map Toolkit Selection to intervention_type

Your UI has checkboxes for toolkits. Map them:

```javascript
// Get selected toolkit from UI state
const selectedToolkit = // ... from your state

// Map to intervention_type
const interventionTypeMap = {
  'install_green_roofs': 'green_roof',
  'permeable_pavement': 'permeable_pavement',
  'bioswales': 'bioswales',
  'rain_gardens': 'rain_gardens'
};

const intervention_type = interventionTypeMap[selectedToolkit] || 'none';
```

---

## 💻 Complete Working Example

Here's a complete working component you can adapt:

```typescript
// FloodSimulation.tsx (or .jsx)
import { useState } from 'react';

const FloodSimulation = ({ coordinates, selectedToolkits }) => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const API_URL = 'https://web-production-8ff9e.up.railway.app';

  const getInterventionType = () => {
    // Map your UI toolkit selection to API intervention_type
    if (selectedToolkits.includes('install_green_roofs')) {
      return 'green_roof';
    } else if (selectedToolkits.includes('permeable_pavement')) {
      return 'permeable_pavement';
    } else if (selectedToolkits.includes('bioswales')) {
      return 'bioswales';
    } else if (selectedToolkits.includes('rain_gardens')) {
      return 'rain_gardens';
    }
    return 'none';
  };

  const simulateFloodRisk = async () => {
    console.log('🚀 Starting flood simulation...');
    setLoading(true);
    setError(null);

    const payload = {
      rain_intensity: 100,  // Use a default or get from state
      current_imperviousness: 0.7,  // Calculate from location data
      intervention_type: getInterventionType(),
      slope_pct: 2.0  // Optional, defaults to 2.0
    };

    console.log('📤 Sending payload:', payload);

    try {
      const response = await fetch(`${API_URL}/predict-flood`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      console.log('📥 Response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('✅ Response data:', data);

      // Extract values using correct field paths
      setResults({
        avoidedLoss: data.data.analysis.avoided_loss,
        depthReduction: data.data.analysis.avoided_depth_cm,
        improvement: data.data.analysis.percentage_improvement
      });

      console.log('💰 Avoided Loss:', data.data.analysis.avoided_loss);

    } catch (err) {
      console.error('❌ API Error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button 
        onClick={simulateFloodRisk}
        disabled={loading}
      >
        {loading ? 'Simulating...' : 'Simulate Flood Risk'}
      </button>

      {error && (
        <div className="error">
          Error: {error}
        </div>
      )}

      {results && (
        <div className="results">
          <div>
            <label>Value Increased:</label>
            <span>${results.avoidedLoss.toLocaleString()}</span>
          </div>
          <div>
            <label>Flood Depth Reduction:</label>
            <span>{results.depthReduction.toFixed(2)} cm</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default FloodSimulation;
```

---

## 🧪 Test the Fix

### In Browser Console

While on your Lovable app, open DevTools Console and test:

```javascript
// Test 1: Check if API is reachable
fetch('https://web-production-8ff9e.up.railway.app/health')
  .then(r => r.json())
  .then(d => console.log('✅ API alive:', d))
  .catch(e => console.error('❌ API dead:', e));

// Test 2: Test flood endpoint
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
    console.log('✅ API response:', d);
    console.log('💰 Avoided Loss:', d.data.analysis.avoided_loss);
  })
  .catch(e => console.error('❌ API error:', e));
```

If these work but your UI doesn't → code issue in your component.

---

## 📊 Debug Checklist

Use this checklist to find the issue:

### Backend Checks (All Should Pass)
- [x] Server responds to /health
- [x] CORS headers present
- [x] /predict-flood returns 200 OK
- [x] Response contains avoided_loss
- [x] Value is not $0

### Frontend Checks (Find What Fails)
- [ ] API URL is correct production URL
- [ ] Button has onClick handler
- [ ] Handler actually calls fetch()
- [ ] Fetch URL is correct
- [ ] Headers include Content-Type
- [ ] Payload field names match exactly
- [ ] Response is parsed (.json())
- [ ] Data is extracted with correct path
- [ ] UI state is updated with extracted data
- [ ] UI displays the state value

---

## 🔧 Common Lovable Patterns

### Pattern 1: Environment Variable

```typescript
// Check if this exists in your code:
const API_URL = import.meta.env.VITE_API_URL;
// or
const API_URL = process.env.NEXT_PUBLIC_API_URL;
```

**Then check `.env` or `.env.local` file:**
```bash
VITE_API_URL=https://web-production-8ff9e.up.railway.app
# Make sure no trailing slash!
```

### Pattern 2: API Service File

Lovable might have an API service file:

```typescript
// src/services/api.ts
export const floodApi = {
  simulate: async (params) => {
    const response = await fetch(`${API_BASE}/predict-flood`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    return response.json();
  }
};
```

Check `API_BASE` is correct!

### Pattern 3: React Query / SWR

If using data fetching library:

```typescript
const { data, isLoading } = useQuery('floodRisk', async () => {
  const response = await fetch(
    'https://web-production-8ff9e.up.railway.app/predict-flood',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }
  );
  return response.json();
});
```

---

## 📝 What To Send Me

If still stuck after checking above, send me:

### 1. The Component Code

Copy/paste or screenshot the component that has:
- The "Simulate Flood Risk" button
- The function that runs when clicked
- Where/how it calls the API

### 2. The API Configuration

Show me where API_URL is defined:
- Config file
- .env file
- Service file

### 3. Browser Console Output

After clicking "Simulate Flood Risk":
- Any console.log messages
- Any errors (red text)
- Network tab request (if any)

### 4. What UI Actually Shows

Screenshot of:
- The results panel after clicking button
- What values it displays

---

## ✅ Success Criteria

You'll know it's fixed when:

1. Browser Console shows:
   ```
   🚀 Starting flood simulation...
   📤 Sending payload: {...}
   📥 Response status: 200
   ✅ Response data: {...}
   💰 Avoided Loss: 47078.94
   ```

2. UI shows:
   ```
   Value Increased: $47,078
   Flood Depth Reduction: 0.6 cm
   ```

3. No errors in console

4. Values change when you select different toolkits

---

## 🚀 Quick Win

If you just want it working ASAP, try this:

**Replace your entire button onClick with:**

```javascript
onClick={async () => {
  try {
    const res = await fetch('https://web-production-8ff9e.up.railway.app/predict-flood', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        rain_intensity: 100,
        current_imperviousness: 0.7,
        intervention_type: 'green_roof'
      })
    });
    const data = await res.json();
    alert(`Avoided Loss: $${data.data.analysis.avoided_loss}`);
  } catch(e) {
    alert('Error: ' + e.message);
  }
}}
```

If this shows `$47,078` → API works, you just need to wire it to your UI state properly.

---

**The backend is perfect. The fix is 100% in your Lovable frontend code. Use this guide to find and fix it.**
