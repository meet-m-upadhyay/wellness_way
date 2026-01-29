import React from 'react';
import { useNavigate, Link } from 'react-router-dom';

interface PendingApprovalPageProps {
  email?: string;
  isNewRegistration?: boolean;
}

const PendingApprovalPage: React.FC<PendingApprovalPageProps> = ({ 
  email, 
  isNewRegistration = false 
}) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900/20">
            <svg
              className="h-8 w-8 text-yellow-600 dark:text-yellow-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-slate-100">
            {isNewRegistration ? 'Registration Submitted' : 'Approval Pending'}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-slate-300">
            Your access to WellnessWay is pending admin approval
          </p>
        </div>

        <div className="mt-8 space-y-6">
          <div className="bg-white dark:bg-slate-800 py-8 px-6 shadow rounded-lg border border-gray-200 dark:border-slate-700">
            <div className="space-y-6">
              <div className="text-center">
                <div className="mb-4">
                  <svg
                    className="mx-auto h-16 w-16 text-yellow-500 dark:text-yellow-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                
                {isNewRegistration ? (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-slate-100 mb-4">
                      Thank you for registering!
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-slate-300 mb-4">
                      Your registration request has been submitted successfully.
                    </p>
                  </div>
                ) : (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-slate-100 mb-4">
                      Access Pending
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-slate-300 mb-4">
                      Your account is awaiting admin approval.
                    </p>
                  </div>
                )}

                {email && (
                  <div className="bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4 mb-6">
                    <p className="text-sm text-gray-700 dark:text-slate-300">
                      <span className="font-medium">Email:</span> {email}
                    </p>
                  </div>
                )}

                <div className="space-y-4 text-left">
                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-500 dark:text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-gray-600 dark:text-slate-300">
                        An admin has been notified of your registration request
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-500 dark:text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-gray-600 dark:text-slate-300">
                        You will receive an email notification once your request is reviewed
                      </p>
                    </div>
                  </div>

                  <div className="flex items-start">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-blue-500 dark:text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-gray-600 dark:text-slate-300">
                        Once approved, you can sign in and start using WellnessWay
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                <button
                  onClick={() => {
                    console.log('Back to Login button clicked');
                    try {
                      // Clear any stored auth data before navigating
                      localStorage.removeItem('health_buddy_access_token');
                      localStorage.removeItem('health_buddy_refresh_token');
                      localStorage.removeItem('health_buddy_user');
                      
                      navigate('/login');
                      console.log('Navigate called successfully');
                      window.location.reload();
                    } catch (error) {
                      console.error('Navigate failed:', error);
                      // Fallback to window.location
                      localStorage.clear();
                      window.location.href = '/login';
                      window.location.reload();
                    }
                  }}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-offset-slate-800"
                >
                  Back to Login
                </button>
                
                {/* Alternative Link-based navigation */}
                <Link
                  to="/login"
                  onClick={() => {
                    console.log('Link to login clicked');
                    // Clear any stored auth data before navigating
                    localStorage.removeItem('health_buddy_access_token');
                    localStorage.removeItem('health_buddy_refresh_token');
                    localStorage.removeItem('health_buddy_user');
                    window.location.reload();
                  }}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:focus:ring-offset-slate-800"
                >
                  Back to Login (Link)
                </Link>
                
                <button
                  onClick={() => window.location.reload()}
                  className="w-full flex justify-center py-2 px-4 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-slate-300 bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-offset-slate-800"
                >
                  Check Status
                </button>
              </div>
            </div>
          </div>

          <div className="text-center">
            <p className="text-xs text-gray-500 dark:text-slate-400">
              Need help? Contact support or try signing in again later.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PendingApprovalPage;