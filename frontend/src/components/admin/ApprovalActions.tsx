import React, { useState } from 'react';

interface ApprovalActionsProps {
  requestId: string;
  userName: string;
  userEmail: string;
  onApprove: (requestId: string) => Promise<void>;
  onDecline: (requestId: string) => Promise<void>;
  disabled?: boolean;
}

const ApprovalActions: React.FC<ApprovalActionsProps> = ({
  requestId,
  userName,
  userEmail,
  onApprove,
  onDecline,
  disabled = false
}) => {
  const [showApproveConfirm, setShowApproveConfirm] = useState(false);
  const [showDeclineConfirm, setShowDeclineConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    try {
      setLoading(true);
      await onApprove(requestId);
      setShowApproveConfirm(false);
    } catch (error) {
      console.error('Error approving request:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDecline = async () => {
    try {
      setLoading(true);
      await onDecline(requestId);
      setShowDeclineConfirm(false);
    } catch (error) {
      console.error('Error declining request:', error);
    } finally {
      setLoading(false);
    }
  };

  if (showApproveConfirm) {
    return (
      <div className="flex flex-col space-y-2 p-3 bg-primary-50 dark:bg-primary-900/10 border border-primary-200/60 dark:border-primary-800/30 rounded-xl">
        <div className="text-sm text-green-800">
          <strong>Approve {userName}?</strong>
        </div>
        <div className="text-xs text-primary-700 dark:text-primary-300">
          This will allow {userEmail} to access the WellnessWay application.
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleApprove}
            disabled={loading}
            className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-1 px-3 rounded-lg text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                Approving...
              </div>
            ) : (
              'Confirm Approve'
            )}
          </button>
          <button
            onClick={() => setShowApproveConfirm(false)}
            disabled={loading}
            className="bg-wellness-light-elevated hover:bg-wellness-light-border dark:bg-wellness-dark-elevated dark:hover:bg-wellness-dark-border text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary font-semibold py-1 px-3 rounded-lg text-xs disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  if (showDeclineConfirm) {
    return (
      <div className="flex flex-col space-y-2 p-3 bg-red-50 dark:bg-red-900/10 border border-red-200/60 dark:border-red-800/30 rounded-xl">
        <div className="text-sm text-red-800">
          <strong>Decline {userName}?</strong>
        </div>
        <div className="text-xs text-red-700">
          This will deny {userEmail} access to the WellnessWay application. They can request access again later.
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleDecline}
            disabled={loading}
            className="bg-red-600 hover:bg-red-700 text-white font-semibold py-1 px-3 rounded-lg text-xs disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                Declining...
              </div>
            ) : (
              'Confirm Decline'
            )}
          </button>
          <button
            onClick={() => setShowDeclineConfirm(false)}
            disabled={loading}
            className="bg-wellness-light-elevated hover:bg-wellness-light-border dark:bg-wellness-dark-elevated dark:hover:bg-wellness-dark-border text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary font-semibold py-1 px-3 rounded-lg text-xs disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex space-x-2">
      <button
        onClick={() => setShowApproveConfirm(true)}
        disabled={disabled}
        className="rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 hover:from-primary-600 hover:to-primary-700 text-white font-semibold py-1 px-3 text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        title="Approve this user's registration request"
      >
        <div className="flex items-center">
          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Approve
        </div>
      </button>

      <button
        onClick={() => setShowDeclineConfirm(true)}
        disabled={disabled}
        className="rounded-xl bg-red-500 hover:bg-red-600 text-white font-semibold py-1 px-3 text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        title="Decline this user's registration request"
      >
        <div className="flex items-center">
          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
          Decline
        </div>
      </button>
    </div>
  );
};

export default ApprovalActions;