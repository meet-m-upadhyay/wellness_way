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
    <div className="mb-12">
      {/* Desktop Stepper */}
      <nav aria-label="Progress" className="hidden sm:block">
        <ol className="flex items-center justify-between w-full">
          {steps.map((step, index) => {
            const isCompleted = index < currentStepIndex;
            const isCurrent = index === currentStepIndex;
            const isClickable = index <= currentStepIndex || isEditMode;

            return (
              <li key={step.id} className={`relative ${index !== steps.length - 1 ? 'flex-1' : ''}`}>
                <div className="flex items-center group">
                  <button
                    onClick={() => isClickable ? goToStep(step.id as SetupStep) : undefined}
                    disabled={!isClickable}
                    className={`relative flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-300 ${isCompleted
                      ? 'bg-emerald-500 border-emerald-500 text-white'
                      : isCurrent
                        ? 'border-emerald-500 text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20 ring-4 ring-emerald-500/10'
                        : isClickable
                          ? 'border-neutral-300 dark:border-neutral-700 text-neutral-500 hover:border-emerald-400 hover:text-emerald-500'
                          : 'border-neutral-200 dark:border-neutral-800 text-neutral-300 dark:text-neutral-700 cursor-not-allowed'
                      }`}
                  >
                    {isCompleted ? (
                      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <span className="text-sm font-bold">{index + 1}</span>
                    )}
                  </button>

                  <div className="ml-4 absolute -bottom-8 left-1/2 -translate-x-1/2 whitespace-nowrap">
                    <span className={`text-xs font-bold uppercase tracking-wider ${isCurrent ? 'text-emerald-600 dark:text-emerald-400' : 'text-neutral-500 dark:text-neutral-400'
                      }`}>
                      {step.title}
                    </span>
                  </div>

                  {index !== steps.length - 1 && (
                    <div className="flex-1 px-4">
                      <div className={`h-0.5 w-full rounded-full transition-colors duration-500 ${isCompleted ? 'bg-emerald-500' : 'bg-neutral-200 dark:bg-neutral-800'
                        }`} />
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      </nav>

      {/* Mobile Stepper */}
      <div className="sm:hidden space-y-4">
        <div className="flex items-center justify-between text-xs font-bold uppercase tracking-widest text-neutral-500">
          <span>Step {currentStepIndex + 1} of {steps.length}</span>
          <span className="text-emerald-600">{steps[currentStepIndex].title}</span>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {steps.map((_, index) => (
            <div
              key={index}
              className={`h-1.5 rounded-full transition-all duration-300 ${index <= currentStepIndex ? 'bg-emerald-500' : 'bg-neutral-200 dark:bg-neutral-800'
                }`}
            />
          ))}
        </div>
      </div>
    </div>
  );

  const renderReviewStep = () => (
    <div className="max-w-4xl mx-auto space-y-8 animate-slide-up">
      <div className="text-center space-y-2">
        <h2 className="text-3xl font-bold text-neutral-900 dark:text-white">
          Ready to finalize?
        </h2>
        <p className="text-neutral-500 dark:text-neutral-400">
          Take a moment to ensure everything looks correct before we build your plan.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
        {/* Basic Info Summary Card */}
        <div className="bg-white dark:bg-neutral-900 rounded-3xl p-8 border border-neutral-200 dark:border-neutral-800 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-4">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white">Basic Info</h3>
            <button
              onClick={() => goToStep('basic')}
              className="text-emerald-600 hover:text-emerald-700 font-bold text-sm uppercase tracking-wider"
            >
              Edit
            </button>
          </div>
          {profileData.userProfile && (
            <div className="grid grid-cols-2 gap-y-4 gap-x-6 text-sm text-left">
              <div>
                <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Name</p>
                <p className="font-semibold text-neutral-900 dark:text-white">{profileData.userProfile.name}</p>
              </div>
              <div>
                <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Age</p>
                <p className="font-semibold text-neutral-900 dark:text-white">{profileData.userProfile.age} yrs</p>
              </div>
              <div>
                <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Gender</p>
                <p className="font-semibold text-neutral-900 dark:text-white capitalize">{profileData.userProfile.gender}</p>
              </div>
              <div>
                <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Activity</p>
                <p className="font-semibold text-neutral-900 dark:text-white capitalize">{profileData.userProfile.activity_level.replace('_', ' ')}</p>
              </div>
              <div>
                <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Height</p>
                <p className="font-semibold text-neutral-900 dark:text-white">{profileData.userProfile.height_cm} cm</p>
              </div>
              <div>
                <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Weight</p>
                <p className="font-semibold text-neutral-900 dark:text-white">{profileData.userProfile.weight_kg} kg</p>
              </div>
            </div>
          )}
        </div>

        {/* Health Goals Summary Card */}
        <div className="bg-white dark:bg-neutral-900 rounded-3xl p-8 border border-neutral-200 dark:border-neutral-800 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-4">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white">Health Goals</h3>
            <button
              onClick={() => goToStep('goals')}
              className="text-emerald-600 hover:text-emerald-700 font-bold text-sm uppercase tracking-wider"
            >
              Edit
            </button>
          </div>
          {profileData.healthGoals && (
            <div className="grid grid-cols-2 gap-y-4 gap-x-6 text-sm text-left">
              <div className="col-span-2">
                <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Primary Goal</p>
                <p className="font-semibold text-neutral-900 dark:text-white capitalize">{profileData.healthGoals.primary_goal.replace('_', ' ')}</p>
              </div>
              {profileData.healthGoals.target_weight_kg && (
                <div>
                  <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Target Weight</p>
                  <p className="font-semibold text-neutral-900 dark:text-white">{profileData.healthGoals.target_weight_kg} kg</p>
                </div>
              )}
              {profileData.healthGoals.timeline_weeks && (
                <div>
                  <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1">Timeline</p>
                  <p className="font-semibold text-neutral-900 dark:text-white">{profileData.healthGoals.timeline_weeks} weeks</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Preferences Summary Card */}
        <div className="md:col-span-2 bg-white dark:bg-neutral-900 rounded-3xl p-8 border border-neutral-200 dark:border-neutral-800 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-neutral-100 dark:border-neutral-800 pb-4">
            <h3 className="text-lg font-bold text-neutral-900 dark:text-white">Diet & Restrictions</h3>
            <button
              onClick={() => goToStep('preferences')}
              className="text-emerald-600 hover:text-emerald-700 font-bold text-sm uppercase tracking-wider"
            >
              Edit
            </button>
          </div>
          {profileData.dietPreferences && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm text-left">
              <div className="space-y-4">
                <div>
                  <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1.5">Dietary Style</p>
                  <p className="font-semibold text-neutral-900 dark:text-white capitalize">{profileData.dietPreferences.diet_type}</p>
                </div>
                {profileData.dietPreferences.budget_constraints && (
                  <div>
                    <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-1.5">Budget</p>
                    <p className="font-semibold text-neutral-900 dark:text-white">{profileData.dietPreferences.budget_constraints}</p>
                  </div>
                )}
              </div>
              <div className="space-y-4">
                {profileData.dietPreferences.allergies.length > 0 && (
                  <div>
                    <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-2">Allergies</p>
                    <div className="flex flex-wrap gap-2">
                      {profileData.dietPreferences.allergies.map(allergy => (
                        <span key={allergy} className="px-3 py-1 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-full text-[11px] font-bold uppercase tracking-wider">
                          {allergy}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {profileData.dietPreferences.foods_to_avoid.length > 0 && (
                  <div>
                    <p className="text-neutral-500 uppercase tracking-widest text-[10px] font-bold mb-2">Avoid</p>
                    <div className="flex flex-wrap gap-2">
                      {profileData.dietPreferences.foods_to_avoid.map(food => (
                        <span key={food} className="px-3 py-1 bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400 rounded-full text-[11px] font-bold uppercase tracking-wider">
                          {food}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {error && <ErrorMessage message={error} className="mb-8" />}

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4">
        <button
          onClick={goBack}
          disabled={isLoading}
          className="w-full sm:w-auto px-10 py-4 font-bold text-neutral-500 hover:text-neutral-700 transition-colors disabled:opacity-50"
        >
          Go Back
        </button>
        <button
          onClick={handleFinalSubmit}
          disabled={isLoading}
          className="w-full sm:w-auto px-12 py-4 bg-emerald-600 text-white rounded-2xl font-bold shadow-lg shadow-emerald-500/20 hover:bg-emerald-700 hover:shadow-emerald-500/40 transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-3"
        >
          {isLoading ? (
            <>
              <LoadingSpinner size="sm" className="opacity-80" message='' />
              <span>{isEditMode ? 'Updating...' : 'Building Plan...'}</span>
            </>
          ) : (
            <span>{isEditMode ? 'Save Changes' : 'Build My Plan'}</span>
          )}
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-wellness-light-bg dark:bg-wellness-dark-bg py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-10 animate-fade-in">
        {/* Header Section */}
        <div className="text-center space-y-3">
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-neutral-900 dark:text-white">
            {isEditMode ? 'Edit Your Profile' : 'Setting up your journey'}
          </h1>
          <p className="max-w-2xl mx-auto text-lg text-neutral-500 dark:text-neutral-400">
            {isEditMode
              ? 'Refine your information to keep your diet plan perfectly aligned with your goals.'
              : 'Tell us a bit about yourself so we can curate a nutrition plan that truly fits your lifestyle.'
            }
          </p>
        </div>

        {isInitialLoading ? (
          <div className="flex flex-col items-center justify-center py-20 space-y-4">
            <LoadingSpinner size="lg" message='' />
            <p className="text-sm text-neutral-500 font-medium">Loading your profile...</p>
          </div>
        ) : (
          <div className="space-y-10">
            {renderProgressBar()}

            <div className="transition-all duration-300 ease-in-out">
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
                  userProfile={profileData.userProfile}
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
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfileSetup;