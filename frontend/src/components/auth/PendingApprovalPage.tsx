import React from 'react';
import { useNavigate } from 'react-router-dom';

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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-wellness-light-bg via-primary-50/30 to-accent-50/20 dark:from-wellness-dark-bg dark:via-wellness-dark-bg dark:to-wellness-dark-card py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6 animate-scale-in">
        <div className="text-left space-y-2 mb-8">
          <div className="h-12 w-12 flex items-center justify-center rounded-2xl bg-amber-50 dark:bg-amber-900/20 mb-4">
            <svg className="h-6 w-6 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Account Pending
          </h1>
          <p className="text-lg text-neutral-500 dark:text-neutral-400">
            {isNewRegistration ? 'Your registration is submitted.' : 'Your access is awaiting review.'}
          </p>
        </div>

        <div className="bg-white dark:bg-neutral-900 rounded-3xl shadow-sm border border-neutral-200 dark:border-neutral-800 overflow-hidden">
          <div className="p-8">
            <div className="text-left space-y-6">
              <div>
                <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-2">
                  {isNewRegistration ? 'Registration Successful' : 'Approval Required'}
                </h3>
                <p className="text-sm text-neutral-500 dark:text-neutral-400 leading-relaxed">
                  To maintain data integrity and security, an administrator must review your access request.
                </p>
              </div>

              {email && (
                <div className="bg-neutral-50 dark:bg-neutral-800/50 rounded-2xl p-4 border border-neutral-100 dark:border-neutral-800">
                  <p className="text-xs font-bold text-neutral-400 uppercase tracking-widest mb-1">Requested Account</p>
                  <p className="text-sm font-semibold text-neutral-900 dark:text-white">{email}</p>
                </div>
              )}

              <div>
                <p className="text-xs font-bold text-neutral-400 uppercase tracking-widest mb-4">Next Steps</p>
                <div className="space-y-4">
                  {[
                    'Admin notification sent for review',
                    'Email notification once review is complete',
                    'Full access granted post-approval',
                  ].map((text, i) => (
                    <div key={i} className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-500/10 flex items-center justify-center mt-0.5">
                        <svg className="h-3.5 w-3.5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                      <p className="text-sm text-neutral-600 dark:text-neutral-400">{text}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 space-y-3">
                <button
                  onClick={() => {
                    localStorage.removeItem('health_buddy_access_token');
                    localStorage.removeItem('health_buddy_refresh_token');
                    localStorage.removeItem('health_buddy_user');
                    navigate('/login');
                    window.location.reload();
                  }}
                  className="w-full rounded-2xl bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 py-3 text-sm font-bold transition-all duration-200 hover:bg-neutral-800 dark:hover:bg-neutral-100 active:scale-[0.98]"
                >
                  Back to Login
                </button>

                <button
                  onClick={() => window.location.reload()}
                  className="w-full rounded-2xl border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 text-neutral-600 dark:text-neutral-400 py-3 text-sm font-bold hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-all duration-200 active:scale-[0.98]"
                >
                  Refresh Status
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center">
          <p className="text-xs text-wellness-light-textMuted dark:text-wellness-dark-textMuted">
            Need help? Contact support or try signing in again later.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PendingApprovalPage;