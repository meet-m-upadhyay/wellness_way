import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ThemeToggle from '../ThemeToggle';
import GoogleLogin from './GoogleLogin';
import ErrorMessage from '../ErrorMessage';
import PendingApprovalPage from './PendingApprovalPage';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, isLoading, error, clearError } = useAuth();
  const [loginError, setLoginError] = useState<string | null>(null);
  const [pendingApproval, setPendingApproval] = useState<{
    email: string;
    isNewRegistration: boolean;
  } | null>(null);

  const handleGoogleSuccess = useCallback(async (credential: string) => {
    try {
      setLoginError(null);
      setPendingApproval(null);
      clearError();
      
      await login(credential);
      
      // The login function should return the user data, but if not, we'll get it from context
      // For now, we'll redirect to home and let the routing logic handle the redirect
      navigate('/');
    } catch (error) {
      // Check if this is a pending approval error (HTTP 202)
      if (error instanceof Error && error.message.includes('202')) {
        try {
          // Parse the error message to extract approval details
          const errorData = JSON.parse(error.message.replace('HTTP 202: ', ''));
          setPendingApproval({
            email: errorData.email,
            isNewRegistration: errorData.is_new_registration
          });
          return;
        } catch (parseError) {
          // If parsing fails, treat as regular error
        }
      }
      
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setLoginError(errorMessage);
    }
  }, [login, navigate, clearError]);

  const handleGoogleError = useCallback((error: string) => {
    setLoginError(error);
    setPendingApproval(null);
  }, []);

  const displayError = error || loginError;

  // Show pending approval page if user needs approval
  if (pendingApproval) {
    return (
      <PendingApprovalPage 
        email={pendingApproval.email}
        isNewRegistration={pendingApproval.isNewRegistration}
      />
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-wellness-light-bg dark:bg-slate-900 py-12 px-4 sm:px-6 lg:px-8 transition-colors duration-200">
      {/* Theme Toggle - Fixed position */}
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>
      
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/50 transition-colors duration-200">
            <svg
              className="h-8 w-8 text-blue-600 dark:text-blue-400 transition-colors duration-200"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-wellness-light-text dark:text-slate-100 transition-colors duration-200">
            Welcome to WellnessWay
          </h2>
          <p className="mt-2 text-center text-sm text-wellness-light-textSecondary dark:text-slate-400 transition-colors duration-200">
            Your AI-powered wellness companion
          </p>
        </div>

        <div className="mt-8 space-y-6">
          <div className="bg-wellness-light-card dark:bg-slate-800 py-8 px-6 shadow rounded-lg border border-wellness-light-border dark:border-slate-600 transition-colors duration-200">
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-medium text-wellness-light-text dark:text-slate-100 mb-4 transition-colors duration-200">
                  Sign in to get started
                </h3>
                <p className="text-sm text-wellness-light-textSecondary dark:text-slate-400 mb-6 transition-colors duration-200">
                  Create personalized diet plans tailored to your health goals, dietary preferences, and lifestyle.
                </p>
              </div>

              {displayError && (
                <ErrorMessage 
                  message={displayError} 
                  onClose={() => {
                    setLoginError(null);
                    clearError();
                  }}
                />
              )}

              <div className="space-y-4">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  disabled={isLoading}
                />

                {isLoading && (
                  <div className="flex items-center justify-center py-4">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 dark:border-blue-400"></div>
                    <span className="ml-2 text-wellness-light-textSecondary dark:text-slate-400 transition-colors duration-200">Signing you in...</span>
                  </div>
                )}
              </div>

              <div className="mt-6">
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-wellness-light-border dark:border-slate-600 transition-colors duration-200" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-wellness-light-card dark:bg-slate-800 text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">Features</span>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-1 gap-4">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-500 dark:text-emerald-400 transition-colors duration-200" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-wellness-light-textSecondary dark:text-slate-400 transition-colors duration-200">
                        AI-powered personalized meal plans
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-500 dark:text-emerald-400 transition-colors duration-200" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-wellness-light-textSecondary dark:text-slate-400 transition-colors duration-200">
                        Dietary preferences and allergy support
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-green-500 dark:text-emerald-400 transition-colors duration-200" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-wellness-light-textSecondary dark:text-slate-400 transition-colors duration-200">
                        Health goal tracking and optimization
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center">
            <p className="text-xs text-wellness-light-textMuted dark:text-slate-500 transition-colors duration-200">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;