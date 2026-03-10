import React, { useState } from 'react';
import { LegacyMeal } from '../../services/api';
import Card from '../ui/Card';
import Button from '../ui/Button';

interface MealCardProps {
  meal: LegacyMeal;
  mealType: string;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
  showRegenerate?: boolean;
}

export const MealCard: React.FC<MealCardProps> = ({
  meal,
  mealType,
  onRegenerate,
  isRegenerating = false,
  showRegenerate = true,
}) => {
  const [showIngredients, setShowIngredients] = useState(false);
  const [showRecipe, setShowRecipe] = useState(false);

  const formatMealType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  const getMealIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'breakfast':
        return '🌅';
      case 'lunch':
        return '🌞';
      case 'dinner':
        return '🌙';
      case 'snack':
      case 'snacks':
        return '🍎';
      default:
        return '🍽️';
    }
  };

  return (
    <Card className="h-full">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">{getMealIcon(mealType)}</span>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white text-left">{formatMealType(mealType)}</h3>
              <p className="text-sm text-gray-600 dark:text-gray-300 text-left">{meal.name}</p>
            </div>
          </div>
          {showRegenerate && onRegenerate && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onRegenerate()}
                disabled={isRegenerating}
                className="flex items-center bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 border-purple-300 dark:border-purple-700"
                title="Regenerate Meal"
              >
                {isRegenerating ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    ...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    🧠
                  </>
                )}
              </Button>
            </div>
          )}
        </div>

        {/* Nutrition Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{Math.round(meal.nutrition.calories)}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Calories</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{Math.round(meal.nutrition.protein_g)}g</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Protein</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{Math.round(meal.nutrition.carbs_g)}g</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Carbs</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{Math.round(meal.nutrition.fat_g)}g</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">Fat</p>
          </div>
        </div>

        {/* Ingredients Section */}
        <div className="mb-4">
          <button
            onClick={() => setShowIngredients(!showIngredients)}
            className="flex items-center justify-between w-full text-left"
          >
            <h4 className="font-medium text-gray-900 dark:text-white">Ingredients ({meal.ingredients.length})</h4>
            <svg
              className={`w-5 h-5 text-gray-500 dark:text-gray-400 transform transition-transform ${showIngredients ? 'rotate-180' : ''
                }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showIngredients && (
            <div className="mt-3 space-y-1">
              {meal.ingredients.map((ingredient, index) => (
                <div key={index} className="flex items-center text-sm text-gray-600 dark:text-gray-300">
                  <span className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full mr-3 flex-shrink-0"></span>
                  {ingredient}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recipe Section */}
        <div>
          <button
            onClick={() => setShowRecipe(!showRecipe)}
            className="flex items-center justify-between w-full text-left"
          >
            <h4 className="font-medium text-gray-900 dark:text-white text-left">Recipe</h4>
            <svg
              className={`w-5 h-5 text-gray-500 dark:text-gray-400 transform transition-transform ${showRecipe ? 'rotate-180' : ''
                }`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showRecipe && (
            <div className="mt-3 text-left">
              <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed whitespace-pre-line text-left">
                {meal.instructions}
              </p>
            </div>
          )}
        </div>

        {/* Additional Nutrition Info */}
        {meal.nutrition.fiber_g && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600 dark:text-gray-300">Fiber:</span>
              <span className="font-medium text-gray-900 dark:text-white">{Math.round(meal.nutrition.fiber_g)}g</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

export default MealCard;