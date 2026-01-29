import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';

interface NavigationProps {
  className?: string;
}

const Navigation: React.FC<NavigationProps> = ({ className = '' }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  const navigationItems = [
    { path: '/', label: 'Home', icon: '🏠', requiresProfile: false },
    { path: '/profile-setup', label: 'Profile Setup', icon: '👤', requiresProfile: false },
    { path: '/diet-plans', label: 'Diet Plans', icon: '🍽️', requiresProfile: true },
  ];

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const handleLogout = () => {
    logout();
    setIsUserMenuOpen(false);
  };

  return (
    <nav className={`bg-wellness-light-card dark:bg-slate-800 shadow-lg transition-colors duration-200 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <span className="text-2xl">🥗</span>
              <span className="text-xl font-bold text-wellness-light-text dark:text-slate-100 hidden sm:block transition-colors duration-200">
                WellnessWay
              </span>
            </Link>
          </div>

          {/* Desktop navigation */}
          <div className="hidden md:flex items-center space-x-8">
            {navigationItems.map((item) => {
              const isDisabled = item.requiresProfile && user && !user.profile_completed;
              const isActive = isActivePath(item.path);
              
              // Debug logging for Diet Plans item
              if (item.path === '/diet-plans') {
                console.log('Diet Plans Navigation Debug:', {
                  requiresProfile: item.requiresProfile,
                  user: user ? {
                    profile_completed: user.profile_completed
                  } : null,
                  isDisabled,
                  calculation: `${item.requiresProfile} && ${!!user} && ${user ? !user.profile_completed : 'no user'} = ${isDisabled}`
                });
              }
              
              if (isDisabled) {
                return (
                  <div
                    key={item.path}
                    className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-wellness-light-textMuted dark:text-slate-500 cursor-not-allowed transition-colors duration-200"
                    title="Complete your profile to access this feature"
                  >
                    <span>{item.icon}</span>
                    <span>{item.label}</span>
                  </div>
                );
              }
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                    isActive
                      ? 'bg-indigo-100 dark:bg-blue-900/50 text-indigo-700 dark:text-blue-300'
                      : 'text-wellness-light-textSecondary dark:text-slate-300 hover:text-wellness-light-text dark:hover:text-slate-100 hover:bg-wellness-light-elevated dark:hover:bg-slate-700'
                  }`}
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              );
            })}

            {/* Theme Toggle */}
            <ThemeToggle size="sm" />

            {/* User menu */}
            {user && (
              <div className="relative">
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-wellness-light-textSecondary dark:text-slate-300 hover:text-wellness-light-text dark:hover:text-slate-100 hover:bg-wellness-light-elevated dark:hover:bg-slate-700 transition-colors duration-200"
                >
                  <div className="w-8 h-8 bg-indigo-500 dark:bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium transition-colors duration-200">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <span className="hidden lg:block">{user.name}</span>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* User dropdown menu */}
                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-wellness-light-card dark:bg-slate-800 rounded-md shadow-lg border border-wellness-light-border dark:border-slate-600 py-1 z-50 transition-colors duration-200">
                    <div className="px-4 py-2 text-sm text-wellness-light-textSecondary dark:text-slate-300 border-b border-wellness-light-border dark:border-slate-600">
                      <div className="font-medium text-left truncate">{user.name}</div>
                      <div className="text-wellness-light-textMuted dark:text-slate-400 truncate" title={user.email}>{user.email}</div>
                    </div>
                    <Link
                      to="/profile-setup"
                      onClick={() => setIsUserMenuOpen(false)}
                      className="block px-4 py-2 text-sm text-wellness-light-textSecondary dark:text-slate-300 hover:bg-wellness-light-elevated dark:hover:bg-slate-700 transition-colors duration-200 text-left"
                    >
                      Profile Settings
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-wellness-light-textSecondary dark:text-slate-300 hover:bg-wellness-light-elevated dark:hover:bg-slate-700 transition-colors duration-200 text-left"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center space-x-2">
            {/* Theme Toggle for mobile */}
            <ThemeToggle size="sm" />
            
            {/* User avatar for mobile */}
            {user && (
              <div className="w-8 h-8 bg-indigo-500 dark:bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium transition-colors duration-200">
                {user.name.charAt(0).toUpperCase()}
              </div>
            )}
            
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-wellness-light-textMuted dark:text-slate-400 hover:text-wellness-light-textSecondary dark:hover:text-slate-300 hover:bg-wellness-light-elevated dark:hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500 dark:focus:ring-blue-400 transition-colors duration-200"
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              {/* Hamburger icon */}
              <svg
                className={`${isMenuOpen ? 'hidden' : 'block'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              {/* Close icon */}
              <svg
                className={`${isMenuOpen ? 'block' : 'hidden'} h-6 w-6`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className={`md:hidden ${isMenuOpen ? 'block' : 'hidden'}`}>
        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-wellness-light-elevated dark:bg-slate-700 transition-colors duration-200">
          {navigationItems.map((item) => {
            const isDisabled = item.requiresProfile && user && !user.profile_completed;
            const isActive = isActivePath(item.path);
            
            if (isDisabled) {
              return (
                <div
                  key={item.path}
                  className="flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium text-wellness-light-textMuted dark:text-slate-500 cursor-not-allowed transition-colors duration-200"
                >
                  <span>{item.icon}</span>
                  <span>{item.label}</span>
                  <span className="text-xs">(Profile Required)</span>
                </div>
              );
            }
            
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 ${
                  isActive
                    ? 'bg-indigo-100 dark:bg-blue-900/50 text-indigo-700 dark:text-blue-300'
                    : 'text-wellness-light-textSecondary dark:text-slate-300 hover:text-wellness-light-text dark:hover:text-slate-100 hover:bg-wellness-light-card dark:hover:bg-slate-600'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}

          {/* Mobile user menu */}
          {user && (
            <div className="border-t border-wellness-light-border dark:border-slate-600 pt-4 transition-colors duration-200">
              <div className="px-3 py-2">
                <div className="text-base font-medium text-wellness-light-text dark:text-slate-200 text-left truncate">{user.name}</div>
                <div className="text-sm text-wellness-light-textMuted dark:text-slate-400 text-left truncate" title={user.email}>{user.email}</div>
              </div>
              <Link
                to="/profile-setup"
                onClick={() => setIsMenuOpen(false)}
                className="block px-3 py-2 text-base font-medium text-wellness-light-textSecondary dark:text-slate-300 hover:text-wellness-light-text dark:hover:text-slate-100 hover:bg-wellness-light-card dark:hover:bg-slate-600 transition-colors duration-200 text-left"
              >
                Profile Settings
              </Link>
              <button
                onClick={() => {
                  handleLogout();
                  setIsMenuOpen(false);
                }}
                className="block w-full text-left px-3 py-2 text-base font-medium text-wellness-light-textSecondary dark:text-slate-300 hover:text-wellness-light-text dark:hover:text-slate-100 hover:bg-wellness-light-card dark:hover:bg-slate-600 transition-colors duration-200 text-left"
              >
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;