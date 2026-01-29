import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AdminDashboard from './AdminDashboard';

const UserDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* User's Personal Dashboard */}
      <div className="bg-wellness-light-card dark:bg-slate-800 shadow overflow-hidden sm:rounded-lg border border-wellness-light-border dark:border-slate-600 transition-colors duration-200">
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-wellness-light-text dark:text-slate-100 transition-colors duration-200">
            Welcome back, {user.name}!
          </h3>
          <p className="mt-1 max-w-2xl text-sm text-wellness-light-textSecondary dark:text-slate-400 transition-colors duration-200">
            Your personal wellness dashboard
          </p>
        </div>
        
        <div className="border-t border-wellness-light-border dark:border-slate-600 transition-colors duration-200">
          <dl>
            <div className="bg-wellness-light-elevated dark:bg-slate-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 transition-colors duration-200">
              <dt className="text-sm font-medium text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">Email</dt>
              <dd className="mt-1 text-sm text-wellness-light-text dark:text-slate-100 sm:mt-0 sm:col-span-2 transition-colors duration-200">{user.email}</dd>
            </div>
            
            <div className="bg-wellness-light-card dark:bg-slate-800 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 transition-colors duration-200">
              <dt className="text-sm font-medium text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">Profile Status</dt>
              <dd className="mt-1 text-sm text-wellness-light-text dark:text-slate-100 sm:mt-0 sm:col-span-2 transition-colors duration-200">
                {user.profile_completed ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-emerald-900/50 text-green-800 dark:text-emerald-200 transition-colors duration-200">
                    Complete
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-200 transition-colors duration-200">
                    Incomplete
                  </span>
                )}
              </dd>
            </div>
            
            {user.is_admin && (
              <div className="bg-red-50 dark:bg-red-900/20 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 transition-colors duration-200">
                <dt className="text-sm font-medium text-red-700 dark:text-red-300 transition-colors duration-200">Admin Status</dt>
                <dd className="mt-1 text-sm text-wellness-light-text dark:text-slate-100 sm:mt-0 sm:col-span-2 transition-colors duration-200">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-200 transition-colors duration-200">
                    Administrator
                  </span>
                </dd>
              </div>
            )}
            
            <div className="bg-wellness-light-elevated dark:bg-slate-700 px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 transition-colors duration-200">
              <dt className="text-sm font-medium text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">Member Since</dt>
              <dd className="mt-1 text-sm text-wellness-light-text dark:text-slate-100 sm:mt-0 sm:col-span-2 transition-colors duration-200">
                {new Date(user.created_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>
        
        <div className="px-4 py-5 sm:px-6">
          <div className="flex flex-col sm:flex-row gap-4">
            {!user.profile_completed ? (
              <button
                onClick={() => navigate('/profile-setup')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 dark:bg-blue-600 hover:bg-indigo-700 dark:hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-800 focus:ring-indigo-500 dark:focus:ring-blue-400 transition-colors duration-200"
              >
                Complete Profile Setup
              </button>
            ) : (
              <>
                {/* <button
                  onClick={() => navigate('/diet-plans')}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  View Diet Plans
                </button> */}
                <button
                  onClick={() => navigate('/profile-setup')}
                  className="inline-flex items-center px-4 py-2 border border-wellness-light-border dark:border-slate-600 text-sm font-medium rounded-md shadow-sm text-wellness-light-textSecondary dark:text-slate-300 bg-wellness-light-card dark:bg-slate-800 hover:bg-wellness-light-elevated dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-800 focus:ring-indigo-500 dark:focus:ring-blue-400 transition-colors duration-200"
                >
                  Edit Profile
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Admin Dashboard - Only visible to admin users */}
      {user.is_admin && (
        <AdminDashboard />
      )}
    </div>
  );
};

export default UserDashboard;