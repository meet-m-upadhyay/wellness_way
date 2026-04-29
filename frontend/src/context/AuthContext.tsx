import React, { createContext, useContext, useReducer, useEffect, useCallback, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';

// Types
interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  is_admin: boolean;
  profile_completed: boolean;
  created_at: string;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  isDisabled: boolean; // New field to track if user is disabled
}

interface AuthContextType extends AuthState {
  login: (credential: string) => Promise<void>;
  emailLogin: (email: string, password: string) => Promise<void>;
  emailSignup: (name: string, email: string, password: string, confirmPassword: string) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  clearError: () => void;
  updateUser: (user: User) => void;
  refreshUserInfo: () => Promise<void>;
  checkUserStatus: () => Promise<void>; // New method to check if user is still active
}

// Action types
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; tokens: AuthTokens } }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'TOKEN_REFRESH_SUCCESS'; payload: AuthTokens }
  | { type: 'UPDATE_USER'; payload: User }
  | { type: 'USER_DISABLED' }
  | { type: 'AUTH_INIT_COMPLETE' }; // New action for completing initialization without error

// Initial state
const initialState: AuthState = {
  user: null,
  tokens: null,
  isAuthenticated: false,
  isLoading: true, // Start with loading = true to prevent premature redirects
  error: null,
  isDisabled: false, // New field
};

// Reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        tokens: action.payload.tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case 'AUTH_ERROR':
      return {
        ...state,
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false, // Important: set loading to false
        error: action.payload,
        isDisabled: false, // Reset disabled state on error
      };
    case 'AUTH_LOGOUT':
      return {
        ...initialState,
        isLoading: false, // Ensure loading is false after logout
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'TOKEN_REFRESH_SUCCESS':
      return {
        ...state,
        tokens: action.payload,
      };
    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload,
        isDisabled: !action.payload.is_active, // Update disabled status
      };
    case 'USER_DISABLED':
      return {
        ...state,
        isDisabled: true,
        isAuthenticated: false, // User is no longer considered authenticated
      };
    case 'AUTH_INIT_COMPLETE':
      return {
        ...state,
        isLoading: false,
        error: null, // Clear any previous errors
      };
    default:
      return state;
  }
};

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Storage keys
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'health_buddy_access_token',
  REFRESH_TOKEN: 'health_buddy_refresh_token',
  USER: 'health_buddy_user',
};

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // API base URL
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

  // Check if token is expired
  const isTokenExpired = (token: string): boolean => {
    try {
      const decoded: any = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      return decoded.exp < currentTime;
    } catch {
      return true;
    }
  };

  // Store authentication data
  const storeAuth = (user: User, tokens: AuthTokens) => {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
  };

  // Clear stored authentication data
  const clearStoredAuth = useCallback(() => {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER);
  }, []);

  // Logout
  const logout = useCallback(() => {
    // Clear stored data
    clearStoredAuth();

    // Optional: Call logout endpoint to invalidate tokens on server
    if (state.tokens?.refresh_token) {
      fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${state.tokens.access_token}`,
        },
        body: JSON.stringify({ refresh_token: state.tokens.refresh_token }),
      }).catch(() => {
        // Ignore errors on logout
      });
    }

    dispatch({ type: 'AUTH_LOGOUT' });
  }, [state.tokens, API_BASE_URL, clearStoredAuth]);

  // Refresh access token
  const refreshTokens = useCallback(async (refreshToken: string): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const tokens: AuthTokens = await response.json();

      // Update stored tokens
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);

      dispatch({
        type: 'TOKEN_REFRESH_SUCCESS',
        payload: tokens,
      });
    } catch (error) {
      // Refresh failed, clear stored data and logout user
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.USER);
      dispatch({ type: 'AUTH_LOGOUT' });
      throw error;
    }
  }, [API_BASE_URL]);

  // Load stored authentication data on mount
  useEffect(() => {
    const loadStoredAuth = async () => {
      console.log('AuthContext: Loading stored auth...');
      const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
      const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
      const userStr = localStorage.getItem(STORAGE_KEYS.USER);

      console.log('AuthContext: Storage check', {
        hasAccessToken: !!accessToken,
        hasRefreshToken: !!refreshToken,
        hasUser: !!userStr
      });

      if (accessToken && refreshToken && userStr) {
        try {
          const user = JSON.parse(userStr);
          
          // Check if access token is expired
          if (isTokenExpired(accessToken)) {
            console.log('AuthContext: Access token expired, trying to refresh...');
            // Try to refresh token
            try {
              const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken }),
              });

              if (response.ok) {
                const tokens: AuthTokens = await response.json();
                
                // Update stored tokens
                localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.access_token);
                localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refresh_token);

                console.log('AuthContext: Token refresh successful');
                dispatch({
                  type: 'AUTH_SUCCESS',
                  payload: { user, tokens },
                });
              } else {
                console.log('AuthContext: Token refresh failed, clearing storage');
                // Refresh failed, clear stored data
                localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
                localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
                localStorage.removeItem(STORAGE_KEYS.USER);
                // Set loading to false since we're done trying to restore auth
                dispatch({ type: 'AUTH_INIT_COMPLETE' });
              }
            } catch (error) {
              console.log('AuthContext: Token refresh error, clearing storage');
              // Refresh failed, clear stored data
              localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
              localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
              localStorage.removeItem(STORAGE_KEYS.USER);
              // Set loading to false since we're done trying to restore auth
              dispatch({ type: 'AUTH_INIT_COMPLETE' });
            }
          } else {
            console.log('AuthContext: Access token valid, restoring auth state');
            // Restore authentication state
            const tokens: AuthTokens = {
              access_token: accessToken,
              refresh_token: refreshToken,
              token_type: 'bearer',
              expires_in: 30 * 60, // 30 minutes
            };
            
            // Check if user is disabled
            if (!user.is_active) {
              console.log('AuthContext: User is disabled, showing disabled page');
              dispatch({ type: 'USER_DISABLED' });
              return;
            }
            
            dispatch({
              type: 'AUTH_SUCCESS',
              payload: { user, tokens },
            });
          }
        } catch (error) {
          console.log('AuthContext: Error parsing stored data, clearing storage');
          // Clear invalid stored data
          localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
          localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
          localStorage.removeItem(STORAGE_KEYS.USER);
          // Set loading to false since we're done trying to restore auth
          dispatch({ type: 'AUTH_INIT_COMPLETE' });
        }
      } else {
        console.log('AuthContext: No stored auth data found');
        // No stored auth data, complete initialization without error
        dispatch({ type: 'AUTH_INIT_COMPLETE' });
      }
    };

    loadStoredAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array - only run on mount

  // Login with Google credential
  const login = async (credential: string): Promise<void> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await fetch(`${API_BASE_URL}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: credential }),
      });

      // Handle pending approval (HTTP 202)
      if (response.status === 202) {
        const errorData = await response.json();
        dispatch({ type: 'AUTH_ERROR', payload: 'User approval pending' });
        // Throw structured error that LoginPage can parse
        throw new Error(`HTTP 202: ${JSON.stringify(errorData.detail)}`);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const data = await response.json();
      const { user, tokens } = data;

      // Check if user is disabled after successful authentication
      if (!user.is_active) {
        dispatch({ type: 'USER_DISABLED' });
        throw new Error('User account is disabled');
      }

      // Store authentication data
      storeAuth(user, tokens);

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: { user, tokens },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
      dispatch({
        type: 'AUTH_ERROR',
        payload: errorMessage,
      });
      throw error;
    }
  };

  const emailLogin = async (email: string, password: string): Promise<void> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (response.status === 202) {
        const errorData = await response.json();
        dispatch({ type: 'AUTH_ERROR', payload: 'User approval pending' });
        throw new Error(`HTTP 202: ${JSON.stringify(errorData.detail)}`);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Authentication failed');
      }

      const data = await response.json();
      const { user, tokens } = data;

      if (!user.is_active) {
        dispatch({ type: 'USER_DISABLED' });
        throw new Error('User account is disabled');
      }

      storeAuth(user, tokens);

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: { user, tokens },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Authentication failed';
      dispatch({
        type: 'AUTH_ERROR',
        payload: errorMessage,
      });
      throw error;
    }
  };

  const emailSignup = async (
    name: string,
    email: string,
    password: string,
    confirmPassword: string
  ): Promise<void> => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await fetch(`${API_BASE_URL}/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          email,
          password,
          confirm_password: confirmPassword,
        }),
      });

      if (response.status === 202) {
        const errorData = await response.json();
        dispatch({ type: 'AUTH_ERROR', payload: 'User approval pending' });
        throw new Error(`HTTP 202: ${JSON.stringify(errorData.detail)}`);
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Signup failed');
      }

      const data = await response.json();
      const { user, tokens } = data;

      if (!user.is_active) {
        dispatch({ type: 'USER_DISABLED' });
        throw new Error('User account is disabled');
      }

      storeAuth(user, tokens);

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: { user, tokens },
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Signup failed';
      dispatch({
        type: 'AUTH_ERROR',
        payload: errorMessage,
      });
      throw error;
    }
  };

  // Refresh token function for external use
  const refreshToken = async (): Promise<void> => {
    if (state.tokens?.refresh_token) {
      await refreshTokens(state.tokens.refresh_token);
    }
  };

  // Update user information
  const updateUser = (user: User) => {
    // Update stored user data
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
    
    // Update state
    dispatch({ type: 'UPDATE_USER', payload: user });
  };

  // Refresh user information from server
  const refreshUserInfo = async (): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)}`,
        },
      });

      if (response.ok) {
        const updatedUser = await response.json();
        updateUser(updatedUser);
      }
    } catch (error) {
      console.error('Failed to refresh user info:', error);
    }
  };

  // Check if user is still active (improved method)
  const checkUserStatus = async (): Promise<void> => {
    try {
      // Only check if we have a valid token and user
      if (!localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN) || !state.user) {
        return;
      }

      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)}`,
        },
      });

      if (response.status === 400) {
        // User is disabled
        console.log('User account has been disabled');
        dispatch({ type: 'USER_DISABLED' });
      } else if (response.status === 429) {
        // Rate limited - skip this check
        console.log('Rate limited - skipping user status check');
        return;
      } else if (response.ok) {
        const updatedUser = await response.json();
        // Only update if user status actually changed
        if (updatedUser.is_active !== state.user?.is_active) {
          updateUser(updatedUser);
        }
      }
    } catch (error) {
      console.error('Failed to check user status:', error);
      // Don't dispatch error for status checks to avoid disrupting user experience
    }
  };

  // Clear error
  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    emailLogin,
    emailSignup,
    logout,
    refreshToken,
    clearError,
    updateUser,
    refreshUserInfo,
    checkUserStatus, // Add new method
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};