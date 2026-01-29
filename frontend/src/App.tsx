import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import ErrorBoundary from './components/ErrorBoundary';
import Header from './components/Header';
import ProfileSetup from './components/ProfileSetup';
import DietPlans from './pages/DietPlans';
import UserDashboard from './components/UserDashboard';
import LoginPage from './components/auth/LoginPage';
import AccountDisabledPage from './components/auth/AccountDisabledPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
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
    <div className="App min-h-screen bg-wellness-light-bg dark:bg-slate-900 transition-colors duration-200">
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* Protected routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <Header />
            <HomePage />
          </ProtectedRoute>
        } />
        
        <Route path="/profile-setup" element={
          <ProtectedRoute>
            <Header />
            <ProfileSetupWrapper />
          </ProtectedRoute>
        } />
        
        <Route path="/diet-plans" element={
          <ProtectedRoute requireProfileComplete={true}>
            <Header />
            <DietPlans />
          </ProtectedRoute>
        } />
        
        {/* Redirect unknown routes to home */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
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
    <main>
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Debug Info - Temporary */}
        {/* {user && (
          <div className="bg-blue-100 border border-blue-400 text-blue-700 px-4 py-3 rounded mb-4">
            <strong>Debug User Info:</strong>
            <pre className="mt-2 text-xs">
              {JSON.stringify({
                id: user.id,
                email: user.email,
                name: user.name,
                is_admin: user.is_admin,
                profile_completed: user.profile_completed,
                created_at: user.created_at
              }, null, 2)}
            </pre>
          </div>
        )} */}
        
        {/* Welcome Section */}
        <div className="text-center mb-8">
          <div className="max-w-md mx-auto bg-wellness-light-card dark:bg-slate-800 rounded-xl shadow-md overflow-hidden md:max-w-2xl transition-colors duration-200 border border-wellness-light-border dark:border-slate-600">
            <div className="p-8">
              <div className="uppercase tracking-wide text-sm text-indigo-500 dark:text-blue-400 font-semibold transition-colors duration-200">
                Welcome to
              </div>
              <h2 className="block mt-1 text-lg leading-tight font-medium text-wellness-light-text dark:text-slate-100 transition-colors duration-200">
                WellnessWay Diet Planner
              </h2>
              <p className="mt-2 text-wellness-light-textSecondary dark:text-slate-400 transition-colors duration-200">
                AI-powered personalized diet planning to help you achieve your health goals.
              </p>
              <div className="mt-6">
                {user && !user.profile_completed ? (
                  // Show only profile setup button if profile is incomplete
                  <Link 
                    to="/profile-setup"
                    className="bg-indigo-500 hover:bg-indigo-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors duration-200"
                  >
                    Complete Profile Setup
                  </Link>
                ) : user && user.profile_completed ? (
                  // Show both buttons if profile is complete
                  <>
                    <Link 
                      to="/profile-setup"
                      className="bg-indigo-500 hover:bg-indigo-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors duration-200 mr-4"
                    >
                      Edit Profile
                    </Link>
                    <Link 
                      to="/diet-plans"
                      className="bg-green-500 hover:bg-green-700 dark:bg-emerald-600 dark:hover:bg-emerald-700 text-white font-bold py-2 px-4 rounded transition-colors duration-200"
                    >
                      View Diet Plans
                    </Link>
                  </>
                ) : (
                  // Show generic buttons if user status is unknown
                  <>
                    <Link 
                      to="/profile-setup"
                      className="bg-indigo-500 hover:bg-indigo-700 dark:bg-blue-600 dark:hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors duration-200 mr-4"
                    >
                      Complete Profile Setup
                    </Link>
                    <span 
                      className="bg-wellness-light-textMuted dark:bg-slate-600 text-white font-bold py-2 px-4 rounded cursor-not-allowed transition-colors duration-200"
                      title="Complete your profile first"
                    >
                      View Diet Plans
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* User Dashboard Section */}
        <div className="max-w-4xl mx-auto">
          <UserDashboard />
        </div>
      </div>
    </main>
  );
}

export default App;