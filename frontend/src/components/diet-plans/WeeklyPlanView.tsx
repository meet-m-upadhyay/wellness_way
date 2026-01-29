import React, { useState } from 'react';
import { LegacyWeeklyPlan } from '../../services/api';
import DailyPlanView from './DailyPlanView';
import NutritionSummary from './NutritionSummary';
import Button from '../ui/Button';

interface WeeklyPlanViewProps {
  plan: LegacyWeeklyPlan;
  onRegenerateMeal?: (dayIndex: number, mealType: string) => void;
  onRegenerateDay?: (dayIndex: number) => void;
  onRegenerateWeek?: () => void;
  regeneratingMeal?: { dayIndex: number; mealType: string } | null;
  regeneratingDay?: number | null;
  isRegeneratingWeek?: boolean;
  showRegenerate?: boolean;
}

export const WeeklyPlanView: React.FC<WeeklyPlanViewProps> = ({
  plan,
  onRegenerateMeal,
  onRegenerateDay,
  onRegenerateWeek,
  regeneratingMeal,
  regeneratingDay,
  isRegeneratingWeek = false,
  showRegenerate = true,
}) => {
  const [selectedDayIndex, setSelectedDayIndex] = useState(0);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatWeekRange = (startDate: string) => {
    const start = new Date(startDate);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    
    return `${start.toLocaleDateString('en-US', { 
      month: 'long', 
      day: 'numeric' 
    })} - ${end.toLocaleDateString('en-US', { 
      month: 'long', 
      day: 'numeric', 
      year: 'numeric' 
    })}`;
  };

  const selectedDay = plan.days[selectedDayIndex];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div className="text-center sm:text-left">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white flex items-center justify-center sm:justify-start">
              <span className="text-2xl mr-2">📅</span>
              Weekly Meal Plan
            </h1>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300 mt-2 flex items-center justify-center sm:justify-start">
              <span className="text-lg mr-2">🗓️</span>
              {formatWeekRange(plan.start_date)}
            </p>
          </div>
          {showRegenerate && onRegenerateWeek && (
            <button
              onClick={onRegenerateWeek}
              disabled={isRegeneratingWeek}
              className="flex items-center justify-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors w-full sm:w-auto"
            >
              {isRegeneratingWeek ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="hidden sm:inline">Regenerating Week...</span>
                  <span className="sm:hidden">Regenerating...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span className="hidden sm:inline">Regenerate Week</span>
                  <span className="sm:hidden">Regenerate</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Weekly Nutrition Summary */}
      <div className="mb-8">
        <NutritionSummary
          nutrition={plan.weekly_nutrition}
          title="Weekly Nutrition Averages"
        />
      </div>

      {/* Day Navigation */}
      <div className="mb-6 sm:mb-8">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-2 sm:space-x-8 overflow-x-auto px-2 sm:px-0">
            {plan.days.map((day, index) => (
              <button
                key={index}
                onClick={() => setSelectedDayIndex(index)}
                className={`whitespace-nowrap py-3 sm:py-4 px-2 sm:px-1 border-b-2 font-medium text-xs sm:text-sm transition-colors min-w-0 flex-shrink-0 ${
                  selectedDayIndex === index
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <div className="text-center">
                  <div className="font-semibold">
                    <span className="hidden sm:inline">{formatDate(day.date)}</span>
                    <span className="sm:hidden">{new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' })}</span>
                  </div>
                  <div className="text-xs mt-1">
                    {Math.round(day.daily_nutrition.total_calories)} cal
                  </div>
                </div>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Selected Day Content */}
      {selectedDay && (
        <DailyPlanView
          plan={selectedDay}
          onRegenerateMeal={onRegenerateMeal ? (mealType) => onRegenerateMeal(selectedDayIndex, mealType) : undefined}
          onRegenerateDay={onRegenerateDay ? () => onRegenerateDay(selectedDayIndex) : undefined}
          regeneratingMeal={
            regeneratingMeal?.dayIndex === selectedDayIndex ? regeneratingMeal.mealType : null
          }
          isRegeneratingDay={regeneratingDay === selectedDayIndex}
          showRegenerate={showRegenerate}
        />
      )}

      {/* Week Overview */}
      <div className="mt-8 sm:mt-12 bg-gray-50 dark:bg-gray-800 rounded-lg p-4 sm:p-6">
        <div className="text-center sm:text-left mb-4 sm:mb-6">
          <h3 className="text-base font-medium text-gray-900 dark:text-white flex items-center justify-center sm:justify-start">
            <span className="text-xl mr-2">📊</span>
            Week at a Glance
          </h3>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3 sm:gap-4">
          {plan.days.map((day, index) => (
            <div
              key={index}
              className={`bg-white dark:bg-gray-700 rounded-lg p-3 sm:p-4 border-2 cursor-pointer transition-all ${
                selectedDayIndex === index
                  ? 'border-blue-500 shadow-md'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
              }`}
              onClick={() => setSelectedDayIndex(index)}
            >
              <div className="text-center">
                <h4 className="font-medium text-gray-900 dark:text-white mb-2 text-sm sm:text-base">
                  <span className="hidden sm:inline">{formatDate(day.date)}</span>
                  <span className="sm:hidden">{new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
                </h4>
                <div className="space-y-1 text-xs sm:text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Calories:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{Math.round(day.daily_nutrition.total_calories)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Protein:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{Math.round(day.daily_nutrition.total_protein_g)}g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Carbs:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{Math.round(day.daily_nutrition.total_carbs_g)}g</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">Fat:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{Math.round(day.daily_nutrition.total_fat_g)}g</span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Weekly Tips */}
      <div className="mt-6 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="text-base font-medium text-blue-900 dark:text-blue-100 mb-4 flex items-center">
          <span className="text-xl mr-2">💡</span>
          Weekly Planning Tips
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800 dark:text-blue-200">
          <div>
            <h4 className="font-medium mb-2">Meal Prep Strategy:</h4>
            <ul className="space-y-1">
              <li>• Sunday: Plan and shop for the week</li>
              <li>• Batch cook proteins and grains</li>
              <li>• Prep vegetables and snacks in advance</li>
              <li>• Use similar ingredients across multiple days</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Flexibility Tips:</h4>
            <ul className="space-y-1">
              <li>• Swap similar meals between days if needed</li>
              <li>• Adjust portion sizes based on hunger</li>
              <li>• Have backup simple meals ready</li>
              <li>• Listen to your body and preferences</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeeklyPlanView;