import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

/**
 * Hook to periodically check if the user is still active
 * This helps detect when an admin disables a user while they're using the app
 * Uses smart checking to avoid rate limits
 */
export const useUserStatusCheck = (intervalMs: number = 300000) => { // Check every 5 minutes instead of 30 seconds
  const { isAuthenticated, checkUserStatus } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    // Don't check immediately on mount to avoid rate limits
    // Only set up periodic checking
    const interval = setInterval(() => {
      checkUserStatus();
    }, intervalMs);

    return () => clearInterval(interval);
  }, [isAuthenticated, checkUserStatus, intervalMs]);
};