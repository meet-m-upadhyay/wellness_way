import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireProfileComplete?: boolean;
  requireAdmin?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireProfileComplete = false,
  requireAdmin = false
}) => {
  const { isAuthenticated, user, isLoading } = useAuth();
  const location = useLocation();

  // Debug logging
  console.log('ProtectedRoute Debug:', {
    path: location.pathname,
    isAuthenticated,
    isLoading,
    requireProfileComplete,
    requireAdmin,
    user: user ? {
      id: user.id,
      email: user.email,
      profile_completed: user.profile_completed,
      is_admin: user.is_admin
    } : null
  });

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    console.log('Redirecting to login - not authenticated');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Redirect to home if admin is required but user is not admin
  if (requireAdmin && user && !user.is_admin) {
    console.log('Redirecting to home - admin required');
    return <Navigate to="/" replace />;
  }

  // Redirect to profile setup if profile is not complete and required
  if (requireProfileComplete && user && !user.profile_completed) {
    console.log('Redirecting to profile setup - profile not complete');
    return <Navigate to="/profile-setup" replace />;
  }

  console.log('Rendering protected content');
  // Render protected content
  return <>{children}</>;
};

export default ProtectedRoute;