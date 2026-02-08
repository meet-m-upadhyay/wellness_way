import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useAppContext } from '../context/AppContext';
import { 
  apiClient, 
  DietPlan, 
  adaptWeeklyPlanToLegacy, 
  adaptDailyPlanToLegacy,
  WeeklyPlanContent,
  DailyPlanContent,
  SafetyViolationError
} from '../services/api';
import PlanTypeSelector from '../components/diet-plans/PlanTypeSelector';
import DailyPlanView from '../components/diet-plans/DailyPlanView';
import WeeklyPlanView from '../components/diet-plans/WeeklyPlanView';
import SafetyViolationScreen from '../components/diet-plans/SafetyViolationScreen';
import BalanceGuidance from '../components/diet-plans/BalanceGuidance';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export const DietPlans: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth(); // Get user from AuthContext
  const { state, dispatch } = useAppContext();
  
  const [selectedPlanType, setSelectedPlanType] = useState<'daily' | 'weekly' | null>(null);
  const [currentPlan, setCurrentPlan] = useState<DietPlan | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [regeneratingMeal, setRegeneratingMeal] = useState<{ dayIndex: number; mealType: string } | null>(null);
  const [regeneratingDay, setRegeneratingDay] = useState<number | null>(null);
  const [isRegeneratingWeek, setIsRegeneratingWeek] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [safetyViolation, setSafetyViolation] = useState<SafetyViolationError | null>(null);
  const [loadingUser, setLoadingUser] = useState(false);
  const [loadingExistingPlan, setLoadingExistingPlan] = useState(false);

  // Check for userId in URL parameters
  const urlUserId = searchParams.get('userId');
  const currentUserId = user?.id || urlUserId; // Use AuthContext user instead of AppContext state.user

  // Debug logging
  console.log('DietPlans Debug:', {
    'user?.id (AuthContext)': user?.id,
    'state.user?.id (AppContext)': state.user?.id,
    urlUserId,
    currentUserId,
    'user (AuthContext)': user ? { id: user.id, email: user.email } : null,
    'state.user (AppContext)': state.user
  });

  // Load user from URL parameter if different from current user
  useEffect(() => {
    const loadUserFromUrl = async () => {
      if (urlUserId && urlUserId !== user?.id) { // Use AuthContext user
        setLoadingUser(true);
        try {
          // Get user profile
          const profileResponse = await apiClient.getUserProfile(urlUserId);
          if (profileResponse.error) {
            setError(`User not found: ${profileResponse.error}`);
            return;
          }

          // Get health goals
          const goalsResponse = await apiClient.getHealthGoals(urlUserId);
          
          // Get diet preferences
          const preferencesResponse = await apiClient.getDietPreferences(urlUserId);

          // Get health context
          const healthContextResponse = await apiClient.getHealthContext(urlUserId);

          // Set user data in context
          if (profileResponse.data) {
            dispatch({
              type: 'SET_USER',
              payload: {
                id: urlUserId,
                profile: profileResponse.data,
                goals: goalsResponse.data || undefined,
                preferences: preferencesResponse.data || undefined,
              }
            });
          }

          // Set health context if available
          if (healthContextResponse.data) {
            dispatch({
              type: 'SET_HEALTH_CONTEXT',
              payload: healthContextResponse.data
            });
          }

        } catch (err) {
          setError('Failed to load user data');
          console.error('Error loading user from URL:', err);
        } finally {
          setLoadingUser(false);
        }
      }
    };

    loadUserFromUrl();
  }, [urlUserId, user?.id, dispatch]); // Use AuthContext user

  // Redirect to profile setup if no user and no URL user ID
  useEffect(() => {
    if (!currentUserId && !loadingUser) {
      navigate('/profile-setup');
    }
  }, [currentUserId, loadingUser, navigate]);

  // Load user's latest diet plan on mount
  useEffect(() => {
    const loadLatestPlan = async () => {
      if (!currentUserId || loadingUser) return;

      setLoadingExistingPlan(true);
      try {
        // Get user's diet plans (latest first)
        const response = await apiClient.getUserDietPlans(currentUserId, undefined, 1);
        
        if (response.data && response.data.plans.length > 0) {
          const latestPlanSummary = response.data.plans[0];
          
          // Get the full plan details
          const planResponse = await apiClient.getDietPlan(latestPlanSummary.id, currentUserId);
          
          if (planResponse.data) {
            setCurrentPlan(planResponse.data);
            setSelectedPlanType(planResponse.data.plan_type as 'daily' | 'weekly');
            console.log('Loaded existing diet plan:', planResponse.data.id);
          }
        } else {
          console.log('No existing diet plans found for user');
        }
      } catch (err) {
        console.error('Error loading existing diet plan:', err);
        // Don't set error state - just continue without existing plan
      } finally {
        setLoadingExistingPlan(false);
      }
    };

    loadLatestPlan();
  }, [currentUserId, loadingUser]);

  const handleGeneratePlan = async (options?: { targetDate?: string; startDate?: string }) => {
    if (!selectedPlanType || !currentUserId) return;

    setIsGenerating(true);
    setError(null);
    setSafetyViolation(null);

    try {
      // Pass the date options to the API client
      const response = await apiClient.generateDietPlan(currentUserId, selectedPlanType, options || {});
      
      if (response.error) {
        // Check if this is a safety violation
        if (response.error === 'SAFETY_VIOLATION' && response.safetyViolation) {
          setSafetyViolation(response.safetyViolation);
          return;
        }
        throw new Error(response.error);
      }

      if (response.data) {
        setCurrentPlan(response.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate diet plan');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRegenerateMeal = async (dayIndex: number | undefined, mealType: string, useML: boolean = false) => {
    if (!currentPlan || !currentUserId) return;

    // Convert mealType to mealIndex
    const mealTypeToIndex = {
      'breakfast': 0,
      'lunch': 1,
      'dinner': 2,
      'snack': 3,
      'snack_1': 3,
      'snack_2': 4,
      'snack_3': 5
    };

    const mealIndex = mealTypeToIndex[mealType as keyof typeof mealTypeToIndex] ?? 0;
    const actualDayIndex = dayIndex !== undefined ? dayIndex : 0;

    const regeneratingData = { dayIndex: actualDayIndex, mealType };
    setRegeneratingMeal(regeneratingData);
    setError(null);
    setSafetyViolation(null);

    try {
      const response = await apiClient.regenerateMeal(currentPlan.id!, actualDayIndex, mealIndex, currentUserId, useML);
      
      if (response.error) {
        // Check if this is a safety violation
        if (response.error === 'SAFETY_VIOLATION' && response.safetyViolation) {
          setSafetyViolation(response.safetyViolation);
          return;
        }
        throw new Error(response.error);
      }

      if (response.data) {
        console.log('Meal regenerated successfully, updating plan:', response.data.id);
        console.log('New plan content:', JSON.stringify(response.data.content).substring(0, 200));
        // Force a new object reference to trigger React re-render
        setCurrentPlan({ ...response.data });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate meal');
    } finally {
      setRegeneratingMeal(null);
    }
  };

  const handleRegenerateDay = async (dayIndex: number, useML: boolean = false) => {
    if (!currentPlan || !currentUserId) return;

    setRegeneratingDay(dayIndex);
    setError(null);
    setSafetyViolation(null);

    try {
      const response = await apiClient.regenerateDay(currentPlan.id!, dayIndex, currentUserId, useML);
      
      if (response.error) {
        // Check if this is a safety violation
        if (response.error === 'SAFETY_VIOLATION' && response.safetyViolation) {
          setSafetyViolation(response.safetyViolation);
          return;
        }
        throw new Error(response.error);
      }

      if (response.data) {
        console.log('Day regenerated successfully, updating plan:', response.data.id);
        // Force a new object reference to trigger React re-render
        setCurrentPlan({ ...response.data });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate day');
    } finally {
      setRegeneratingDay(null);
    }
  };

  const handleRegenerateWeek = async (useML: boolean = false) => {
    if (!currentPlan || !currentUserId) return;

    setIsRegeneratingWeek(true);
    setError(null);
    setSafetyViolation(null);

    try {
      const response = await apiClient.regenerateFullPlan(currentPlan.id!, currentUserId, useML);
      
      if (response.error) {
        // Check if this is a safety violation
        if (response.error === 'SAFETY_VIOLATION' && response.safetyViolation) {
          setSafetyViolation(response.safetyViolation);
          return;
        }
        throw new Error(response.error);
      }

      if (response.data) {
        console.log('Week regenerated successfully, updating plan:', response.data.id);
        // Force a new object reference to trigger React re-render
        setCurrentPlan({ ...response.data });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to regenerate week');
    } finally {
      setIsRegeneratingWeek(false);
    }
  };

  const handleStartOver = () => {
    setCurrentPlan(null);
    setSelectedPlanType(null);
    setError(null);
    setSafetyViolation(null);
  };

  const handleRetryAfterSafetyViolation = () => {
    setSafetyViolation(null);
    handleGeneratePlan();
  };

  const handleGoBackFromSafetyViolation = () => {
    setSafetyViolation(null);
    setSelectedPlanType(null);
  };

  const handleGoToProfile = () => {
    navigate('/profile-setup');
  };

  if (!currentUserId || loadingUser || loadingExistingPlan) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" message=''/>
          {loadingUser && <p className="mt-4 text-gray-600 dark:text-gray-300">Loading user data...</p>}
          {loadingExistingPlan && <p className="mt-4 text-gray-600 dark:text-gray-300">Loading your diet plans...</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
            <div className="text-center sm:text-left">
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
                Welcome, {user?.name || 'User'}! {/* Use AuthContext user */}
              </h1>
              <p className="text-gray-600 dark:text-gray-300 mt-2">
                Let's create your personalized diet plan
              </p>
              {urlUserId && urlUserId !== user?.id && ( // Use AuthContext user
                <p className="text-sm text-indigo-600 dark:text-indigo-400 mt-1">
                  Viewing profile for user ID: {urlUserId}
                </p>
              )}
            </div>
            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-3">
              <button
                onClick={() => navigate('/')}
                className="flex items-center justify-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                <span className="hidden sm:inline">Back to Home</span>
                <span className="sm:hidden">Home</span>
              </button>
              <button
                onClick={handleGoToProfile}
                className="flex items-center justify-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <span className="hidden sm:inline">Edit Profile</span>
                <span className="sm:hidden">Profile</span>
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-8">
            <ErrorMessage message={error} />
          </div>
        )}

        {/* Safety Violation Screen */}
        {safetyViolation && (
          <SafetyViolationScreen
            violations={safetyViolation.violations}
            onRetry={handleRetryAfterSafetyViolation}
            onGoBack={handleGoBackFromSafetyViolation}
            isRetrying={isGenerating}
          />
        )}

        {/* Plan Generation or Display */}
        {!currentPlan && !safetyViolation ? (
          <PlanTypeSelector
            selectedType={selectedPlanType}
            onSelect={setSelectedPlanType}
            onGenerate={handleGeneratePlan}
            isLoading={isGenerating}
          />
        ) : currentPlan && !safetyViolation ? (
          <div>
            {/* Plan Header with Actions */}
            <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
              <div className="text-center sm:text-left">
                <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
                  Your {currentPlan.plan_type.charAt(0).toUpperCase() + currentPlan.plan_type.slice(1)} Plan
                </h2>
                <p className="text-gray-600 dark:text-gray-300">
                  Generated on {new Date(currentPlan.created_at!).toLocaleDateString()}
                </p>
              </div>
              <div className="flex justify-center sm:justify-end">
                <button
                  onClick={handleStartOver}
                  className="flex items-center justify-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  <span className="hidden sm:inline">Generate New Plan</span>
                  <span className="sm:hidden">New Plan</span>
                </button>
              </div>
            </div>

            {/* Plan Content */}
            {/* Balance Guidance */}
            {currentPlan.balance_guidance && (
              <div className="mb-6">
                <BalanceGuidance guidance={currentPlan.balance_guidance} />
              </div>
            )}
            
            {currentPlan.plan_type === 'daily' ? (
              <DailyPlanView
                plan={adaptDailyPlanToLegacy(currentPlan.content as DailyPlanContent)}
                onRegenerateMeal={(mealType, useML) => handleRegenerateMeal(undefined, mealType, useML)}
                onRegenerateDay={(useML) => handleRegenerateDay(0, useML)}
                regeneratingMeal={regeneratingMeal?.mealType || null}
                isRegeneratingDay={regeneratingDay === 0}
              />
            ) : (
              <WeeklyPlanView
                plan={adaptWeeklyPlanToLegacy(currentPlan.content as WeeklyPlanContent)}
                onRegenerateMeal={handleRegenerateMeal}
                onRegenerateDay={handleRegenerateDay}
                onRegenerateWeek={handleRegenerateWeek}
                regeneratingMeal={regeneratingMeal}
                regeneratingDay={regeneratingDay}
                isRegeneratingWeek={isRegeneratingWeek}
              />
            )}
          </div>
        ) : null}

        {/* Loading State */}
        {isGenerating && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-md mx-4">
              <div className="text-center">
                <LoadingSpinner size="lg" className="mx-auto mb-4" message=''/>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Generating Your Diet Plan
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Our AI is creating a personalized {selectedPlanType} plan based on your profile, goals, and preferences. This may take a moment...
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DietPlans;