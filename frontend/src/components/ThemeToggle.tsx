import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({
  className = '',
  showLabel = false,
}) => {
  const { theme, toggleTheme, isLoading } = useTheme();
  const isDark = theme === 'dark';

  if (isLoading) {
    return (
      <div className={`w-14 h-7 rounded-full bg-neutral-100 dark:bg-neutral-800 animate-pulse ${className}`} />
    );
  }

  return (
    <div className={`flex items-center justify-between gap-3 ${className}`}>
      {showLabel && (
        <span className="text-sm font-bold text-neutral-600 dark:text-neutral-400">
          {isDark ? 'Dark Mode' : 'Light Mode'}
        </span>
      )}
      <button
        onClick={toggleTheme}
        className="relative flex h-7 w-14 items-center rounded-full bg-neutral-100 dark:bg-neutral-800 p-1 transition-colors duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
        aria-label="Toggle theme"
      >
        <motion.div
          className="flex h-5 w-5 items-center justify-center rounded-full bg-white dark:bg-neutral-900 shadow-sm"
          animate={{
            x: isDark ? 28 : 0,
          }}
          transition={{
            type: "spring",
            stiffness: 500,
            damping: 30,
          }}
        >
          <AnimatePresence mode="wait" initial={false}>
            {isDark ? (
              <motion.div
                key="moon"
                initial={{ opacity: 0, rotate: -90, scale: 0.5 }}
                animate={{ opacity: 1, rotate: 0, scale: 1 }}
                exit={{ opacity: 0, rotate: 90, scale: 0.5 }}
                transition={{ duration: 0.2 }}
                className="text-primary-400"
              >
                <Moon size={12} fill="currentColor" />
              </motion.div>
            ) : (
              <motion.div
                key="sun"
                initial={{ opacity: 0, rotate: -90, scale: 0.5 }}
                animate={{ opacity: 1, rotate: 0, scale: 1 }}
                exit={{ opacity: 0, rotate: 90, scale: 0.5 }}
                transition={{ duration: 0.2 }}
                className="text-amber-500"
              >
                <Sun size={12} fill="currentColor" />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </button>
    </div>
  );
};

export default ThemeToggle;