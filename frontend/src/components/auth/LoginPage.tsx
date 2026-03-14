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
        }
      }

      const errorMessage = error instanceof Error ? error.message : 'Signup failed';
      setLoginError(errorMessage);
    }
  }, [emailSignup, name, email, password, confirmPassword, navigate, clearError]);

  const displayError = error || loginError;

  if (pendingApproval) {
    return (
      <PendingApprovalPage
        email={pendingApproval.email}
        isNewRegistration={pendingApproval.isNewRegistration}
      />
    );
  }

  const inputBaseClass = "w-full rounded-xl border px-4 py-2.5 text-sm leading-normal bg-white dark:bg-wellness-dark-bg text-wellness-light-text dark:text-wellness-dark-text placeholder:text-wellness-light-textMuted dark:placeholder:text-wellness-dark-textMuted focus:outline-none focus:ring-2 transition-all duration-200";
  const inputNormalBorder = "border-wellness-light-border dark:border-wellness-dark-border focus:ring-primary-500 dark:focus:ring-primary-400 focus:border-primary-500 dark:focus:border-primary-400";
  const inputErrorBorder = "border-red-400 dark:border-red-500 focus:ring-red-500 dark:focus:ring-red-400";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-wellness-light-bg via-primary-50/30 to-accent-50/20 dark:from-wellness-dark-bg dark:via-wellness-dark-bg dark:to-wellness-dark-card py-12 px-4 sm:px-6 lg:px-8">
      {/* Theme Toggle */}
      <div className="fixed top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      <div className="max-w-md w-full space-y-6 animate-scale-in">
        {/* Product Intro Section */}
        <div className="text-left space-y-2 mb-8">
          <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-gradient-to-br from-primary-400 to-primary-600 shadow-glow-emerald mb-4">
            <svg
              className="h-6 w-6 text-white"
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
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Personalized Diet Planning
          </h1>
          <p className="text-lg text-neutral-500 dark:text-neutral-400">
            Powered by AI. Tailored for your unique health goals.
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white dark:bg-neutral-900 rounded-3xl shadow-sm border border-neutral-200 dark:border-neutral-800 overflow-hidden">
          <div className="p-8">
            <div className="space-y-8">
              <div className="text-left">
                <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-2">
                  {authMode === 'signin' ? 'Sign in to your account' : 'Create your account'}
                </h3>
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                  {authMode === 'signin'
                    ? 'Welcome back! Please enter your details.'
                    : 'Start your journey to better health today.'}
                </p>
              </div>

              {/* Auth Mode Toggle */}
              <div className="flex rounded-2xl bg-neutral-100 dark:bg-neutral-800 p-1 gap-1">
                <button
                  type="button"
                  onClick={() => {
                    setAuthMode('signin');
                    setLoginError(null);
                    clearError();
                  }}
                  className={`flex-1 py-2.5 text-sm font-bold rounded-xl transition-all duration-200 ${authMode === 'signin'
                    ? 'bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white shadow-sm'
                    : 'text-neutral-400 dark:text-neutral-500 hover:text-neutral-900 dark:hover:text-white'
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
                  className={`flex-1 py-2.5 text-sm font-bold rounded-xl transition-all duration-200 ${authMode === 'signup'
                    ? 'bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white shadow-sm'
                    : 'text-neutral-400 dark:text-neutral-500 hover:text-neutral-900 dark:hover:text-white'
                    }`}
                >
                  Sign up
                </button>
              </div>

              <div className="space-y-4 text-left">
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
                      <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                        Email Address
                      </label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
                        className={`${inputBaseClass} ${showEmailInvalid ? inputErrorBorder : inputNormalBorder}`}
                        placeholder="you@example.com"
                        required
                      />
                      {showEmailInvalid && (
                        <p className="mt-1.5 text-xs text-red-500 dark:text-red-400">
                          Email must end with .com
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                        Password
                      </label>
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
                        className={`${inputBaseClass} ${showPasswordInvalid ? inputErrorBorder : inputNormalBorder}`}
                        placeholder="Enter your password"
                        required
                      />
                      {showPasswordInvalid && (
                        <p className="mt-1.5 text-xs text-red-500 dark:text-red-400">
                          Password must be at least 8 characters
                        </p>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={isLoading || !canSubmitSignIn}
                      className="w-full rounded-2xl bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 py-3 text-sm font-bold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neutral-800 dark:hover:bg-neutral-100 active:scale-[0.98]"
                    >
                      Sign In
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
                      <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, name: true }))}
                        className={`${inputBaseClass} ${inputNormalBorder}`}
                        placeholder="Your name"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                        Email Address
                      </label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, email: true }))}
                        className={`${inputBaseClass} ${showEmailInvalid ? inputErrorBorder : inputNormalBorder}`}
                        placeholder="you@example.com"
                        required
                      />
                      {showEmailInvalid && (
                        <p className="mt-1.5 text-xs text-red-500 dark:text-red-400">
                          Email must end with .com
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                        Create Password
                      </label>
                      <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
                        className={`${inputBaseClass} ${showPasswordInvalid ? inputErrorBorder : inputNormalBorder}`}
                        placeholder="Create a password"
                        required
                      />
                      {showPasswordInvalid && (
                        <p className="mt-1.5 text-xs text-red-500 dark:text-red-400">
                          Password must be at least 8 characters
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-neutral-700 dark:text-neutral-300 mb-2">
                        Confirm Password
                      </label>
                      <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        onBlur={() => setTouched((prev) => ({ ...prev, confirmPassword: true }))}
                        className={`${inputBaseClass} ${showConfirmInvalid ? inputErrorBorder : inputNormalBorder}`}
                        placeholder="Re-enter your password"
                        required
                      />
                      {showConfirmInvalid && (
                        <p className="mt-1.5 text-xs text-red-500 dark:text-red-400">
                          Passwords do not match
                        </p>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={isLoading || !canSubmitSignUp}
                      className="w-full rounded-2xl bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 py-3 text-sm font-bold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-neutral-800 dark:hover:bg-neutral-100 active:scale-[0.98]"
                    >
                      Create Account
                    </button>
                  </form>
                )}

                {/* Divider */}
                <div className="relative py-2">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-neutral-200 dark:border-neutral-800" />
                  </div>
                  <div className="relative flex justify-center text-xs">
                    <span className="px-3 bg-white dark:bg-neutral-900 text-neutral-400 uppercase tracking-widest font-bold">
                      or
                    </span>
                  </div>
                </div>

                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  disabled={isLoading}
                />

                {isLoading && (
                  <div className="flex items-center justify-center py-3">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-wellness-light-border dark:border-wellness-dark-border border-t-primary-500 dark:border-t-primary-400"></div>
                    <span className="ml-2.5 text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">Signing you in...</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Benefits Section */}
          <div className="bg-neutral-100 dark:bg-neutral-800/50 px-8 py-6 border-t border-neutral-200 dark:border-neutral-800">
            <div className="space-y-4">
              {[
                { title: 'AI Personalized Meal Plans', desc: 'Precision nutrition tailored for you' },
                { title: 'Dietary & Allergy Support', desc: 'Smart exclusions and alternatives' },
                { title: 'Health Goal Optimization', desc: 'Real-time tracking and adjustments' },
              ].map((benefit, index) => (
                <div key={index} className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/10 flex items-center justify-center mt-0.5">
                    <svg className="h-4 w-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-bold text-neutral-900 dark:text-white">{benefit.title}</p>
                    <p className="text-xs text-neutral-500 dark:text-neutral-400">{benefit.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="text-center">
          <p className="text-[10px] text-neutral-400 uppercase tracking-widest font-bold">
            Secure Cloud Environment • AES-256 Encryption
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;