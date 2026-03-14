import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../LoadingSpinner';
import ErrorMessage from '../ErrorMessage';

interface RegistrationRequest {
  id: string;
  email: string;
  name: string;
  google_id: string;
  status: 'pending' | 'approved' | 'declined';
  created_at: string;
  updated_at: string;
}

interface PendingRequestsListProps {
  onApprove: (requestId: string) => Promise<void>;
  onDecline: (requestId: string) => Promise<void>;
  refreshTrigger?: number; // Used to trigger refresh from parent
}

const PendingRequestsList: React.FC<PendingRequestsListProps> = ({
  onApprove,
  onDecline,
  refreshTrigger = 0
}) => {
  const [requests, setRequests] = useState<RegistrationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

  const loadPendingRequests = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('health_buddy_access_token');
      if (!token) {
        throw new Error('No access token found');
      }

      const response = await fetch(`${API_BASE_URL}/admin/pending-requests`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to load pending requests');
      }

      const data = await response.json();
      setRequests(data.requests || []);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load pending requests';
      setError(errorMessage);
      console.error('Error loading pending requests:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPendingRequests();
  }, [refreshTrigger]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleApprove = async (requestId: string) => {
    try {
      setActionLoading(requestId);
      await onApprove(requestId);
      // Refresh the list after successful approval
      await loadPendingRequests();
    } catch (err) {
      console.error('Error approving request:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDecline = async (requestId: string) => {
    try {
      setActionLoading(requestId);
      await onDecline(requestId);
      // Refresh the list after successful decline
      await loadPendingRequests();
    } catch (err) {
      console.error('Error declining request:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid date';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-8">
        <LoadingSpinner message='' />
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-4">
        <ErrorMessage message={error} />
        <button
          onClick={loadPendingRequests}
          className="mt-4 rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white py-2 px-4 text-sm font-semibold transition-all duration-200"
        >
          Retry
        </button>
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="bg-white dark:bg-wellness-dark-card shadow-card dark:shadow-card-dark rounded-2xl border border-wellness-light-border dark:border-wellness-dark-border p-6">
        <div className="text-center py-8">
          <svg
            className="mx-auto h-12 w-12 text-wellness-light-textMuted dark:text-wellness-dark-textMuted"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-wellness-light-text dark:text-wellness-dark-text">No pending requests</h3>
          <p className="mt-1 text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
            All registration requests have been processed.
          </p>
          <button
            onClick={loadPendingRequests}
            className="mt-4 rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white py-2 px-4 text-sm font-semibold transition-all duration-200"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-wellness-dark-card shadow-card dark:shadow-card-dark rounded-2xl border border-wellness-light-border dark:border-wellness-dark-border">
      <div className="px-4 py-5 sm:px-6 border-b border-wellness-light-border dark:border-wellness-dark-border">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg leading-6 font-medium text-wellness-light-text dark:text-wellness-dark-text">
              Pending Registration Requests
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
              {requests.length} user{requests.length !== 1 ? 's' : ''} awaiting approval
            </p>
          </div>
          <button
            onClick={loadPendingRequests}
            className="rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white py-2 px-4 text-sm font-semibold transition-all duration-200"
          >
            Refresh
          </button>
        </div>
      </div>

      <ul className="divide-y divide-wellness-light-border dark:divide-wellness-dark-border">
        {requests.map((request) => (
          <li key={request.id} className="px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {request.name?.charAt(0)?.toUpperCase() || 'U'}
                    </span>
                  </div>
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-wellness-light-text dark:text-wellness-dark-text">
                    {request.name}
                  </div>
                  <div className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                    {request.email}
                  </div>
                  <div className="text-xs text-wellness-light-textMuted dark:text-wellness-dark-textMuted">
                    Requested: {formatDate(request.created_at)}
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-lg text-xs font-medium bg-amber-100 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200">
                  Pending
                </span>

                <div className="flex space-x-2">
                  <button
                    onClick={() => handleApprove(request.id)}
                    disabled={actionLoading === request.id}
                    className="rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white py-1 px-3 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    {actionLoading === request.id ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                        Approving...
                      </div>
                    ) : (
                      'Approve'
                    )}
                  </button>

                  <button
                    onClick={() => handleDecline(request.id)}
                    disabled={actionLoading === request.id}
                    className="rounded-xl bg-red-500 hover:bg-red-600 text-white py-1 px-3 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    {actionLoading === request.id ? (
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                        Declining...
                      </div>
                    ) : (
                      'Decline'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default PendingRequestsList;