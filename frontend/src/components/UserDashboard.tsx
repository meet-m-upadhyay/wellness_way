import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, ArrowRight } from 'lucide-react';

const UserDashboard: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6 animate-slide-up">
      {/* User's Personal Dashboard */}
      {/* User's Personal Dashboard Section Header */}
      <div className="flex items-center gap-3 border-b border-neutral-100 dark:border-neutral-800 pb-2 text-left">
        <div className="h-2 w-2 rounded-full bg-emerald-500" />
        <h3 className="text-sm font-bold uppercase tracking-widest text-neutral-400">Account Overview</h3>
      </div>

      <div className="bg-white dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 shadow-sm overflow-hidden text-left">

        <div className="border-t border-wellness-light-border dark:border-wellness-dark-border">
          {/* Info rows */}
          <div className="divide-y divide-wellness-light-border dark:divide-wellness-dark-border">
            <div className="px-6 py-4 sm:px-8 sm:grid sm:grid-cols-3 sm:gap-4 bg-wellness-light-elevated/50 dark:bg-wellness-dark-elevated/50">
              <dt className="text-sm font-medium text-wellness-light-textMuted dark:text-wellness-dark-textMuted">Email</dt>
              <dd className="mt-1 text-sm text-wellness-light-text dark:text-wellness-dark-text sm:mt-0 sm:col-span-2">{user.email}</dd>
            </div>

            <div className="px-6 py-4 sm:px-8 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-wellness-light-textMuted dark:text-wellness-dark-textMuted">Profile Status</dt>
              <dd className="mt-1 text-sm sm:mt-0 sm:col-span-2">
                {user.profile_completed ? (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300">
                    ✓ Complete
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-50 dark:bg-amber-900/20 text-amber-700 dark:text-amber-300">
                    ○ Incomplete
                  </span>
                )}
              </dd>
            </div>

            {user.is_admin && (
              <div className="px-6 py-4 sm:px-8 sm:grid sm:grid-cols-3 sm:gap-4 bg-red-50/30 dark:bg-red-900/10">
                <dt className="text-sm font-medium text-red-600 dark:text-red-400">Admin Status</dt>
                <dd className="mt-1 text-sm sm:mt-0 sm:col-span-2 flex flex-col sm:flex-row sm:items-center gap-4">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300">
                    🛡️ Administrator
                  </span>
                  <Link
                    to="/admin"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-xl transition-all hover:scale-105 active:scale-95 shadow-sm"
                  >
                    <ShieldCheck size={14} />
                    Go to Admin Dashboard
                    <ArrowRight size={14} />
                  </Link>
                </dd>
              </div>
            )}

            <div className="px-6 py-4 sm:px-8 sm:grid sm:grid-cols-3 sm:gap-4 bg-wellness-light-elevated/50 dark:bg-wellness-dark-elevated/50">
              <dt className="text-sm font-medium text-wellness-light-textMuted dark:text-wellness-dark-textMuted">Member Since</dt>
              <dd className="mt-1 text-sm text-wellness-light-text dark:text-wellness-dark-text sm:mt-0 sm:col-span-2">
                {new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
              </dd>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default UserDashboard;