# Quick Test Guide - ML Regeneration Buttons

## Prerequisites
- Backend running on port 8000
- Frontend running on port 3000
- User profile completed with health context

## Start Services

### Backend
```bash
cd backend
python start_backend.py
```

### Frontend (if not running)
```bash
cd frontend
npm start
```

## Test Sequence

### 1. Generate Initial Plan
1. Navigate to Diet Plans page
2. Select "Daily Plan" or "Weekly Plan"
3. Click either:
   - **🤖 Generate Plan (AI)** - blue button
   - **🧠 Generate Plan (ML)** - purple button

### 2. Test Meal Regeneration
**Location**: Any meal card in the plan

**Steps**:
1. Find a meal (e.g., Breakfast)
2. Click **🤖** button (AI regeneration)
   - Watch for loading spinner
   - Meal should update in ~2-5 seconds
3. Click **🧠** button (ML regeneration)
   - Watch for loading spinner
   - Meal should update in ~1-2 seconds (faster)

**Expected Result**:
- Meal name changes
- Ingredients update
- Nutrition values recalculate
- Daily/weekly totals update

### 3. Test Day Regeneration
**Location**: Top of daily plan view OR inside weekly plan view

**Steps**:
1. Click **🤖 Regenerate Day** (AI)
   - All meals regenerate using AI
   - Takes ~5-10 seconds
2. Click **🧠 Regenerate Day** (ML)
   - All meals regenerate using ML
   - Takes ~2-4 seconds (faster)

**Expected Result**:
- All meals (breakfast, lunch, dinner, snacks) update
- Daily nutrition totals recalculate
- If in weekly view, weekly totals also update

### 4. Test Week Regeneration
**Location**: Top of weekly plan view

**Steps**:
1. Generate a weekly plan first
2. Click **🤖 Regenerate Week** (AI)
   - Entire week regenerates using AI
   - Takes ~30-60 seconds
3. Click **🧠 Regenerate Week** (ML)
   - Entire week regenerates using ML
   - Takes ~10-20 seconds (faster)

**Expected Result**:
- All 7 days regenerate
- All meals in all days update
- Weekly nutrition totals recalculate

## Visual Verification

### Button Appearance
- [ ] AI buttons (🤖) have gray/blue styling
- [ ] ML buttons (🧠) have purple gradient styling
- [ ] Both buttons show emoji indicators
- [ ] Loading spinners appear when clicked
- [ ] Buttons disable during regeneration

### Responsive Design
- [ ] Buttons work on desktop
- [ ] Buttons work on mobile (may stack)
- [ ] Text abbreviates on small screens
- [ ] Icons remain visible

## Backend Log Verification

Watch backend logs for these entries:

### AI Regeneration
```
[REGENERATE_MEAL_INIT] plan_id=...
[AI_SERVICE_CALL] ...
[REGENERATE_MEAL_SUCCESS] ...
```

### ML Regeneration
```
[ML_REGENERATE_MEAL_INIT] request_id=...
[TEMPLATE_SELECTED] ...
[ML_REGENERATE_MEAL_SUCCESS] ...
```

## Common Issues

### Issue: Buttons not visible
**Solution**: 
- Refresh page
- Ensure plan is loaded
- Check browser console for errors

### Issue: ML button returns error
**Solution**:
- Check backend logs
- Verify ML pipeline is initialized
- Ensure sentence-transformers model is downloaded

### Issue: Slow regeneration
**Solution**:
- AI is slower (normal)
- ML should be fast (~1-2 seconds per meal)
- Check network tab for API call times

### Issue: Nutrition totals don't update
**Solution**:
- Check backend logs for calculation errors
- Verify plan content structure
- Refresh page to reload plan

## Performance Comparison

### Expected Timings

| Operation | AI Pipeline | ML Pipeline |
|-----------|-------------|-------------|
| Single Meal | 2-5 sec | 1-2 sec |
| Full Day | 5-10 sec | 2-4 sec |
| Full Week | 30-60 sec | 10-20 sec |

ML should be **2-3x faster** than AI.

## Success Criteria

✅ All buttons visible and styled correctly
✅ AI buttons work and use AI pipeline
✅ ML buttons work and use ML pipeline
✅ Loading states show correctly
✅ Plans update after regeneration
✅ Nutrition totals recalculate
✅ No console errors
✅ Backend logs show correct pipeline usage
✅ ML is noticeably faster than AI

## Next Steps After Testing

1. **If all tests pass**: Feature is complete! ✅
2. **If issues found**: Check backend logs and browser console
3. **Performance issues**: Verify ML model is loaded correctly
4. **Styling issues**: Check Tailwind CSS compilation

## Quick Debug Commands

### Check Backend Status
```bash
curl http://localhost:8000/health
```

### Check ML Endpoints
```bash
curl http://localhost:8000/docs
# Look for /diet-plans-ml/* endpoints
```

### View Backend Logs
```bash
cd backend
tail -f logs/app.log
```

### Check Frontend Build
```bash
cd frontend
npm run build
```
