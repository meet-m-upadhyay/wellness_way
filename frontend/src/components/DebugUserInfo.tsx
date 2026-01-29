import React from 'react';
import { useAuth } from '../context/AuthContext';

const DebugUserInfo: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (!isAuthenticated) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        <strong>Debug:</strong> User not authenticated
      </div>
    );
  }

  return (
    <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
      <strong>Debug User Info:</strong>
      <pre className="mt-2 text-xs">
        {JSON.stringify({
          isAuthenticated,
          isLoading,
          user: user ? {
            id: user.id,
            email: user.email,
            name: user.name,
            is_admin: user.is_admin,
            profile_completed: user.profile_completed,
            created_at: user.created_at
          } : null
        }, null, 2)}
      </pre>
    </div>
  );
};

export default DebugUserInfo;