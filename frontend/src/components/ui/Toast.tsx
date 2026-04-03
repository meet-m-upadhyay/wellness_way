import React, { useEffect, useState } from 'react';

interface ToastProps {
  message: string;
  type?: 'warning' | 'error' | 'info' | 'success';
  /** If true, the toast will NOT auto-close. User must click the close icon. */
  persistent?: boolean;
  /** Auto-close duration in ms (only used if persistent=false). Default: 5000 */
  duration?: number;
  onClose: () => void;
  /** Optional action button */
  action?: {
    label: string;
    onClick: () => void;
  };
}

const Toast: React.FC<ToastProps> = ({
  message,
  type = 'warning',
  persistent = false,
  duration = 5000,
  onClose,
  action,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Trigger entrance animation
    requestAnimationFrame(() => setIsVisible(true));

    if (!persistent) {
      const timer = setTimeout(() => handleClose(), duration);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [persistent, duration]);

  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => onClose(), 300); // Wait for exit animation
  };

  const colorMap = {
    warning: {
      bg: 'bg-amber-50 dark:bg-amber-950/80',
      border: 'border-amber-200 dark:border-amber-800',
      icon: 'text-amber-500',
      text: 'text-amber-800 dark:text-amber-200',
      close: 'text-amber-400 hover:text-amber-600 dark:hover:text-amber-300',
      actionBg: 'bg-amber-600 hover:bg-amber-700 text-white',
    },
    error: {
      bg: 'bg-red-50 dark:bg-red-950/80',
      border: 'border-red-200 dark:border-red-800',
      icon: 'text-red-500',
      text: 'text-red-800 dark:text-red-200',
      close: 'text-red-400 hover:text-red-600 dark:hover:text-red-300',
      actionBg: 'bg-red-600 hover:bg-red-700 text-white',
    },
    info: {
      bg: 'bg-blue-50 dark:bg-blue-950/80',
      border: 'border-blue-200 dark:border-blue-800',
      icon: 'text-blue-500',
      text: 'text-blue-800 dark:text-blue-200',
      close: 'text-blue-400 hover:text-blue-600 dark:hover:text-blue-300',
      actionBg: 'bg-blue-600 hover:bg-blue-700 text-white',
    },
    success: {
      bg: 'bg-emerald-50 dark:bg-emerald-950/80',
      border: 'border-emerald-200 dark:border-emerald-800',
      icon: 'text-emerald-500',
      text: 'text-emerald-800 dark:text-emerald-200',
      close: 'text-emerald-400 hover:text-emerald-600 dark:hover:text-emerald-300',
      actionBg: 'bg-emerald-600 hover:bg-emerald-700 text-white',
    },
  };

  const colors = colorMap[type];

  const iconPaths: Record<string, string> = {
    warning: 'M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z',
    error: 'M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z',
    info: 'M11.25 11.25l.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z',
    success: 'M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z',
  };

  return (
    <div
      className={`fixed top-6 left-1/2 z-[9999] w-[calc(100%-2rem)] max-w-lg
        transform -translate-x-1/2 transition-all duration-300 ease-out
        ${isVisible && !isExiting ? 'translate-y-0 opacity-100' : '-translate-y-4 opacity-0'}
      `}
      role="alert"
    >
      <div
        className={`${colors.bg} ${colors.border} border rounded-2xl shadow-2xl shadow-black/10
          backdrop-blur-sm p-4 sm:p-5`}
      >
        <div className="flex items-start gap-3">
          {/* Icon */}
          <div className={`flex-shrink-0 mt-0.5 ${colors.icon}`}>
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d={iconPaths[type]} />
            </svg>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium leading-relaxed ${colors.text}`}>
              {message}
            </p>
            {action && (
              <button
                onClick={action.onClick}
                className={`mt-3 px-4 py-1.5 text-xs font-bold rounded-lg transition-colors ${colors.actionBg}`}
              >
                {action.label}
              </button>
            )}
          </div>

          {/* Close button */}
          <button
            onClick={handleClose}
            className={`flex-shrink-0 p-1 rounded-lg transition-colors ${colors.close}`}
            aria-label="Close notification"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default Toast;
