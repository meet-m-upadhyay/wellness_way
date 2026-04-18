/**
 * API Client Service for WellnessWay Diet Planner
 * Handles all communication with the backend API
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
  safetyViolation?: SafetyViolationError;
}

export interface SafetyViolationError {
  status: 'rejected';
  violations: string[];
  message: string;
}

export interface UserProfile {
  id?: string; // Changed from number to string for UUID
  name: string;
  email?: string;
  age: number;
  gender: 'male' | 'female' | 'other';
  height_cm: number;
  weight_kg: number;
  body_fat_percentage?: number;
  muscle_mass_kg?: number;
  activity_level: 'sedentary' | 'lightly_active' | 'moderately_active' | 'very_active' | 'extremely_active';
  is_active?: boolean;
  is_admin?: boolean;
  profile_completed?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface HealthGoals {
  id?: string; // Changed from number to string for UUID
  user_id?: string; // Changed from number to string for UUID
  primary_goal: 'fat_loss' | 'muscle_gain' | 'maintenance';
  target_weight_kg?: number;
  timeline_weeks?: number;
}

export interface DietPreferences {
  id?: string; // Changed from number to string for UUID
  user_id?: string; // Changed from number to string for UUID
  diet_type: 'vegetarian' | 'non_vegetarian' | 'vegan';
  allergies: string[];
  foods_to_avoid: string[];
  meals_per_day?: number;
  cuisine: string;
  reuse_ingredients: boolean;
  budget_constraints?: string;
  lifestyle_constraints?: string;
}

export interface CompleteProfile {
  profile: UserProfile;
  goals: HealthGoals;
  preferences: DietPreferences;
}

export interface Ingredient {
  name: string;
  quantity: number;
  unit: string;
}

export interface Nutrition {
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber?: number;
  sodium?: number;
}

export interface Meal {
  type: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  name: string;
  ingredients: Ingredient[];
  instructions: string;
  nutrition: Nutrition;
}

export interface DayPlan {
  date: string; // YYYY-MM-DD format
  day_name: string;
  meals: Meal[];
  daily_totals: Nutrition;
}

export interface WeeklyPlanContent {
  plan_type: 'weekly';
  start_date: string; // YYYY-MM-DD format
  days: DayPlan[];
  weekly_totals: Nutrition;
  summary?: string;
  notes?: string;
}

export interface DailyPlanContent {
  plan_type: 'daily';
  date: string; // YYYY-MM-DD format
  day_name: string;
  meals: Meal[];
  daily_totals: Nutrition;
  summary?: string;
  notes?: string;
}

export interface BalanceGuidance {
  type: string; // "info" | "warning"
  severity: string; // "low" | "medium"
  message: string;
  calorie_delta: number;
  protein_delta: number;
}

export interface DietPlan {
  id: string; // UUID
  user_id: string; // UUID
  hcd_id: string; // UUID
  plan_type: 'daily' | 'weekly';
  start_date: string; // Date string
  content: WeeklyPlanContent | DailyPlanContent;
  created_at: string; // ISO datetime string
  validation_status?: string; // "compliant" | "buffer_accepted" | "auto_corrected" | "rejected"
  validation_violations?: string[];
  balance_guidance?: BalanceGuidance; // NEW: Optional balance guidance
}

export interface DietPlanSummary {
  id: string; // UUID
  plan_type: 'daily' | 'weekly';
  start_date: string; // Date string
  created_at: string; // ISO datetime string
  total_calories?: number;
  total_meals?: number;
}

export interface DietPlanSummaryListResponse {
  plans: DietPlanSummary[];
  total: number;
}

export interface Message {
  id: string;
  chat_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata_json?: any;
  created_at: string;
}

export interface Chat {
  id: string;
  user_id: string;
  title?: string;
  created_at: string;
  messages?: Message[];
}

// Legacy interfaces for backward compatibility with existing components
export interface LegacyMeal {
  name: string;
  ingredients: string[];
  instructions: string;
  nutrition: {
    calories: number;
    protein_g: number;
    carbs_g: number;
    fat_g: number;
    fiber_g?: number;
  };
}

export interface LegacyDailyPlan {
  date: string;
  meals: {
    breakfast: LegacyMeal;
    lunch: LegacyMeal;
    dinner: LegacyMeal;
    snacks?: LegacyMeal[];
  };
  daily_nutrition: {
    total_calories: number;
    total_protein_g: number;
    total_carbs_g: number;
    total_fat_g: number;
  };
  summary?: string;
  notes?: string;
}

export interface LegacyWeeklyPlan {
  start_date: string;
  days: LegacyDailyPlan[];
  weekly_nutrition: {
    avg_daily_calories: number;
    avg_daily_protein_g: number;
    avg_daily_carbs_g: number;
    avg_daily_fat_g: number;
  };
  summary?: string;
  notes?: string;
}

// Adapter functions to convert new interfaces to legacy format
export function adaptMealToLegacy(meal: Meal): LegacyMeal {
  return {
    name: meal.name,
    ingredients: meal.ingredients.map(ing => `${Math.round(ing.quantity)} ${ing.unit} ${ing.name}`),
    instructions: meal.instructions,
    nutrition: {
      calories: meal.nutrition.calories,
      protein_g: meal.nutrition.protein,
      carbs_g: meal.nutrition.carbohydrates,
      fat_g: meal.nutrition.fat,
      fiber_g: meal.nutrition.fiber,
    }
  };
}

export function adaptDayPlanToLegacy(dayPlan: DayPlan): LegacyDailyPlan {
  const mealsByType: { [key: string]: Meal } = {};
  const snacks: Meal[] = [];

  dayPlan.meals.forEach(meal => {
    if (meal.type === 'snack') {
      snacks.push(meal);
    } else {
      mealsByType[meal.type] = meal;
    }
  });

  // CRITICAL FIX: Calculate nutrition totals from actual meal data
  const calculatedNutrition = calculateNutritionTotals(dayPlan.meals);

  // Check for discrepancies and log warnings
  const aiProtein = dayPlan.daily_totals.protein;
  const actualProtein = calculatedNutrition.total_protein_g;

  if (Math.abs(aiProtein - actualProtein) > Math.max(aiProtein * 0.1, 5)) {
    console.warn(`Nutrition calculation mismatch detected: AI claimed ${aiProtein}g protein, actual ${actualProtein}g. Using calculated values.`);
  }

  return {
    date: dayPlan.date,
    meals: {
      breakfast: adaptMealToLegacy(mealsByType.breakfast),
      lunch: adaptMealToLegacy(mealsByType.lunch),
      dinner: adaptMealToLegacy(mealsByType.dinner),
      snacks: snacks.length > 0 ? snacks.map(adaptMealToLegacy) : undefined,
    },
    daily_nutrition: calculatedNutrition, // Use calculated values instead of AI totals
  };
}

export function adaptWeeklyPlanToLegacy(weeklyPlan: WeeklyPlanContent): LegacyWeeklyPlan {
  const adaptedDays = weeklyPlan.days.map(adaptDayPlanToLegacy);

  // Calculate weekly nutrition from corrected daily values
  const weeklyNutrition = {
    avg_daily_calories: 0,
    avg_daily_protein_g: 0,
    avg_daily_carbs_g: 0,
    avg_daily_fat_g: 0,
  };

  adaptedDays.forEach(day => {
    weeklyNutrition.avg_daily_calories += day.daily_nutrition.total_calories;
    weeklyNutrition.avg_daily_protein_g += day.daily_nutrition.total_protein_g;
    weeklyNutrition.avg_daily_carbs_g += day.daily_nutrition.total_carbs_g;
    weeklyNutrition.avg_daily_fat_g += day.daily_nutrition.total_fat_g;
  });

  // Calculate averages
  weeklyNutrition.avg_daily_calories = Math.round((weeklyNutrition.avg_daily_calories / 7) * 10) / 10;
  weeklyNutrition.avg_daily_protein_g = Math.round((weeklyNutrition.avg_daily_protein_g / 7) * 10) / 10;
  weeklyNutrition.avg_daily_carbs_g = Math.round((weeklyNutrition.avg_daily_carbs_g / 7) * 10) / 10;
  weeklyNutrition.avg_daily_fat_g = Math.round((weeklyNutrition.avg_daily_fat_g / 7) * 10) / 10;

  return {
    start_date: weeklyPlan.start_date,
    days: adaptedDays,
    weekly_nutrition: weeklyNutrition, // Use calculated averages
    summary: weeklyPlan.summary,
    notes: weeklyPlan.notes,
  };
}

export function adaptDailyPlanToLegacy(dailyPlan: DailyPlanContent): LegacyDailyPlan {
  const mealsByType: { [key: string]: Meal } = {};
  const snacks: Meal[] = [];

  dailyPlan.meals.forEach(meal => {
    if (meal.type === 'snack') {
      snacks.push(meal);
    } else {
      mealsByType[meal.type] = meal;
    }
  });

  // CRITICAL FIX: Calculate nutrition totals from actual meal data
  // This prevents displaying incorrect AI-calculated totals
  const calculatedNutrition = calculateNutritionTotals(dailyPlan.meals);

  // Check for discrepancies and log warnings
  const aiProtein = dailyPlan.daily_totals.protein;
  const actualProtein = calculatedNutrition.total_protein_g;

  if (Math.abs(aiProtein - actualProtein) > Math.max(aiProtein * 0.1, 5)) {
    console.warn(`Nutrition calculation mismatch detected: AI claimed ${aiProtein}g protein, actual ${actualProtein}g. Using calculated values.`);
  }

  return {
    date: dailyPlan.date,
    meals: {
      breakfast: adaptMealToLegacy(mealsByType.breakfast),
      lunch: adaptMealToLegacy(mealsByType.lunch),
      dinner: adaptMealToLegacy(mealsByType.dinner),
      snacks: snacks.length > 0 ? snacks.map(adaptMealToLegacy) : undefined,
    },
    daily_nutrition: calculatedNutrition, // Use calculated values instead of AI totals
    summary: dailyPlan.summary,
    notes: dailyPlan.notes,
  };
}

// Helper function to calculate accurate nutrition totals from meals
function calculateNutritionTotals(meals: Meal[]): {
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fat_g: number;
} {
  const totals = {
    total_calories: 0,
    total_protein_g: 0,
    total_carbs_g: 0,
    total_fat_g: 0,
  };

  meals.forEach(meal => {
    const nutrition = meal.nutrition;
    totals.total_calories += nutrition.calories || 0;
    totals.total_protein_g += nutrition.protein || 0;
    totals.total_carbs_g += nutrition.carbohydrates || 0;
    totals.total_fat_g += nutrition.fat || 0;
  });

  // Round to 1 decimal place for consistency
  return {
    total_calories: Math.round(totals.total_calories * 10) / 10,
    total_protein_g: Math.round(totals.total_protein_g * 10) / 10,
    total_carbs_g: Math.round(totals.total_carbs_g * 10) / 10,
    total_fat_g: Math.round(totals.total_fat_g * 10) / 10,
  };
}

// ============================================================
// V2 Meal Engine Types & Adapters
// ============================================================

export interface V2MealComponent {
  llm_name: string;
  resolved_code: string | null;
  resolved_name: string;
  match_method: string;
  match_confidence: number;
  grams: number;
  role: string;
  food_group: string;
}

export interface V2ScoreBreakdown {
  macro_accuracy: number;
  plate_composition: number;
  culinary_coherence: number;
  micro_diversity: number;
  goal_alignment: number;
  practicality: number;
  total: number;
  band: string;
}

export interface V2SingleMeal {
  archetype: string;
  dish_name: string;
  components: V2MealComponent[];
  macros: { calories: number; protein: number; carbs: number; fat: number; fiber: number };
  score: V2ScoreBreakdown;
  cultural_note?: string;
  prep_time_minutes?: number;
  quality_warning: boolean;
}

export interface V2DailyPlanResponse {
  id?: string;
  meals: V2SingleMeal[];
  daily_totals: { calories: number; protein: number; carbs: number; fat: number; fiber: number };
  goal: string;
  macro_display_order: string[];
  engine_version?: string;
}

/** Convert a V2 meal to LegacyMeal for existing components. */
export function adaptV2MealToLegacy(v2Meal: V2SingleMeal, mealType: string): LegacyMeal {
  return {
    name: v2Meal.dish_name,
    ingredients: v2Meal.components.map(c =>
      `${Math.round(c.grams)} g ${c.resolved_name}`
    ),
    instructions: v2Meal.cultural_note || `${v2Meal.archetype} meal — ${v2Meal.components.map(c => c.resolved_name).join(', ')}`,
    nutrition: {
      calories: v2Meal.macros.calories,
      protein_g: v2Meal.macros.protein,
      carbs_g: v2Meal.macros.carbs,
      fat_g: v2Meal.macros.fat,
      fiber_g: v2Meal.macros.fiber,
    },
  };
}

/** Convert a V2 daily plan response to LegacyDailyPlan for existing components. */
export function adaptV2DailyToLegacy(v2Plan: V2DailyPlanResponse): LegacyDailyPlan {
  const mealTypes = ['breakfast', 'lunch', 'dinner'];
  const meals: { [key: string]: LegacyMeal } = {};
  const snacks: LegacyMeal[] = [];

  v2Plan.meals.forEach((v2Meal, i) => {
    const mealType = mealTypes[i] || 'snack';
    const legacy = adaptV2MealToLegacy(v2Meal, mealType);
    if (mealType === 'snack') {
      snacks.push(legacy);
    } else {
      meals[mealType] = legacy;
    }
  });

  // Fill missing meal types with empty placeholders
  for (const mt of mealTypes) {
    if (!meals[mt]) {
      meals[mt] = { name: `No ${mt}`, ingredients: [], instructions: '', nutrition: { calories: 0, protein_g: 0, carbs_g: 0, fat_g: 0 } };
    }
  }

  return {
    date: new Date().toISOString().split('T')[0],
    meals: {
      breakfast: meals.breakfast,
      lunch: meals.lunch,
      dinner: meals.dinner,
      snacks: snacks.length > 0 ? snacks : undefined,
    },
    daily_nutrition: {
      total_calories: v2Plan.daily_totals.calories,
      total_protein_g: v2Plan.daily_totals.protein,
      total_carbs_g: v2Plan.daily_totals.carbs,
      total_fat_g: v2Plan.daily_totals.fat,
    },
    summary: `V2 Engine | Goal: ${v2Plan.goal} | Scores: ${v2Plan.meals.map(m => `${m.score.total.toFixed(0)}`).join('/')}`,
    notes: v2Plan.macro_display_order ? `Macro priority: ${v2Plan.macro_display_order.join(' > ')}` : undefined,
  };
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = localStorage.getItem('health_buddy_access_token');
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
      };
    }
    return {};
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders(),
          ...options.headers,
        },
        ...options,
      });

      const data = await response.json();

      if (!response.ok) {
        // Handle 401 Unauthorized - token might be expired
        if (response.status === 401) {
          // Try to refresh token
          const refreshToken = localStorage.getItem('health_buddy_refresh_token');
          if (refreshToken) {
            try {
              const refreshResponse = await fetch(`${this.baseUrl}/auth/refresh`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken }),
              });

              if (refreshResponse.ok) {
                const tokens = await refreshResponse.json();
                localStorage.setItem('health_buddy_access_token', tokens.access_token);
                localStorage.setItem('health_buddy_refresh_token', tokens.refresh_token);

                // Retry original request with new token
                const retryResponse = await fetch(url, {
                  headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokens.access_token}`,
                    ...options.headers,
                  },
                  ...options,
                });

                if (retryResponse.ok) {
                  const retryData = await retryResponse.json();
                  return {
                    data: retryData,
                    status: retryResponse.status,
                  };
                }
              }
            } catch (refreshError) {
              // Refresh failed, redirect to login
              this.handleAuthFailure();
            }
          } else {
            // No refresh token, redirect to login
            this.handleAuthFailure();
          }
        }

        // Handle 422 Unprocessable Entity (Safety Violations)
        if (response.status === 422 && data && typeof data === 'object') {
          // Check if this is a safety violation response
          if (data.status === 'rejected' && data.violations && Array.isArray(data.violations)) {
            return {
              error: 'SAFETY_VIOLATION',
              safetyViolation: data as SafetyViolationError,
              status: response.status,
            };
          }
        }

        return {
          error: data.detail || `HTTP ${response.status}: ${response.statusText}`,
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  private handleAuthFailure() {
    // Clear stored tokens
    localStorage.removeItem('health_buddy_access_token');
    localStorage.removeItem('health_buddy_refresh_token');
    localStorage.removeItem('health_buddy_user');

    // Redirect to login page
    window.location.href = '/login';
  }

  // User Profile API
  async getAllUsers(limit?: number, offset?: number): Promise<ApiResponse<UserProfile[]>> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';

    return this.request<UserProfile[]>(`/users/profiles${queryString}`);
  }

  async createUserProfile(profile: UserProfile): Promise<ApiResponse<UserProfile>> {
    return this.request<UserProfile>('/users/profile', {
      method: 'POST',
      body: JSON.stringify(profile),
    });
  }

  async getUserProfile(userId: string): Promise<ApiResponse<UserProfile>> {
    return this.request<UserProfile>(`/users/profile/${userId}`);
  }

  async updateUserProfile(userId: string, profile: Partial<UserProfile>): Promise<ApiResponse<UserProfile>> {
    return this.request<UserProfile>(`/users/profile/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(profile),
    });
  }

  // Health Goals API
  async createHealthGoals(userId: string, goals: HealthGoals): Promise<ApiResponse<HealthGoals>> {
    return this.request<HealthGoals>(`/users/profile/${userId}/goals`, {
      method: 'POST',
      body: JSON.stringify(goals),
    });
  }

  async getHealthGoals(userId: string): Promise<ApiResponse<HealthGoals>> {
    return this.request<HealthGoals>(`/users/profile/${userId}/goals`);
  }

  async updateHealthGoals(userId: string, goals: Partial<HealthGoals>): Promise<ApiResponse<HealthGoals>> {
    return this.request<HealthGoals>(`/users/profile/${userId}/goals`, {
      method: 'PUT',
      body: JSON.stringify(goals),
    });
  }

  // Diet Preferences API
  async createDietPreferences(userId: string, preferences: DietPreferences): Promise<ApiResponse<DietPreferences>> {
    return this.request<DietPreferences>(`/users/profile/${userId}/preferences`, {
      method: 'POST',
      body: JSON.stringify(preferences),
    });
  }

  async getDietPreferences(userId: string): Promise<ApiResponse<DietPreferences>> {
    return this.request<DietPreferences>(`/users/profile/${userId}/preferences`);
  }

  async updateDietPreferences(userId: string, preferences: Partial<DietPreferences>): Promise<ApiResponse<DietPreferences>> {
    return this.request<DietPreferences>(`/users/profile/${userId}/preferences`, {
      method: 'PUT',
      body: JSON.stringify(preferences),
    });
  }

  // Complete Profile API
  async createCompleteProfile(profile: CompleteProfile): Promise<ApiResponse<CompleteProfile & { user_id: string }>> {
    // Use the authenticated user endpoint that doesn't require email
    const response = await this.request<any>('/users/my-profile', {
      method: 'POST',
      body: JSON.stringify(profile),
    });

    if (response.data) {
      // Extract user_id from the profile response
      return {
        ...response,
        data: {
          ...response.data,
          user_id: response.data.profile.id
        }
      };
    }

    return response as ApiResponse<CompleteProfile & { user_id: string }>;
  }

  async getCompleteProfile(userId: string): Promise<ApiResponse<CompleteProfile>> {
    return this.request<CompleteProfile>(`/users/complete-profile/${userId}`);
  }

  // Health Context Document API
  async generateHealthContext(userId: string): Promise<ApiResponse<{ document_id: string }>> {
    return this.request<{ document_id: string }>(`/health-context/${userId}/update-from-profile`, {
      method: 'POST',
      headers: {
        'X-User-Id': userId,
      },
    });
  }

  async getHealthContext(userId: string, version?: number): Promise<ApiResponse<any>> {
    const endpoint = version
      ? `/health-context/${userId}/version/${version}`
      : `/health-context/${userId}/current`;
    return this.request<any>(endpoint);
  }

  async getHealthContextHistory(userId: string, limit?: number, offset?: number): Promise<ApiResponse<any>> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';

    return this.request<any>(`/health-context/${userId}/history${queryString}`);
  }

  async getHealthContextMetrics(userId: string, version?: number): Promise<ApiResponse<any>> {
    const params = version ? `?version=${version}` : '';
    return this.request<any>(`/health-context/${userId}/metrics${params}`);
  }

  // Diet Plan API
  async generateDietPlan(
    userId: string,
    planType: 'daily' | 'weekly',
    options?: { regenerate?: boolean; startDate?: string; targetDate?: string }
  ): Promise<ApiResponse<DietPlan>> {
    // ALWAYS use ML pipeline now
    const baseEndpoint = '/diet-plans-ml';
    const endpoint = planType === 'weekly' ? `${baseEndpoint}/weekly` : `${baseEndpoint}/daily`;

    // Prepare request body based on plan type
    let body: any = {};

    if (planType === 'weekly') {
      if (options?.startDate) {
        body.start_date = options.startDate;
      }
      // If no start date provided, backend will default to next Monday
    } else {
      // For daily plans, only include target_date if it's provided
      if (options?.targetDate) {
        body.target_date = options.targetDate;
      }
      // If no target date provided, backend will default to today
    }

    return this.request<DietPlan>(endpoint, {
      method: 'POST',
      headers: {
        'X-User-Id': userId, // Pass user ID in header for authentication
      },
      body: JSON.stringify(body),
    });
  }

  // V2 Meal Engine API
  async generateV2DailyPlan(
    userId: string,
    cuisine?: string,
  ): Promise<ApiResponse<V2DailyPlanResponse>> {
    return this.request<V2DailyPlanResponse>('/v2/meal-engine/generate-daily', {
      method: 'POST',
      headers: { 'X-User-Id': userId },
      body: JSON.stringify({
        meal_type: 'lunch',
        cuisine: cuisine || 'indian',
        plan_type: 'daily',
      }),
    });
  }

  async generateV2SingleMeal(
    userId: string,
    mealType: string = 'lunch',
    cuisine?: string,
  ): Promise<ApiResponse<V2SingleMeal>> {
    return this.request<V2SingleMeal>('/v2/meal-engine/generate-meal', {
      method: 'POST',
      headers: { 'X-User-Id': userId },
      body: JSON.stringify({
        meal_type: mealType,
        cuisine: cuisine || 'indian',
      }),
    });
  }

  async getLatestV2Plan(userId: string): Promise<ApiResponse<V2DailyPlanResponse | null>> {
    return this.request<V2DailyPlanResponse | null>('/v2/meal-engine/latest', {
      headers: { 'X-User-Id': userId },
    });
  }

  async getDietPlan(planId: string, userId: string): Promise<ApiResponse<DietPlan>> {
    return this.request<DietPlan>(`/diet-plans-ml/${planId}`, {
      headers: {
        'X-User-Id': userId,
      },
    });
  }

  async getUserDietPlans(userId: string, planType?: 'daily' | 'weekly', limit?: number): Promise<ApiResponse<DietPlanSummaryListResponse>> {
    const params = new URLSearchParams();
    if (planType) params.append('plan_type', planType);
    if (limit) params.append('limit', limit.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';

    return this.request<DietPlanSummaryListResponse>(`/diet-plans-ml/${queryString}`, {
      headers: {
        'X-User-Id': userId,
      },
    });
  }

  async regenerateMeal(
    planId: string,
    dayIndex: number,
    mealIndex: number,
    userId: string
  ): Promise<ApiResponse<DietPlan>> {
    const endpoint = `/diet-plans-ml/${planId}/regenerate-meal-ml`;

    return this.request<DietPlan>(endpoint, {
      method: 'POST',
      headers: {
        'X-User-Id': userId,
      },
      body: JSON.stringify({
        day_index: dayIndex,
        meal_index: mealIndex
      }),
    });
  }

  async regenerateDay(
    planId: string,
    dayIndex: number,
    userId: string
  ): Promise<ApiResponse<DietPlan>> {
    const endpoint = `/diet-plans-ml/${planId}/regenerate-day-ml`;

    return this.request<DietPlan>(endpoint, {
      method: 'POST',
      headers: {
        'X-User-Id': userId,
      },
      body: JSON.stringify({ day_index: dayIndex }),
    });
  }

  async regenerateFullPlan(
    planId: string,
    userId: string
  ): Promise<ApiResponse<DietPlan>> {
    const endpoint = `/diet-plans-ml/${planId}/regenerate-ml`;

    return this.request<DietPlan>(endpoint, {
      method: 'POST',
      headers: {
        'X-User-Id': userId,
      },
    });
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request<{ status: string }>('/health');
  }

  // Database health check
  async databaseHealthCheck(): Promise<ApiResponse<{ status: string; database: string }>> {
    return this.request<{ status: string; database: string }>('/db-health');
  }

  // Chat API
  async createChat(userId: string, title?: string): Promise<ApiResponse<Chat>> {
    return this.request<Chat>('/chats/', {
      method: 'POST',
      headers: {
        'X-User-Id': userId,
      },
      body: JSON.stringify({ title }),
    });
  }

  async getChats(userId: string): Promise<ApiResponse<Chat[]>> {
    return this.request<Chat[]>('/chats/', {
      headers: {
        'X-User-Id': userId,
      },
    });
  }

  async getChatDetail(chatId: string, userId: string): Promise<ApiResponse<Chat>> {
    return this.request<Chat>(`/chats/${chatId}`, {
      headers: {
        'X-User-Id': userId,
      },
    });
  }

  async addMessage(chatId: string, role: string, content: string, userId: string, metadata?: any): Promise<ApiResponse<Message>> {
    return this.request<Message>(`/chats/${chatId}/messages`, {
      method: 'POST',
      headers: {
        'X-User-Id': userId,
      },
      body: JSON.stringify({ role, content, metadata_json: metadata }),
    });
  }

  // Delete diet plan
  async deleteDietPlan(planId: string, userId: string): Promise<ApiResponse<{ message: string }>> {
    return this.request<{ message: string }>(`/diet-plans-ml/${planId}`, {
      method: 'DELETE',
      headers: {
        'X-User-Id': userId,
      },
    });
  }

  // Delete user profile
  async deleteUserProfile(userId: string): Promise<ApiResponse<void>> {
    return this.request<void>(`/users/profile/${userId}`, {
      method: 'DELETE',
    });
  }
}

export const apiClient = new ApiClient();
export default apiClient;