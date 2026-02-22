# ML Pipeline UI Guide

## What You'll See in the UI

### Before (Old UI)
```
┌─────────────────────────────────────────────────┐
│  Choose Your Diet Plan Type                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ○ Daily Plan          ○ Weekly Plan           │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │                                           │ │
│  │  Generate Daily Plan                     │ │  ← Only one button
│  │                                           │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### After (New UI with ML)
```
┌─────────────────────────────────────────────────┐
│  Choose Your Diet Plan Type                     │
├─────────────────────────────────────────────────┤
│                                                 │
│  ○ Daily Plan          ○ Weekly Plan           │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ 🤖 Generate Daily Plan (AI)              │ │  ← Existing (Blue)
│  │ Uses GenAI for creative meal generation  │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ 🧠 Generate Daily Plan (ML) [NEW]        │ │  ← NEW (Purple)
│  │ Uses ML templates + deterministic        │ │
│  │ nutrition                                 │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Button Styles

### AI Button (Existing - Blue)
- **Color:** Blue gradient
- **Icon:** 🤖 Robot emoji
- **Label:** "Generate [Type] Plan (AI)"
- **Description:** "Uses GenAI for creative meal generation"
- **When to use:** Want creative, varied meals

### ML Button (NEW - Purple)
- **Color:** Purple-to-indigo gradient
- **Icon:** 🧠 Brain emoji
- **Label:** "Generate [Type] Plan (ML)"
- **Badge:** "NEW" in purple
- **Description:** "Uses ML templates + deterministic nutrition"
- **When to use:** Want fast, predictable meals

## User Flow

### Step 1: Choose Plan Type
```
User clicks: ○ Daily Plan  or  ○ Weekly Plan
```

### Step 2: Choose Generation Method
```
User sees two buttons:

┌─────────────────────────────────┐
│ 🤖 Generate Daily Plan (AI)    │  ← Creative, varied
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ 🧠 Generate Daily Plan (ML)    │  ← Fast, predictable
│ [NEW]                           │
└─────────────────────────────────┘
```

### Step 3: Generation
```
Loading screen appears:

┌─────────────────────────────────┐
│  Generating Your Diet Plan      │
│                                 │
│  [Spinner Animation]            │
│                                 │
│  Our AI/ML is creating a        │
│  personalized plan...           │
└─────────────────────────────────┘
```

### Step 4: View Plan
```
Plan appears with meals, nutrition, and regenerate options
(Same UI for both AI and ML plans)
```

## Visual Indicators

### NEW Badge
```
┌──────┐
│ NEW  │  ← Purple background, white text
└──────┘
```

### Button Hover States
```
AI Button:
  Normal: Blue (#4F46E5)
  Hover:  Darker Blue (#4338CA)

ML Button:
  Normal: Purple-Indigo Gradient (#9333EA → #4F46E5)
  Hover:  Darker Gradient (#7E22CE → #4338CA)
```

## Mobile View

### Stacked Buttons
```
┌─────────────────────────┐
│ ○ Daily Plan           │
│ ○ Weekly Plan          │
│                         │
│ ┌─────────────────────┐ │
│ │ 🤖 Generate (AI)   │ │
│ │ Uses GenAI         │ │
│ └─────────────────────┘ │
│                         │
│ ┌─────────────────────┐ │
│ │ 🧠 Generate (ML)   │ │
│ │ [NEW] Uses ML      │ │
│ └─────────────────────┘ │
└─────────────────────────┘
```

## Comparison Table (Shown in UI)

```
┌─────────────────────────────────────────────────┐
│  💡 How it works                                │
├─────────────────────────────────────────────────┤
│                                                 │
│  AI Pipeline (Blue):                           │
│  • Creative meal suggestions                   │
│  • High variety                                │
│  • Self-healing with retries                   │
│  • Best for: Exploring new meals               │
│                                                 │
│  ML Pipeline (Purple):                         │
│  • Template-based meals                        │
│  • Fast generation                             │
│  • Predictable results                         │
│  • Best for: Consistent planning               │
└─────────────────────────────────────────────────┘
```

## Loading States

### AI Generation
```
Generating Your Diet Plan

[Spinner]

Our AI is creating a personalized daily plan
based on your profile, goals, and preferences.
This may take a moment...

Time: ~5-10 seconds
```

### ML Generation
```
Generating Your Diet Plan with ML

[Spinner]

Our ML system is selecting optimal meal templates
and calculating precise nutrition.
This is fast!

Time: ~2-5 seconds
```

## Success States

### Both Show Same Result
```
┌─────────────────────────────────────────────────┐
│  Your Daily Plan                                │
│  Generated on [Date]                            │
│                                                 │
│  [Meal Cards with Nutrition]                   │
│                                                 │
│  • Breakfast: [Meal Name]                      │
│  • Lunch: [Meal Name]                          │
│  • Dinner: [Meal Name]                         │
│                                                 │
│  Daily Totals: [Calories] cal, [Protein]g     │
└─────────────────────────────────────────────────┘
```

## Error States

### ML-Specific Errors
```
┌─────────────────────────────────────────────────┐
│  ⚠️ ML Pipeline Error                          │
├─────────────────────────────────────────────────┤
│                                                 │
│  The ML pipeline encountered an issue.         │
│                                                 │
│  Try:                                          │
│  • Using the AI button instead                 │
│  • Checking your profile is complete           │
│  • Refreshing the page                         │
│                                                 │
│  [Try AI Pipeline] [Go Back]                   │
└─────────────────────────────────────────────────┘
```

## Accessibility

### Screen Reader Announcements
```
AI Button:
"Generate daily plan using AI. Uses GenAI for creative meal generation."

ML Button:
"Generate daily plan using ML. New feature. Uses ML templates and deterministic nutrition."
```

### Keyboard Navigation
```
Tab Order:
1. Daily Plan radio button
2. Weekly Plan radio button
3. AI Generate button
4. ML Generate button
5. Back to Home button
6. Edit Profile button
```

## Dark Mode Support

### AI Button (Dark Mode)
- Background: Dark blue (#1E3A8A)
- Text: White
- Hover: Lighter blue

### ML Button (Dark Mode)
- Background: Dark purple-indigo gradient
- Text: White
- Hover: Lighter gradient
- NEW badge: Purple with lighter text

## Responsive Breakpoints

### Desktop (≥1024px)
- Buttons side by side
- Full descriptions visible

### Tablet (768px - 1023px)
- Buttons side by side
- Shortened descriptions

### Mobile (<768px)
- Buttons stacked vertically
- Minimal descriptions
- Full-width buttons

## Animation

### Button Hover
```css
transition: all 0.2s ease-in-out
transform: translateY(-2px)
box-shadow: 0 4px 12px rgba(0,0,0,0.15)
```

### Loading Spinner
```css
animation: spin 1s linear infinite
```

### Success Fade-in
```css
animation: fadeIn 0.3s ease-in
```

## User Feedback

### After Generation
```
┌─────────────────────────────────────────────────┐
│  ✅ Plan Generated Successfully!               │
│                                                 │
│  Generated using: [AI / ML] Pipeline           │
│  Time taken: [X] seconds                       │
│                                                 │
│  [View Plan] [Generate Another]                │
└─────────────────────────────────────────────────┘
```

## Tips & Hints

### Tooltip on ML Button
```
Hover over ML button:

┌─────────────────────────────────┐
│ NEW: ML Pipeline                │
│                                 │
│ • Faster generation             │
│ • Template-based meals          │
│ • Deterministic nutrition       │
│ • No AI retries                 │
└─────────────────────────────────┘
```

### First-Time User
```
┌─────────────────────────────────────────────────┐
│  💡 New Feature: ML Pipeline                   │
├─────────────────────────────────────────────────┤
│                                                 │
│  Try our new ML-powered diet plan generator!   │
│                                                 │
│  • Faster than AI generation                   │
│  • Uses proven meal templates                  │
│  • Deterministic nutrition calculations        │
│                                                 │
│  [Try ML Pipeline] [Maybe Later]               │
└─────────────────────────────────────────────────┘
```

## Summary

The UI now offers **two clear choices**:

1. **🤖 AI Pipeline** (Blue) - Creative, varied, LLM-powered
2. **🧠 ML Pipeline** (Purple) - Fast, predictable, template-based

Both are clearly labeled, visually distinct, and provide the same high-quality diet plans - just generated differently!
