import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useAppContext } from '../context/AppContext';
import { apiClient, UserProfile, HealthGoals, DietPreferences, CompleteProfile } from '../services/api';
import BasicInfoForm from './forms/BasicInfoForm';
import GoalsForm from './forms/GoalsForm';
import PreferencesForm from './forms/PreferencesForm';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';

type SetupStep = 'basic' | 'goals' | 'preferences' | 'review';

interface ProfileData {
  userProfile?: UserProfile;
  healthGoals?: HealthGoals;
  dietPreferences?: DietPreferences;
}

export const ProfileSetup: React.FC = () => {
  const { user, refreshUserInfo } = useAuth();
  const { dispatch, state } = useAppContext();
  const navigate = useNavigate();
  
  const [currentStep, setCurrentStep] = useState<SetupStep>('basic');
  const [profileData, setProfileData] = useState<ProfileData>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const loadedUserIdRef = useRef<string | null>(null);

  // Load existing user data if available (for edit mode)
  useEffect(() => {
    const loadExistingData = async () => {
      // Only load if user ID has changed
      if (!user || loadedUserIdRef.current === user.id) {
        return;
      }

      // Reset all form state when user changes
      setCurrentStep('basic');
      setProfileData({});
      setIsLoading(false);
      setError(null);
      setIsEditMode(false);
      loadedUserIdRef.current = user.id;

      if (user.profile_completed) {
        setIsEditMode(true);
        try {
          // Fetch existing profile data for edit mode
          const response = await apiClient.getCompleteProfile(user.id);
          if (response.data) {
            setProfileData({
              userProfile: response.data.profile,
              healthGoals: response.data.goals,
              dietPreferences: response.data.preferences,
            });
          } else if (response.error) {
            console.error('Failed to load existing profile:', response.error);
            setError('Failed to load existing profile data');
          }
        } catch (err) {
          console.error('Error loading existing profile:', err);
          setError('Failed to load existing profile data');
        }
      }
      setIsInitialLoading(false);
    };

    loadExistingData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, user?.profile_completed]);

  const steps = [
    { id: 'basic', title: 'Basic Info', description: 'Personal information' },
    { id: 'goals', title: 'Health Goals', description: 'What you want to achieve' },
    { id: 'preferences', title: 'Diet Preferences', description: 'Food preferences and restrictions' },
    { id: 'review', title: 'Review', description: 'Confirm your information' },
  ];

  const currentStepIndex = steps.findIndex(step => step.id === currentStep);

  const handleBasicInfoSubmit = (data: UserProfile) => {
    setProfileData(prev => ({ ...prev, userProfile: data }));
    setCurrentStep('goals');
  };

  const handleGoalsSubmit = (data: HealthGoals) => {
    setProfileData(prev => ({ ...prev, healthGoals: data }));
    setCurrentStep('preferences');
  };

  const handlePreferencesSubmit = (data: DietPreferences) => {
    setProfileData(prev => ({ ...prev, dietPreferences: data }));
    setCurrentStep('review');
  };

  const handleFinalSubmit = async () => {
    if (!profileData.userProfile || !profileData.healthGoals || !profileData.dietPreferences) {
      setError('Missing required profile data');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      if (isEditMode && state.user) {
        // Update existing profile
        const updatePromises = [];
        
        // Update profile
        updatePromises.push(apiClient.updateUserProfile(state.user.id, profileData.userProfile));
        
        // Update goals
        updatePromises.push(apiClient.updateHealthGoals(state.user.id, profileData.healthGoals));
        
        // Update preferences
        updatePromises.push(apiClient.updateDietPreferences(state.user.id, profileData.dietPreferences));

        const responses = await Promise.all(updatePromises);
        
        // Check for errors
        const errors = responses.filter(response => response.error);
        if (errors.length > 0) {
          throw new Error(errors[0].error);
        }

        // Update global state
        dispatch({
          type: 'SET_USER',
          payload: {
            id: state.user.id,
            profile: profileData.userProfile,
            goals: profileData.healthGoals,
            preferences: profileData.dietPreferences,
          },
        });

        // Regenerate health context document with updated data
        await apiClient.generateHealthContext(state.user.id);

        // Navigate to home page after successful update
        navigate('/');
      } else {
        // Create new profile
        const completeProfile: CompleteProfile = {
          profile: profileData.userProfile,
          goals: profileData.healthGoals,
          preferences: profileData.dietPreferences,
        };

        const response = await apiClient.createCompleteProfile(completeProfile);
        
        if (response.error) {
          throw new Error(response.error);
        }

        if (response.data) {
          // Refresh user information from server to get updated profile_completed status
          await refreshUserInfo();

          // Update global state with user ID and profile data
          dispatch({
            type: 'SET_USER',
            payload: {
              id: response.data.user_id,
              profile: response.data.profile,
              goals: response.data.goals,
              preferences: response.data.preferences,
            },
          });

          // Generate health context document
          await apiClient.generateHealthContext(response.data.user_id);

          // Navigate to home page after successful profile creation
          navigate('/');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${isEditMode ? 'update' : 'create'} profile`);
    } finally {
      setIsLoading(false);
    }
  };

  const goToStep = (step: SetupStep) => {
    setCurrentStep(step);
  };

  const goBack = () => {
    const prevStepIndex = currentStepIndex - 1;
    if (prevStepIndex >= 0) {
      setCurrentStep(steps[prevStepIndex].id as SetupStep);
    }
  };

  const renderProgressBar = () => (
    <div className="mb-6 sm:mb-8">
      {/* Desktop Progress Bar */}
      <div className="hidden sm:flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = index < currentStepIndex;
          const isCurrent = index === currentStepIndex;
          const isClickable = index <= currentStepIndex || isEditMode;
          
          return (
            <div key={step.id} className="flex items-center flex-1">
              <div className="flex items-center">
                <button
                  onClick={() => isClickable ? goToStep(step.id as SetupStep) : undefined}
                  disabled={!isClickable}
                  className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300 transform ${
                    isCompleted
                      ? 'bg-green-500 border-green-500 text-white shadow-lg hover:shadow-xl hover:scale-105'
                      : isCurrent
                      ? 'bg-blue-600 border-blue-600 text-white shadow-lg ring-4 ring-blue-200 dark:ring-blue-800 animate-pulse'
                      : isClickable
                      ? 'border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 hover:shadow-md hover:scale-105'
                      : 'border-gray-200 dark:border-gray-700 text-gray-300 dark:text-gray-600 bg-gray-50 dark:bg-gray-900 cursor-not-allowed'
                  } ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                >
                  {isCompleted ? (
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <span className="text-sm font-bold">{index + 1}</span>
                  )}
                </button>
                <div className="ml-4 min-w-0 flex-1">
                  <button
                    onClick={() => isClickable ? goToStep(step.id as SetupStep) : undefined}
                    disabled={!isClickable}
                    className={`text-left transition-all duration-200 ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed'}`}
                  >
                    <p className={`text-sm font-semibold transition-colors duration-200 ${
                      isCompleted
                        ? 'text-green-600 dark:text-green-400'
                        : isCurrent
                        ? 'text-blue-600 dark:text-blue-400'
                        : isClickable
                        ? 'text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400'
                        : 'text-gray-400 dark:text-gray-600'
                    }`}>
                      {step.title}
                      {isCompleted && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300">
                          Complete
                        </span>
                      )}
                      {isCurrent && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300">
                          Current
                        </span>
                      )}
                    </p>
                    <p className={`text-xs mt-1 transition-colors duration-200 ${
                      isCompleted || isCurrent
                        ? 'text-gray-600 dark:text-gray-300'
                        : isClickable
                        ? 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                        : 'text-gray-400 dark:text-gray-600'
                    }`}>
                      {step.description}
                    </p>
                  </button>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div className={`flex-1 h-1 mx-6 rounded-full transition-all duration-500 ${
                  isCompleted 
                    ? 'bg-gradient-to-r from-green-400 to-green-600 shadow-sm' 
                    : index < currentStepIndex 
                    ? 'bg-gradient-to-r from-blue-400 to-blue-600 shadow-sm'
                    : 'bg-gray-200 dark:bg-gray-700'
                }`}>
                  {/* Animated progress line */}
                  {index === currentStepIndex - 1 && (
                    <div className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full animate-pulse"></div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Mobile Progress Bar */}
      <div className="sm:hidden">
        {/* Progress indicator */}
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm font-medium text-gray-900 dark:text-white">
            Step {currentStepIndex + 1} of {steps.length}
          </div>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            {Math.round(((currentStepIndex + 1) / steps.length) * 100)}%
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mb-4">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${((currentStepIndex + 1) / steps.length) * 100}%` }}
          ></div>
        </div>
        
        {/* Current step info */}
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {steps[currentStepIndex].title}
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {steps[currentStepIndex].description}
          </p>
        </div>
        
        {/* Step dots */}
        <div className="flex justify-center space-x-2 mt-4">
          {steps.map((_, index) => (
            <div
              key={index}
              className={`w-2 h-2 rounded-full transition-colors duration-200 ${
                index <= currentStepIndex
                  ? 'bg-blue-600'
                  : 'bg-gray-300 dark:bg-gray-600'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );

  const renderReviewStep = () => (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg p-4 sm:p-6">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-4 sm:mb-6 text-left">
          {isEditMode ? 'Update Your Profile' : 'Review Your Profile'}
        </h2>
        <p className="text-gray-600 dark:text-gray-300 mb-6 sm:mb-8 text-left text-sm sm:text-base">
          {isEditMode 
            ? 'Review your updated information before saving changes.'
            : 'Please review your information before creating your profile.'
          }</p>

        {/* Basic Info Review */}
        <div className="mb-4 sm:mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base sm:text-lg font-medium text-gray-900 dark:text-white">Basic Information</h3>
            <button
              onClick={() => goToStep('basic')}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm px-2 py-1 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
            >
              Edit
            </button>
          </div>
          {profileData.userProfile && (
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 sm:p-4 space-y-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm sm:text-base">
                <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Name:</span> {profileData.userProfile.name}</p>
                <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Age:</span> {profileData.userProfile.age} years</p>
                <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Gender:</span> {profileData.userProfile.gender}</p>
                <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Activity:</span> {profileData.userProfile.activity_level.replace('_', ' ')}</p>
                <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Height:</span> {profileData.userProfile.height_cm} cm</p>
                <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Weight:</span> {profileData.userProfile.weight_kg} kg</p>
                {profileData.userProfile.body_fat_percentage && (
                  <p className="text-gray-900 dark:text-gray-100 sm:col-span-2"><span className="font-medium">Body Fat:</span> {profileData.userProfile.body_fat_percentage}%</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Goals Review */}
        <div className="mb-4 sm:mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base sm:text-lg font-medium text-gray-900 dark:text-white">Health Goals</h3>
            <button
              onClick={() => goToStep('goals')}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm px-2 py-1 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
            >
              Edit
            </button>
          </div>
          {profileData.healthGoals && (
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 sm:p-4 space-y-2">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm sm:text-base">
                <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Goal:</span> {profileData.healthGoals.primary_goal.replace('_', ' ')}</p>
                {profileData.healthGoals.target_weight_kg && (
                  <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Target Weight:</span> {profileData.healthGoals.target_weight_kg} kg</p>
                )}
                {profileData.healthGoals.timeline_weeks && (
                  <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Timeline:</span> {profileData.healthGoals.timeline_weeks} weeks</p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Preferences Review */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base sm:text-lg font-medium text-gray-900 dark:text-white">Diet Preferences</h3>
            <button
              onClick={() => goToStep('preferences')}
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 text-sm px-2 py-1 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors"
            >
              Edit
            </button>
          </div>
          {profileData.dietPreferences && (
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 sm:p-4 space-y-2">
              <div className="space-y-2 text-sm sm:text-base">
                <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Dietary Style:</span> {profileData.dietPreferences.diet_type}</p>
                {profileData.dietPreferences.allergies.length > 0 && (
                  <div className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">Allergies:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {profileData.dietPreferences.allergies.map((allergy, index) => (
                        <span key={index} className="inline-block bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 px-2 py-1 rounded-full text-xs">
                          {allergy}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {profileData.dietPreferences.foods_to_avoid.length > 0 && (
                  <div className="text-gray-900 dark:text-gray-100">
                    <span className="font-medium">Foods to Avoid:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {profileData.dietPreferences.foods_to_avoid.map((food, index) => (
                        <span key={index} className="inline-block bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 px-2 py-1 rounded-full text-xs">
                          {food}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {profileData.dietPreferences.budget_constraints && (
                  <p className="text-gray-900 dark:text-gray-100"><span className="font-medium">Budget:</span> {profileData.dietPreferences.budget_constraints}</p>
                )}
              </div>
            </div>
          )}
        </div>

        {error && <ErrorMessage message={error} className="mb-4 sm:mb-6" />}

        <div className="flex flex-col sm:flex-row justify-between space-y-3 sm:space-y-0 sm:space-x-4">
          <button
            onClick={goBack}
            disabled={isLoading}
            className="w-full sm:w-auto px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 bg-white dark:bg-gray-800 transition-colors"
          >
            Back
          </button>
          <button
            onClick={handleFinalSubmit}
            disabled={isLoading}
            className="w-full sm:w-auto px-8 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center transition-colors"
          >
            {isLoading ? (
              <>
                {isEditMode ? 'Update Profile' : 'Create Profile'}
                <LoadingSpinner size="sm" className="ml-2" message=''/>
              </>
            ) : (
              isEditMode ? 'Update Profile' : 'Create Profile'
            )}
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-4 sm:py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-6 sm:mb-8 text-center">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">
            {isEditMode ? 'Edit Your Profile' : 'Set Up Your Profile'}
          </h1>
          <p className="text-gray-600 dark:text-gray-300 mt-2 text-sm sm:text-base px-2">
            {isEditMode 
              ? 'Update your information to get better personalized recommendations'
              : 'Tell us about yourself to get personalized diet recommendations'
            }
          </p>
        </div>

        {isInitialLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner size="lg" message=''/>
          </div>
        ) : (
          <>
            {renderProgressBar()}

            <div className="px-2 sm:px-0">
              {currentStep === 'basic' && (
                <BasicInfoForm
                  key={user?.id || 'no-user'}
                  initialData={profileData.userProfile}
                  onSubmit={handleBasicInfoSubmit}
                  isLoading={isLoading}
                />
              )}

              {currentStep === 'goals' && (
                <GoalsForm
                  key={user?.id || 'no-user'}
                  initialData={profileData.healthGoals}
                  onSubmit={handleGoalsSubmit}
                  onBack={goBack}
                  isLoading={isLoading}
                />
              )}

              {currentStep === 'preferences' && (
                <PreferencesForm
                  key={user?.id || 'no-user'}
                  initialData={profileData.dietPreferences}
                  onSubmit={handlePreferencesSubmit}
                  onBack={goBack}
                  isLoading={isLoading}
                />
              )}

              {currentStep === 'review' && renderReviewStep()}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ProfileSetup;