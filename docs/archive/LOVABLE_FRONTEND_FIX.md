# Lovable Frontend Fix - Flood Simulation

## Issue Identified

✅ **Console test works** → Backend API is accessible
❌ **UI shows dummy values** → Frontend code not calling API or not displaying results

## What We Know

Based on your screenshot and console test:

1. ✅ Backend API responds correctly
2. ✅ Browser can reach the API (no CORS issues)
3. ✅ Console fetch returns: `avoided_loss: 47078.94`
4. ❌ UI shows: `$0.00` for "Value Increased"
5. ❌ UI shows: `0 cm` for "Flood Depth Reduction"

**Conclusion:** The "Simulate Flood Risk" button is NOT calling the API or NOT updating the UI with API results.

---

## Root Cause Analysis

Looking at your UI, I can see:
- Left panel: "Simulate Flood Risk" button
- Selected coordinates: `-33.924142, 18.524361` (Cape Town)
- Sponge City Toolkit options selected
- Results panel shows: `$0.00` value increased, `0 cm` flood depth reduction

**The issue is one of these:**

### Option A: Button Not Wired to API (Most Likely)
The "Simulate Flood Risk" button might be:
- Showing hardcoded dummy data
- Not calling the flood API at all
- Calling API but not updating UI with results

### Option B: Using Wrong Parameters
The UI might be:
- Sending parameters in wrong format
- Missing required fields (intervention_type, rain_intensity, etc.)
- Getting error response (400/500) but not showing it

### Option C: Display Logic Issue
The API call might work, but:
- Results not mapped to UI fields
- Using wrong field paths to extract values
- State not updating after API response

---

## How to Debug in Lovable

### Step 1: Check Network Tab for API Calls

From your screenshot, I need to see:

1. **Filter the Network tab:**
   - Type "predict" in the filter box
   - Click "Simulate Flood Risk" button
   - Look for a request to `/predict-flood`

2. **Check if request appears:**
   - ✅ If YES → Click on it, check Request/Response tabs
   - ❌ If NO → Button is not calling API (Option A)

**What to screenshot:**
- Network tab after clicking "Simulate Flood Risk"
- Any request to `/predict-flood` (or lack thereof)
- If request exists: Request Headers, Payload, Response tabs

### Step 2: Check Browser Console for Errors

After clicking "Simulate Flood Risk":

1. Open Console tab (next to Network)
2. Look for any red errors
3. Look for any API-related logs

**Common errors to look for:**
- `TypeError: Cannot read property...`
- `Failed to fetch`
- `400 Bad Request`
- `Missing required fields`

### Step 3: Find the Button Code in Lovable

In your Lovable project:

1. **Find the Simulate Flood Risk component:**
   - Search for: "Simulate Flood Risk"
   - Or search for: `simulate-flood` or `SimulateFloodRisk`

2. **Check what it does:**
   ```javascript
   // Look for something like:
   const handleSimulate = () => {
     // Does it call an API?
     // Or does it just set dummy data?
   };
   ```

3. **Check for API integration:**
   - Search for: `predict-flood` in your project
   - Search for: `flood` in `src/services/` or `src/api/`

---

## Most Likely Issues & Fixes

### Issue #1: Hardcoded Dummy Data (80% probability)

**Current code might look like:**
```javascript
const FloodSimulation = () => {
  const [results, setResults] = useState({
    valueIncreased: 0,      // ← Hardcoded!
    floodDepthReduction: 0  // ← Hardcoded!
  });

  const handleSimulate = () => {
    // Just sets dummy data, doesn't call API
    setResults({
      valueIncreased: 0,
      floodDepthReduction: 0
    });
  };
  
  return <div>{results.valueIncreased}</div>;
};
```

**Fix:**
```javascript
const FloodSimulation = () => {
  const [results, setResults] = useState({
    valueIncreased: 0,
    floodDepthReduction: 0
  });
  const [loading, setLoading] = useState(false);

  const handleSimulate = async () => {
    setLoading(true);
    
    try {
      const response = await fetch(
        'https://web-production-8ff9e.up.railway.app/predict-flood',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            rain_intensity: 100,  // Use actual value from form
            current_imperviousness: 0.7,  // Use actual value
            intervention_type: 'green_roof',  // Use selected toolkit
            slope_pct: 2.0
          })
        }
      );

      const data = await response.json();
      
      // Update UI with real values
      setResults({
        valueIncreased: data.data.analysis.avoided_loss,
        floodDepthReduction: data.data.analysis.avoided_depth_cm
      });
    } catch (error) {
      console.error('Flood API error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleSimulate} disabled={loading}>
        {loading ? 'Simulating...' : 'Simulate Flood Risk'}
      </button>
      <div>Value Increased: ${results.valueIncreased.toLocaleString()}</div>
      <div>Flood Depth Reduction: {results.floodDepthReduction} cm</div>
    </div>
  );
};
```

### Issue #2: Missing Parameter Mapping

The UI needs to map selected options to API parameters:

**Sponge City Toolkit Options → intervention_type:**
- "Install Green Roofs" → `green_roof`
- "Permeable Pavement" → `permeable_pavement`
- (Other options need to be mapped)

**Example mapping:**
```javascript
const TOOLKIT_TO_INTERVENTION = {
  'install_green_roofs': 'green_roof',
  'permeable_pavement': 'permeable_pavement',
  'bioswales': 'bioswales',
  'rain_gardens': 'rain_gardens'
};

// In your API call:
const selectedToolkit = getSelectedToolkit(); // From UI state
const intervention = TOOLKIT_TO_INTERVENTION[selectedToolkit] || 'none';

const payload = {
  rain_intensity: 100,  // Could be calculated or user input
  current_imperviousness: 0.7,  // Could be from location data
  intervention_type: intervention,
  slope_pct: 2.0
};
```

### Issue #3: Rain Intensity Not Set

The flood model requires `rain_intensity` (10-150 mm/hr). Your UI might not have this input.

**Options:**

**A. Use default value:**
```javascript
const payload = {
  rain_intensity: 100,  // Default moderate rain
  current_imperviousness: 0.7,
  intervention_type: selectedIntervention
};
```

**B. Add rain intensity slider to UI:**
```javascript
<input 
  type="range" 
  min="10" 
  max="150" 
  value={rainIntensity}
  onChange={(e) => setRainIntensity(e.target.value)}
/>
<label>Rain Intensity: {rainIntensity} mm/hr</label>
```

**C. Calculate from location (advanced):**
```javascript
// Could fetch historical rainfall data for selected location
// Then use that as rain_intensity
```

---

## Quick Fix Template

Here's a complete working example you can adapt:

```javascript
// FloodSimulation.jsx (or similar component)
import { useState } from 'react';

const FloodSimulation = ({ selectedCoordinates, selectedToolkits }) => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Map toolkit selections to intervention types
  const getInterventionType = () => {
    if (selectedToolkits.includes('install_green_roofs')) {
      return 'green_roof';
    } else if (selectedToolkits.includes('permeable_pavement')) {
      return 'permeable_pavement';
    }
    // Add other mappings
    return 'none';
  };

  const simulateFloodRisk = async () => {
    setLoading(true);
    setError(null);

    try {
      const payload = {
        rain_intensity: 100,  // Default or from input
        current_imperviousness: 0.7,  // Could calculate from land use
        intervention_type: getInterventionType(),
        slope_pct: 2.0  // Default or from terrain data
      };

      console.log('Calling flood API with:', payload);

      const response = await fetch(
        'https://web-production-8ff9e.up.railway.app/predict-flood',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Flood API response:', data);

      setResults({
        avoidedLoss: data.data.analysis.avoided_loss,
        depthReduction: data.data.analysis.avoided_depth_cm,
        improvement: data.data.analysis.percentage_improvement,
        recommendation: data.data.analysis.recommendation
      });

    } catch (err) {
      console.error('Flood simulation error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flood-simulation">
      <button 
        onClick={simulateFloodRisk}
        disabled={loading}
        className="simulate-button"
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
          <div className="result-item">
            <label>Value Increased:</label>
            <span>${results.avoidedLoss.toLocaleString()}</span>
          </div>
          <div className="result-item">
            <label>Flood Depth Reduction:</label>
            <span>{results.depthReduction.toFixed(2)} cm</span>
          </div>
          <div className="result-item">
            <label>Improvement:</label>
            <span>{results.improvement.toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default FloodSimulation;
```

---

## Testing the Fix

After implementing the fix:

1. **Click "Simulate Flood Risk" button**
2. **Check Network tab:**
   - Should see request to `/predict-flood`
   - Status: 200
   - Response contains real values

3. **Check UI updates:**
   - "Value Increased" should show: ~$47,000
   - "Flood Depth Reduction" should show: ~0.6 cm
   - Values should change based on selected toolkit

---

## What I Need from You

To provide more specific guidance:

### 1. Network Tab After Button Click

Click "Simulate Flood Risk" and screenshot:
- Network tab filtered by "predict"
- Show if `/predict-flood` request appears
- If it appears, show the Request and Response tabs

### 2. Share the Component Code

In Lovable, find and share:
- The component with "Simulate Flood Risk" button
- The function that runs when button is clicked
- Any API service files in `src/services/` or `src/api/`

### 3. Console Errors

After clicking "Simulate Flood Risk":
- Any red errors in console
- Any warnings or logs

---

## Expected Behavior After Fix

**Before Fix:**
- Click "Simulate Flood Risk"
- Shows: $0.00 value increased, 0 cm reduction
- No network request visible

**After Fix:**
- Click "Simulate Flood Risk"
- Network request to `/predict-flood` appears
- Status: 200 OK
- UI updates to: ~$47,000 value increased, ~0.6 cm reduction
- Values change based on selected toolkit and parameters

---

## Summary

**The Problem:**
Your Lovable frontend "Simulate Flood Risk" button is not calling the backend API. It's either showing hardcoded zeros or not implemented yet.

**The Solution:**
Add API call to the button's onClick handler using the template above.

**The Test:**
Console fetch works → proves API is ready → just need to wire it to the button.

**Next Step:**
1. Click "Simulate Flood Risk"
2. Screenshot Network tab
3. Share any component code you can find
4. I'll provide exact code to paste in Lovable

---

**Status:**
- ✅ Backend API: Working
- ✅ Browser Access: Working  
- ❌ UI Integration: Not wired up yet
- ⏱️ ETA: 10-15 minutes once code is shared
