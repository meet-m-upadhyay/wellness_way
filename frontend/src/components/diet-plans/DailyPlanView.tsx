import React from 'react';
import { LegacyDailyPlan } from '../../services/api';
import MealCard from './MealCard';
import NutritionSummary from './NutritionSummary';
import Button from '../ui/Button';

interface DailyPlanViewProps {
  plan: LegacyDailyPlan;
  onRegenerateMeal?: (mealType: string) => void;
  onRegenerateDay?: () => void;
  regeneratingMeal?: string | null;
  isRegeneratingDay?: boolean;
  showRegenerate?: boolean;
}

export const DailyPlanView: React.FC<DailyPlanViewProps> = ({
  plan,
  onRegenerateMeal,
  onRegenerateDay,
  regeneratingMeal,
  isRegeneratingDay = false,
  showRegenerate = true,
}) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const meals = [
    { type: 'breakfast', meal: plan.meals.breakfast },
    { type: 'lunch', meal: plan.meals.lunch },
    { type: 'dinner', meal: plan.meals.dinner },
  ];

  // Add snacks if they exist
  if (plan.meals.snacks) {
    if (Array.isArray(plan.meals.snacks)) {
      plan.meals.snacks.forEach((snack, index) => {
        meals.push({ type: `snack_${index + 1}`, meal: snack });
      });
    } else {
      meals.push({ type: 'snack', meal: plan.meals.snacks });
    }
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div className="text-center sm:text-left">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white flex items-center justify-center sm:justify-start">
              <span className="text-2xl mr-2">🍽️</span>
              Daily Meal Plan
            </h1>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300 mt-2 flex items-center justify-center sm:justify-start">
              <span className="text-lg mr-2">📅</span>
              {formatDate(plan.date)}
            </p>
          </div>
          {showRegenerate && onRegenerateDay && (
            <button
              onClick={onRegenerateDay}
              disabled={isRegeneratingDay}
              className="flex items-center justify-center px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors w-full sm:w-auto"
            >
              {isRegeneratingDay ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="hidden sm:inline">Regenerating Day...</span>
                  <span className="sm:hidden">Regenerating...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  <span className="hidden sm:inline">Regenerate Day</span>
                  <span className="sm:hidden">Regenerate</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Nutrition Summary */}
      <div className="mb-8">
        <NutritionSummary
          nutrition={plan.daily_nutrition}
          title="Daily Nutrition Totals"
        />
      </div>

      {/* Meals Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 mb-8">
        {meals.map(({ type, meal }) => (
          <MealCard
            key={type}
            meal={meal}
            mealType={type}
            onRegenerate={onRegenerateMeal ? () => onRegenerateMeal(type) : undefined}
            isRegenerating={regeneratingMeal === type}
            showRegenerate={showRegenerate}
          />
        ))}
      </div>

      {/* Meal Timing Suggestions */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="text-base font-medium text-blue-900 dark:text-blue-100 mb-4 flex items-center">
          <span className="text-xl mr-2">🕐</span>
          Suggested Meal Timing
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center">
            <span className="text-2xl mr-3">🌅</span>
            <div>
              <p className="font-medium text-blue-900 dark:text-blue-100 text-left">Breakfast</p>
              <p className="text-blue-700 dark:text-blue-300 text-left">7:00 - 9:00 AM</p>
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-2xl mr-3">🌞</span>
            <div>
              <p className="font-medium text-blue-900 dark:text-blue-100 text-left">Lunch</p>
              <p className="text-blue-700 dark:text-blue-300 text-left">12:00 - 2:00 PM</p>
            </div>
          </div>
          <div className="flex items-center">
            <span className="text-2xl mr-3">🌙</span>
            <div>
              <p className="font-medium text-blue-900 dark:text-blue-100 text-left">Dinner</p>
              <p className="text-blue-700 dark:text-blue-300 text-left">6:00 - 8:00 PM</p>
            </div>
          </div>
        </div>
        {plan.meals.snacks && (
          <div className="mt-4 pt-4 border-t border-blue-200 dark:border-blue-800">
            <div className="flex items-center">
              <span className="text-2xl mr-3">🍎</span>
              <div>
                <p className="font-medium text-blue-900 dark:text-blue-100">Snacks</p>
                <p className="text-blue-700 dark:text-blue-300">Between meals as needed</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Preparation Tips */}
      <div className="mt-6 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
        <h3 className="text-base font-medium text-green-900 dark:text-green-100 mb-4 flex items-center">
          <span className="text-xl mr-2">💡</span>
          Preparation Tips
        </h3>
        <ul className="text-sm text-green-800 dark:text-green-200 space-y-2">
          <li>• Review all recipes and create a shopping list before grocery shopping</li>
          <li>• Prep ingredients in advance when possible (wash vegetables, marinate proteins)</li>
          <li>• Cook grains and proteins in batches to save time</li>
          <li>• Stay hydrated throughout the day - aim for 8-10 glasses of water</li>
          <li>• Listen to your body and adjust portion sizes as needed</li>
        </ul>
      </div>
    </div>
  );
};

export default DailyPlanView;