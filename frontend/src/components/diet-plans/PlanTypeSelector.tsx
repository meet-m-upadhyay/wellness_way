import React, { useState } from 'react';
import Card from '../ui/Card';
import Button from '../ui/Button';

interface PlanTypeSelectorProps {
  selectedType: 'daily' | 'weekly' | null;
  onSelect: (type: 'daily' | 'weekly') => void;
  onGenerate: (options?: { targetDate?: string; startDate?: string }) => void;
  isLoading?: boolean;
}

export const PlanTypeSelector: React.FC<PlanTypeSelectorProps> = ({
  selectedType,
  onSelect,
  onGenerate,
  isLoading = false,
}) => {
  const [targetDate, setTargetDate] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');

  // Get today's date in YYYY-MM-DD format for min date
  const today = new Date().toISOString().split('T')[0];

  // Get next Monday for weekly plan default
  const getNextMonday = () => {
    const date = new Date();
    const day = date.getDay();
    const daysUntilMonday = day === 0 ? 1 : 8 - day; // If Sunday, next day is Monday
    date.setDate(date.getDate() + daysUntilMonday);
    return date.toISOString().split('T')[0];
  };

  const handleGenerate = () => {
    const options: { targetDate?: string; startDate?: string } = {};

    if (selectedType === 'daily' && targetDate) {
      options.targetDate = targetDate;
    } else if (selectedType === 'weekly' && startDate) {
      options.startDate = startDate;
    }

    onGenerate(options);
  };

  return (
    <Card className="max-w-4xl mx-auto">
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-left">Choose Your Diet Plan Type</h2>
        <p className="text-gray-600 dark:text-gray-300 mb-8 text-left">
          Select the type of diet plan you'd like to generate based on your profile and goals.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Daily Plan Option */}
          <div
            className={`border-2 rounded-lg p-6 cursor-pointer transition-all ${selectedType === 'daily'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 bg-white dark:bg-gray-800'
              }`}
            onClick={() => onSelect('daily')}
          >
            <div className="flex items-center mb-4">
              <div className={`w-4 h-4 rounded-full border-2 mr-3 ${selectedType === 'daily'
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-300 dark:border-gray-600'
                }`}>
                {selectedType === 'daily' && (
                  <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                )}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Daily Plan</h3>
            </div>

            <div className="space-y-3">
              <p className="text-gray-600 dark:text-gray-300">
                Get a complete meal plan for a single day with breakfast, lunch, dinner, and snacks.
              </p>

              {/* Date Input for Daily Plan */}
              {selectedType === 'daily' && (
                <div className="mt-4">
                  <label htmlFor="target-date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Target Date (optional)
                  </label>
                  <input
                    type="date"
                    id="target-date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    min={today}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Leave blank to generate for today
                  </p>
                </div>
              )}

              <div className="space-y-2">
                <h4 className="font-medium text-gray-900 dark:text-white">Perfect for:</h4>
                <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                  <li>• Trying out new meal ideas</li>
                  <li>• Planning today's meals</li>
                  <li>• Quick meal inspiration</li>
                  <li>• Testing dietary preferences</li>
                </ul>
              </div>

              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-3 mt-4">
                <p className="text-sm text-green-800 dark:text-green-300">
                  <span className="font-medium">⚡ Quick:</span> Generated in seconds
                </p>
              </div>
            </div>
          </div>

          {/* Weekly Plan Option */}
          <div
            className={`border-2 rounded-lg p-6 cursor-pointer transition-all ${selectedType === 'weekly'
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-400'
                : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 bg-white dark:bg-gray-800'
              }`}
            onClick={() => onSelect('weekly')}
          >
            <div className="flex items-center mb-4">
              <div className={`w-4 h-4 rounded-full border-2 mr-3 ${selectedType === 'weekly'
                  ? 'border-blue-500 bg-blue-500'
                  : 'border-gray-300 dark:border-gray-600'
                }`}>
                {selectedType === 'weekly' && (
                  <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                )}
              </div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Weekly Plan</h3>
            </div>

            <div className="space-y-3">
              <p className="text-gray-600 dark:text-gray-300">
                Get a comprehensive 7-day meal plan with varied meals and balanced nutrition throughout the week.
              </p>

              {/* Date Input for Weekly Plan */}
              {selectedType === 'weekly' && (
                <div className="mt-4">
                  <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Start Date (optional)
                  </label>
                  <input
                    type="date"
                    id="start-date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    min={today}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 dark:focus:ring-blue-400 focus:border-blue-500 dark:focus:border-blue-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                    placeholder={getNextMonday()}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Leave blank to start from next Monday ({new Date(getNextMonday()).toLocaleDateString()})
                  </p>
                </div>
              )}

              <div className="space-y-2">
                <h4 className="font-medium text-gray-900 dark:text-white">Perfect for:</h4>
                <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1">
                  <li>• Meal prep planning</li>
                  <li>• Grocery shopping lists</li>
                  <li>• Long-term nutrition goals</li>
                  <li>• Consistent eating habits</li>
                </ul>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3 mt-4">
                <p className="text-sm text-blue-800 dark:text-blue-300">
                  <span className="font-medium">📊 Comprehensive:</span> Balanced weekly nutrition
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Generation Buttons */}
        <div className="text-center space-y-4">
          <div>
            <Button
              onClick={handleGenerate}
              disabled={!selectedType || isLoading}
              size="lg"
              className="px-8 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Generating {selectedType} plan...
                </>
              ) : (
                <>
                  🧠 Generate {selectedType ? selectedType.charAt(0).toUpperCase() + selectedType.slice(1) : ''} Plan
                </>
              )}
            </Button>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Uses ML templates + deterministic nutrition calculations
            </p>
          </div>

          {selectedType && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
              {selectedType === 'daily'
                ? `This will create a personalized meal plan for ${targetDate ? new Date(targetDate).toLocaleDateString() : 'today'}`
                : `This will create a personalized meal plan starting ${startDate ? new Date(startDate).toLocaleDateString() : 'next Monday'}`
              }
            </p>
          )}
        </div>

        {/* Additional Info */}
        <div className="mt-8 bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2 text-left">💡 How it works</h4>
          <ul className="text-sm text-gray-600 dark:text-gray-300 space-y-1 text-left">
            <li>• Plans are generated based on your profile, goals, and preferences</li>
            <li>• All meals respect your dietary restrictions and allergies</li>
            <li>• Nutrition targets are calculated for your specific needs</li>
            <li>• You can regenerate individual meals or entire days if needed</li>
          </ul>
        </div>
      </div>
    </Card>
  );
};

export default PlanTypeSelector;