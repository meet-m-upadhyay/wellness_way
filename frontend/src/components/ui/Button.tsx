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
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-800 transition-colors duration-200';
  
  const variantClasses = {
    primary: 'bg-indigo-600 dark:bg-blue-600 text-white hover:bg-indigo-700 dark:hover:bg-blue-700 focus:ring-indigo-500 dark:focus:ring-blue-400 disabled:bg-indigo-300 dark:disabled:bg-blue-400',
    secondary: 'bg-wellness-light-textMuted dark:bg-slate-600 text-white hover:bg-wellness-light-textSecondary dark:hover:bg-slate-500 focus:ring-wellness-light-textSecondary dark:focus:ring-slate-400 disabled:bg-wellness-light-textMuted/50 dark:disabled:bg-slate-700',
    outline: 'border border-wellness-light-border dark:border-slate-600 bg-wellness-light-card dark:bg-slate-800 text-wellness-light-textSecondary dark:text-slate-300 hover:bg-wellness-light-elevated dark:hover:bg-slate-700 focus:ring-indigo-500 dark:focus:ring-blue-400 disabled:bg-wellness-light-elevated dark:disabled:bg-slate-700 disabled:text-wellness-light-textMuted dark:disabled:text-slate-500',
    ghost: 'text-wellness-light-textSecondary dark:text-slate-300 hover:bg-wellness-light-elevated dark:hover:bg-slate-700 focus:ring-indigo-500 dark:focus:ring-blue-400 disabled:text-wellness-light-textMuted dark:disabled:text-slate-500',
    danger: 'bg-red-600 dark:bg-red-700 text-white hover:bg-red-700 dark:hover:bg-red-800 focus:ring-red-500 dark:focus:ring-red-400 disabled:bg-red-300 dark:disabled:bg-red-800',
  };
  
  const sizeClasses = {
    sm: 'px-3 py-2 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };
  
  const widthClass = fullWidth ? 'w-full' : '';
  
  const isDisabled = disabled || loading;
  
  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${widthClass} ${className}`}
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