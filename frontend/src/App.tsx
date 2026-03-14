import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { AnimatePresence } from 'framer-motion';
import PageLayout from './components/layout/PageLayout';
import {
  Salad,
  User,
  Sparkles,
  TrendingUp
} from 'lucide-react';
import ErrorBoundary from './components/ErrorBoundary';
import Header from './components/Header';
import ProfileSetup from './components/ProfileSetup';
import DietPlans from './pages/DietPlans';
import UserDashboard from './components/UserDashboard';
import LoginPage from './components/auth/LoginPage';
import AccountDisabledPage from './components/auth/AccountDisabledPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AdminPage from './pages/AdminPage';
import { useUserStatusCheck } from './hooks/useUserStatusCheck';
import './App.css';

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <AppProvider>
            <Router>
              <AppContent />
            </Router>
          </AppProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

function AppContent() {
  const { isDisabled, user } = useAuth();
  const location = useLocation();

  // Periodically check if user is still active (every 5 minutes to avoid rate limits)
  useUserStatusCheck(300000); // 5 minutes = 300,000ms

  // Show disabled page if user is disabled
  if (isDisabled) {
    return (
      <AccountDisabledPage
        userEmail={user?.email}
        userName={user?.name}
      />
    );
  }

  return (
    <div className="App min-h-screen bg-wellness-light-bg dark:bg-wellness-dark-bg transition-colors duration-200">
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          {/* Public routes */}
          <Route path="/login" element={<PageLayout><LoginPage /></PageLayout>} />

          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Header />
              <PageLayout>
                <HomePage />
              </PageLayout>
            </ProtectedRoute>
          } />

          <Route path="/profile-setup" element={
            <ProtectedRoute>
              <Header />
              <PageLayout>
                <ProfileSetupWrapper />
              </PageLayout>
            </ProtectedRoute>
          } />

          <Route path="/diet-plans" element={
            <ProtectedRoute requireProfileComplete={true}>
              <Header />
              <PageLayout>
                <DietPlans />
              </PageLayout>
            </ProtectedRoute>
          } />

          <Route path="/admin" element={
            <ProtectedRoute requireAdmin={true}>
              <Header />
              <PageLayout>
                <AdminPage />
              </PageLayout>
            </ProtectedRoute>
          } />

          {/* Redirect unknown routes to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AnimatePresence>
    </div>
  );
}

// Wrapper component to provide user key to ProfileSetup
function ProfileSetupWrapper() {
  // This will be implemented in ProfileSetup itself
  return <ProfileSetup />;
}

// Home page component
function HomePage() {
  const { user } = useAuth();

  return (
    <main className="animate-page-enter">
      <div className="max-w-7xl mx-auto py-8 sm:py-12 px-4 sm:px-6 lg:px-8">
        {/* Greeting Section */}
        <div className="text-left space-y-2">
          <h1 className="text-4xl font-bold text-neutral-900 dark:text-white tracking-tight">
            Hello {user?.name?.split(' ')[0] || 'there'} 👋
          </h1>
          <p className="text-lg text-neutral-500 dark:text-neutral-400">
            Welcome back to WellnessWay. Your precision nutrition journey continues here.
          </p>
        </div>

        {/* Quick Actions Section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {user && !user.profile_completed ? (
            <Link
              to="/profile-setup"
              className="group p-6 bg-white dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 shadow-sm hover:shadow-md hover:border-emerald-500/30 transition-all duration-300 flex items-center gap-4"
            >
              <div className="h-12 w-12 rounded-2xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center text-emerald-600 group-hover:scale-110 transition-transform">
                <Sparkles size={24} />
              </div>
              <div className="text-left">
                <h3 className="font-bold text-neutral-900 dark:text-white">Complete Profile</h3>
                <p className="text-xs text-neutral-500">Unlock your AI diet plan</p>
              </div>
            </Link>
          ) : user?.profile_completed ? (
            <>
              <Link
                to="/diet-plans"
                className="group p-6 bg-white dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 shadow-sm hover:shadow-md hover:border-emerald-500/30 transition-all duration-300 flex items-center gap-4"
              >
                <div className="h-12 w-12 rounded-2xl bg-emerald-50 dark:bg-emerald-900/20 flex items-center justify-center text-emerald-600 group-hover:scale-110 transition-transform">
                  <Salad size={24} />
                </div>
                <div className="text-left">
                  <h3 className="font-bold text-neutral-900 dark:text-white">View Diet Plans</h3>
                  <p className="text-xs text-neutral-500">Check your latest meals</p>
                </div>
              </Link>
              <Link
                to="/profile-setup"
                className="group p-6 bg-white dark:bg-neutral-900 rounded-3xl border border-neutral-200 dark:border-neutral-800 shadow-sm hover:shadow-md hover:border-blue-500/30 transition-all duration-300 flex items-center gap-4"
              >
                <div className="h-12 w-12 rounded-2xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                  <User size={24} />
                </div>
                <div className="text-left">
                  <h3 className="font-bold text-neutral-900 dark:text-white">Edit Profile</h3>
                  <p className="text-xs text-neutral-500">Update health metrics</p>
                </div>
              </Link>
            </>
          ) : null}

          <div className="p-6 bg-neutral-50 dark:bg-neutral-800/50 rounded-3xl border border-neutral-100 dark:border-neutral-800 flex items-center gap-4 opacity-60">
            <div className="h-12 w-12 rounded-2xl bg-neutral-200 dark:bg-neutral-700 flex items-center justify-center text-neutral-400">
              <TrendingUp size={24} />
            </div>
            <div className="text-left">
              <h3 className="font-bold text-neutral-400 dark:text-neutral-500">Insights</h3>
              <p className="text-xs text-neutral-400">Coming soon</p>
            </div>
          </div>
        </div>

        {/* User Dashboard Section */}
        <div className="pt-4">
          <UserDashboard />
        </div>
      </div>
    </main>
  );
}

export default App;