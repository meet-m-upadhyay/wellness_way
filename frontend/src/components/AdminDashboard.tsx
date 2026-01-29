import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiClient, UserProfile } from '../services/api';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import PendingRequestsList from './admin/PendingRequestsList';
import UserActions from './admin/UserActions';

type TabType = 'requests' | 'users';

const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [activeTab, setActiveTab] = useState<TabType>('requests');

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

  useEffect(() => {
    if (user?.is_admin) {
      loadUsers();
    }
  }, [user]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiClient.getAllUsers(50);
      
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setUsers(response.data);
      }
    } catch (err) {
      setError('Failed to load users');
      console.error('Error loading users:', err);
    } finally {
      setLoading(false);
    }
  };

  const getActivityLevelDisplay = (level: string | null) => {
    if (!level) return 'Not specified';
    
    const levels = {
      'sedentary': 'Sedentary',
      'lightly_active': 'Lightly Active',
      'moderately_active': 'Moderately Active',
      'very_active': 'Very Active',
      'extremely_active': 'Extremely Active'
    };
    return levels[level as keyof typeof levels] || level;
  };

  const getGenderDisplay = (gender: string | null) => {
    if (!gender) return 'Not specified';
    return gender.charAt(0).toUpperCase() + gender.slice(1);
  };

  const handleApproveUser = async (requestId: string) => {
    try {
      const token = localStorage.getItem('health_buddy_access_token');
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await fetch(`${API_BASE_URL}/admin/approve-user/${requestId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to approve user');
      }

      // Trigger refresh of both pending requests and user list
      setRefreshTrigger(prev => prev + 1);
      await loadUsers();
    } catch (err) {
      console.error('Error approving user:', err);
      throw err;
    }
  };

  const handleDeclineUser = async (requestId: string) => {
    try {
      const token = localStorage.getItem('health_buddy_access_token');
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await fetch(`${API_BASE_URL}/admin/decline-user/${requestId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to decline user');
      }

      // Trigger refresh of pending requests
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      console.error('Error declining user:', err);
      throw err;
    }
  };

  const handleEnableUser = async (userId: string) => {
    try {
      const token = localStorage.getItem('health_buddy_access_token');
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await fetch(`${API_BASE_URL}/admin/enable-user/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to enable user');
      }

      // Refresh the user list
      await loadUsers();
    } catch (err) {
      console.error('Error enabling user:', err);
      throw err;
    }
  };

  const handleDisableUser = async (userId: string) => {
    try {
      const token = localStorage.getItem('health_buddy_access_token');
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await fetch(`${API_BASE_URL}/admin/disable-user/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to disable user');
      }

      // Refresh the user list
      await loadUsers();
    } catch (err) {
      console.error('Error disabling user:', err);
      throw err;
    }
  };

  if (!user?.is_admin) {
    return (
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 transition-colors duration-200">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400 dark:text-red-300" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Access Denied</h3>
            <div className="mt-2 text-sm text-red-700 dark:text-red-300">
              <p>You don't have admin privileges to access this section.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <LoadingSpinner message=''/>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-4">
        <ErrorMessage message={error} />
        <button
          onClick={loadUsers}
          className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-wellness-light-card dark:bg-slate-800 shadow-sm border border-wellness-light-border dark:border-slate-600 rounded-lg transition-colors duration-200">
        <div className="px-6 py-4">
          <h1 className="text-2xl font-bold text-wellness-light-text dark:text-slate-100 transition-colors duration-200">
            Admin Dashboard
          </h1>
          <p className="mt-1 text-sm text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">
            Manage user registrations and system users
          </p>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-wellness-light-card dark:bg-slate-800 shadow-sm border border-wellness-light-border dark:border-slate-600 rounded-lg transition-colors duration-200">
        <div className="border-b border-wellness-light-border dark:border-slate-600">
          <nav className="-mb-px flex space-x-4 sm:space-x-8 px-4 sm:px-6 overflow-x-auto" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('requests')}
              className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors duration-200 ${
                activeTab === 'requests'
                  ? 'border-indigo-500 dark:border-blue-400 text-indigo-600 dark:text-blue-400'
                  : 'border-transparent text-wellness-light-textMuted dark:text-slate-400 hover:text-wellness-light-textSecondary dark:hover:text-slate-300 hover:border-wellness-light-border dark:hover:border-slate-500'
              }`}
            >
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
                <span className="hidden sm:inline">Registration Requests</span>
                <span className="sm:hidden">Requests</span>
              </div>
            </button>
            <button
              onClick={() => setActiveTab('users')}
              className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap transition-colors duration-200 ${
                activeTab === 'users'
                  ? 'border-indigo-500 dark:border-blue-400 text-indigo-600 dark:text-blue-400'
                  : 'border-transparent text-wellness-light-textMuted dark:text-slate-400 hover:text-wellness-light-textSecondary dark:hover:text-slate-300 hover:border-wellness-light-border dark:hover:border-slate-500'
              }`}
            >
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <span className="hidden sm:inline">Manage Users ({users.length})</span>
                <span className="sm:hidden">Users ({users.length})</span>
              </div>
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-4 sm:p-6">
          {activeTab === 'requests' && (
            <div>
              <PendingRequestsList
                onApprove={handleApproveUser}
                onDecline={handleDeclineUser}
                refreshTrigger={refreshTrigger}
              />
            </div>
          )}

          {activeTab === 'users' && (
            <div>
              {/* Users Section Header */}
              <div className="mb-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                  <div>
                    <h2 className="text-lg font-medium text-wellness-light-text dark:text-slate-100 transition-colors duration-200 text-left">
                      System Users
                    </h2>
                    <p className="mt-1 text-sm text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200 text-left">
                      View and manage all approved users in the system
                    </p>
                  </div>
                  <button
                    onClick={loadUsers}
                    className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 dark:bg-blue-600 hover:bg-indigo-700 dark:hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:focus:ring-blue-400 transition-colors duration-200 w-full sm:w-auto"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    Refresh
                  </button>
                </div>
              </div>

              {/* Users List */}
              {users.length === 0 ? (
                <div className="text-center py-12">
                  <svg className="mx-auto h-12 w-12 text-wellness-light-textMuted dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-wellness-light-text dark:text-slate-100 transition-colors duration-200">No users found</h3>
                  <p className="mt-1 text-sm text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">
                    No approved users are currently in the system.
                  </p>
                </div>
              ) : (
                <div className="bg-white dark:bg-slate-700 shadow overflow-hidden sm:rounded-md border border-wellness-light-border dark:border-slate-600 transition-colors duration-200">
                  <ul className="divide-y divide-wellness-light-border dark:divide-slate-600">
                    {users.map((userItem) => (
                      <li key={userItem.id} className="px-4 sm:px-6 py-4 transition-colors duration-200">
                        {/* Mobile Layout */}
                        <div className="block sm:hidden">
                          <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0">
                              <div className={`h-12 w-12 rounded-full flex items-center justify-center transition-colors duration-200 ${
                                userItem.is_admin ? 'bg-red-500 dark:bg-red-600' : 'bg-indigo-500 dark:bg-blue-600'
                              }`}>
                                <span className="text-sm font-medium text-white">
                                  {userItem.name?.charAt(0)?.toUpperCase() || 'U'}
                                </span>
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center flex-wrap gap-1 mb-1">
                                <div className="text-sm font-medium text-wellness-light-text dark:text-slate-100 transition-colors duration-200 truncate">
                                  {userItem.name}
                                </div>
                                {userItem.is_admin && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-200 transition-colors duration-200">
                                    Admin
                                  </span>
                                )}
                                {userItem.profile_completed && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-emerald-900/50 text-green-800 dark:text-emerald-200 transition-colors duration-200">
                                    Complete
                                  </span>
                                )}
                                {!userItem.is_active && (
                                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-200 transition-colors duration-200">
                                    Disabled
                                  </span>
                                )}
                              </div>
                              <div className="text-sm text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200 truncate mb-1 text-left">
                                {userItem.email || 'No email'}
                              </div>
                              <div className="text-xs text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200 mb-2 text-left">
                                {userItem.age ? `${userItem.age} years` : 'Age not set'} • {getGenderDisplay(userItem.gender)}
                              </div>
                              <div className="text-xs text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200 mb-3 text-left">
                                {userItem.height_cm ? `${userItem.height_cm} cm` : 'Height not set'} • {userItem.weight_kg ? `${userItem.weight_kg} kg` : 'Weight not set'}
                                {userItem.body_fat_percentage && ` • ${userItem.body_fat_percentage}% BF`}
                              </div>
                              <div className="flex items-center justify-between">
                                <div className="text-xs text-wellness-light-textMuted dark:text-slate-500 transition-colors duration-200">
                                  Joined: {userItem.created_at ? new Date(userItem.created_at).toLocaleDateString() : 'Unknown'}
                                </div>
                                <div className="flex-shrink-0">
                                  {userItem.id ? (
                                    <UserActions
                                      userId={userItem.id}
                                      userName={userItem.name || 'User'}
                                      userEmail={userItem.email || ''}
                                      isActive={userItem.is_active ?? true}
                                      isAdmin={userItem.is_admin ?? false}
                                      onEnable={handleEnableUser}
                                      onDisable={handleDisableUser}
                                    />
                                  ) : (
                                    <span className="text-xs text-wellness-light-textMuted dark:text-slate-500 italic transition-colors duration-200">
                                      No actions
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Desktop Layout */}
                        <div className="hidden sm:flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="flex-shrink-0">
                              <div className={`h-12 w-12 rounded-full flex items-center justify-center transition-colors duration-200 ${
                                userItem.is_admin ? 'bg-red-500 dark:bg-red-600' : 'bg-indigo-500 dark:bg-blue-600'
                              }`}>
                                <span className="text-sm font-medium text-white">
                                  {userItem.name?.charAt(0)?.toUpperCase() || 'U'}
                                </span>
                              </div>
                            </div>
                            <div className="ml-4">
                              <div className="flex items-center flex-wrap gap-2">
                                <div className="text-sm font-medium text-wellness-light-text dark:text-slate-100 transition-colors duration-200">
                                  {userItem.name}
                                </div>
                                {userItem.is_admin && (
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-200 transition-colors duration-200">
                                    Admin
                                  </span>
                                )}
                                {userItem.profile_completed && (
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-emerald-900/50 text-green-800 dark:text-emerald-200 transition-colors duration-200">
                                    Profile Complete
                                  </span>
                                )}
                                {!userItem.is_active && (
                                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-200 transition-colors duration-200">
                                    Disabled
                                  </span>
                                )}
                              </div>
                              <div className="text-sm text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200 text-left">
                                {userItem.email || 'No email'}
                              </div>
                              <div className="text-sm text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200 text-left">
                                {userItem.age ? `${userItem.age} years old` : 'Age not specified'} • {getGenderDisplay(userItem.gender)} • {getActivityLevelDisplay(userItem.activity_level)}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-6">
                            <div className="text-right text-sm text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">
                              <div className="font-medium">
                                {userItem.height_cm ? `${userItem.height_cm} cm` : 'Height not set'} • {userItem.weight_kg ? `${userItem.weight_kg} kg` : 'Weight not set'}
                              </div>
                              {userItem.body_fat_percentage && (
                                <div>
                                  Body Fat: {userItem.body_fat_percentage}%
                                </div>
                              )}
                              <div className="text-xs text-wellness-light-textMuted dark:text-slate-500 transition-colors duration-200">
                                Joined: {userItem.created_at ? new Date(userItem.created_at).toLocaleDateString() : 'Unknown'}
                              </div>
                            </div>
                            <div className="flex-shrink-0">
                              {userItem.id ? (
                                <UserActions
                                  userId={userItem.id}
                                  userName={userItem.name || 'User'}
                                  userEmail={userItem.email || ''}
                                  isActive={userItem.is_active ?? true}
                                  isAdmin={userItem.is_admin ?? false}
                                  onEnable={handleEnableUser}
                                  onDisable={handleDisableUser}
                                />
                              ) : (
                                <span className="text-xs text-wellness-light-textMuted dark:text-slate-500 italic transition-colors duration-200">
                                  No actions available
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;