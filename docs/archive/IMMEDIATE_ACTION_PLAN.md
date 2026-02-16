# Immediate Action Plan - Fix Lovable Frontend

## 🎯 The Problem

**Backend:** ✅ Working perfectly (tested and verified)
**Frontend:** ❌ Not calling API or using wrong configuration

**You need to fix the Lovable frontend code.**

---

## ⚡ Do This RIGHT NOW (5 minutes)

### Step 1: Test API from Browser Console (2 min)

1. **Open your Lovable app** in browser
2. **Press F12** to open DevTools
3. **Go to Console tab**
4. **Paste this code and press Enter:**

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
  console.log('✅ SUCCESS!');
  console.log('💰 Avoided Loss: $' + d.data.analysis.avoided_loss);
  alert('API WORKS! Avoided Loss: $' + d.data.analysis.avoided_loss);
})
.catch(e => {
  console.error('❌ FAILED:', e);
  alert('API FAILED: ' + e.message);
});
```

**Expected:** Alert showing "API WORKS! Avoided Loss: $47078.94"

**If this works:**
→ API is fine, issue is in your Lovable component code

**If this fails:**
→ Screenshot the error and send to me

---

### Step 2: Find Your Lovable Code (3 min)

#### Option A: Using Lovable Editor

1. **In Lovable**, press **Ctrl+Shift+F** (or Cmd+Shift+F)
2. **Search for:** `Simulate Flood Risk`
3. **Click on the result** to open the component
4. **Find the button** that says "Simulate Flood Risk"
5. **Look at what happens** when you click it

**Send me a screenshot of the onClick function**

#### Option B: Check Files Directly

Look in these files (Lovable project structure):
- `src/components/FloodSimulation.tsx`
- `src/pages/index.tsx`
- `src/lib/api.ts`

**Find:**
- Where "Simulate Flood Risk" button is
- What function runs onClick
- Where API URL is defined

---

## 🔍 What to Look For

### Check #1: API URL

**Search your code for:**
- `localhost`
- `railway.app`
- `API_URL`
- `VITE_`

**It should be:**
```javascript
const API_URL = 'https://web-production-8ff9e.up.railway.app';
```

**NOT:**
```javascript
const API_URL = 'http://localhost:5001';  // ❌
const API_URL = 'https://adaptmetric-backend.railway.app';  // ❌
```

### Check #2: Button Handler

**The button onClick should:**
1. Call `fetch()` or `axios.post()`
2. Use correct URL ending in `/predict-flood`
3. Send JSON payload
4. Parse response with `.json()`
5. Update state with the result

**If it just does this:**
```javascript
onClick={() => setResults({ value: 0 })}
```
→ That's the problem! It's not calling the API at all.

### Check #3: Field Names

**Payload must have:**
- `rain_intensity` (NOT `rainfall`)
- `current_imperviousness` (NOT `imperviousness`)
- `intervention_type` (NOT `intervention`)

---

## 💊 Quick Fix Options

### Option 1: Add Console Logs

**In your Lovable component, add logs:**

```javascript
const handleSimulate = async () => {
  console.log('🚀 Button clicked!');
  
  const url = 'https://web-production-8ff9e.up.railway.app/predict-flood';
  console.log('📍 URL:', url);
  
  const payload = {
    rain_intensity: 100,
    current_imperviousness: 0.7,
    intervention_type: 'green_roof'
  };
  console.log('📤 Payload:', payload);
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    console.log('📥 Status:', response.status);
    
    const data = await response.json();
    console.log('✅ Data:', data);
    console.log('💰 Avoided Loss:', data.data.analysis.avoided_loss);
    
    // Update your UI here
    setResults({
      value: data.data.analysis.avoided_loss,
      depth: data.data.analysis.avoided_depth_cm
    });
    
  } catch (error) {
    console.error('❌ Error:', error);
  }
};
```

**Then:**
1. Click "Simulate Flood Risk"
2. Check console for the logs
3. Screenshot what you see

### Option 2: Replace Component Code

If you can edit the component, replace the entire onClick with this working version:

```typescript
const FloodSimulation = () => {
  const [result, setResult] = useState(null);
  
  const simulateFlood = async () => {
    try {
      const response = await fetch(
        'https://web-production-8ff9e.up.railway.app/predict-flood',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            rain_intensity: 100,
            current_imperviousness: 0.7,
            intervention_type: 'green_roof'
          })
        }
      );
      
      const data = await response.json();
      setResult(data.data.analysis);
      
    } catch (error) {
      console.error('Error:', error);
      alert('API Error: ' + error.message);
    }
  };
  
  return (
    <div>
      <button onClick={simulateFlood}>
        Simulate Flood Risk
      </button>
      
      {result && (
        <div>
          <div>Value: ${result.avoided_loss.toLocaleString()}</div>
          <div>Depth: {result.avoided_depth_cm} cm</div>
        </div>
      )}
    </div>
  );
};
```

---

## 📊 Debugging Decision Tree

```
Can you find the component code?
├─ YES
│  └─ Does it call fetch() or axios?
│     ├─ YES
│     │  └─ Check URL is correct
│     │     └─ Check field names match
│     │        └─ Check response parsing
│     └─ NO → That's the problem! Add API call
│
└─ NO
   └─ Run browser console test
      ├─ Works → Code exists but wrong
      └─ Fails → Share error with me
```

---

## 📸 What to Send Me

**I need to see:**

1. **Browser console test result**
   - Run the console code from Step 1
   - Screenshot showing success or error

2. **Component code**
   - The file with "Simulate Flood Risk" button
   - The onClick function
   - Where API_URL is defined

3. **Console logs after clicking button**
   - DevTools Console tab
   - After clicking "Simulate Flood Risk"
   - Any red errors or logs

4. **Network tab**
   - DevTools Network tab
   - Filter by "predict"
   - After clicking button
   - Show if request appears

**With these 4 screenshots, I can give you the exact fix.**

---

## ⏰ Timeline

- **2 minutes:** Run browser console test
- **3 minutes:** Find component code
- **5 minutes:** Add console logs or fix
- **Total:** 10 minutes to identify exact issue

---

## 🎁 Bonus: Environment Variable Method

If Lovable uses environment variables:

1. **Create `.env.local` file** in project root:
```bash
VITE_API_URL=https://web-production-8ff9e.up.railway.app
```

2. **Use in code:**
```javascript
const API_URL = import.meta.env.VITE_API_URL;
```

3. **Restart dev server** (Lovable might need refresh)

---

## ✅ Success Checklist

Mark these as you complete them:

- [ ] Ran browser console test (Step 1)
- [ ] Found "Simulate Flood Risk" button in code
- [ ] Checked API URL is correct production URL
- [ ] Verified onClick function exists
- [ ] Confirmed it calls fetch() or similar
- [ ] Added console.log statements
- [ ] Clicked button and checked console
- [ ] Saw logs showing API call
- [ ] Got response with $47,078 value
- [ ] UI updated with real value

---

## 🆘 Still Stuck?

**Send me:**
1. ✅ Browser console test result (screenshot)
2. ✅ Component code (screenshot or paste)
3. ✅ Console after clicking button (screenshot)
4. ✅ Network tab (screenshot)

**I'll give you the exact fix within 5 minutes.**

---

**Bottom Line:**
- Backend works perfectly ✅
- Issue is 100% in frontend code ❌
- You need to find and share the frontend code
- Then I can give you exact fix

**Do Step 1 NOW and share result! →**
