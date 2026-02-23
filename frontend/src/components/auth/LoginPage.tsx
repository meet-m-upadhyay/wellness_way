import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import ThemeToggle from '../ThemeToggle';
import GoogleLogin from './GoogleLogin';
import ErrorMessage from '../ErrorMessage';
import PendingApprovalPage from './PendingApprovalPage';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, emailLogin, emailSignup, isLoading, error, clearError } = useAuth();
  const [loginError, setLoginError] = useState<string | null>(null);
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [touched, setTouched] = useState({
    name: false,
    email: false,
    password: false,
    confirmPassword: false,
  });
  const [pendingApproval, setPendingApproval] = useState<{
    email: string;
    isNewRegistration: boolean;
  } | null>(null);

  const isValidEmail = (value: string) => /^[^\s@]+@[^\s@]+\.com$/.test(value);
  const showEmailInvalid = touched.email && email.length > 0 && !isValidEmail(email);
  const showPasswordInvalid = touched.password && password.length > 0 && password.length < 8;
  const showConfirmInvalid = touched.confirmPassword && confirmPassword.length > 0 && confirmPassword !== password;
  const canSubmitSignIn = isValidEmail(email) && password.length >= 8;
  const canSubmitSignUp = isValidEmail(email)
    && name.trim().length > 0
    && password.length >= 8
    && confirmPassword.length >= 8
    && password === confirmPassword;

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

  const handleEmailSignIn = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();

    try {
      setLoginError(null);
      setPendingApproval(null);
      clearError();

      await emailLogin(email, password);
      navigate('/');
    } catch (error) {
      if (error instanceof Error && error.message.includes('202')) {
        try {
          const errorData = JSON.parse(error.message.replace('HTTP 202: ', ''));
          setPendingApproval({
            email: errorData.email,
            isNewRegistration: errorData.is_new_registration
          });
          return;
        } catch (parseError) {
          // Fall through to standard error handling
        }
      }

      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setLoginError(errorMessage);
    }
  }, [emailLogin, email, password, navigate, clearError]);

  const handleEmailSignUp = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();

    if (password !== confirmPassword) {
      setLoginError('Passwords do not match');
      return;
    }

    try {
      setLoginError(null);
      setPendingApproval(null);
      clearError();

      await emailSignup(name.trim(), email, password, confirmPassword);
      navigate('/');
    } catch (error) {
      if (error instanceof Error && error.message.includes('202')) {
        try {
          const errorData = JSON.parse(error.message.replace('HTTP 202: ', ''));
          setPendingApproval({
            email: errorData.email,
            isNewRegistration: errorData.is_new_registration
          });
          return;
        } catch (parseError) {
          // Fall through to standard error handling
        }
      }

      const errorMessage = error instanceof Error ? error.message : 'Signup failed';
      setLoginError(errorMessage);
    }
  }, [emailSignup, name, email, password, confirmPassword, navigate, clearError]);

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

              <div className="space-y-4 text-left">
                <div className="flex rounded-lg border border-wellness-light-border dark:border-slate-600 overflow-hidden">
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode('signin');
                      setLoginError(null);
                      clearError();
                    }}
                    className={`flex-1 py-2 text-sm font-medium transition-colors duration-200 ${
                      authMode === 'signin'
                        ? 'bg-blue-600 text-white'
                        : 'bg-wellness-light-card dark:bg-slate-800 text-wellness-light-textSecondary dark:text-slate-400'
                    }`}
                  >
                    Sign in
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode('signup');
                      setLoginError(null);
                      clearError();
                    }}
                    className={`flex-1 py-2 text-sm font-medium transition-colors duration-200 ${
                      authMode === 'signup'
                        ? 'bg-blue-600 text-white'
                        : 'bg-wellness-light-card dark:bg-slate-800 text-wellness-light-textSecondary dark:text-slate-400'
                    }`}
                  >
                    Sign up
                  </button>
                </div>

                {authMode === 'signin' ? (
                  <form className="space-y-4 text-left" onSubmit={handleEmailSignIn}>
                    {displayError && (
                      <ErrorMessage 
                        message={displayError} 
                        onClose={() => {
                          setLoginError(null);
                          clearError();
                        }}
                      />
                    )}
                    <div>
                      <label className="block text-sm font-medium text-wellness-light-text dark:text-slate-200 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
                        className={`w-full rounded-md border bg-wellness-light-bg dark:bg-slate-900 px-3 py-2 text-sm text-wellness-light-text dark:text-slate-100 focus:outline-none focus:ring-2 ${
                          showEmailInvalid
                            ? 'border-red-500 focus:ring-red-500'
                            : 'border-wellness-light-border dark:border-slate-600 focus:ring-blue-500'
                        }`}
                        placeholder="you@example.com"
                        required
                      />
                      {showEmailInvalid && (
                        <p className="mt-1 text-xs text-red-500">
                          Email must end with .com
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-wellness-light-text dark:text-slate-200 mb-1">
                        Password
                      </label>
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
                        className={`w-full rounded-md border bg-wellness-light-bg dark:bg-slate-900 px-3 py-2 text-sm text-wellness-light-text dark:text-slate-100 focus:outline-none focus:ring-2 ${
                          showPasswordInvalid
                            ? 'border-red-500 focus:ring-red-500'
                            : 'border-wellness-light-border dark:border-slate-600 focus:ring-blue-500'
                        }`}
                        placeholder="Enter your password"
                        required
                      />
                      {showPasswordInvalid && (
                        <p className="mt-1 text-xs text-red-500">
                          Password must be at least 8 characters
                        </p>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={isLoading || !canSubmitSignIn}
                      className="w-full rounded-md bg-blue-600 hover:bg-blue-700 text-white py-2 text-sm font-medium transition-colors duration-200 disabled:opacity-60"
                    >
                      Sign in with email
                    </button>
                  </form>
                ) : (
                  <form className="space-y-4 text-left" onSubmit={handleEmailSignUp}>
                    {displayError && (
                      <ErrorMessage 
                        message={displayError} 
                        onClose={() => {
                          setLoginError(null);
                          clearError();
                        }}
                      />
                    )}
                    <div>
                      <label className="block text-sm font-medium text-wellness-light-text dark:text-slate-200 mb-1">
                        Name
                      </label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, name: true }))}
                        className="w-full rounded-md border border-wellness-light-border dark:border-slate-600 bg-wellness-light-bg dark:bg-slate-900 px-3 py-2 text-sm text-wellness-light-text dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Your name"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-wellness-light-text dark:text-slate-200 mb-1">
                        Email
                      </label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
                        className={`w-full rounded-md border bg-wellness-light-bg dark:bg-slate-900 px-3 py-2 text-sm text-wellness-light-text dark:text-slate-100 focus:outline-none focus:ring-2 ${
                          showEmailInvalid
                            ? 'border-red-500 focus:ring-red-500'
                            : 'border-wellness-light-border dark:border-slate-600 focus:ring-blue-500'
                        }`}
                        placeholder="you@example.com"
                        required
                      />
                      {showEmailInvalid && (
                        <p className="mt-1 text-xs text-red-500">
                          Email must end with .com
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-wellness-light-text dark:text-slate-200 mb-1">
                        Password
                      </label>
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
                        className={`w-full rounded-md border bg-wellness-light-bg dark:bg-slate-900 px-3 py-2 text-sm text-wellness-light-text dark:text-slate-100 focus:outline-none focus:ring-2 ${
                          showPasswordInvalid
                            ? 'border-red-500 focus:ring-red-500'
                            : 'border-wellness-light-border dark:border-slate-600 focus:ring-blue-500'
                        }`}
                        placeholder="Create a password"
                        required
                      />
                      {showPasswordInvalid && (
                        <p className="mt-1 text-xs text-red-500">
                          Password must be at least 8 characters
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-wellness-light-text dark:text-slate-200 mb-1">
                        Confirm password
                      </label>
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, confirmPassword: true }))}
                        className={`w-full rounded-md border bg-wellness-light-bg dark:bg-slate-900 px-3 py-2 text-sm text-wellness-light-text dark:text-slate-100 focus:outline-none focus:ring-2 ${
                          showConfirmInvalid
                            ? 'border-red-500 focus:ring-red-500'
                            : 'border-wellness-light-border dark:border-slate-600 focus:ring-blue-500'
                        }`}
                        placeholder="Re-enter your password"
                        required
                      />
                      {showConfirmInvalid && (
                        <p className="mt-1 text-xs text-red-500">
                          Passwords do not match
                        </p>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={isLoading || !canSubmitSignUp}
                      className="w-full rounded-md bg-blue-600 hover:bg-blue-700 text-white py-2 text-sm font-medium transition-colors duration-200 disabled:opacity-60"
                    >
                      Create account
                    </button>
                  </form>
                )}

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-wellness-light-border dark:border-slate-600 transition-colors duration-200" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-wellness-light-card dark:bg-slate-800 text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">
                      Or continue with
                    </span>
                  </div>
                </div>

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