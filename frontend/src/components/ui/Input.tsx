import React, { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helperText,
  fullWidth = false,
  className = '',
  ...props
}, ref) => {
  const inputClasses = `
    block px-3 py-2 border rounded-md shadow-sm 
    placeholder-wellness-light-textMuted dark:placeholder-slate-500
    focus:outline-none focus:ring-indigo-500 dark:focus:ring-blue-400 
    focus:border-indigo-500 dark:focus:border-blue-400 sm:text-sm
    transition-colors duration-200
    ${error 
      ? 'border-red-300 dark:border-red-600 text-red-900 dark:text-red-200 focus:ring-red-500 focus:border-red-500 bg-red-50 dark:bg-red-900/20' 
      : 'border-wellness-light-border dark:border-slate-600'
    }
    ${fullWidth ? 'w-full' : ''}
    ${props.disabled 
      ? 'bg-wellness-light-elevated dark:bg-slate-700 text-wellness-light-textMuted dark:text-slate-500' 
      : 'bg-wellness-light-card dark:bg-slate-800 text-wellness-light-text dark:text-slate-100'
    }
  `;

  return (
    <div className={fullWidth ? 'w-full' : ''}>
      {label && (
        <label className="block text-sm font-medium text-wellness-light-textSecondary dark:text-slate-300 mb-1 transition-colors duration-200">
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <input
        ref={ref}
        className={`${inputClasses} ${className}`}
        {...props}
      />
      
      {error && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400 transition-colors duration-200">{error}</p>
      )}
      
      {helperText && !error && (
        <p className="mt-1 text-sm text-wellness-light-textMuted dark:text-slate-400 transition-colors duration-200">{helperText}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;