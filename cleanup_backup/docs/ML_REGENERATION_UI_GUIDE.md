# ML Regeneration Buttons - UI Guide

## What You'll See

### 1. Meal Card Regeneration
Each meal card now has **TWO** regenerate buttons:

```
┌─────────────────────────────────────┐
│  🍳 Breakfast                       │
│  Oatmeal with Berries               │
│  ─────────────────────────────────  │
│  Calories: 350 | Protein: 12g       │
│  ─────────────────────────────────  │
│  [🔄 🤖]  [🔄 🧠]                   │
│   AI       ML                       │
└─────────────────────────────────────┘
```

- **Left Button (🤖)**: Regenerate using AI (blue/gray)
- **Right Button (🧠)**: Regenerate using ML (purple gradient)

### 2. Daily Plan Regeneration
At the top of daily plan view:

```
┌─────────────────────────────────────────────────┐
│  🍽️ Daily Meal Plan                            │
│  📅 Monday, February 8, 2026                    │
│                                                 │
│  [🔄 🤖 Regenerate Day]  [🔄 🧠 Regenerate Day] │
│   AI (gray/blue)          ML (purple)          │
└─────────────────────────────────────────────────┘
```

### 3. Weekly Plan Regeneration
At the top of weekly plan view:

```
┌─────────────────────────────────────────────────┐
│  📅 Weekly Meal Plan                            │
│  🗓️ February 8 - February 14, 2026             │
│                                                 │
│  [🔄 🤖 Regenerate Week] [🔄 🧠 Regenerate Week]│
│   AI (gray/blue)          ML (purple)          │
└─────────────────────────────────────────────────┘
```

## Button Behavior

### When Clicked
1. Button shows loading spinner
2. Both buttons are disabled during regeneration
3. After completion, plan updates automatically
4. Nutrition totals recalculate

### Visual States

#### AI Button (🤖)
- **Normal**: White/gray background, gray text
- **Hover**: Light gray background
- **Loading**: Spinner + "..."
- **Disabled**: 50% opacity

#### ML Button (🧠)
- **Normal**: Purple gradient background, purple text
- **Hover**: Darker purple gradient
- **Loading**: Spinner + "..."
- **Disabled**: 50% opacity

## Mobile View

On mobile devices, buttons adapt:
- Buttons may stack vertically
- Text may abbreviate (e.g., "Regen" instead of "Regenerate")
- Icons remain visible (🤖 and 🧠)

## How to Test

### Test Meal Regeneration
1. Generate any plan (daily or weekly)
2. Find a meal card
3. Click the **🤖 AI** button → Meal regenerates using AI
4. Click the **🧠 ML** button → Meal regenerates using ML
5. Compare results (ML should be faster, more deterministic)

### Test Day Regeneration
1. Generate a daily plan OR view a day in weekly plan
2. Click **🤖 Regenerate Day** → All meals regenerate using AI
3. Click **🧠 Regenerate Day** → All meals regenerate using ML

### Test Week Regeneration
1. Generate a weekly plan
2. Click **🤖 Regenerate Week** → Entire week regenerates using AI
3. Click **🧠 Regenerate Week** → Entire week regenerates using ML

## Expected Differences

### AI Pipeline (🤖)
- Uses GenAI for ingredient selection
- More creative/varied meals
- Slower (API calls to AI service)
- May have retries if validation fails

### ML Pipeline (🧠)
- Uses ML templates + deterministic calculations
- Consistent, reliable meals
- Faster (no AI API calls for ingredients)
- No retries (soft acceptance of results)

## Troubleshooting

### Buttons Not Showing
- Ensure backend is running: `cd backend && python start_backend.py`
- Check browser console for errors
- Verify you have an active plan loaded

### ML Button Not Working
- Check backend logs for `[ML_REGENERATE_*]` entries
- Verify ML endpoints are registered
- Ensure ML pipeline dependencies are installed

### Styling Issues
- Clear browser cache
- Check that Tailwind CSS is compiled
- Verify purple gradient classes are available

## Color Reference

### AI Buttons (🤖)
- Background: `bg-white dark:bg-gray-800`
- Border: `border-gray-300 dark:border-gray-600`
- Text: `text-gray-700 dark:text-gray-300`
- Hover: `hover:bg-gray-50 dark:hover:bg-gray-700`

### ML Buttons (🧠)
- Background: `bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20`
- Border: `border-purple-300 dark:border-purple-700`
- Text: `text-purple-700 dark:text-purple-300`
- Hover: `hover:from-purple-100 hover:to-indigo-100 dark:hover:from-purple-900/30 dark:hover:to-indigo-900/30`
