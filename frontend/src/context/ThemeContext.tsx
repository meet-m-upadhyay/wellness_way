import React, { createContext, useContext, useReducer, useEffect, useCallback, ReactNode } from 'react';

// Types
export type Theme = 'light' | 'dark';

export interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
  systemPreference: Theme;
  isLoading: boolean;
}

interface ThemeState {
  theme: Theme;
  systemPreference: Theme;
  isLoading: boolean;
}

// Action types
type ThemeAction =
  | { type: 'SET_THEME'; payload: Theme }
  | { type: 'SET_SYSTEM_PREFERENCE'; payload: Theme }
  | { type: 'TOGGLE_THEME' }
  | { type: 'INIT_COMPLETE' };

// Initial state
const initialState: ThemeState = {
  theme: 'light',
  systemPreference: 'light',
  isLoading: true,
};

// Reducer
const themeReducer = (state: ThemeState, action: ThemeAction): ThemeState => {
  switch (action.type) {
    case 'SET_THEME':
      return {
        ...state,
        theme: action.payload,
      };
    case 'SET_SYSTEM_PREFERENCE':
      return {
        ...state,
        systemPreference: action.payload,
      };
    case 'TOGGLE_THEME':
      return {
        ...state,
        theme: state.theme === 'light' ? 'dark' : 'light',
      };
    case 'INIT_COMPLETE':
      return {
        ...state,
        isLoading: false,
      };
    default:
      return state;
  }
};

// Create context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Storage key
const THEME_STORAGE_KEY = 'wellnessway_theme_preference';

// Theme provider component
interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(themeReducer, initialState);

  // Detect system preference
  const getSystemPreference = useCallback((): Theme => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  }, []);

  // Apply theme to HTML element
  const applyTheme = useCallback((theme: Theme) => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      if (theme === 'dark') {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  }, []);

  // Load stored theme preference on mount
  useEffect(() => {
    const initializeTheme = () => {
      console.log('ThemeContext: Initializing theme...');
      
      try {
        // Get system preference
        const systemPref = getSystemPreference();
        dispatch({ type: 'SET_SYSTEM_PREFERENCE', payload: systemPref });

        // Try to load stored preference with error handling
        let storedTheme: Theme | null = null;
        try {
          if (typeof Storage !== 'undefined' && localStorage) {
            const stored = localStorage.getItem(THEME_STORAGE_KEY);
            if (stored === 'light' || stored === 'dark') {
              storedTheme = stored;
            } else if (stored !== null) {
              // Invalid stored value, clear it
              localStorage.removeItem(THEME_STORAGE_KEY);
              console.warn('ThemeContext: Invalid stored theme value cleared');
            }
          }
        } catch (error) {
          console.warn('ThemeContext: Failed to read from localStorage:', error);
          // Gracefully fallback to system preference
        }

        // Use stored preference or fall back to system preference, then light theme
        const initialTheme = storedTheme || systemPref || 'light';
        
        console.log('ThemeContext: Theme initialized', {
          systemPreference: systemPref,
          storedTheme,
          finalTheme: initialTheme
        });

        dispatch({ type: 'SET_THEME', payload: initialTheme });
        applyTheme(initialTheme);
        dispatch({ type: 'INIT_COMPLETE' });
      } catch (error) {
        console.error('ThemeContext: Critical error during theme initialization:', error);
        // Ultimate fallback to light theme
        dispatch({ type: 'SET_THEME', payload: 'light' });
        applyTheme('light');
        dispatch({ type: 'INIT_COMPLETE' });
      }
    };

    initializeTheme();

    // Listen for system preference changes with error handling
    if (typeof window !== 'undefined' && window.matchMedia) {
      try {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        const handleChange = (e: MediaQueryListEvent) => {
          try {
            const newSystemPref = e.matches ? 'dark' : 'light';
            dispatch({ type: 'SET_SYSTEM_PREFERENCE', payload: newSystemPref });
          } catch (error) {
            console.warn('ThemeContext: Error handling system preference change:', error);
          }
        };

        mediaQuery.addEventListener('change', handleChange);
        return () => {
          try {
            mediaQuery.removeEventListener('change', handleChange);
          } catch (error) {
            console.warn('ThemeContext: Error removing event listener:', error);
          }
        };
      } catch (error) {
        console.warn('ThemeContext: Error setting up system preference listener:', error);
      }
    }
  }, [getSystemPreference, applyTheme]);

  // Apply theme whenever it changes with error handling
  useEffect(() => {
    if (!state.isLoading) {
      try {
        applyTheme(state.theme);
        
        // Store preference with error handling
        try {
          if (typeof Storage !== 'undefined' && localStorage) {
            localStorage.setItem(THEME_STORAGE_KEY, state.theme);
          }
        } catch (error) {
          console.warn('ThemeContext: Failed to save to localStorage:', error);
          // Theme still works, just won't persist
        }
      } catch (error) {
        console.error('ThemeContext: Error applying theme:', error);
        // Try to fallback to light theme
        try {
          applyTheme('light');
        } catch (fallbackError) {
          console.error('ThemeContext: Critical error - even light theme failed:', fallbackError);
        }
      }
    }
  }, [state.theme, state.isLoading, applyTheme]);

  // Toggle theme function with debouncing
  const toggleTheme = useCallback(() => {
    // Simple debouncing to prevent rapid theme switching issues
    if (state.isLoading) return;
    
    dispatch({ type: 'TOGGLE_THEME' });
  }, [state.isLoading]);

  // Set specific theme function with validation
  const setTheme = useCallback((theme: Theme) => {
    // Validate theme value
    if (theme !== 'light' && theme !== 'dark') {
      console.warn('ThemeContext: Invalid theme value provided:', theme);
      return;
    }
    
    if (state.isLoading) return;
    
    dispatch({ type: 'SET_THEME', payload: theme });
  }, [state.isLoading]);

  const contextValue: ThemeContextType = {
    theme: state.theme,
    toggleTheme,
    setTheme,
    systemPreference: state.systemPreference,
    isLoading: state.isLoading,
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};

// Hook to use theme context
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};