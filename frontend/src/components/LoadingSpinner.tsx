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

  const borderClasses = {
    sm: 'border-2',
    md: 'border-[3px]',
    lg: 'border-4'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  return (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`}>
      <div className={`
        animate-spin rounded-full 
        ${sizeClasses[size]} ${borderClasses[size]}
        border-wellness-light-border dark:border-wellness-dark-border
        border-t-primary-500 dark:border-t-primary-400
      `}></div>
      {message && (
        <p className={`text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary font-medium ${textSizeClasses[size]}`}>
          {message}
        </p>
      )}
    </div>
  );
};

export default LoadingSpinner;