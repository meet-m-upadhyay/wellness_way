import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface AccountDisabledPageProps {
  userEmail?: string;
  userName?: string;
}

const AccountDisabledPage: React.FC<AccountDisabledPageProps> = ({ 
  userEmail, 
  userName 
}) => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    console.log('Sign Out button clicked');
    try {
      // Clear auth state first
      logout();
      
      // Clear localStorage as backup
      localStorage.removeItem('health_buddy_access_token');
      localStorage.removeItem('health_buddy_refresh_token');
      localStorage.removeItem('health_buddy_user');
      
      console.log('Logout called successfully');
      navigate('/login');
      console.log('Navigate to login called');
    } catch (error) {
      console.error('Logout/Navigate failed:', error);
      // Fallback: clear all localStorage and redirect
      localStorage.clear();
      window.location.href = '/login';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-wellness-light-bg dark:bg-wellness-dark-bg py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-red-100 dark:bg-red-900/20">
            <svg
              className="h-8 w-8 text-red-600 dark:text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-wellness-light-text dark:text-wellness-dark-text">
            Account Disabled
          </h2>
          <p className="mt-2 text-center text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
            Your access to WellnessWay has been temporarily disabled
          </p>
        </div>

        <div className="mt-8 space-y-6">
          <div className="bg-wellness-light-card dark:bg-wellness-dark-card py-8 px-6 shadow rounded-lg">
            <div className="space-y-6">
              <div className="text-center">
                <div className="mb-4">
                  <svg
                    className="mx-auto h-16 w-16 text-red-500 dark:text-red-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L5.636 5.636"
                    />
                  </svg>
                </div>
                
                <div>
                  <h3 className="text-lg font-medium text-wellness-light-text dark:text-wellness-dark-text mb-4">
                    Access Temporarily Disabled
                  </h3>
                  <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary mb-4">
                    Your WellnessWay account has been temporarily disabled by an administrator.
                  </p>
                </div>

                {userEmail && (
                  <div className="bg-wellness-light-elevated dark:bg-wellness-dark-elevated rounded-lg p-4 mb-6">
                    <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                      <span className="font-medium">Account:</span> {userEmail}
                    </p>
                    {userName && (
                      <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                        <span className="font-medium">Name:</span> {userName}
                      </p>
                    )}
                  </div>
                )}

                <div className="space-y-4 text-left">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-500 dark:text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                        This is a temporary restriction and may be lifted by an administrator
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-primary-500 dark:text-primary-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                        Your account data and profile information remain safe and intact
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-primary-500 dark:text-primary-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                        If you believe this is an error, please contact support
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <button
                  onClick={handleLogout}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:focus:ring-offset-slate-800"
                >
                  Sign Out
                </button>
                
                <button
                  onClick={() => window.location.reload()}
                  className="w-full flex justify-center py-2 px-4 border border-wellness-light-border dark:border-wellness-dark-border rounded-md shadow-sm text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary bg-wellness-light-card dark:bg-wellness-dark-card hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                >
                  Check Status Again
                </button>
                
                {/* Alternative Link-based navigation */}
                <Link
                  to="/login"
                  onClick={() => {
                    console.log('Link to login clicked');
                    // Clear auth state and navigate
                    logout();
                    // Also clear localStorage as backup
                    localStorage.removeItem('health_buddy_access_token');
                    localStorage.removeItem('health_buddy_refresh_token');
                    localStorage.removeItem('health_buddy_user');
                    window.location.reload();
                  }}
                  className="w-full flex justify-center py-2 px-4 border border-wellness-light-border dark:border-wellness-dark-border rounded-md shadow-sm text-sm font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary bg-wellness-light-card dark:bg-wellness-dark-card hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                >
                  Back to Login (Alternative)
                </Link>
              </div>
            </div>
          </div>

          <div className="text-center">
            <p className="text-xs text-wellness-light-textMuted dark:text-wellness-dark-textMuted">
              Need help? Contact support at{' '}
              <a href="mailto:support@wellnessway.com" className="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300">
                support@wellnessway.com
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccountDisabledPage;