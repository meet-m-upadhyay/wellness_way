import React, { useState } from 'react';

interface UserActionsProps {
  userId: string;
  userName: string;
  userEmail: string;
  isActive: boolean;
  isAdmin: boolean;
  onEnable: (userId: string) => Promise<void>;
  onDisable: (userId: string) => Promise<void>;
  disabled?: boolean;
}

const UserActions: React.FC<UserActionsProps> = ({
  userId,
  userName,
  userEmail,
  isActive,
  isAdmin,
  onEnable,
  onDisable,
  disabled = false
}) => {
  const [showEnableConfirm, setShowEnableConfirm] = useState(false);
  const [showDisableConfirm, setShowDisableConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

  // Don't show actions for admin users
  if (isAdmin) {
    return (
      <span className="text-xs text-wellness-light-textMuted dark:text-wellness-dark-textMuted italic">
        Admin Account
      </span>
    );
  }

  const handleEnable = async () => {
    try {
      setLoading(true);
      await onEnable(userId);
      setShowEnableConfirm(false);
    } catch (error) {
      console.error('Error enabling user:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async () => {
    try {
      setLoading(true);
      await onDisable(userId);
      setShowDisableConfirm(false);
    } catch (error) {
      console.error('Error disabling user:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="flex space-x-2">
        {!isActive ? (
          <button
            onClick={() => setShowEnableConfirm(true)}
            disabled={disabled}
            className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-xl text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            title="Enable this user's access to the application"
          >
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Enable
          </button>
        ) : (
          <button
            onClick={() => setShowDisableConfirm(true)}
            disabled={disabled}
            className="inline-flex items-center px-3 py-1 text-sm font-medium rounded-xl text-white bg-red-500 hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            title="Disable this user's access to the application"
          >
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            Disable
          </button>
        )}
      </div>

      {/* Enable Confirmation Modal */}
      {showEnableConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div
              className="fixed inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm transition-opacity"
              aria-hidden="true"
              onClick={() => !loading && setShowEnableConfirm(false)}
            ></div>

            {/* Modal positioning */}
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

            {/* Modal content */}
            <div className="inline-block align-bottom bg-white dark:bg-wellness-dark-card rounded-2xl px-4 pt-5 pb-4 text-left overflow-hidden shadow-card-hover dark:shadow-card-dark-hover border border-wellness-light-border dark:border-wellness-dark-border transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div className="sm:flex sm:items-start">
                <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-green-100 dark:bg-green-900/30 sm:mx-0 sm:h-10 sm:w-10">
                  <svg className="h-6 w-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                  <h3 className="text-lg leading-6 font-semibold text-wellness-light-text dark:text-wellness-dark-text" id="modal-title">
                    Enable User Access
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                      Are you sure you want to enable <strong>{userName}</strong>? This will allow <strong>{userEmail}</strong> to access the WellnessWay application again.
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={handleEnable}
                  disabled={loading}
                  className="w-full inline-flex justify-center rounded-xl border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-semibold text-white hover:bg-primary-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  {loading ? (
                    <div className="flex items-center">
                      Enable User
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-2"></div>
                    </div>
                  ) : (
                    'Enable User'
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowEnableConfirm(false)}
                  disabled={loading}
                  className="mt-3 w-full inline-flex justify-center rounded-xl border border-wellness-light-border dark:border-wellness-dark-border shadow-sm px-4 py-2 bg-white dark:bg-wellness-dark-elevated text-base font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-card sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50 transition-colors duration-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Disable Confirmation Modal */}
      {showDisableConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <div
              className="fixed inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm transition-opacity"
              aria-hidden="true"
              onClick={() => !loading && setShowDisableConfirm(false)}
            ></div>

            {/* Modal positioning */}
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

            {/* Modal content */}
            <div className="inline-block align-bottom bg-white dark:bg-wellness-dark-card rounded-2xl px-4 pt-5 pb-4 text-left overflow-hidden shadow-card-hover dark:shadow-card-dark-hover border border-wellness-light-border dark:border-wellness-dark-border transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div className="sm:flex sm:items-start">
                <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 dark:bg-red-900/30 sm:mx-0 sm:h-10 sm:w-10">
                  <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                  <h3 className="text-lg leading-6 font-semibold text-wellness-light-text dark:text-wellness-dark-text" id="modal-title">
                    Disable User Access
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary">
                      Are you sure you want to disable <strong>{userName}</strong>? This will prevent <strong>{userEmail}</strong> from accessing the WellnessWay application. They can be re-enabled later.
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={handleDisable}
                  disabled={loading}
                  className="w-full inline-flex justify-center rounded-xl border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-semibold text-white hover:bg-red-700 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  {loading ? (
                    <div className="flex items-center">
                      Disable User
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-2"></div>
                    </div>
                  ) : (
                    'Disable User'
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setShowDisableConfirm(false)}
                  disabled={loading}
                  className="mt-3 w-full inline-flex justify-center rounded-xl border border-wellness-light-border dark:border-wellness-dark-border shadow-sm px-4 py-2 bg-white dark:bg-wellness-dark-elevated text-base font-medium text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-card sm:mt-0 sm:w-auto sm:text-sm disabled:opacity-50 transition-colors duration-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default UserActions;