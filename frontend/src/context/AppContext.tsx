import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { UserProfile, HealthGoals, DietPreferences } from '../services/api';

// Extended user interface for app state
export interface AppUser {
  id: string; // Changed from number to string for UUID
  profile?: UserProfile;
  goals?: HealthGoals;
  preferences?: DietPreferences;
}

export interface HealthContextDocument {
  id: string;
  version: number;
  content: string;
  bmr_calories: number;
  tdee_calories: number;
  min_daily_calories: number;
  max_calorie_deficit: number;
  min_protein_grams: number;
  created_at: string;
  is_active: boolean;
}

export interface DietPlan {
  id: string;
  plan_type: 'weekly' | 'daily';
  start_date: string;
  content: any;
  created_at: string;
}

export interface AppState {
  // User data
  user: AppUser | null;
  healthContext: HealthContextDocument | null;
  
  // Diet plans
  activePlan: DietPlan | null;
  planHistory: DietPlan[];
  
  // UI state
  isLoading: boolean;
  error: string | null;
  
  // Navigation state
  currentStep: 'profile' | 'goals' | 'preferences' | 'complete';
}

// Actions
export type AppAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_USER'; payload: AppUser | null }
  | { type: 'SET_HEALTH_CONTEXT'; payload: HealthContextDocument | null }
  | { type: 'SET_ACTIVE_PLAN'; payload: DietPlan | null }
  | { type: 'ADD_PLAN_TO_HISTORY'; payload: DietPlan }
  | { type: 'SET_PLAN_HISTORY'; payload: DietPlan[] }
  | { type: 'SET_CURRENT_STEP'; payload: AppState['currentStep'] }
  | { type: 'RESET_STATE' };

// Initial state
const initialState: AppState = {
  user: null,
  healthContext: null,
  activePlan: null,
  planHistory: [],
  isLoading: false,
  error: null,
  currentStep: 'profile',
};

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    
    case 'SET_USER':
      return { ...state, user: action.payload };
    
    case 'SET_HEALTH_CONTEXT':
      return { ...state, healthContext: action.payload };
    
    case 'SET_ACTIVE_PLAN':
      return { ...state, activePlan: action.payload };
    
    case 'ADD_PLAN_TO_HISTORY':
      return {
        ...state,
        planHistory: [action.payload, ...state.planHistory],
      };
    
    case 'SET_PLAN_HISTORY':
      return { ...state, planHistory: action.payload };
    
    case 'SET_CURRENT_STEP':
      return { ...state, currentStep: action.payload };
    
    case 'RESET_STATE':
      return initialState;
    
    default:
      return state;
  }
}

// Context
interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<AppAction>;
  
  // Helper functions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  isProfileComplete: () => boolean;
  canGeneratePlans: () => boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider
interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Helper functions
  const setLoading = (loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  };

  const setError = (error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  };

  const clearError = () => {
    dispatch({ type: 'SET_ERROR', payload: null });
  };

  const isProfileComplete = () => {
    return !!(state.user?.profile && state.user?.goals && state.user?.preferences);
  };

  const canGeneratePlans = () => {
    return isProfileComplete() && !!state.healthContext;
  };

  const contextValue: AppContextType = {
    state,
    dispatch,
    setLoading,
    setError,
    clearError,
    isProfileComplete,
    canGeneratePlans,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// Hook
export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export default AppContext;