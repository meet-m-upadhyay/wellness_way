# ML Pipeline Setup Guide

## Quick Start

### 1. Install ML Dependencies

```bash
cd backend
pip install -r requirements-ml.txt
```

This will install:
- `sentence-transformers` - For ML ingredient canonicalization
- `torch` - Required by sentence-transformers (CPU version)

**Note:** First run will download the ML model (~90MB). This happens automatically.

### 2. Restart Backend

```bash
python start_backend.py
```

### 3. Test ML Endpoints

The ML pipeline is now available at:
- `POST /api/v1/diet-plans-ml/daily` - Generate daily plan with ML
- `POST /api/v1/diet-plans-ml/weekly` - Generate weekly plan with ML

### 4. Use the UI

1. Navigate to Diet Plans page
2. Select Daily or Weekly plan type
3. Click the **"🧠 Generate Plan (ML)"** button (purple gradient)
4. The ML pipeline will generate your plan!

## What's Different?

### GenAI Pipeline (Existing - Blue Button)
- Uses LLM for meal creativity
- LLM suggests ingredients and portions
- Backend calculates nutrition
- Self-healing with retries
- More creative but less predictable

### ML Pipeline (NEW - Purple Button)
- Uses ML for ingredient matching
- Predefined meal templates
- Deterministic nutrition calculation
- NO AI retries
- More predictable and faster

## Architecture

```
User clicks "Generate Plan (ML)"
    ↓
Frontend calls /diet-plans-ml/daily or /diet-plans-ml/weekly
    ↓
ML Pipeline Orchestrator
    ↓
1. ML Template Selector (heuristic scoring)
    ↓
2. Nutrition Engine Adapter (deterministic calculation)
    ↓
3. Scaling Engine (math-only portion adjustment)
    ↓
4. Validation Engine (rules-only checks)
    ↓
5. Text Generator (constrained GenAI for names/instructions)
    ↓
Plan saved to database
    ↓
Returned to frontend
```

## Troubleshooting

### Model Download Issues

If the sentence-transformer model fails to download:

```bash
# Manual download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Import Errors

If you see `ModuleNotFoundError: No module named 'sentence_transformers'`:

```bash
pip install sentence-transformers torch
```

### Memory Issues

The ML model requires ~500MB RAM. If you have memory constraints:

1. The model loads lazily (only when first used)
2. Consider using a smaller model (edit `ingredient_canonicalizer.py`)

## Testing

### Test ML Endpoint Directly

```bash
# Test daily plan
curl -X POST http://localhost:8000/api/v1/diet-plans-ml/daily \
  -H "Content-Type: application/json" \
  -H "X-User-Id: YOUR_USER_ID" \
  -d '{}'

# Test weekly plan
curl -X POST http://localhost:8000/api/v1/diet-plans-ml/weekly \
  -H "Content-Type: application/json" \
  -H "X-User-Id: YOUR_USER_ID" \
  -d '{}'
```

### Check Logs

Look for these log prefixes:
- `[ML_PIPELINE_INIT]` - Pipeline started
- `[ML_PIPELINE_SUCCESS]` - Plan generated successfully
- `[ML_PIPELINE_FAILED]` - Generation failed
- `[ML_STEP_1]` through `[ML_STEP_5]` - Individual steps
- `[ING_CANONICALIZED]` - Ingredient matching
- `[TEMPLATE_SELECTED]` - Template selection
- `[SCALING_APPLIED]` - Portion scaling

## Performance

### Expected Response Times

- **Daily Plan:** 2-5 seconds
- **Weekly Plan:** 15-30 seconds (7 daily plans)

### First Request

The first request will be slower (~10-15 seconds) due to:
1. ML model loading
2. Model initialization
3. Embedding generation

Subsequent requests will be faster as the model stays in memory.

## Comparison: GenAI vs ML

| Feature | GenAI Pipeline | ML Pipeline |
|---------|---------------|-------------|
| **Creativity** | High | Medium |
| **Predictability** | Medium | High |
| **Speed** | Medium | Fast |
| **Retries** | Yes (up to 10) | No |
| **Variety** | High | Medium (15 templates) |
| **Nutrition Accuracy** | High | High |
| **Failure Handling** | Self-healing | Soft acceptance |
| **Dependencies** | OpenAI/Groq API | Local ML model |

## Next Steps

1. **Test both pipelines** - Compare quality and speed
2. **Collect feedback** - Which do users prefer?
3. **Monitor metrics** - Success rates, latency, errors
4. **Expand templates** - Add more meal templates
5. **Upgrade selector** - Replace heuristic with LightGBM

## Support

For issues or questions:
1. Check logs for error messages
2. Verify ML dependencies are installed
3. Ensure backend is running
4. Check network connectivity

## Future Enhancements

- [ ] Add more meal templates (target: 50+)
- [ ] Upgrade template selector to LightGBM
- [ ] Add user feedback loop
- [ ] Implement ingredient substitutions
- [ ] Add cuisine preferences
- [ ] Support meal prep mode
