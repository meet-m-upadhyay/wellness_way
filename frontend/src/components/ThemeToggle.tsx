import React from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSun, faMoon } from '@fortawesome/free-solid-svg-icons';
import { useTheme } from '../context/ThemeContext';

interface ThemeToggleProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  className = '', 
  size = 'md' 
}) => {
  const { theme, toggleTheme, isLoading } = useTheme();

  const sizeClasses = {
    sm: 'w-8 h-8 text-sm',
    md: 'w-10 h-10 text-base',
    lg: 'w-12 h-12 text-lg'
  };

  const iconSizes = {
    sm: 'sm',
    md: '1x',
    lg: 'lg'
  } as const;

  if (isLoading) {
    return (
      <div 
        className={`${sizeClasses[size]} rounded-full bg-gray-200 dark:bg-slate-700 animate-pulse ${className}`}
        aria-label="Loading theme toggle"
      />
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className={`
        ${sizeClasses[size]} 
        rounded-full 
        flex items-center justify-center 
        transition-all duration-200 ease-in-out
        bg-gray-100 hover:bg-gray-200 
        dark:bg-slate-700 dark:hover:bg-slate-600
        text-gray-700 hover:text-gray-900
        dark:text-slate-300 dark:hover:text-slate-100
        border border-gray-300 dark:border-slate-600
        focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
        dark:focus:ring-blue-400 dark:focus:ring-offset-slate-800
        transform hover:scale-105 active:scale-95
        ${className}
      `}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
    >
      <FontAwesomeIcon
        icon={theme === 'light' ? faMoon : faSun}
        size={iconSizes[size]}
        className={`
          transition-all duration-200 ease-in-out
          ${theme === 'light' 
            ? 'text-slate-600 dark:text-slate-400' 
            : 'text-yellow-500 dark:text-yellow-400'
          }
        `}
      />
    </button>
  );
};

export default ThemeToggle;