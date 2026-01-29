# WellnessWay Diet Planner - Requirements

## 1. Overview

WellnessWay Diet Planner is an AI-powered diet planning application that helps single users create personalized weekly and daily meal plans based on their health profile, goals, and preferences.

## 2. User Stories

### 2.1 User Profile Creation
**As a user**, I want to create my health profile so that the system can generate personalized diet plans.

**Acceptance Criteria:**
- 2.1.1 User can input basic physical details (name, age, gender, height, weight)
- 2.1.2 User can input body composition data (body fat %, muscle mass) if available
- 2.1.3 System calculates BMR and TDEE deterministically using standard formulas
- 2.1.4 User can specify activity level for TDEE calculation
- 2.1.5 All data is validated for reasonable ranges and safety

### 2.2 Goal Setting
**As a user**, I want to set my health goals so that my diet plan aligns with my objectives.

**Acceptance Criteria:**
- 2.2.1 User can select primary goal (fat loss, muscle gain, maintenance)
- 2.2.2 User can set target metrics (weight goal, timeline)
- 2.2.3 System validates goals are realistic and safe
- 2.2.4 System calculates appropriate calorie targets based on goals

### 2.3 Diet Preferences
**As a user**, I want to specify my dietary preferences so that my meal plans are suitable for me.

**Acceptance Criteria:**
- 2.3.1 User can select diet type (vegetarian, non-vegetarian, vegan)
- 2.3.2 User can specify allergies and foods to avoid
- 2.3.3 User can set preferred number of meals per day
- 2.3.4 User can specify budget or lifestyle constraints
- 2.3.5 All preferences are stored and used in plan generation

### 2.4 Health Context Document Generation
**As a user**, I want my profile information organized into a structured document so that it can be used consistently for AI planning.

**Acceptance Criteria:**
- 2.4.1 System generates a markdown Health Context Document (HCD) from user inputs
- 2.4.2 HCD includes all profile data, goals, preferences, and calculated metrics
- 2.4.3 HCD includes system-calculated safety constraints (min calories, max deficit, protein bounds)
- 2.4.4 HCD is versioned and immutable once created
- 2.4.5 New versions are created when user updates their profile

### 2.5 Weekly Diet Plan Generation
**As a user**, I want to generate a weekly diet plan so that I have structured meal guidance for the week.

**Acceptance Criteria:**
- 2.5.1 User can request a weekly diet plan covering 7 consecutive days
- 2.5.2 System uses current HCD and AI to generate balanced meal plans
- 2.5.3 Plan includes breakfast, lunch, dinner, and optional snacks for each day
- 2.5.4 Each meal includes ingredients, portions, and nutritional information
- 2.5.5 Daily and weekly nutritional totals are calculated and displayed
- 2.5.6 Plan respects all user preferences, allergies, and safety constraints
- 2.5.7 Plan provides variety across the week while maintaining nutritional balance

### 2.6 Daily Diet Plan Generation
**As a user**, I want to generate a single day's diet plan so that I can get fresh meal ideas on demand.

**Acceptance Criteria:**
- 2.6.1 User can request a diet plan for a specific day
- 2.6.2 System generates meals for that day only using current HCD
- 2.6.3 Daily plan follows same structure and constraints as weekly plans
- 2.6.4 User can regenerate daily plans without affecting existing weekly plans

### 2.7 Plan Display and Navigation
**As a user**, I want to view my diet plans in an organized, easy-to-read format so that I can follow them effectively.

**Acceptance Criteria:**
- 2.7.1 Plans are displayed in a clean, mobile-friendly interface
- 2.7.2 User can navigate between days in a weekly plan
- 2.7.3 Each meal shows ingredients, portions, and prep instructions
- 2.7.4 Nutritional information is clearly displayed for meals and daily totals
- 2.7.5 User can view macro breakdown (protein, carbs, fats) and calories

### 2.8 Basic Plan Modifications
**As a user**, I want to make simple modifications to my diet plan so that I can adapt it to my needs.

**Acceptance Criteria:**
- 2.8.1 User can regenerate a specific meal while keeping the rest of the plan
- 2.8.2 User can regenerate an entire day while keeping the rest of the week
- 2.8.3 User can regenerate the entire weekly plan
- 2.8.4 All regenerations respect the same constraints and preferences
- 2.8.5 Modified plans maintain nutritional balance

### 2.9 Nutrition Calculation Accuracy
**As a user**, I want accurate nutrition calculations so that I can trust the dietary information provided.

**Acceptance Criteria:**
- 2.9.1 All nutrition calculations are performed by backend using verified food database
- 2.9.2 AI provides only meal names and ingredients, never nutrition values
- 2.9.3 System enforces raw weight measurements for all ingredients
- 2.9.4 Nutrition calculations are deterministic and reproducible
- 2.9.5 System detects and corrects unrealistic nutrition values automatically

### 2.10 System Reliability and Safety
**As a user**, I want the system to be reliable and safe so that I can depend on it for my health goals.

**Acceptance Criteria:**
- 2.10.1 System prevents generation of unsafe calorie deficits (>1kg/week weight loss)
- 2.10.2 System ensures minimum protein requirements are always met
- 2.10.3 System provides variety in meal plans without repeating primary ingredients
- 2.10.4 System handles AI service failures gracefully with fallback providers
- 2.10.5 System validates all AI responses against safety constraints
- 2.10.6 System maintains data integrity through comprehensive validation

## 3. Technical Requirements

### 3.1 Architecture
- 3.1.1 Web application built with React.js frontend and FastAPI backend
- 3.1.2 PostgreSQL database for persistent data storage
- 3.1.3 Multi-provider AI integration (OpenAI, Groq, Ollama, Mock) for resilient planning
- 3.1.4 RESTful API design with comprehensive error handling and validation
- 3.1.5 Hardened nutrition calculation engine with deterministic algorithms
- 3.1.6 Centralized nutrition database abstraction for consistent food data

### 3.2 Data Management
- 3.2.1 Health Context Documents stored as versioned, immutable records in both JSON and Markdown formats
- 3.2.2 Generated plans stored with timestamps and version references
- 3.2.3 All AI interactions logged for traceability and debugging
- 3.2.4 User data encrypted at rest and in transit
- 3.2.5 Nutrition database with USDA/IFCT food composition data
- 3.2.6 Raw weight enforcement for all ingredient calculations

### 3.3 AI Integration
- 3.3.1 Fixed master system prompt defining safety rules and constraints
- 3.3.2 Structured JSON output from AI with strict contract enforcement
- 3.3.3 Input validation to ensure AI receives properly formatted context
- 3.3.4 Error handling for AI service failures with automatic provider switching
- 3.3.5 LLM contract enforcement - AI provides ONLY meal names and ingredients, NO nutrition calculations
- 3.3.6 Backend authority over all nutrition calculations and safety constraints

### 3.4 Safety and Validation
- 3.4.1 Minimum daily calorie limits based on user profile (never below BMR)
- 3.4.2 Maximum calorie deficit limits for safe weight loss (≤1kg/week, ≤500 kcal/day)
- 3.4.3 Unified protein requirements based on goals (1.5-2.2g per kg body weight)
- 3.4.4 Allergy and dietary restriction enforcement with strict validation
- 3.4.5 Medical disclaimers and safety warnings displayed prominently
- 3.4.6 Unrealistic goal detection and automatic safety capping
- 3.4.7 Deterministic variety validation to prevent ingredient repetition
- 3.4.8 Hardened auto-correction with priority order (protein → carbs → fats)

## 4. Non-Functional Requirements

### 4.1 Performance
- 4.1.1 Plan generation completes within 30 seconds under normal conditions
- 4.1.2 Application loads and displays existing plans within 3 seconds
- 4.1.3 Database queries optimized for sub-second response times

### 4.2 Usability
- 4.2.1 Interface works on desktop and mobile web browsers
- 4.2.2 Clear error messages and validation feedback
- 4.2.3 Intuitive navigation and user flow
- 4.2.4 Accessible design following WCAG guidelines

### 4.3 Reliability
- 4.3.1 System handles AI service outages gracefully
- 4.3.2 Data backup and recovery procedures in place
- 4.3.3 Input validation prevents system crashes from invalid data

## 5. Out of Scope

### 5.1 Excluded from Initial Implementation
- 5.1.1 Couple mode functionality
- 5.1.2 Workout planning features
- 5.1.3 Progress tracking and analytics
- 5.1.4 Chat-based plan modifications
- 5.1.5 Native mobile applications
- 5.1.6 Wearable device integration
- 5.1.7 Social features or sharing capabilities

## 6. Success Criteria

### 6.1 Functional Success
- 6.1.1 Users can complete the full flow from profile creation to plan generation
- 6.1.2 Generated plans meet all specified nutritional and safety constraints
- 6.1.3 Plans show appropriate variety and balance across the week
- 6.1.4 All user preferences and restrictions are properly respected

### 6.2 Technical Success
- 6.2.1 System handles expected user load without performance degradation
- 6.2.2 All data is properly persisted and retrievable
- 6.2.3 AI integration works reliably with proper error handling
- 6.2.4 Security requirements are met for user data protection