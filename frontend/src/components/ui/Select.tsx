import React, { SelectHTMLAttributes, forwardRef } from 'react';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  fullWidth?: boolean;
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  label,
  error,
  helperText,
  options,
  placeholder,
  fullWidth = false,
  className = '',
  ...props
}, ref) => {
  const selectClasses = `
    block px-3 py-2 border rounded-md shadow-sm 
    focus:outline-none focus:ring-indigo-500 dark:focus:ring-blue-400 
    focus:border-indigo-500 dark:focus:border-blue-400 sm:text-sm
    transition-colors duration-200
    ${error 
      ? 'border-red-300 dark:border-red-600 text-red-900 dark:text-red-200 focus:ring-red-500 focus:border-red-500 bg-red-50 dark:bg-red-900/20' 
      : 'border-gray-300 dark:border-gray-600'
    }
    ${fullWidth ? 'w-full' : ''}
    ${props.disabled 
      ? 'bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400' 
      : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100'
    }
  `;

  return (
    <div className={fullWidth ? 'w-full' : ''}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 transition-colors duration-200">
          {label}
          {props.required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <select
        ref={ref}
        className={`${selectClasses} ${className}`}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </select>
      
      {error && (
        <p className="mt-1 text-sm text-red-600 dark:text-red-400 transition-colors duration-200">{error}</p>
      )}
      
      {helperText && !error && (
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 transition-colors duration-200 text-left">{helperText}</p>
      )}
    </div>
  );
});

Select.displayName = 'Select';

export default Select;