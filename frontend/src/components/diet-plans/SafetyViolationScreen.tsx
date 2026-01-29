import React from 'react';
import Button from '../ui/Button';

interface SafetyViolationScreenProps {
  violations: string[];
  onRetry: () => void;
  onGoBack: () => void;
  isRetrying?: boolean;
}

const SafetyViolationScreen: React.FC<SafetyViolationScreenProps> = ({
  violations,
  onRetry,
  onGoBack,
  isRetrying = false
}) => {
  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 flex items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900/30 mb-4">
            <svg
              className="h-10 w-10 text-yellow-600 dark:text-yellow-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Safety Check Failed
          </h2>
          <p className="text-gray-600 dark:text-gray-300">
            The generated diet plan doesn't meet our safety requirements
          </p>
        </div>

        {/* Safety Violations */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Safety Issues Detected:
          </h3>
          <div className="space-y-3">
            {violations.map((violation, index) => (
              <div
                key={index}
                className="flex items-start p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg"
              >
                <div className="flex-shrink-0 mr-3">
                  <svg
                    className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200">
                    {violation.replace('SAFETY VIOLATION: ', '')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Safety Information */}
        <div className="mb-8 p-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
            Why We Have Safety Checks
          </h3>
          <div className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
            <p>
              • <strong>Minimum Calories:</strong> Ensures you get enough energy for basic body functions
            </p>
            <p>
              • <strong>Minimum Protein:</strong> Protects muscle mass and supports healthy metabolism
            </p>
            <p>
              • <strong>Balanced Nutrition:</strong> Prevents nutrient deficiencies and health risks
            </p>
          </div>
        </div>

        {/* What Happens Next */}
        <div className="mb-8 p-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-3">
            What Happens When You Retry
          </h3>
          <div className="space-y-2 text-sm text-green-800 dark:text-green-200">
            <p>
              • Our AI will generate a new plan that meets all safety requirements
            </p>
            <p>
              • The system will automatically adjust portions and add healthy foods if needed
            </p>
            <p>
              • You'll only see plans that are safe and nutritionally balanced
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            onClick={onRetry}
            disabled={isRetrying}
            className="flex items-center justify-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-lg transition-colors"
          >
            {isRetrying ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating New Plan...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Try Again
              </>
            )}
          </Button>
          
          <Button
            onClick={onGoBack}
            variant="outline"
            className="flex items-center justify-center px-6 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Choose Different Plan Type
          </Button>
        </div>

        {/* Help Text */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            If you continue to see safety violations, consider updating your profile with more realistic goals or dietary preferences.
          </p>
        </div>
      </div>
    </div>
  );
};

export default SafetyViolationScreen;