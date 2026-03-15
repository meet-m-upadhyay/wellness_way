import React, { ButtonHTMLAttributes } from 'react';
import LoadingSpinner from '../LoadingSpinner';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  fullWidth = false,
  disabled,
  children,
  className = '',
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-wellness-dark-bg transition-all duration-200 active:scale-[0.98]';

  const variantClasses = {
    primary: 'bg-gradient-to-r from-primary-500 to-primary-600 text-white hover:from-primary-600 hover:to-primary-700 focus-visible:ring-primary-500 disabled:from-primary-300 disabled:to-primary-400 dark:disabled:from-primary-700 dark:disabled:to-primary-800 shadow-sm hover:shadow-md',
    secondary: 'bg-wellness-light-elevated dark:bg-wellness-dark-elevated text-wellness-light-text dark:text-wellness-dark-text hover:bg-gray-200 dark:hover:bg-wellness-dark-border focus-visible:ring-gray-400 disabled:opacity-50',
    outline: 'border border-wellness-light-border dark:border-wellness-dark-border bg-white dark:bg-wellness-dark-card text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated focus-visible:ring-primary-500 disabled:opacity-50',
    ghost: 'text-wellness-light-textSecondary dark:text-wellness-dark-textSecondary hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated focus-visible:ring-primary-500 disabled:opacity-50',
    danger: 'bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-600 hover:to-red-700 focus-visible:ring-red-500 disabled:from-red-300 disabled:to-red-400 shadow-sm hover:shadow-md',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm gap-1.5',
    md: 'px-4 py-2 text-sm gap-2',
    lg: 'px-6 py-2.5 text-base gap-2',
  };

  const widthClass = fullWidth ? 'w-full' : '';

  const isDisabled = disabled || loading;

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${widthClass} ${isDisabled ? 'cursor-not-allowed' : 'hover:scale-[1.02]'} ${className}`}
      disabled={isDisabled}
      {...props}
    >
      {loading && (
        <LoadingSpinner size="sm" message="" className="mr-2" />
      )}
      {children}
    </button>
  );
};

export default Button;