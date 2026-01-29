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
      <div className="flex flex-col space-y-2 p-3 bg-green-50 border border-green-200 rounded-md">
        <div className="text-sm text-green-800">
          <strong>Approve {userName}?</strong>
        </div>
        <div className="text-xs text-green-700">
          This will allow {userEmail} to access the WellnessWay application.
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleApprove}
            disabled={loading}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-1 px-3 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed"
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
            className="bg-wellness-light-textMuted hover:bg-wellness-light-textSecondary text-wellness-light-card dark:bg-wellness-dark-textMuted dark:hover:bg-wellness-dark-textSecondary dark:text-wellness-dark-card font-bold py-1 px-3 rounded text-xs disabled:opacity-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  if (showDeclineConfirm) {
    return (
      <div className="flex flex-col space-y-2 p-3 bg-red-50 border border-red-200 rounded-md">
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
            className="bg-red-600 hover:bg-red-700 text-white font-bold py-1 px-3 rounded text-xs disabled:opacity-50 disabled:cursor-not-allowed"
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
            className="bg-wellness-light-textMuted hover:bg-wellness-light-textSecondary text-wellness-light-card dark:bg-wellness-dark-textMuted dark:hover:bg-wellness-dark-textSecondary dark:text-wellness-dark-card font-bold py-1 px-3 rounded text-xs disabled:opacity-50 transition-colors"
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
        className="bg-secondary-500 hover:bg-secondary-600 text-white font-bold py-1 px-3 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
        className="bg-red-500 hover:bg-red-600 text-white font-bold py-1 px-3 rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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