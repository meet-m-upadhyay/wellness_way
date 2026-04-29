import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ThemeToggle from './ThemeToggle';
import {
  Home,
  Utensils,
  User,
  ShieldCheck,
  Settings,
  LogOut,
  Salad,
  ChevronDown,
  History
} from 'lucide-react';

interface NavigationProps {
  className?: string;
}

const Navigation: React.FC<NavigationProps> = ({ className = '' }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  const userMenuRef = useRef<HTMLDivElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      // Close desktop user menu if clicking outside
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
      // Close mobile menu if clicking outside the nav container
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target as Node)) {
        // We only want to close if it's currently open
        // Check if the click was on the toggle button itself (handled by its own onClick)
        const toggleButton = (mobileMenuRef.current as HTMLElement).querySelector('button[aria-expanded]');
        if (toggleButton && toggleButton.contains(event.target as Node)) return;

        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navigationItems = [
    { path: '/', label: 'Home', icon: <Home size={18} />, requiresProfile: false },
    { path: '/diet-plans', label: 'Diet Plans', icon: <Utensils size={18} />, requiresProfile: true },
    { path: '/history', label: 'History', icon: <History size={18} />, requiresProfile: true },
    { path: '/profile-setup', label: 'Profile Setup', icon: <User size={18} />, requiresProfile: false },
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
    <nav
      ref={mobileMenuRef}
      className={`transition-colors duration-200 border-b border-wellness-light-border dark:border-wellness-dark-border bg-white/80 dark:bg-wellness-dark-bg/80 backdrop-blur-md sticky top-0 z-50 ${className}`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-20">
          {/* Logo and brand */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-gradient-to-br from-primary-400 to-primary-600 shadow-sm group-hover:scale-105 group-hover:rotate-6 transition-all duration-300 text-white">
                <Salad size={22} strokeWidth={2.5} />
              </div>
              <div className="flex flex-col text-left leading-[1.1] hidden sm:block">
                <span className="text-lg font-bold tracking-tight text-neutral-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors duration-200">
                  WellnessWay
                </span>
                <span className="text-[10px] font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-widest mt-0.5">
                  AI Diet Planner
                </span>
              </div>
            </Link>
          </div>

          {/* Desktop navigation */}
          <div className="hidden md:flex items-center space-x-2">
            {navigationItems.map((item) => {
              const isDisabled = item.requiresProfile && user && !user.profile_completed;
              const isActive = isActivePath(item.path);
              const isCore = item.path === '/diet-plans';

              if (isDisabled) {
                return (
                  <div
                    key={item.path}
                    className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-sm font-medium text-wellness-light-textMuted dark:text-wellness-dark-textMuted cursor-not-allowed"
                    title="Complete your profile to access this feature"
                  >
                    <span className="text-base">{item.icon}</span>
                    <span>{item.label}</span>
                  </div>
                );
              }

              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-2xl text-sm font-bold transition-all duration-300 transform hover:scale-[1.03] hover:shadow-sm ${isActive
                    ? isCore
                      ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 shadow-md scale-[1.02]'
                      : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-white'
                    : 'text-neutral-500 hover:text-neutral-900 dark:hover:text-white hover:bg-neutral-50 dark:hover:bg-neutral-800/50'
                    }`}
                >
                  <span className={`${isActive ? 'scale-110' : 'group-hover:scale-110'} transition-transform duration-300`}>{item.icon}</span>
                  <span>{item.label}</span>
                </Link>
              );
            })}


            {/* User menu */}
            {user && (
              <div className="relative ml-2" ref={userMenuRef}>
                <button
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className={`flex items-center space-x-3 p-1 rounded-2xl border transition-all duration-300 group ${isUserMenuOpen
                    ? 'border-primary-200 dark:border-primary-800 bg-primary-50/50 dark:bg-primary-900/10'
                    : 'border-transparent hover:border-neutral-200 dark:hover:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/50'}`}
                >
                  <div className="relative">
                    <div className="w-9 h-9 bg-gradient-to-br from-primary-400 to-primary-600 rounded-xl flex items-center justify-center text-white text-sm font-bold shadow-sm group-hover:shadow-md transition-all duration-300">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                    <div className={`absolute -inset-1 rounded-[14px] border-2 border-primary-500/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
                  </div>
                  <div className="flex flex-col items-start leading-none hidden lg:flex mr-1 ml-0.5">
                    <span className="text-sm font-bold text-neutral-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors duration-300">{user.name}</span>
                    <span className="text-[10px] text-neutral-400 uppercase font-bold mt-1 tracking-wider opacity-80">Account</span>
                  </div>
                  <ChevronDown className={`w-4 h-4 text-neutral-400 transition-all duration-300 ${isUserMenuOpen ? 'rotate-180 text-primary-50 text-primary-500' : 'group-hover:text-neutral-600 dark:group-hover:text-neutral-300'}`} strokeWidth={2.5} />
                </button>

                {/* User dropdown menu */}
                {isUserMenuOpen && (
                  <div className="absolute right-0 mt-3 w-64 bg-white dark:bg-neutral-900 rounded-3xl shadow-xl border border-neutral-200 dark:border-neutral-800 py-3 z-50 animate-scale-in">
                    <div className="px-6 py-4 border-b border-neutral-100 dark:border-neutral-800">
                      <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-2.5">Authenticated User</p>
                      <div className="font-bold text-sm text-neutral-900 dark:text-white truncate">{user.name}</div>
                      <div className="text-xs text-neutral-500 truncate mt-1" title={user.email}>{user.email}</div>
                    </div>

                    <div className="px-3 py-3 space-y-1">
                      <div className="px-3 py-2 flex items-center justify-between bg-neutral-50 dark:bg-neutral-800/50 rounded-2xl mb-2">
                        <span className="text-xs font-bold text-neutral-500 dark:text-neutral-400">Theme</span>
                        <ThemeToggle />
                      </div>

                      <Link
                        to="/profile-setup"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center gap-3 px-3 py-3 text-sm font-bold text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-primary-600 dark:hover:text-primary-400 rounded-2xl transition-all duration-300 transform hover:translate-x-1"
                      >
                        <Settings size={18} />
                        Profile Settings
                      </Link>

                      {user.is_admin && (
                        <Link
                          to="/admin"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="flex items-center gap-3 px-3 py-3 text-sm font-bold text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 hover:text-primary-600 dark:hover:text-primary-400 rounded-2xl transition-all duration-300 transform hover:translate-x-1"
                        >
                          <ShieldCheck size={18} />
                          Admin Dashboard
                        </Link>
                      )}
                    </div>

                    <div className="px-3 pb-1 border-t border-neutral-100 dark:border-neutral-800 mt-1 pt-3">
                      <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 w-full text-left px-3 py-3 text-sm font-bold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10 rounded-2xl transition-all duration-300 transform hover:translate-x-1"
                      >
                        <LogOut size={18} />
                        Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center space-x-2">

            {user && (
              <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-xl flex items-center justify-center text-white text-sm font-semibold shadow-sm">
                {user.name.charAt(0).toUpperCase()}
              </div>
            )}

            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="inline-flex items-center justify-center p-2 rounded-xl text-wellness-light-textMuted dark:text-wellness-dark-textMuted hover:bg-wellness-light-elevated dark:hover:bg-wellness-dark-elevated focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 transition-all duration-200"
              aria-expanded="false"
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className={`${isMenuOpen ? 'hidden' : 'block'} h-5 w-5`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
              <svg
                className={`${isMenuOpen ? 'block' : 'hidden'} h-5 w-5`}
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className={`md:hidden transition-all duration-300 ease-in-out border-t border-neutral-100 dark:border-neutral-800 ${isMenuOpen ? 'max-h-[700px] opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
        <div className="px-5 py-6 space-y-8 bg-white dark:bg-wellness-dark-bg">
          {/* Navigation Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between px-3">
              <p className="text-[10px] font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-widest">Main Navigation</p>
              <div className="h-px flex-1 bg-neutral-100 dark:bg-neutral-800 ml-4"></div>
            </div>
            <div className="space-y-2">
              {navigationItems.map((item) => {
                const isDisabled = item.requiresProfile && user && !user.profile_completed;
                const isActive = isActivePath(item.path);

                if (isDisabled) {
                  return (
                    <div
                      key={item.path}
                      className="flex items-center space-x-3 px-4 py-3.5 rounded-2xl text-base font-bold text-neutral-300 dark:text-neutral-700 cursor-not-allowed border border-transparent"
                    >
                      <div className="grayscale opacity-50">{item.icon}</div>
                      <span className="opacity-50">{item.label}</span>
                      <div className="ml-auto flex items-center gap-1.5 opacity-40">
                        <span className="text-[10px] font-bold uppercase tracking-tight">Locked</span>
                        <span className="text-xs">🔒</span>
                      </div>
                    </div>
                  );
                }

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setIsMenuOpen(false)}
                    className={`flex items-center space-x-3 px-4 py-3.5 rounded-2xl text-base font-bold transition-all duration-300 transform active:scale-[0.98] ${isActive
                      ? 'bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 shadow-lg'
                      : 'text-neutral-500 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 border border-transparent hover:border-neutral-100 dark:hover:border-neutral-800'
                      }`}
                  >
                    <div className={`transition-transform duration-300 ${isActive ? 'scale-110' : ''}`}>{item.icon}</div>
                    <span>{item.label}</span>
                    {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary-500"></div>}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Account Section */}
          {user && (
            <div className="space-y-4">
              <div className="flex items-center justify-between px-3">
                <p className="text-[10px] font-bold text-neutral-400 dark:text-neutral-500 uppercase tracking-widest">Account Settings</p>
                <div className="h-px flex-1 bg-neutral-100 dark:bg-neutral-800 ml-4"></div>
              </div>

              <div className="bg-neutral-50 dark:bg-neutral-800/40 border border-neutral-100 dark:border-neutral-800/60 rounded-[32px] p-5 mb-4 shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-gradient-to-br from-primary-400 to-primary-600 rounded-[20px] flex items-center justify-center text-white text-xl font-bold shadow-md border-2 border-white dark:border-neutral-900">
                    {user.name.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex flex-col text-left truncate">
                    <div className="text-base font-bold text-neutral-900 dark:text-white truncate">{user.name}</div>
                    <div className="text-xs text-neutral-500 truncate mt-0.5" title={user.email}>{user.email}</div>
                    <div className="mt-2 text-[9px] font-bold text-primary-600 dark:text-primary-400 uppercase tracking-wider bg-primary-50 dark:bg-primary-900/20 px-2 py-0.5 rounded-full w-fit">
                      Premium Member
                    </div>
                  </div>
                </div>
              </div>

              <div className="px-2 space-y-2">
                <div className="flex items-center justify-between px-4 py-3.5 rounded-2xl bg-neutral-50 dark:bg-neutral-800/40 border border-neutral-100 dark:border-neutral-800/60">
                  <span className="text-base font-bold text-neutral-600 dark:text-neutral-400">Appearance</span>
                  <ThemeToggle />
                </div>

                <Link
                  to="/profile-setup"
                  onClick={() => setIsMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3.5 rounded-2xl text-base font-bold text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-all duration-300 transform active:scale-[0.98] border border-transparent hover:border-neutral-100 dark:hover:border-neutral-800"
                >
                  <Settings size={20} />
                  <span>Profile Settings</span>
                </Link>

                {user.is_admin && (
                  <Link
                    to="/admin"
                    onClick={() => setIsMenuOpen(false)}
                    className="flex items-center gap-3 px-4 py-3.5 rounded-2xl text-base font-bold text-neutral-600 dark:text-neutral-400 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-all duration-300 transform active:scale-[0.98] border border-transparent hover:border-neutral-100 dark:hover:border-neutral-800"
                  >
                    <ShieldCheck size={20} />
                    <span>Admin Dashboard</span>
                  </Link>
                )}
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMenuOpen(false);
                  }}
                  className="flex items-center gap-3 w-full text-left px-4 py-3.5 rounded-2xl text-base font-bold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/10 transition-all duration-300 transform active:scale-[0.98] border border-transparent hover:border-red-100/50 dark:hover:border-red-900/20"
                >
                  <LogOut size={20} />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;