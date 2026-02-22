# 🚀 Quick Start: ML Pipeline

## 3-Step Setup

### Step 1: Install ML Dependencies (One-time)

```bash
cd backend
pip install -r requirements-ml.txt
```

**What this does:** Installs sentence-transformers and PyTorch for ML ingredient matching.

**Time:** ~2-3 minutes (downloads ~200MB)

### Step 2: Start Backend

```bash
cd backend
python start_backend.py
```

**What to look for:** Backend starts on `http://localhost:8000`

### Step 3: Start Frontend

```bash
cd frontend
npm start
```

**What to look for:** Frontend opens at `http://localhost:3000`

## Using the ML Pipeline

### In the UI:

1. **Navigate** to Diet Plans page
2. **Select** Daily or Weekly plan type
3. **Click** the **purple "🧠 Generate Plan (ML)"** button
4. **Wait** 2-5 seconds (daily) or 15-30 seconds (weekly)
5. **View** your ML-generated plan!

### What You'll See:

```
┌─────────────────────────────────────────┐
│  Choose Your Diet Plan Type             │
├─────────────────────────────────────────┤
│                                         │
│  ○ Daily Plan    ○ Weekly Plan         │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 🤖 Generate Daily Plan (AI)      │ │  ← Existing (Blue)
│  │ Uses GenAI for creative meals    │ │
│  └───────────────────────────────────┘ │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ 🧠 Generate Daily Plan (ML) [NEW]│ │  ← NEW (Purple)
│  │ Uses ML templates + deterministic│ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Differences at a Glance

| Feature | AI Button (Blue) | ML Button (Purple) |
|---------|------------------|-------------------|
| **Speed** | Medium | Fast ⚡ |
| **Variety** | High | Medium |
| **Predictability** | Medium | High |
| **Creativity** | High | Medium |
| **Best For** | Exploring new meals | Consistent planning |

## Troubleshooting

### "sentence_transformers not found"
```bash
pip install sentence-transformers torch
```

### "No active health context"
Complete your profile setup first (Profile Setup page)

### Backend won't start
Check if port 8000 is already in use

### Frontend won't start
Check if port 3000 is already in use

## Testing

### Quick Test (No UI needed):

```bash
cd backend
python test_ml_pipeline.py
```

Expected output:
```
✅ All ML pipeline modules imported successfully
✅ Loaded 17 meal templates
✅ ML Pipeline Basic Tests Complete!
```

### API Test:

```bash
curl -X POST http://localhost:8000/api/v1/diet-plans-ml/daily \
  -H "Content-Type: application/json" \
  -H "X-User-Id: f53f6cb3-4b52-47ca-9cdb-bb61ece32610" \
  -d '{}'
```

## What's Happening Behind the Scenes

When you click "Generate Plan (ML)":

1. **Template Selection** - ML picks best meal templates for your diet
2. **Nutrition Calculation** - Backend calculates accurate nutrition
3. **Portion Scaling** - Math-only scaling to meet your targets
4. **Validation** - Rules-based safety checks
5. **Text Generation** - Creates meal names and instructions
6. **Save & Return** - Stores plan and shows it to you

**No AI retries** - Fast and deterministic!

## Logs to Watch

Open backend terminal and look for:

```
[ML_PIPELINE_INIT] request_id=ml_daily_... ← Started
[ML_STEP_1] Template selection              ← Step 1
[ML_STEP_2] Nutrition calculation           ← Step 2
[ML_STEP_3] Portion scaling                 ← Step 3
[ML_STEP_4] Validation                      ← Step 4
[ML_STEP_5] Text generation                 ← Step 5
[ML_PIPELINE_SUCCESS] request_id=...        ← Done! ✅
```

## Performance

- **First request:** 10-15 seconds (model loading)
- **Subsequent requests:** 2-5 seconds (daily), 15-30 seconds (weekly)
- **Memory usage:** ~500MB for ML model

## Next Steps

1. ✅ Try both AI and ML buttons
2. ✅ Compare the results
3. ✅ Share feedback on which you prefer
4. ✅ Report any issues

## Need Help?

1. Check `ML_PIPELINE_COMPLETE.md` for full documentation
2. Check `ML_PIPELINE_SETUP.md` for detailed setup
3. Run `python test_ml_pipeline.py` to verify installation
4. Check backend logs for error messages

**That's it! You're ready to use the ML pipeline! 🎉**
