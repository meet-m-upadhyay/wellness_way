# WellnessWay Diet Planner - Design Document

## 1. System Architecture

### 1.1 High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React.js      │    │   FastAPI       │    │  PostgreSQL     │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Multi-Provider │
                       │  AI Integration │
                       │ (OpenAI/Groq/   │
                       │  Ollama/Mock)   │
                       └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Hardened Backend Architecture                │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  Nutrition      │  Nutrition      │     AI Service              │
│  Database       │  Engine         │     (Contract Enforced)     │
│  (USDA/IFCT)    │  (Calculations) │     (Meals Only)            │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### 1.2 Technology Stack
- **Frontend**: React.js with TypeScript, Tailwind CSS for styling
- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL 15+ with SQLAlchemy ORM
- **AI Integration**: Multi-provider system (OpenAI GPT-4, Groq, Ollama, Mock AI)
- **Nutrition Data**: USDA Food Data Central and IFCT database integration
- **Deployment**: Docker containers, cloud hosting (AWS/GCP/Azure)

### 1.3 Hardened Architecture Principles
- **LLM Contract Enforcement**: AI provides ONLY meal names and ingredients, never nutrition data
- **Backend Authority**: All nutrition calculations, safety constraints, and validation handled by backend
- **Deterministic Calculations**: All nutrition and safety calculations are reproducible and testable
- **Raw Weight Enforcement**: All ingredient quantities must be in raw weight for accuracy
- **Safety-First Design**: Multiple layers of validation prevent unsafe recommendations
- **Graceful Degradation**: System handles AI failures with provider switching and fallbacks

## 2. Data Models

### 2.1 User Profile
```python
class UserProfile:
    id: UUID
    name: str
    age: int
    gender: Literal["male", "female", "other"]
    height_cm: float
    weight_kg: float
    body_fat_percentage: Optional[float]
    muscle_mass_kg: Optional[float]
    activity_level: Literal["sedentary", "lightly_active", "moderately_active", "very_active", "extremely_active"]
    created_at: datetime
    updated_at: datetime
```

### 2.2 Health Goals
```python
class HealthGoals:
    id: UUID
    user_id: UUID
    primary_goal: Literal["fat_loss", "muscle_gain", "maintenance"]
    target_weight_kg: Optional[float]
    timeline_weeks: Optional[int]
    created_at: datetime
```

### 2.3 Diet Preferences
```python
class DietPreferences:
    id: UUID
    user_id: UUID
    diet_type: Literal["vegetarian", "non_vegetarian", "vegan"]
    allergies: List[str]
    foods_to_avoid: List[str]
    meals_per_day: int
    budget_constraints: Optional[str]
    lifestyle_constraints: Optional[str]
    created_at: datetime
```

### 2.4 Health Context Document
```python
class HealthContextDocument:
    id: UUID
    user_id: UUID
    version: int
    content: str  # Markdown content
    json_context: dict  # JSON format for machine processing
    bmr_calories: float
    tdee_calories: float
    min_daily_calories: float
    max_calorie_deficit: float
    min_protein_grams: float
    created_at: datetime
    is_active: bool
```

### 2.5 Diet Plan
```python
class DietPlan:
    id: UUID
    user_id: UUID
    hcd_id: UUID  # Reference to Health Context Document used
    plan_type: Literal["weekly", "daily"]
    start_date: date
    content: dict  # JSON structure with meals and nutrition
    created_at: datetime

class Meal:
    name: str
    ingredients: List[dict]  # {name, quantity_grams, unit} - RAW WEIGHT ONLY
    instructions: str
    nutrition: dict  # Backend-calculated, never from AI
```

### 2.6 Nutrition Database Models
```python
class FoodItem:
    id: UUID
    name: str
    source: Literal["usda", "ifct", "custom"]
    nutrition_per_100g: dict  # Standardized nutrition data
    raw_to_cooked_ratio: Optional[float]  # For weight conversion
    category: str
    created_at: datetime

class NutritionProfile:
    calories_per_100g: float
    protein_per_100g: float
    carbs_per_100g: float
    fat_per_100g: float
    fiber_per_100g: float
    sodium_per_100g: float
```

## 3. API Design

### 3.1 User Profile Endpoints
```
POST   /api/users/profile          # Create user profile
GET    /api/users/profile          # Get current user profile
PUT    /api/users/profile          # Update user profile
```

### 3.2 Health Context Endpoints
```
GET    /api/health-context         # Get current HCD
GET    /api/health-context/history # Get HCD version history
POST   /api/health-context/update  # Update profile and create new HCD version
```

### 3.3 Diet Planning Endpoints
```
POST   /api/diet-plans/weekly      # Generate weekly diet plan
POST   /api/diet-plans/daily       # Generate daily diet plan
GET    /api/diet-plans             # Get user's diet plans
GET    /api/diet-plans/{id}        # Get specific diet plan
POST   /api/diet-plans/{id}/regenerate  # Regenerate specific meal/day
```

## 4. Core Business Logic

### 4.1 Hardened Nutrition Calculation Engine
```python
class NutritionEngine:
    """Centralized nutrition calculation with safety constraints"""
    
    def calculate_meal_nutrition(self, ingredients: List[dict]) -> dict:
        """Calculate nutrition from raw ingredients using food database"""
        # All calculations use raw weight and verified food data
        # Never trust AI-provided nutrition values
        
    def validate_daily_nutrition(self, meals: List[dict], targets: dict) -> dict:
        """Validate daily nutrition meets safety constraints"""
        # Enforce minimum calories (never below BMR)
        # Ensure protein requirements are met
        # Validate macro distribution
        
    def auto_correct_nutrition(self, plan: dict, targets: dict) -> dict:
        """Auto-correct nutrition with priority order: protein → carbs → fats"""
        # Hard limits: ≤40g protein/meal, ≤target+10% fat
        # Maximum 3 correction attempts
        # Maintain meal structure while adjusting portions
```

### 4.2 BMR and TDEE Calculations (Unchanged)
```python
def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
    if gender.lower() == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def calculate_tdee(bmr: float, activity_level: str) -> float:
    """Calculate Total Daily Energy Expenditure"""
    multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extremely_active": 1.9
    }
    return bmr * multipliers[activity_level]
```

### 4.3 Enhanced Safety Constraints Calculation
```python
def calculate_safety_constraints(user_profile: UserProfile, goals: HealthGoals, tdee: float) -> dict:
    """Calculate enhanced safety constraints with unrealistic goal detection"""
    # Minimum calories: never below BMR
    min_calories = calculate_bmr(user_profile.weight_kg, user_profile.height_cm, 
                                user_profile.age, user_profile.gender)
    
    # Enhanced deficit calculation with safety capping
    max_deficit = min(tdee * 0.2, 500)  # 20% of TDEE or 500 calories
    
    # Detect unrealistic goals (>1kg/week or >1% bodyweight/week)
    if goals.timeline_weeks and goals.target_weight_kg:
        weekly_loss = (user_profile.weight_kg - goals.target_weight_kg) / goals.timeline_weeks
        max_safe_weekly_loss = min(1.0, user_profile.weight_kg * 0.01)  # 1kg or 1% bodyweight
        
        if weekly_loss > max_safe_weekly_loss:
            # Cap to safe limits and add warning flag
            max_deficit = min(max_deficit, max_safe_weekly_loss * 7700 / 7)  # 7700 cal/kg fat
    
    # Unified protein requirements based on goals
    protein_multipliers = {
        "fat_loss": 1.8,      # 1.8-2.0g per kg
        "muscle_gain": 2.0,   # 2.0-2.2g per kg
        "maintenance": 1.5    # 1.5-1.8g per kg
    }
    min_protein = user_profile.weight_kg * protein_multipliers.get(goals.primary_goal, 1.5)
    
    return {
        "min_daily_calories": min_calories,
        "max_calorie_deficit": max_deficit,
        "min_protein_grams": min_protein,
        "unrealistic_goal_detected": weekly_loss > max_safe_weekly_loss if goals.timeline_weeks else False
    }
```

### 4.4 Deterministic Variety Validation
```python
class VarietyValidator:
    """Ensure meal variety using algorithmic validation"""
    
    def identify_primary_protein_source(self, ingredients: List[dict]) -> str:
        """Identify primary protein source using normalized ingredient names"""
        # Normalize ingredient names and identify protein sources
        # Return primary protein category (chicken, beef, fish, legumes, etc.)
        
    def identify_primary_carb_source(self, ingredients: List[dict]) -> str:
        """Identify primary carbohydrate source"""
        # Normalize ingredient names and identify carb sources
        # Return primary carb category (rice, wheat, potato, etc.)
        
    def validate_weekly_variety(self, weekly_plan: dict) -> bool:
        """Validate no repetition of primary ingredients across consecutive days"""
        # Check protein and carb variety across the week
        # Ensure no identical primary combinations on consecutive days
```

### 4.5 Health Context Document Generation (Enhanced)
```python
def generate_hcd(user_profile: UserProfile, goals: HealthGoals, 
                preferences: DietPreferences) -> tuple[str, dict]:
    """Generate both markdown and JSON Health Context Documents"""
    bmr = calculate_bmr(user_profile.weight_kg, user_profile.height_cm,
                       user_profile.age, user_profile.gender)
    tdee = calculate_tdee(bmr, user_profile.activity_level)
    constraints = calculate_safety_constraints(user_profile, goals, tdee)
    
    # Generate clean JSON (omit "None" strings and empty blocks)
    json_context = {
        "profile": {k: v for k, v in user_profile.dict().items() if v is not None},
        "goals": {k: v for k, v in goals.dict().items() if v is not None},
        "preferences": {k: v for k, v in preferences.dict().items() if v is not None},
        "calculated_metrics": constraints
    }
    
    # Generate structured markdown document for human readability
    markdown_content = generate_markdown_hcd(json_context)
    
    return markdown_content, json_context
```

## 5. AI Integration

### 5.1 Hardened Master System Prompt
```
You are a professional nutritionist AI assistant for WellnessWay Diet Planner.

CRITICAL CONTRACT RULES:
- You MUST ONLY provide meal names, ingredients, and preparation instructions
- You MUST NEVER provide nutrition values (calories, protein, carbs, fat, etc.)
- All nutrition calculations are handled by the backend system
- Any response containing nutrition values will be REJECTED

SAFETY RULES:
- Always respect allergies and dietary restrictions
- Provide balanced meal variety across the plan
- Use realistic ingredient portions and combinations
- Include clear preparation instructions

OUTPUT FORMAT:
- Always return valid JSON in the specified structure
- Include complete ingredient lists with quantities in grams (raw weight)
- Provide simple preparation instructions
- DO NOT include any nutrition information

CONSTRAINTS:
- Respect all user preferences and restrictions
- Maintain meal variety across the plan
- Keep meals practical and achievable
- Use common, accessible ingredients
```

### 5.2 Multi-Provider AI System
```python
class AIProviderManager:
    """Manages multiple AI providers with automatic failover"""
    
    providers = {
        "openai": OpenAIProvider(),      # Premium, high quality
        "groq": GroqProvider(),          # Free 14,400 requests/day, fast
        "ollama": OllamaProvider(),      # Local, completely free
        "mock": MockAIProvider()         # Development, no API key needed
    }
    
    def generate_diet_plan(self, context: str, retries: int = 3) -> dict:
        """Generate diet plan with provider failover"""
        for provider_name in self.get_provider_priority():
            try:
                response = self.providers[provider_name].generate(context)
                self._enforce_llm_contract(response)  # Reject nutrition data
                return response
            except Exception as e:
                self.log_provider_failure(provider_name, e)
                continue
        raise AIServiceUnavailableError("All AI providers failed")
```

### 5.3 LLM Contract Enforcement
```python
class LLMContractViolationError(Exception):
    """Raised when AI response violates the contract by including nutrition data"""
    pass

def _enforce_llm_contract(self, ai_response: dict) -> None:
    """Strictly enforce that AI provides NO nutrition calculations"""
    forbidden_fields = [
        'calories', 'protein', 'carbs', 'carbohydrates', 'fat', 'fats',
        'fiber', 'sodium', 'nutrition', 'nutritional', 'macro', 'macros'
    ]
    
    # Recursively check all fields in the response
    if self._contains_nutrition_fields(ai_response, forbidden_fields):
        raise LLMContractViolationError(
            "AI response contains forbidden nutrition fields. "
            "AI must only provide meal names and ingredients."
        )
```

### 5.4 Diet Planner Tool Schema (Updated)
```python
class DietPlanRequest:
    health_context: str  # Full HCD markdown
    plan_type: Literal["weekly", "daily"]
    # NO nutrition targets sent to AI - calculated by backend

class DietPlanResponse:
    plan_type: str
    days: List[DayPlan]
    # NO nutrition totals from AI - calculated by backend

class DayPlan:
    date: str
    meals: List[Meal]
    # NO daily totals from AI - calculated by backend

class Meal:
    type: Literal["breakfast", "lunch", "dinner", "snack"]
    name: str
    ingredients: List[Ingredient]  # RAW WEIGHT ONLY
    instructions: str
    # NO nutrition field - calculated by backend

class Ingredient:
    name: str
    quantity_grams: float  # MUST be raw weight
    unit: str  # For display only, calculations use grams
```

## 6. Frontend Components

### 6.1 Component Hierarchy
```
App
├── ProfileSetup
│   ├── BasicInfoForm
│   ├── GoalsForm
│   └── PreferencesForm
├── Dashboard
│   ├── PlanOverview
│   ├── WeeklyPlanView
│   ├── DailyPlanView
│   └── NutritionSummary
└── PlanGeneration
    ├── PlanTypeSelector
    ├── GenerationProgress
    └── PlanDisplay
```

### 6.2 State Management
```typescript
interface AppState {
  user: UserProfile | null;
  currentHCD: HealthContextDocument | null;
  activePlan: DietPlan | null;
  isGenerating: boolean;
  error: string | null;
}

// Use React Context + useReducer for state management
// Consider Zustand for more complex state needs
```

## 7. Database Schema

### 7.1 Core Tables
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL CHECK (age > 0 AND age < 150),
    gender VARCHAR(20) NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    height_cm DECIMAL(5,2) NOT NULL CHECK (height_cm > 0),
    weight_kg DECIMAL(5,2) NOT NULL CHECK (weight_kg > 0),
    body_fat_percentage DECIMAL(4,2) CHECK (body_fat_percentage >= 0 AND body_fat_percentage <= 100),
    muscle_mass_kg DECIMAL(5,2) CHECK (muscle_mass_kg >= 0),
    activity_level VARCHAR(30) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health Context Documents table
CREATE TABLE health_context_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    bmr_calories DECIMAL(7,2) NOT NULL,
    tdee_calories DECIMAL(7,2) NOT NULL,
    min_daily_calories DECIMAL(7,2) NOT NULL,
    max_calorie_deficit DECIMAL(7,2) NOT NULL,
    min_protein_grams DECIMAL(6,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, version)
);

-- Diet Plans table
CREATE TABLE diet_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hcd_id UUID NOT NULL REFERENCES health_context_documents(id),
    plan_type VARCHAR(20) NOT NULL CHECK (plan_type IN ('weekly', 'daily')),
    start_date DATE NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 8. Correctness Properties

Based on the requirements analysis and hardened architecture, here are the key correctness properties that must be validated through property-based testing:

### 8.1 BMR and TDEE Calculation Properties
**Property 1.1: BMR Determinism**
- **Validates: Requirements 2.1.3**
- For any given user profile (weight, height, age, gender), BMR calculation must always return the same result
- BMR must be positive and within reasonable bounds (800-3000 calories)

**Property 1.2: TDEE Consistency**
- **Validates: Requirements 2.1.3, 2.1.4**
- TDEE must always be greater than BMR
- TDEE must increase monotonically with activity level
- TDEE = BMR × activity_multiplier (exact relationship)

### 8.2 Enhanced Safety Constraint Properties
**Property 2.1: Calorie Safety Bounds**
- **Validates: Requirements 2.1.5, 2.2.3, 2.10.1**
- Minimum daily calories must never be below BMR
- Maximum calorie deficit must not exceed 20% of TDEE or 500 calories
- Target calories must be within [min_calories, TDEE - max_deficit] range
- System must detect and cap unrealistic goals (>1kg/week weight loss)

**Property 2.2: Unified Protein Requirements**
- **Validates: Requirements 2.1.5, 2.2.4, 2.10.2**
- Minimum protein must follow unified requirements: fat loss (1.8-2.0g/kg), muscle gain (2.0-2.2g/kg), maintenance (1.5-1.8g/kg)
- Generated plans must meet or exceed minimum protein requirements
- Auto-correction must prioritize protein targets over other macros

### 8.3 Health Context Document Properties
**Property 3.1: HCD Completeness and Dual Format**
- **Validates: Requirements 2.4.2, 2.9.4**
- Every HCD must contain both markdown and JSON formats
- All calculated values (BMR, TDEE, constraints) must be present and valid
- JSON format must omit "None" strings and empty blocks
- Both formats must contain identical calculated data

**Property 3.2: HCD Immutability**
- **Validates: Requirements 2.4.4**
- Once created, HCD content must never change
- Version numbers must be sequential and unique per user
- Only one HCD per user can be marked as active

### 8.4 LLM Contract Enforcement Properties
**Property 4.1: AI Response Contract Compliance**
- **Validates: Requirements 2.9.1, 2.9.2**
- AI responses must NEVER contain nutrition fields (calories, protein, carbs, fat, etc.)
- AI responses must contain only meal names, ingredients, and instructions
- System must reject any AI response containing forbidden nutrition data

**Property 4.2: Raw Weight Enforcement**
- **Validates: Requirements 2.9.3**
- All ingredient quantities must be specified in raw weight (grams)
- System must detect and flag cooked weight specifications
- Nutrition calculations must use only raw weight values

### 8.5 Nutrition Calculation Properties
**Property 5.1: Deterministic Nutrition Calculations**
- **Validates: Requirements 2.9.4, 2.9.5**
- Same ingredients must always produce identical nutrition values
- All nutrition calculations must be performed by backend, never AI
- Nutrition values must be within realistic bounds for given ingredients

**Property 5.2: Auto-Correction Consistency**
- **Validates: Requirements 2.9.5, 2.10.2**
- Auto-correction must follow priority order: protein → carbs → fats
- Hard limits must be enforced: ≤40g protein/meal, ≤target+10% fat
- Maximum 3 correction attempts before failure
- Corrected plans must still meet minimum safety constraints

### 8.6 Variety and Safety Properties
**Property 6.1: Deterministic Variety Validation**
- **Validates: Requirements 2.10.3**
- Primary protein and carb sources must be identified algorithmically
- No repetition of identical primary ingredient combinations on consecutive days
- Variety validation must be deterministic and reproducible

**Property 6.2: Safety Constraint Preservation**
- **Validates: Requirements 2.10.1, 2.10.2, 2.10.5, 2.10.6**
- Generated plans must never violate minimum calorie requirements
- Generated plans must never violate minimum protein requirements
- All safety constraints must be validated before plan acceptance
- System must maintain data integrity through comprehensive validation

### 8.7 Multi-Provider AI Properties
**Property 7.1: Provider Failover Reliability**
- **Validates: Requirements 2.10.4**
- System must handle individual provider failures gracefully
- Provider switching must maintain response quality and format
- All providers must produce contract-compliant responses

**Property 7.2: Response Validation Consistency**
- **Validates: Requirements 2.10.5**
- All AI responses must pass identical validation regardless of provider
- Contract enforcement must be consistent across all providers
- Invalid responses must be rejected with clear error messages

## 9. Testing Strategy

### 9.1 Unit Testing
- Test all calculation functions (BMR, TDEE, constraints) with known inputs/outputs
- Test data validation and error handling
- Test HCD generation with various user profiles
- Test API endpoint request/response handling

### 9.2 Property-Based Testing Framework
- **Framework**: Hypothesis (Python) for backend, fast-check (TypeScript) for frontend
- **Test Data Generation**: Smart generators that create valid user profiles, goals, and preferences
- **Property Validation**: Automated verification of all correctness properties
- **Counterexample Analysis**: Systematic investigation of any property violations

### 9.3 Integration Testing
- Test complete user flows from profile creation to plan generation
- Test AI integration with mock and real LLM responses
- Test database operations and data persistence
- Test error handling and recovery scenarios

## 10. Security Considerations

### 10.1 Data Protection
- Encrypt sensitive user data at rest using AES-256
- Use HTTPS for all API communications
- Implement proper authentication and session management
- Regular security audits and dependency updates

### 10.2 Input Validation
- Validate all user inputs on both frontend and backend
- Sanitize data before database storage
- Implement rate limiting for API endpoints
- Validate AI responses before processing

### 10.3 Privacy
- Minimal data collection - only what's necessary for functionality
- Clear privacy policy and data usage terms
- Option for users to delete their data
- No sharing of personal health data with third parties

## 11. Performance Considerations

### 11.1 Response Times
- Profile operations: < 1 second
- HCD generation: < 2 seconds
- Diet plan generation: < 30 seconds (due to AI processing)
- Plan retrieval: < 1 second

### 11.2 Scalability
- Database indexing on frequently queried fields
- Connection pooling for database access
- Caching of frequently accessed data
- Horizontal scaling capability for API servers

### 11.3 AI Integration Optimization
- Implement request queuing for AI calls
- Cache similar requests to reduce AI usage
- Implement fallback mechanisms for AI service outages
- Monitor and optimize prompt efficiency

## 12. Deployment Architecture

### 12.1 Development Environment
- Docker Compose for local development
- Hot reloading for frontend and backend
- Local PostgreSQL instance
- Environment-specific configuration

### 12.2 Production Environment
- Container orchestration (Kubernetes or Docker Swarm)
- Load balancing for API servers
- Database clustering for high availability
- CDN for static asset delivery
- Monitoring and logging infrastructure

## 13. Monitoring and Observability

### 13.1 Application Metrics
- API response times and error rates
- Diet plan generation success/failure rates
- User engagement and retention metrics
- AI service usage and costs

### 13.2 Health Checks
- Database connectivity and performance
- AI service availability and response times
- Application server health and resource usage
- End-to-end functionality verification

### 13.3 Logging
- Structured logging for all API requests
- User action tracking (privacy-compliant)
- Error logging with context and stack traces
- AI interaction logging for debugging and improvement