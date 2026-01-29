import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  className?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  message = 'Loading...', 
  className = '' 
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  return (
    <div className={`flex flex-col items-center justify-center space-y-2 ${className}`}>
      <div className={`animate-spin rounded-full border-b-2 border-indigo-600 dark:border-blue-400 transition-colors duration-200 ${sizeClasses[size]}`}></div>
      {message && (
        <p className={`text-wellness-light-textSecondary dark:text-slate-400 transition-colors duration-200 ${textSizeClasses[size]}`}>
          {message}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;