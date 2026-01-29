# WellnessWay – Specification Document

## 1. Purpose

WellnessWay is an AI-powered health planning application that helps users design diet plans, workout plans, and track health progress over time.

The system is modular and allows users to opt into:
- Diet planning only
- Workout planning only
- Tracking only
- Any combination of the above

The first development priority is the Diet Planner, followed by Workout Planner, then Progress Tracking.

---

## 2. Target Platforms

### Phase 1
- Web Application (Desktop + Mobile Web)
- Single User Mode
- Couple Mode

### Phase 2
- Native iOS Application
- Native Android Application
- Shared backend and AI orchestration layer

---

## 3. Core Principles

- Application owns all state
- LLM is stateless and reasoning-only
- Deterministic calculations before AI usage
- Modular and optional feature usage
- Versioned health context
- Weekly plans by default
- Daily plans generated on user request
- Safety-first constraints
- Traceability of all AI outputs

---

## 4. User Modes

### 4.1 Single User Mode
- One user
- One Health Context Document
- One set of goals, preferences, and plans

### 4.2 Couple Mode
- Two individual users
- Two Health Context Documents
- Shared planning allowed
- Individual constraints must always be respected
- Support for:
  - Shared meals
  - Partially shared meals
  - Fully separate meals

---

## 5. Health Context Document (HCD)

### 5.1 Definition
The Health Context Document is the single source of truth used by all AI tools.

### 5.2 Format
- Markdown
- Versioned
- Immutable once stored
- One per user (two per couple)

### 5.3 Structure

#### User Profile
- Name
- Age
- Gender
- Height
- Weight
- Body Fat Percentage
- Muscle Mass
- Basal Metabolic Rate (BMR)
- Total Daily Energy Expenditure (TDEE)

#### Goals
- Primary Goal (fat loss / muscle gain / maintenance)
- Target Metrics
- Timeline

#### Diet Preferences
- Diet Type (veg / non-veg / vegan)
- Allergies
- Foods to Avoid
- Meals per Day
- Budget or Lifestyle Constraints

#### Activity Level
- Average Daily Steps
- Workout Experience Level
- Injuries or Physical Limitations

#### System Constraints
- Minimum Daily Calories
- Maximum Allowed Deficit
- Protein Bounds
- Safety Rules

---

## 6. User Flow

### 6.1 Step 1 – User Intake (No LLM)
- Collect user physical details
- Collect smart scale readings
- Calculate BMR and TDEE deterministically
- Generate Health Context Version 1
- Persist raw and derived data

---

### 6.2 Step 2 – Goals and Preferences (Controlled LLM)
- Collect goals and preferences
- Include number of users (single or couple)
- Send Health Context v1 and new inputs to LLM
- LLM may only append or update allowed sections
- Generate Health Context Version 2
- Persist versioned document

---

### 6.3 Step 3 – Plan Generation (Tool-Based LLM)
- User selects plan scope:
  - Weekly (default)
  - Daily (on demand)
- Combine Health Context v2 with user request
- Call appropriate planning tool
- Return structured plan output
- Render plan in UI

---

## 7. Weekly and Daily Planning

### 7.1 Weekly Plans
- Generated once per week
- Cover 7 consecutive days
- Optimized for nutritional balance, variety, and preparation
- Stored as versioned plan output

---

### 7.2 Daily Plans
- Generated only on user request
- Use current Health Context
- May override one day or one meal
- Do not regenerate full week unless explicitly requested

---

## 8. AI Prompt Architecture

### 8.1 Master System Prompt
- Fixed
- Defines safety rules, nutrition boundaries, and tone
- Must never be modified dynamically

---

### 8.2 Context Prompt
- Health Context Document
- Passed to all AI tools
- Updated only through controlled steps

---

### 8.3 Tool Prompts
- Diet Planner Tool
- Workout Planner Tool (future)
- Tracker Tool (future)

All tools:
- Output structured JSON
- Respect constraints
- Must not invent user data

---

## 9. LLM Tools

### 9.1 Diet Planner Tool

#### Inputs
- Health Context Document
- Plan scope (daily or weekly)
- Calorie and macro targets

#### Outputs
- Structured JSON containing days, meals, nutrition, and totals

---

## 10. Chat Interaction Model

### 10.1 Intent Classification
- Modify meal
- Replace ingredient
- Regenerate plan
- Update preferences
- Ask explanation

---

### 10.2 Chat Processing Flow
1. Classify intent
2. Decide action:
   - Update Health Context
   - Regenerate plan via tool
3. Return updated plan or explanation
4. Persist changes

---

## 11. Backend Architecture

### 11.1 Technology Stack
- FastAPI
- React.js
- PostgreSQL
- Object storage for context versions
- External LLM provider

---

### 11.2 Core Services
- User Profile Service
- Health Context Service
- Prompt Orchestration Service
- Tool Execution Service
- Audit and Logging Service

---

## 12. Data Storage

### 12.1 Core Entities
- Users
- Health Context Versions
- Generated Plans
- Chat Sessions
- Audit Logs

---

### 12.2 Storage Rules
- Context versions are immutable
- AI outputs are reproducible
- Full traceability required

---

## 13. Safety and Guardrails

- Maximum calorie deficit limits
- Minimum protein thresholds
- Allergy enforcement
- Explicit medical disclaimers
- No diagnosis or treatment claims

---

## 14. MVP Scope

### Included
- Web application
- Single user mode
- Couple mode
- Diet planner
- Weekly plans
- Daily on-demand plans
- Chat-based modifications

---

### Excluded
- Workout planner
- Long-term analytics
- Wearable integration
- Native mobile applications

---

## 15. Future Roadmap

- Workout Planner Tool
- Progress Tracking (daily to yearly)
- Native iOS application
- Native Android application
- AI coaching insights
- Habit and adherence analytics

---

## 16. Success Metrics

- Weekly plan adherence
- Frequency of plan modification
- 30- and 60-day retention
- User satisfaction

---

## 17. Non-Goals

- Medical diagnosis
- Real-time human coaching
- Wearable-first design

---

## End of Specification Document
